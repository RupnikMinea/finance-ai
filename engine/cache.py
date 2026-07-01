import json
import os
from datetime import datetime
from pathlib import Path
from config import SCAN_CACHE, JOURNAL_FILE, PRED_HISTORY


class _Encoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'item'):   return obj.item()
        if hasattr(obj, 'tolist'): return obj.tolist()
        if isinstance(obj, datetime): return obj.isoformat()
        return super().default(obj)


def _get_supabase():
    url = os.getenv('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_KEY', '')
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def save_scan(result_dict: dict, path: Path = SCAN_CACHE) -> None:
    sb = _get_supabase()
    if sb:
        try:
            sb.table('scan_cache').upsert({'id': 'latest', 'data': result_dict}).execute()
        except Exception as e:
            import sys
            print(f'[cache] Supabase save_scan failed: {e}', file=sys.stderr)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, cls=_Encoder, indent=2)


def load_scan(path: Path = SCAN_CACHE) -> dict | None:
    sb = _get_supabase()
    if sb:
        try:
            res = sb.table('scan_cache').select('data').eq('id', 'latest').execute()
            if res.data:
                return res.data[0]['data']
        except Exception:
            pass
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def scan_age_minutes(path: Path = SCAN_CACHE) -> float | None:
    sb = _get_supabase()
    if sb:
        try:
            res = sb.table('scan_cache').select('updated_at').eq('id', 'latest').execute()
            if res.data:
                updated = datetime.fromisoformat(res.data[0]['updated_at'].replace('Z', '+00:00'))
                age = (datetime.now().astimezone() - updated).total_seconds() / 60
                return round(age, 1)
        except Exception:
            pass
    p = Path(path)
    if not p.exists():
        return None
    return round((datetime.now().timestamp() - p.stat().st_mtime) / 60, 1)


def append_journal(date_str: str, top10: list[dict],
                   path: Path = JOURNAL_FILE) -> None:
    sb = _get_supabase()
    entry = {
        'date': date_str,
        'top10': [{'ticker': r['ticker'], 'confidence': r['confidence'],
                   'expected_return': r['expected_return'],
                   'rating': r['rating']}
                  for r in top10[:10]]
    }
    if sb:
        try:
            sb.table('ai_journal').upsert({'date': date_str, 'data': entry}).execute()
        except Exception:
            pass
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            journal = json.load(f)
    except Exception:
        journal = []
    journal = [e for e in journal if e['date'] != date_str]
    journal.append(entry)
    journal.sort(key=lambda x: x['date'])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(journal, f, cls=_Encoder, indent=2)


def load_journal(path: Path = JOURNAL_FILE) -> list[dict]:
    sb = _get_supabase()
    if sb:
        try:
            res = sb.table('ai_journal').select('data').order('date', desc=True).limit(30).execute()
            if res.data:
                return [r['data'] for r in res.data]
        except Exception:
            pass
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def append_prediction_history(date_str: str, predictions: list[dict],
                               path: Path = PRED_HISTORY) -> None:
    entry = {
        'scan_date': date_str,
        'horizon_end': None,
        'predictions': [
            {'ticker': r['ticker'], 'predicted_return': r['expected_return'],
             'actual_return': None, 'error': None}
            for r in predictions
        ]
    }
    sb = _get_supabase()
    if sb:
        try:
            sb.table('prediction_history').upsert({'scan_date': date_str, 'data': entry}).execute()
        except Exception:
            pass
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except Exception:
        history = []
    history = [e for e in history if e['scan_date'] != date_str]
    history.append(entry)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, cls=_Encoder, indent=2)


def load_prediction_history(path: Path = PRED_HISTORY) -> list[dict]:
    sb = _get_supabase()
    if sb:
        try:
            res = sb.table('prediction_history').select('data').order('scan_date', desc=True).limit(90).execute()
            if res.data:
                return [r['data'] for r in res.data]
        except Exception:
            pass
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []
