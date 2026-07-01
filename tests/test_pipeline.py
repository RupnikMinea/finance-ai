"""
Smoke testi za Finance AI pipeline.
Poženi: cd C:\\Users\\minea\\Desktop\\finance_ai && python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

import pytest
import pandas as pd
import numpy as np

MINI_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL']
DOWNLOAD_END = '2025-01-10'
DOWNLOAD_START = '2021-01-01'


# ── 1. Data download ──────────────────────────────────────────────────────────

def test_yahoo_download_single():
    from engine.data import download_yahoo
    ticker, df = download_yahoo('AAPL', DOWNLOAD_START, DOWNLOAD_END)
    assert ticker == 'AAPL'
    assert df is not None, "Download vrnil None"
    assert len(df) > 100, f"Premalo vrstic: {len(df)}"
    assert 'Close' in df.columns
    assert df['Close'].isna().sum() / len(df) < 0.05, "Preveč NaN v Close"
    print(f"  AAPL: {len(df)} vrstic, {df.index[0].date()} – {df.index[-1].date()}")


def test_yahoo_download_all_mini():
    from engine.data import download_all
    price_data = download_all(MINI_TICKERS, DOWNLOAD_END)
    assert len(price_data) == len(MINI_TICKERS), f"Pričakovano {len(MINI_TICKERS)}, dobljeno {len(price_data)}"
    for t in MINI_TICKERS:
        assert t in price_data, f"{t} manjka"
        assert len(price_data[t]) > 100


# ── 2. Feature building ───────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def price_cache():
    from engine.data import download_all, download_yahoo
    from engine.features import build_cache
    price_data = download_all(MINI_TICKERS, DOWNLOAD_END)
    _, qqq = download_yahoo('QQQ', DOWNLOAD_START, DOWNLOAD_END)
    qqq_c = qqq['Close']
    qqq_rets = {
        '1m':  qqq_c.pct_change(21) * 100,
        '3m':  qqq_c.pct_change(63) * 100,
        '6m':  qqq_c.pct_change(126) * 100,
        '12m': qqq_c.pct_change(252) * 100,
    }
    price_data['QQQ'] = qqq
    cache = build_cache(price_data, qqq_rets)
    return cache


def test_build_cache(price_cache):
    assert len(price_cache) >= len(MINI_TICKERS)
    for t in MINI_TICKERS:
        assert t in price_cache, f"{t} manjka v cache"
        df = price_cache[t]
        for col in ['close', 'ret_1m', 'vol_20d', 'rs_1m']:
            assert col in df.columns, f"{t}: stolpec {col} manjka"
    print(f"  Cache: {len(price_cache)} tickerjev")


def test_today_snapshot(price_cache):
    from engine.features import get_today_snapshot
    from config import ALL_FEATS
    snap = get_today_snapshot(price_cache)
    assert len(snap) >= len(MINI_TICKERS) - 1
    for feat in ALL_FEATS[:5]:
        assert feat in snap.columns, f"Feature {feat} manjka v snapshot"
    assert snap[ALL_FEATS].isna().sum().sum() == 0, "NaN v snapshot features"
    print(f"  Snapshot: {len(snap)} tickerjev, {len(snap.columns)} stolpcev")


# ── 3. Model training ─────────────────────────────────────────────────────────

def test_model_training(price_cache):
    from engine.models import train_models
    import gc
    models, train_stats = train_models(price_cache, '2021-01-01', '2024-06-01')
    expected = {'max_upside', 'expected_return', 'expected_dd', 'prob_safe'}
    missing = expected - set(models.keys())
    assert not missing, f"Manjkajoči modeli: {missing}"
    assert len(train_stats) > 0, "train_stats je prazen"
    print(f"  Modeli: {list(models.keys())}")
    print(f"  Train stats: {len(train_stats)} featur")
    gc.collect()


def test_predictions(price_cache):
    from engine.models import train_models
    from engine.features import get_today_snapshot
    from engine.ranking import predict_and_rank
    import gc
    models, _ = train_models(price_cache, '2021-01-01', '2024-06-01')
    snap = get_today_snapshot(price_cache)
    ranked = predict_and_rank(snap, models)
    assert len(ranked) >= len(MINI_TICKERS) - 1
    for col in ['ticker', 'expected_return', 'expected_dd', 'confidence', 'rating']:
        assert col in ranked.columns, f"Stolpec {col} manjka"
    assert ranked['confidence'].between(0, 100).all(), "Confidence izven [0,100]"
    assert ranked['rating'].isin(['A+','A','A-','B+','B','B-','C+']).all()
    print(f"  Ranked: {len(ranked)} tickerjev")
    print(ranked[['ticker','rating','confidence','expected_return']].to_string())
    gc.collect()


# ── 4. Supabase ───────────────────────────────────────────────────────────────

def test_supabase_connection():
    url = os.getenv('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_KEY', '')
    if not url or not key:
        pytest.skip("SUPABASE_URL/KEY nista nastavljeni — naložite .env")
    from supabase import create_client
    sb = create_client(url, key)
    res = sb.table('scan_cache').select('id').limit(1).execute()
    assert res is not None
    print("  Supabase: povezava OK")


def test_supabase_write_read():
    url = os.getenv('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_KEY', '')
    if not url or not key:
        pytest.skip("SUPABASE_URL/KEY nista nastavljeni")
    from supabase import create_client
    sb = create_client(url, key)
    test_data = {'test': True, 'value': 42}
    sb.table('scan_cache').upsert({'id': '_test_', 'data': test_data}).execute()
    res = sb.table('scan_cache').select('data').eq('id', '_test_').execute()
    assert res.data, "Ni podatkov po upsertu"
    assert res.data[0]['data']['value'] == 42
    sb.table('scan_cache').delete().eq('id', '_test_').execute()
    print("  Supabase write/read/delete: OK")
