"""
predictor.py — edina vstopna točka med UI in AI Engine.

UI kliče samo:
    run_scan(progress_cb)  -> ScanResult
    get_last_results()     -> ScanResult | None
    result.market / result.stocks / result.stable / ...
"""

from __future__ import annotations
import gc
import time
from math import ceil
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Callable

import pandas as pd

from config import (NASDAQ100, TRAIN_START, DOWNLOAD_START, MAX_PORTFOLIO,
                    SCAN_CACHE, JOURNAL_FILE, PRED_HISTORY, SECTOR_MAP)
from engine.data    import download_all, get_market_data, download_yahoo
from engine.features import build_cache, get_today_snapshot, get_raw_rows, snapshot_from_rows
from engine.models   import train_models, save_models, load_models, models_are_stale
from engine.ranking  import predict_and_rank, apply_correlation_filter
from engine.explain  import compute_shap_reasons, compute_feature_drift, build_stock_card_reasons
from engine.portfolio import build_portfolio, PortfolioResult
from engine.cache    import (save_scan, load_scan, scan_age_minutes,
                              append_journal, append_prediction_history)

_BATCH_SIZE = 120  # max tickers per batch — keeps peak RAM under ~250 MB on Railway


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class MarketSnapshot:
    spy_ret:  float = 0.0
    qqq_ret:  float = 0.0
    vix:      float = 0.0
    spy_price: float = 0.0
    qqq_price: float = 0.0

@dataclass
class StockSignal:
    ticker:          str   = ''
    sector:          str   = ''
    rating:          str   = 'B'      # A+, A, A-, B+, B, B-, C+
    confidence:      float = 0.0      # 0–100
    stable_score:    float = 0.0      # 0–100
    growth_score:    float = 0.0      # 0–100
    crash_prob:      float = 0.0      # 0–100
    expected_return: float = 0.0      # %
    expected_dd:     float = 0.0      # % (negative)
    max_upside:      float = 0.0      # %
    ci_low:          float = 0.0      # placeholder for Sprint 2 quantile
    ci_high:         float = 0.0
    kelly:           float = 0.0      # 0–25 %
    rr:              float = 0.0      # reward/risk ratio
    agreement:       int   = 0        # 0–4
    in_portfolio:    bool  = False
    reasons_pos:     list  = field(default_factory=list)
    reasons_neg:     list  = field(default_factory=list)
    alpha_sp500:     float = 0.0   # predicted 6m alpha vs SPY
    alpha_sector:    float = 0.0   # predicted 6m alpha vs sector
    # extra raw fields for details page
    days_since_ath:  float = 0.0
    ath_strength:    float = 0.0
    dollar_vol_20d:  float = 0.0
    rs_1m:           float = 0.0
    rs_3m:           float = 0.0


@dataclass
class ScanResult:
    market:      MarketSnapshot          = field(default_factory=MarketSnapshot)
    stocks:      list[StockSignal]       = field(default_factory=list)  # all, sorted by confidence
    stable:      list[StockSignal]       = field(default_factory=list)  # stable_score > 60, sorted
    growth:      list[StockSignal]       = field(default_factory=list)  # growth_score > 60, sorted
    high_risk:   list[StockSignal]       = field(default_factory=list)  # crash_prob > 60, sorted
    portfolio:   PortfolioResult         = field(default_factory=PortfolioResult)
    drift:       list[dict]              = field(default_factory=list)
    last_update: datetime                = field(default_factory=datetime.now)
    runtime_sec: float                   = 0.0
    n_tickers:   int                     = 0

    # Convenience getters
    def top(self, n: int = 10) -> list[StockSignal]:
        return self.stocks[:n]

    def get(self, ticker: str) -> StockSignal | None:
        return next((s for s in self.stocks if s.ticker == ticker), None)

    @property
    def n_stable_opp(self) -> int:
        return sum(1 for s in self.stocks if s.stable_score >= 60)

    @property
    def n_growth_opp(self) -> int:
        return sum(1 for s in self.stocks if s.growth_score >= 60)

    @property
    def n_high_risk(self) -> int:
        return sum(1 for s in self.stocks if s.crash_prob >= 60)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['last_update'] = self.last_update.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> ScanResult:
        d = dict(d)
        d['last_update'] = datetime.fromisoformat(d.get('last_update', datetime.now().isoformat()))
        d['market'] = MarketSnapshot(**d.get('market', {}))
        d['stocks']    = [StockSignal(**s) for s in d.get('stocks', [])]
        d['stable']    = [StockSignal(**s) for s in d.get('stable', [])]
        d['growth']    = [StockSignal(**s) for s in d.get('growth', [])]
        d['high_risk'] = [StockSignal(**s) for s in d.get('high_risk', [])]
        d['portfolio'] = PortfolioResult(**d.get('portfolio', {}))
        d['drift']     = d.get('drift', [])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_scan(progress_cb: Callable | None = None,
             tickers: list | None = None) -> ScanResult:
    """
    Full pipeline: download → features → models → rank → portfolio → ScanResult.
    progress_cb(step: str, pct: int) is called at each stage for UI progress bars.
    """
    t0 = time.time()
    today_str    = datetime.today().strftime('%Y-%m-%d')
    download_end = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    tickers_use  = tickers if tickers else NASDAQ100

    def _progress(step: str, pct: int):
        if progress_cb:
            progress_cb(step, pct)

    train_end  = (datetime.today() - timedelta(days=126 + 10)).strftime('%Y-%m-%d')
    market_raw = get_market_data(download_end)

    # QQQ + SPY — vedno prenesi najprej (QQQ za RS features, SPY za alpha target)
    _progress('Downloading QQQ + SPY...', 4)
    _, qqq_dl = download_yahoo('QQQ', DOWNLOAD_START, download_end)
    _, spy_dl = download_yahoo('SPY', DOWNLOAD_START, download_end)
    if qqq_dl is None:
        raise RuntimeError('QQQ download failed — check internet connection.')
    qqq_c    = qqq_dl['Close']
    qqq_rets = {
        '1m':  qqq_c.pct_change(21)  * 100,
        '3m':  qqq_c.pct_change(63)  * 100,
        '6m':  qqq_c.pct_change(126) * 100,
        '12m': qqq_c.pct_change(252) * 100,
    }
    spy_close = spy_dl['Close'] if spy_dl is not None else None

    large_scan = len(tickers_use) > _BATCH_SIZE

    if large_scan:
        # ── Batch mode: 120 tickers at a time to stay within Railway RAM ────
        # Sort by sector so tickers in the same sector land in the same batch
        # → sector_rs features computed on more complete peer groups
        sorted_tickers = sorted(tickers_use, key=lambda t: SECTOR_MAP.get(t, 'Other'))
        n_batches = ceil(len(sorted_tickers) / _BATCH_SIZE)
        all_raw_rows: dict = {}
        close_for_corr: dict = {}
        models = None; train_stats = None

        for bi, start in enumerate(range(0, len(sorted_tickers), _BATCH_SIZE)):
            batch = sorted_tickers[start:start + _BATCH_SIZE]
            pct   = 5 + int(bi / n_batches * 55)
            _progress(f'Batch {bi+1}/{n_batches} — downloading {len(batch)} tickers...', pct)

            price_batch = download_all(batch, download_end)
            price_batch['QQQ'] = qqq_dl

            _progress(f'Batch {bi+1}/{n_batches} — features...', pct + 2)
            cache_batch = build_cache(price_batch, qqq_rets, spy_close=spy_close)

            if bi == 0:
                _progress('Loading / training models...', pct + 4)
                if models_are_stale():
                    try:
                        models, train_stats = train_models(cache_batch, TRAIN_START, train_end)
                        save_models(models, train_stats)
                    except MemoryError:
                        raise RuntimeError('Premalo RAM-a za trening — poskusi z manjšim universum.')
                else:
                    models, train_stats = load_models()

            all_raw_rows.update(get_raw_rows(cache_batch))

            for t, df in price_batch.items():
                if t != 'QQQ':
                    close_for_corr[t] = df['Close'].iloc[-252:]

            del price_batch, cache_batch
            gc.collect()

        _progress('Building full snapshot...', 62)
        snap       = snapshot_from_rows(all_raw_rows)
        price_data = {t: pd.DataFrame({'Close': s}) for t, s in close_for_corr.items()}

    else:
        # ── Single-batch mode (original path) ────────────────────────────────
        _progress('Downloading prices...', 5)

        def dl_progress(done, total, ok):
            pct = 5 + int(done / total * 25)
            _progress(f'Downloading {done}/{total}  ({ok} OK)', pct)

        price_data = download_all(tickers_use, download_end, progress_cb=dl_progress)
        price_data['QQQ'] = qqq_dl

        _progress('Building features...', 32)
        cache = build_cache(price_data, qqq_rets, spy_close=spy_close)

        _progress('Training models...', 50)
        if models_are_stale():
            try:
                models, train_stats = train_models(cache, TRAIN_START, train_end)
                save_models(models, train_stats)
            except MemoryError:
                raise RuntimeError('Premalo RAM-a za trening — poskusi znova čez minuto.')
        else:
            models, train_stats = load_models()

        snap = get_today_snapshot(cache)

    # ── 4. Predictions ───────────────────────────────────────────────────────
    _progress('Running AI predictions...', 65)
    ranked_df  = predict_and_rank(snap, models)

    # ── 5. SHAP Explainability ───────────────────────────────────────────────
    _progress('Computing explanations...', 75)
    shap_reasons = compute_shap_reasons(snap, models, top_n=20)
    drift        = compute_feature_drift(train_stats, snap)

    # ── 6. Portfolio ─────────────────────────────────────────────────────────
    _progress('Building portfolio...', 88)
    portfolio_tickers = apply_correlation_filter(ranked_df, price_data)
    portfolio         = build_portfolio(ranked_df, portfolio_tickers, price_data)

    # ── 7. Assemble ScanResult ───────────────────────────────────────────────
    _progress('Assembling results...', 97)
    market = MarketSnapshot(
        spy_ret  = market_raw.get('SPY',  {}).get('ret1d', 0.0),
        qqq_ret  = market_raw.get('QQQ',  {}).get('ret1d', 0.0),
        vix      = market_raw.get('VIX',  {}).get('price', 0.0),
        spy_price= market_raw.get('SPY',  {}).get('price', 0.0),
        qqq_price= market_raw.get('QQQ',  {}).get('price', 0.0),
    )

    stocks = []
    for _, row in ranked_df.iterrows():
        reasons = build_stock_card_reasons(row['ticker'], row.to_dict(), shap_reasons)
        sig = StockSignal(
            ticker=row['ticker'], sector=row['sector'],
            rating=row['rating'], confidence=row['confidence'],
            stable_score=row['stable_score'], growth_score=row['growth_score'],
            crash_prob=row['crash_prob'],
            expected_return=row['expected_return'], expected_dd=row['expected_dd'],
            max_upside=row['max_upside'],
            ci_low=row['expected_return'] - 15.0,   # placeholder until quantile models
            ci_high=row['expected_return'] + 20.0,
            kelly=row['kelly'], rr=row['rr'], agreement=row['agreement'],
            in_portfolio=row['ticker'] in portfolio_tickers,
            reasons_pos=reasons['pos'], reasons_neg=reasons['neg'],
            alpha_sp500=row.get('alpha_sp500', 0.0),
            alpha_sector=row.get('alpha_sector', 0.0),
            days_since_ath=row['days_since_ath'], ath_strength=row['ath_strength'],
            dollar_vol_20d=row['dollar_vol_20d'],
            rs_1m=row['rs_1m'], rs_3m=row['rs_3m'],
        )
        stocks.append(sig)

    stable    = sorted([s for s in stocks if s.stable_score >= 60],
                       key=lambda x: x.stable_score, reverse=True)
    growth    = sorted([s for s in stocks if s.growth_score >= 60],
                       key=lambda x: x.growth_score, reverse=True)
    high_risk = sorted([s for s in stocks if s.crash_prob >= 60],
                       key=lambda x: x.crash_prob, reverse=True)

    result = ScanResult(
        market=market, stocks=stocks, stable=stable,
        growth=growth, high_risk=high_risk,
        portfolio=portfolio, drift=drift,
        last_update=datetime.now(),
        runtime_sec=round(time.time() - t0, 1),
        n_tickers=len(stocks),
    )

    # ── 8. Persist ───────────────────────────────────────────────────────────
    save_scan(result.to_dict())
    append_journal(today_str, [{'ticker': s.ticker, 'confidence': s.confidence,
                                 'expected_return': s.expected_return,
                                 'rating': s.rating} for s in stocks[:10]])
    append_prediction_history(today_str, [{'ticker': s.ticker,
                                            'expected_return': s.expected_return}
                                           for s in stocks])
    _progress('Done', 100)
    return result


def get_last_results() -> ScanResult | None:
    d = load_scan()
    if d is None:
        return None
    try:
        return ScanResult.from_dict(d)
    except Exception:
        return None


def cache_is_fresh(max_age_minutes: int = 30) -> bool:
    age = scan_age_minutes()
    return age is not None and age < max_age_minutes
