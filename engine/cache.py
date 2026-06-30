import json
from datetime import datetime
from pathlib import Path
from config import SCAN_CACHE, JOURNAL_FILE, PRED_HISTORY


class _Encoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'item'):   return obj.item()   # numpy scalar
        if hasattr(obj, 'tolist'): return obj.tolist()  # numpy array
        if isinstance(obj, datetime): return obj.isoformat()
        return super().default(obj)


def save_scan(result_dict: dict, path: Path = SCAN_CACHE) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, cls=_Encoder, indent=2)


def load_scan(path: Path = SCAN_CACHE) -> dict | None:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def scan_age_minutes(path: Path = SCAN_CACHE) -> float | None:
    p = Path(path)
    if not p.exists():
        return None
    age = (datetime.now().timestamp() - p.stat().st_mtime) / 60
    return round(age, 1)


def append_journal(date_str: str, top10: list[dict],
                   path: Path = JOURNAL_FILE) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            journal = json.load(f)
    except Exception:
        journal = []

    entry = {
        'date': date_str,
        'top10': [{'ticker': r['ticker'], 'confidence': r['confidence'],
                   'expected_return': r['expected_return'],
                   'rating': r['rating']}
                  for r in top10[:10]]
    }
    journal = [e for e in journal if e['date'] != date_str]
    journal.append(entry)
    journal.sort(key=lambda x: x['date'])

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(journal, f, cls=_Encoder, indent=2)


def load_journal(path: Path = JOURNAL_FILE) -> list[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def append_prediction_history(date_str: str, predictions: list[dict],
                               path: Path = PRED_HISTORY) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except Exception:
        history = []

    entry = {
        'scan_date': date_str,
        'horizon_end': None,    # filled when actual return is known
        'predictions': [
            {'ticker': r['ticker'], 'predicted_return': r['expected_return'],
             'actual_return': None, 'error': None}
            for r in predictions
        ]
    }
    history = [e for e in history if e['scan_date'] != date_str]
    history.append(entry)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, cls=_Encoder, indent=2)


def load_prediction_history(path: Path = PRED_HISTORY) -> list[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []
