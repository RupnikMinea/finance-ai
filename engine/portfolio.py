import numpy as np
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class PortfolioResult:
    tickers:        list[str]    = field(default_factory=list)
    weights:        dict         = field(default_factory=dict)  # ticker -> weight %
    expected_return: float       = 0.0
    expected_dd:    float        = 0.0
    sharpe_est:     float        = 0.0
    kelly_exposure: float        = 0.0
    diversification: str         = 'N/A'
    correlation_level: str       = 'N/A'
    n_sectors:      int          = 0


def build_portfolio(ranked_df: pd.DataFrame, portfolio_tickers: set,
                    price_data: dict) -> PortfolioResult:
    sel = ranked_df[ranked_df['ticker'].isin(portfolio_tickers)].copy()
    if sel.empty:
        return PortfolioResult()

    # Kelly-weighted
    total_kelly = sel['kelly'].sum()
    if total_kelly > 0.5:
        sel['weight'] = sel['kelly'] / total_kelly * 100
    else:
        sel['weight'] = 100.0 / len(sel)

    # Portfolio metrics (weighted average)
    er  = float((sel['expected_return'] * sel['weight'] / 100).sum())
    edd = float((sel['expected_dd']     * sel['weight'] / 100).sum())

    # Sharpe estimate: ER / |EDD| * adjustment
    sharpe_est = round(er / max(abs(edd), 1.0) * 1.5, 2) if edd < 0 else 0.0

    kelly_exp = float(sel['kelly'].sum())

    # Diversification
    n_sectors = sel['sector'].nunique()
    if n_sectors >= 5:   div = 'Excellent'
    elif n_sectors >= 3: div = 'Good'
    elif n_sectors >= 2: div = 'Moderate'
    else:                div = 'Concentrated'

    # Correlation level
    rets = {}
    for t in sel['ticker']:
        if t in price_data:
            c = price_data[t]['Close']
            if len(c) > 63:
                rets[t] = c.pct_change().iloc[-126:].fillna(0)
    if len(rets) > 1:
        corr_mat = pd.DataFrame(rets).corr()
        # average off-diagonal correlation
        mask = np.triu(np.ones(corr_mat.shape), k=1).astype(bool)
        avg_corr = float(corr_mat.values[mask].mean())
        if avg_corr < 0.4:   corr_level = 'Low'
        elif avg_corr < 0.6: corr_level = 'Moderate'
        else:                corr_level = 'High'
    else:
        corr_level = 'N/A'

    return PortfolioResult(
        tickers=list(sel['ticker']),
        weights={row['ticker']: round(row['weight'], 1) for _, row in sel.iterrows()},
        expected_return=round(er, 1),
        expected_dd=round(edd, 1),
        sharpe_est=sharpe_est,
        kelly_exposure=round(kelly_exp, 1),
        diversification=div,
        correlation_level=corr_level,
        n_sectors=n_sectors,
    )
