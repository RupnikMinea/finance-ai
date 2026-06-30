import numpy as np
import pandas as pd
from config import FEATURE_COLS, ALL_FEATS, SECTOR_MAP, HORIZON, SAFE_DD


def compute_features(df: pd.DataFrame, qqq_rets: dict | None = None) -> pd.DataFrame:
    c, h, l, v = df['Close'], df['High'], df['Low'], df['Volume']
    out = pd.DataFrame(index=df.index)

    def sma(s, n): return s.rolling(n, min_periods=n).mean()
    def ema(s, n): return s.ewm(span=n, adjust=False).mean()
    def rsi_fn(s, n=14):
        d = s.diff(); g = d.clip(lower=0).rolling(n).mean()
        ls = (-d.clip(upper=0)).rolling(n).mean()
        return 100 - 100 / (1 + g / ls.replace(0, np.nan))

    sma20 = sma(c, 20); sma50 = sma(c, 50); sma200 = sma(c, 200)
    ema12 = ema(c, 12); ema26 = ema(c, 26)
    out['price_vs_sma20']  = (c / sma20  - 1) * 100
    out['price_vs_sma50']  = (c / sma50  - 1) * 100
    out['price_vs_sma200'] = (c / sma200 - 1) * 100
    out['sma20_vs_sma50']  = (sma20 / sma50  - 1) * 100
    out['sma50_vs_sma200'] = (sma50 / sma200 - 1) * 100

    r1m = c.pct_change(21) * 100; r3m = c.pct_change(63) * 100
    r6m = c.pct_change(126) * 100; r12m = c.pct_change(252) * 100
    out['ret_1m'] = r1m; out['ret_3m'] = r3m
    out['ret_6m'] = r6m; out['ret_12m'] = r12m

    if qqq_rets is not None:
        out['rs_1m']  = r1m  - qqq_rets['1m'].reindex(c.index)
        out['rs_3m']  = r3m  - qqq_rets['3m'].reindex(c.index)
        out['rs_6m']  = r6m  - qqq_rets['6m'].reindex(c.index)
        out['rs_12m'] = r12m - qqq_rets['12m'].reindex(c.index)
    else:
        for k in ['rs_1m', 'rs_3m', 'rs_6m', 'rs_12m']:
            out[k] = 0.0

    out['rsi28'] = rsi_fn(c, 28)
    macd = ema12 - ema26; out['macd_hist'] = macd - ema(macd, 9)
    vm20 = v.rolling(20).mean()
    out['rel_vol_5d'] = v.rolling(5).mean() / (vm20 + 1e-9)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    out['atr_pct'] = atr14 / c * 100
    rd = c.pct_change()
    out['vol_20d']  = rd.rolling(20).std()  * np.sqrt(252) * 100
    out['vol_60d']  = rd.rolling(60).std()  * np.sqrt(252) * 100
    out['vol_120d'] = rd.rolling(120).std() * np.sqrt(252) * 100
    out['vc_2060']  = out['vol_20d']  / (out['vol_60d']  + 1e-9)
    out['vc_60120'] = out['vol_60d']  / (out['vol_120d'] + 1e-9)
    out['pct_52wh'] = (c / h.rolling(252).max() - 1) * 100
    out['pct_52wl'] = (c / l.rolling(252).min() - 1) * 100
    rm = h.rolling(min(252 * 5, len(df))).max()
    out['ath_pct']   = (c / rm - 1) * 100
    out['roc10']     = c.pct_change(10) * 100
    out['sharpe_30'] = (rd.rolling(21).mean() / (rd.rolling(21).std() + 1e-9)) * np.sqrt(252)
    out['sharpe_90'] = (rd.rolling(63).mean() / (rd.rolling(63).std() + 1e-9)) * np.sqrt(252)
    out['maxdd_60']  = (c / c.rolling(60).max() - 1) * 100
    out['trend_cons']= (c > sma50).astype(float).rolling(20).mean() * 100
    out['vol_regime']= atr14 / (tr.rolling(90).mean() + 1e-9)
    out['slope_sma50']  = (sma50  / sma50.shift(10)  - 1) * 100
    out['slope_sma200'] = (sma200 / sma200.shift(10) - 1) * 100
    atr20 = tr.rolling(20).mean(); atr100 = tr.rolling(100).mean()
    out['atr_ratio']   = atr20 / (atr100 + 1e-9)
    out['rel_vol_90d'] = v.rolling(5).mean() / (v.rolling(90).mean() + 1e-9)
    ds = pd.Series(np.arange(len(df)), index=df.index)
    last_ath = ds.where(h >= rm).ffill()
    out['days_since_ath'] = (ds - last_ath).clip(0, 500)
    out['breakout20'] = (c > c.rolling(20).max().shift(1)).astype(int)
    out['breakout50'] = (c > c.rolling(50).max().shift(1)).astype(int)
    out['dollar_vol_20d'] = (c * v).rolling(20).mean() / 1e6
    out['rel_vol_20d']    = vm20 / (v.rolling(90).mean() + 1e-9)
    rm_prev = rm.shift(1)
    ath_break_pct = np.where(c > rm_prev, (c / rm_prev - 1) * 100, 0.0)
    out['ath_strength'] = (pd.Series(ath_break_pct, index=c.index)
                           .rolling(60, min_periods=1).max().fillna(0))
    return out


def compute_targets(close: pd.Series, horizon: int = 126,
                    safe_pct: float = 0.10) -> tuple:
    arr = close.values.astype(float); n = len(arr)
    mu  = np.full(n, np.nan); er  = np.full(n, np.nan)
    ls  = np.zeros(n, dtype=np.int8); edd = np.full(n, np.nan)
    for i in range(n - horizon):
        if arr[i] > 0:
            fut   = arr[i + 1:i + horizon + 1]
            mu[i]  = (fut.max()      / arr[i] - 1) * 100
            er[i]  = (arr[i+horizon] / arr[i] - 1) * 100
            ls[i]  = int(fut.min()   / arr[i] - 1 >= -safe_pct)
            edd[i] = (fut.min()      / arr[i] - 1) * 100
    return (pd.Series(mu, index=close.index),
            pd.Series(er, index=close.index),
            pd.Series(ls.astype(int), index=close.index),
            pd.Series(edd, index=close.index))


def build_cache(price_data: dict, qqq_rets: dict) -> dict:
    raw = {}
    for ticker, df in price_data.items():
        feats = compute_features(df, qqq_rets)
        mu, er, ls, edd = compute_targets(df['Close'], HORIZON, SAFE_DD / 100)
        raw[ticker] = {'feats': feats, 'mu': mu, 'er': er,
                       'ls': ls, 'edd': edd, 'close': df['Close']}

    rs20 = pd.DataFrame({t: raw[t]['feats']['rs_1m'] for t in raw})
    rs60 = pd.DataFrame({t: raw[t]['feats']['rs_3m'] for t in raw})
    cache = {}
    for ticker, r in raw.items():
        sector = SECTOR_MAP.get(ticker, 'Other')
        peers  = [t for t in rs20.columns if SECTOR_MAP.get(t, 'Other') == sector and t != ticker]
        idx    = r['feats'].index
        comb   = r['feats'].copy()
        comb['sector_rs_20d']   = (rs20[peers].mean(axis=1).reindex(idx).fillna(0)
                                   if peers else pd.Series(0.0, index=idx))
        comb['sector_rs_60d']   = (rs60[peers].mean(axis=1).reindex(idx).fillna(0)
                                   if peers else pd.Series(0.0, index=idx))
        comb['max_upside']      = r['mu']
        comb['expected_return'] = r['er']
        comb['label_safe']      = r['ls']
        comb['expected_dd']     = r['edd']
        comb['close']           = r['close']
        cache[ticker] = comb
    return cache


def build_train_df(cache: dict, date_from: str, date_to: str,
                   target_col: str) -> pd.DataFrame:
    rows = []
    for ticker, df in cache.items():
        mask = (df.index >= date_from) & (df.index <= date_to)
        sub  = df[mask].dropna(subset=FEATURE_COLS + [target_col])
        rows.append(sub)
    if not rows:
        return pd.DataFrame()
    full = pd.concat(rows).sort_index()
    for col in FEATURE_COLS:
        full[f'cs_{col}'] = full.groupby(level=0)[col].rank(pct=True)
    return full


def get_today_snapshot(cache: dict) -> pd.DataFrame:
    rows = {}
    for ticker, df in cache.items():
        row = df[FEATURE_COLS].iloc[-1] if len(df) > 0 else None
        if row is None or row.isnull().mean() > 0.2:
            continue
        rows[ticker] = row.fillna(0)
    if len(rows) < 5:
        return pd.DataFrame()
    snap = pd.DataFrame(rows).T
    snap.index.name = 'ticker'
    for col in FEATURE_COLS:
        snap[f'cs_{col}'] = snap[col].rank(pct=True)
    for col in ALL_FEATS:
        if col not in snap.columns:
            snap[col] = 0.0
    return snap


def time_weights(idx):
    d = pd.to_datetime(idx)
    days = (d - d.min()).days.values
    return 0.2 + 0.8 * (days / max(days.max(), 1))
