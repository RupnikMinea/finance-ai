"""
Dynamic US stock universe fetcher.
Sources (tried in order):
  1. SEC EDGAR  company_tickers.json  (~8,400 symbols, verify=False for Windows SSL)
  2. NASDAQ FTP nasdaqlisted.txt      (~6,000 symbols, works on Railway Linux)
  3. Wikipedia  S&P 500 list          (~500 symbols, last-resort fallback)
"""
import requests
import warnings


def _get(url: str, timeout: int = 20) -> requests.Response:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return requests.get(
            url, timeout=timeout,
            headers={'User-Agent': 'minea.rupnik@gmail.com'},
            verify=False,
        )


def _is_valid(sym: str) -> bool:
    if not sym:
        return False
    # Allow only alpha + optional hyphen (BRK-B style)
    clean = sym.replace('-', '')
    if not clean.isalpha():
        return False
    if not (1 <= len(sym) <= 5):
        return False
    last = sym[-1]
    # Drop OTC foreign (F), mutual funds (X), units (U), warrants (W), rights (R)
    if last in ('F', 'X', 'U', 'W', 'R', 'Z', 'L') and len(clean) > 2:
        return False
    if sym.endswith('PR') or sym.endswith('PRA') or sym.endswith('PRB'):
        return False
    return True


def fetch_us_tickers() -> list[str]:
    """
    Return all US-listed common stock tickers (NYSE + NASDAQ + AMEX).
    Excludes ETFs, OTC foreign stocks, warrants, preferred shares and SPACs.
    Typical result: ~5,000–8,000 symbols.
    """
    tickers: set[str] = set()

    # ── Source 1: SEC EDGAR (works on Windows with verify=False) ─────────────
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
                r = _get(
                    f'https://ftp.nasdaqtrader.com/dynamic/SymDir/{filename}',
                    timeout=20,
                )
                if r.status_code != 200:
                    continue
                for line in r.text.splitlines()[1:]:
                    parts = line.split('|')
                    if len(parts) < 7:
                        continue
                    sym = parts[0].strip().upper()
                    # nasdaqlisted: col3=TestIssue, col4=FinStatus, col6=ETF
                    # otherlisted:  col4=ETF, col6=TestIssue
                    if _is_valid(sym):
                        tickers.add(sym)
            except Exception:
                continue

    # ── Source 3: Wikipedia S&P 500 (last-resort fallback) ───────────────────
    if not tickers:
        try:
            import pandas as pd
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                tables = pd.read_html(
                    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
                )
            for sym in tables[0]['Symbol'].tolist():
                clean = str(sym).replace('.', '-').strip().upper()
                if _is_valid(clean):
                    tickers.add(clean)
        except Exception:
            pass

    # ── Source 4: hardcoded curated list ─────────────────────────────────────
    if not tickers:
        from config import NASDAQ100, SP500_ADD
        tickers.update(NASDAQ100)
        tickers.update(SP500_ADD)

    return sorted(tickers)
