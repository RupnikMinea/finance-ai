import time
import pandas as pd
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import DOWNLOAD_START, DOWNLOAD_WORKERS, FINNHUB_TOKEN, DATA_SOURCE


# ── Yahoo Finance ─────────────────────────────────────────────────────────────

def download_yahoo(ticker: str, start_str: str, end_str: str) -> tuple[str, pd.DataFrame | None]:
    p1 = int(datetime.strptime(start_str, '%Y-%m-%d').timestamp())
    p2 = int(datetime.strptime(end_str,   '%Y-%m-%d').timestamp())
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
           f'?interval=1d&period1={p1}&period2={p2}')
    for attempt in range(3):
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 429:
                time.sleep(2 + attempt * 4)  # 2s, 6s, 10s backoff
                continue
            r.raise_for_status()
            res = r.json()['chart']['result'][0]
            q   = res['indicators']['quote'][0]
            df  = pd.DataFrame(
                {'Open': q['open'], 'High': q['high'], 'Low': q['low'],
                 'Close': q['close'], 'Volume': q['volume']},
                index=pd.to_datetime(res['timestamp'], unit='s').normalize()
            )
            df.index.name = 'Date'
            df = df.dropna()
            return ticker, df if len(df) >= 200 else None
        except Exception:
            if attempt < 2:
                time.sleep(1)
    return ticker, None


# ── Finnhub ───────────────────────────────────────────────────────────────────

def download_finnhub(ticker: str, start_str: str, end_str: str) -> tuple[str, pd.DataFrame | None]:
    """Finnhub /stock/candle endpoint. Requires FINNHUB_TOKEN env variable."""
    if not FINNHUB_TOKEN:
        return ticker, None
    try:
        p1 = int(datetime.strptime(start_str, '%Y-%m-%d').timestamp())
        p2 = int(datetime.strptime(end_str,   '%Y-%m-%d').timestamp())
        url = ('https://finnhub.io/api/v1/stock/candle'
               f'?symbol={ticker}&resolution=D&from={p1}&to={p2}&token={FINNHUB_TOKEN}')
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        if data.get('s') != 'ok' or not data.get('t'):
            return ticker, None
        df = pd.DataFrame({
            'Open':   data['o'], 'High':  data['h'],
            'Low':    data['l'], 'Close': data['c'],
            'Volume': data['v'],
        }, index=pd.to_datetime(data['t'], unit='s').normalize())
        df.index.name = 'Date'
        df = df.dropna()
        return ticker, df if len(df) >= 200 else None
    except Exception:
        return ticker, None


# ── Unified download (picks source from config) ───────────────────────────────

def download_ticker(ticker: str, start_str: str, end_str: str) -> tuple[str, pd.DataFrame | None]:
    if DATA_SOURCE == 'finnhub' and FINNHUB_TOKEN:
        result = download_finnhub(ticker, start_str, end_str)
        # Finnhub free: 60 req/min — small throttle between calls
        time.sleep(0.05)
        return result
    return download_yahoo(ticker, start_str, end_str)


def download_all(tickers: list[str], end_str: str,
                 progress_cb=None) -> dict[str, pd.DataFrame]:
    # Finnhub free tier: max 60 req/min → lower parallelism
    workers = 4 if (DATA_SOURCE == 'finnhub' and FINNHUB_TOKEN) else DOWNLOAD_WORKERS
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download_ticker, t, DOWNLOAD_START, end_str): t
                   for t in tickers}
        done = 0
        for f in as_completed(futures):
            ticker, df = f.result()
            done += 1
            if df is not None:
                results[ticker] = df
            if progress_cb:
                progress_cb(done, len(tickers), len(results))
    return results


def get_market_data(end_str: str) -> dict:
    market = {}
    start_recent = (datetime.today() - timedelta(days=10)).strftime('%Y-%m-%d')
    for sym in ['SPY', 'QQQ', '^VIX']:
        finnhub_sym = sym.replace('^', '')   # Finnhub ne pozna ^ prefix
        _, df = download_ticker(finnhub_sym if DATA_SOURCE == 'finnhub' else sym,
                                start_recent, end_str)
        if df is not None and len(df) >= 2:
            c = df['Close']
            market[finnhub_sym] = {
                'price': round(float(c.iloc[-1]), 2),
                'ret1d': round((float(c.iloc[-1]) / float(c.iloc[-2]) - 1) * 100, 2),
                'ret1w': round((float(c.iloc[-1]) / float(c.iloc[-6]) - 1) * 100, 2) if len(c) > 5 else 0.0,
            }
    return market
