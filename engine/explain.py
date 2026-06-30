import numpy as np
import pandas as pd
from config import ALL_FEATS, FEAT_DISPLAY, DRIFT_THRESHOLD


def compute_shap_reasons(snap: pd.DataFrame, models: dict,
                          top_n: int = 20) -> dict[str, dict]:
    try:
        import shap
        X_all = snap[ALL_FEATS].fillna(0).values
        model_key = 'max_upside' if 'max_upside' in models else list(models.keys())[0]
        explainer = shap.TreeExplainer(models[model_key])
        shap_vals = explainer.shap_values(X_all)
        reasons = {}
        for i, ticker in enumerate(snap.index[:top_n]):
            vals  = shap_vals[i]
            pairs = sorted(zip(ALL_FEATS, vals), key=lambda x: abs(x[1]), reverse=True)
            pos   = [(FEAT_DISPLAY.get(f, f), round(v, 3)) for f, v in pairs if v > 0][:3]
            neg   = [(FEAT_DISPLAY.get(f, f), round(v, 3)) for f, v in pairs if v < 0][:2]
            reasons[ticker] = {'pos': pos, 'neg': neg}
        return reasons
    except Exception:
        return {}


def compute_feature_drift(train_stats: dict, snap: pd.DataFrame) -> list[dict]:
    drift = []
    for feat in ALL_FEATS:
        if feat not in train_stats or feat not in snap.columns:
            continue
        t_mean = train_stats[feat]['mean']
        t_std  = train_stats[feat]['std']
        c_mean = float(snap[feat].mean())
        if t_std > 1e-6:
            z = abs(c_mean - t_mean) / t_std
            drift.append({
                'feat':       feat,
                'display':    FEAT_DISPLAY.get(feat, feat),
                'train_mean': round(t_mean, 3),
                'now_mean':   round(c_mean, 3),
                'drift_z':    round(z, 2),
                'alert':      z > DRIFT_THRESHOLD,
            })
    drift.sort(key=lambda x: x['drift_z'], reverse=True)
    return drift


def build_stock_card_reasons(ticker: str, row: dict,
                              shap_reasons: dict) -> dict:
    """Convert SHAP reasons + raw feature values into human-readable card text."""
    pos_labels = []
    neg_labels = []

    # SHAP-based reasons
    shap = shap_reasons.get(ticker, {})
    for feat_disp, _ in shap.get('pos', []):
        pos_labels.append(feat_disp)
    for feat_disp, _ in shap.get('neg', []):
        neg_labels.append(feat_disp)

    # Rule-based fallbacks if SHAP not available
    if not pos_labels:
        if row.get('ath_strength', 0) > 2:
            pos_labels.append('ATH Strength')
        if row.get('dollar_vol_20d', 0) > 500:
            pos_labels.append('High Dollar Volume')
        if row.get('rs_1m', 0) > 5:
            pos_labels.append('Strong Relative Strength')
        if row.get('days_since_ath', 999) < 30:
            pos_labels.append('Near All-Time High')
    if not neg_labels:
        if row.get('days_since_ath', 0) > 200:
            neg_labels.append('Far from ATH')
        if row.get('expected_dd', 0) < -25:
            neg_labels.append('High Expected Drawdown')

    return {'pos': pos_labels[:3], 'neg': neg_labels[:2]}
