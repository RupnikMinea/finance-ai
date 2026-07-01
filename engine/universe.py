"""
Dynamic US stock universe fetcher.

fetch_us_tickers()      — all US-listed stocks from SEC EDGAR (~6,400)
fetch_largecap_tickers() — S&P 500 + S&P 400 MidCap from Wikipedia (~900, all $5B+)

SSL verification is disabled (verify=False) to work around Windows cert issues.
On Railway Linux the standard CA bundle works fine.
"""
import io
import warnings
import requests


def _get(url: str, timeout: int = 20) -> requests.Response:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return requests.get(
            url, timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0'},
            verify=False,
        )


def _is_valid(sym: str) -> bool:
    if not sym:
        return False
    clean = sym.replace('-', '')
    if not clean.isalpha():
        return False
    if not (1 <= len(sym) <= 5):
        return False
    last = sym[-1]
    if last in ('F', 'X', 'U', 'W', 'R', 'Z', 'L') and len(clean) > 2:
        return False
    if sym.endswith('PR') or sym.endswith('PRA') or sym.endswith('PRB'):
        return False
    return True


def _wikipedia_tickers(url: str, symbol_col: str = 'Symbol') -> list[str]:
    """Fetch a ticker list from a Wikipedia index page."""
    import pandas as pd
    r = _get(url, timeout=20)
    r.raise_for_status()
    tables = pd.read_html(io.StringIO(r.text))
    col = tables[0][symbol_col].tolist()
    return [str(t).replace('.', '-').strip().upper() for t in col if t and str(t) != 'nan']


def fetch_largecap_tickers() -> list[str]:
    """
    Return US stocks with ~$5B+ market cap: S&P 500 + S&P 400 MidCap (~900 tickers).
    Source: Wikipedia. Falls back to hardcoded curated config lists.
    """
    tickers: set[str] = set()

    for url, col in [
        ('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', 'Symbol'),
        ('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', 'Symbol'),
    ]:
        try:
            batch = _wikipedia_tickers(url, col)
            tickers.update(t for t in batch if _is_valid(t.replace('-', '')))
        except Exception:
            pass

    # Fallback: use the curated config lists (already $5B+)
    if not tickers:
        from config import NASDAQ100, SP500_ADD, RUSSELL2000_TOP
        tickers.update(NASDAQ100)
        tickers.update(SP500_ADD)
        tickers.update(RUSSELL2000_TOP)

    return sorted(tickers)


def fetch_us_tickers() -> list[str]:
    """
    Return all US-listed common stock tickers (NYSE + NASDAQ + AMEX) from SEC EDGAR.
    Excludes ETFs, OTC foreign, warrants, preferred shares. ~6,400 tickers.
    Falls back to NASDAQ FTP (works on Railway), then Wikipedia, then hardcoded.
    """
    tickers: set[str] = set()

    # ── Source 1: SEC EDGAR (verify=False for Windows SSL) ───────────────────
    try:
        r = _get('https://www.sec.gov/files/company_tickers.json', timeout=15)
        if r.status_code == 200:
            for entry in r.json().values():
                sym = str(entry.get('ticker', '')).upper().strip()
                if _is_valid(sym):
                    tickers.add(sym)
    except Exception:
        pass

    # ── Source 2: NASDAQ FTP (works on Railway Linux) ────────────────────────
    if not tickers:
        for filename in ['nasdaqlisted.txt', 'otherlisted.txt']:
            try:
                r = _get(f'https://ftp.nasdaqtrader.com/dynamic/SymDir/{filename}', timeout=20)
                if r.status_code != 200:
                    continue
                for line in r.text.splitlines()[1:]:
                    parts = line.split('|')
                    if len(parts) < 7:
                        continue
                    sym = parts[0].strip().upper()
                    if _is_valid(sym):
                        tickers.add(sym)
            except Exception:
                continue

    # ── Source 3: Wikipedia S&P 500 fallback ─────────────────────────────────
    if not tickers:
        try:
            tickers.update(fetch_largecap_tickers())
        except Exception:
            pass

    # ── Source 4: hardcoded curated list ─────────────────────────────────────
    if not tickers:
        from config import NASDAQ100, SP500_ADD
        tickers.update(NASDAQ100)
        tickers.update(SP500_ADD)

    return sorted(tickers)
