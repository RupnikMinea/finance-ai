"""
Dynamic US stock universe fetcher.
Uses NASDAQ FTP (free, no auth) — returns all common stocks listed on
NYSE, NASDAQ, AMEX. Excludes ETFs, warrants, preferred shares, test issues.
"""
import requests


def fetch_us_tickers() -> list[str]:
    """
    Download all US-listed common stock tickers from NASDAQ FTP.
    Typical result: 5,000–7,000 symbols (NYSE + NASDAQ + AMEX).
    ETFs, warrants (.W), rights (.R), units (.U), preferred (ending with P/PR)
    and test issues are excluded.
    """
    tickers: set[str] = set()

    # ── NASDAQ-listed stocks ──────────────────────────────────────────────────
    # Format: Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
    try:
        r = requests.get(
            'https://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt',
            timeout=20, headers={'User-Agent': 'Mozilla/5.0'}
        )
        r.raise_for_status()
        for line in r.text.splitlines()[1:]:
            parts = line.split('|')
            if len(parts) < 7:
                continue
            sym, test_issue, fin_status, etf = parts[0], parts[3], parts[4], parts[6]
            if _is_valid(sym) and test_issue == 'N' and fin_status == 'N' and etf == 'N':
                tickers.add(sym)
    except Exception:
        pass

    # ── NYSE + AMEX + other exchange stocks ───────────────────────────────────
    # Format: ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
    try:
        r = requests.get(
            'https://ftp.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt',
            timeout=20, headers={'User-Agent': 'Mozilla/5.0'}
        )
        r.raise_for_status()
        for line in r.text.splitlines()[1:]:
            parts = line.split('|')
            if len(parts) < 7:
                continue
            sym, etf, test_issue = parts[0], parts[4], parts[6]
            if _is_valid(sym) and test_issue == 'N' and etf == 'N':
                tickers.add(sym)
    except Exception:
        pass

    return sorted(tickers)


def _is_valid(sym: str) -> bool:
    """Keep only clean common-stock symbols (1–5 uppercase letters, no suffixes)."""
    if not sym or not sym.isalpha():
        return False
    if not (1 <= len(sym) <= 5):
        return False
    # Skip obvious preferred/warrant/unit suffixes
    if sym.endswith(('P', 'W', 'R', 'U', 'Z', 'L', 'PR')):
        return False
    return True
