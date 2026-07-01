import numpy as np
import pandas as pd
from config import ENS_W, SECTOR_MAP, MAX_PORTFOLIO, MAX_CORR, MAX_PER_SECTOR, ALL_FEATS

AI_RATING_THRESHOLDS = [
    (93, 'A+'), (85, 'A'), (75, 'A-'), (65, 'B+'), (55, 'B'), (45, 'B-'), (0, 'C+')
]


def compute_ai_rating(confidence: float, stable_score: float,
                      growth_score: float, crash_prob: float) -> str:
    score = (confidence * 0.4 + stable_score * 0.3
             + growth_score * 0.2 + (100 - crash_prob) * 0.1)
    return next(g for t, g in AI_RATING_THRESHOLDS if score >= t)


def predict_and_rank(snap: pd.DataFrame, models: dict) -> pd.DataFrame:
    X = snap[ALL_FEATS].fillna(0)
    n = len(snap)

    mu_p  = models['max_upside'].predict(X)           if 'max_upside'      in models else np.zeros(n)
    er_p  = models['expected_return'].predict(X)      if 'expected_return' in models else np.zeros(n)
    edd_p = models['expected_dd'].predict(X)          if 'expected_dd'     in models else np.full(n, -10.0)
    ps_p  = (models['prob_safe'].predict_proba(X)[:, 1]
             if 'prob_safe' in models else np.full(n, 0.5))

    edd_p = np.clip(edd_p, -70.0, -0.5)
    rr    = er_p / np.abs(edd_p)

    abs_edd = np.abs(edd_p)
    b_dyn     = np.where((er_p > 0.5) & (abs_edd > 0.5), er_p / (abs_edd + 1e-9), 0.0)
    kelly_dyn = np.where(b_dyn > 0, ps_p - (1 - ps_p) / (b_dyn + 1e-9), 0.0)
    kelly_dyn = np.clip(kelly_dyn * 100, 0.0, 25.0)

    def rk(arr):  return pd.Series(arr).rank(pct=True).values
    def n100(arr):
        mn, mx = arr.min(), arr.max()
        return (arr - mn) / (mx - mn + 1e-9) * 100

    w_er, w_k, w_ps, w_u = ENS_W
    r_er = rk(er_p); r_k = rk(kelly_dyn); r_ps = rk(ps_p); r_u = rk(mu_p)
    ensemble   = w_er*r_er + w_k*r_k + w_ps*r_ps + w_u*r_u
    confidence = 0.35*n100(ensemble) + 0.25*n100(ps_p) + 0.20*n100(kelly_dyn) + 0.20*n100(rr)

    # Stable Score: high p_safe + low expected_dd + moderate return
    stable_score = (0.50 * n100(ps_p) + 0.30 * n100(-edd_p) + 0.20 * n100(er_p))

    # Growth Score: high max_upside + high expected_return, dd less important
    growth_score = (0.50 * n100(mu_p) + 0.30 * n100(er_p) + 0.20 * n100(kelly_dyn))

    # Crash probability proxy: low p_safe + large negative expected_dd
    crash_proxy  = (0.60 * n100(1 - ps_p) + 0.40 * n100(np.abs(edd_p)))

    agree = ((r_er > 0.60).astype(int) + (r_u > 0.60).astype(int) +
             (kelly_dyn > 5.0).astype(int) + (ps_p > 0.45).astype(int))

    rows = []
    for i, ticker in enumerate(snap.index):
        ss = float(stable_score[i]); gs = float(growth_score[i]); cp = float(crash_proxy[i])
        conf = float(confidence[i])
        rows.append({
            'ticker':          ticker,
            'sector':          SECTOR_MAP.get(ticker, 'Other'),
            'rating':          compute_ai_rating(conf, ss, gs, cp),
            'confidence':      round(conf, 1),
            'stable_score':    round(ss, 1),
            'growth_score':    round(gs, 1),
            'crash_prob':      round(cp, 1),
            'expected_return': round(float(er_p[i]), 1),
            'expected_dd':     round(float(edd_p[i]), 1),
            'max_upside':      round(float(mu_p[i]), 1),
            'prob_safe':       round(float(ps_p[i]), 3),
            'kelly':           round(float(kelly_dyn[i]), 1),
            'rr':              round(float(rr[i]), 2),
            'ensemble':        round(float(ensemble[i]), 4),
            'agreement':       int(agree[i]),
            'days_since_ath':  round(float(snap['days_since_ath'].iloc[i]), 0),
            'ath_strength':    round(float(snap['ath_strength'].iloc[i]), 1),
            'dollar_vol_20d':  round(float(snap['dollar_vol_20d'].iloc[i]), 0),
            'rs_1m':           round(float(snap['rs_1m'].iloc[i]), 1),
            'rs_3m':           round(float(snap['rs_3m'].iloc[i]), 1),
        })
    return (pd.DataFrame(rows)
            .sort_values('confidence', ascending=False)
            .reset_index(drop=True))


def apply_correlation_filter(ranked_df: pd.DataFrame,
                              price_data: dict) -> set[str]:
    rets = {}
    for t in ranked_df['ticker']:
        if t in price_data:
            c = price_data[t]['Close']
            if len(c) > 63:
                rets[t] = c.pct_change().iloc[-252:].fillna(0)

    corr_mat = pd.DataFrame(rets).corr() if len(rets) > 1 else pd.DataFrame()
    selected = []; sector_counts = {}
    for _, row in ranked_df.iterrows():
        t = row['ticker']; s = row['sector']
        if len(selected) >= MAX_PORTFOLIO: break
        if sector_counts.get(s, 0) >= MAX_PER_SECTOR: continue
        too_corr = False
        if not corr_mat.empty and t in corr_mat.columns:
            for sel in selected:
                if sel in corr_mat.columns and corr_mat.loc[t, sel] > MAX_CORR:
                    too_corr = True; break
        if not too_corr:
            selected.append(t)
            sector_counts[s] = sector_counts.get(s, 0) + 1
    return set(selected)
