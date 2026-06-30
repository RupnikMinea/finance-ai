import pickle
import numpy as np
import lightgbm as lgb
from pathlib import Path
from config import ALL_FEATS, MODEL_DIR
from engine.features import build_train_df, time_weights

LGB_PARAMS = dict(n_estimators=200, learning_rate=0.05, max_depth=5,
                  num_leaves=31, min_child_samples=40, subsample=0.8,
                  colsample_bytree=0.7, random_state=42, n_jobs=1, verbose=-1,
                  max_bin=127)


def train_models(cache: dict, train_s: str, train_e: str) -> tuple[dict, dict]:
    models = {}; train_stats = {}

    df_stat = build_train_df(cache, train_s, train_e, 'expected_return')
    if len(df_stat) > 0:
        for feat in ALL_FEATS:
            if feat in df_stat.columns:
                train_stats[feat] = {'mean': float(df_stat[feat].mean()),
                                     'std':  float(df_stat[feat].std())}

    for target in ['max_upside', 'expected_return', 'expected_dd']:
        df = build_train_df(cache, train_s, train_e, target)
        if len(df) < 500: continue
        X = df[ALL_FEATS].fillna(0).values; y = df[target].values
        m = lgb.LGBMRegressor(**LGB_PARAMS)
        m.fit(X, y, sample_weight=time_weights(df.index))
        models[target] = m

    df = build_train_df(cache, train_s, train_e, 'label_safe')
    if len(df) >= 500:
        X = df[ALL_FEATS].fillna(0).values; y = df['label_safe'].values
        pos_w = (y == 0).sum() / max((y == 1).sum(), 1)
        m = lgb.LGBMClassifier(**LGB_PARAMS, scale_pos_weight=pos_w)
        m.fit(X, y, sample_weight=time_weights(df.index))
        models['prob_safe'] = m

    return models, train_stats


def save_models(models: dict, train_stats: dict, path: Path = MODEL_DIR) -> None:
    path = Path(path)
    path.mkdir(exist_ok=True)
    for name, model in models.items():
        with open(path / f'{name}.pkl', 'wb') as f:
            pickle.dump(model, f)
    with open(path / 'train_stats.pkl', 'wb') as f:
        pickle.dump(train_stats, f)


def load_models(path: Path = MODEL_DIR) -> tuple[dict, dict]:
    path = Path(path)
    models = {}; train_stats = {}
    for name in ['max_upside', 'expected_return', 'expected_dd', 'prob_safe']:
        p = path / f'{name}.pkl'
        if p.exists():
            with open(p, 'rb') as f:
                models[name] = pickle.load(f)
    stats_p = path / 'train_stats.pkl'
    if stats_p.exists():
        with open(stats_p, 'rb') as f:
            train_stats = pickle.load(f)
    return models, train_stats


def models_are_stale(path: Path = MODEL_DIR, max_age_days: int = 7) -> bool:
    from datetime import datetime
    p = Path(path) / 'expected_return.pkl'
    if not p.exists():
        return True
    age = (datetime.now().timestamp() - p.stat().st_mtime) / 86400
    return age > max_age_days
