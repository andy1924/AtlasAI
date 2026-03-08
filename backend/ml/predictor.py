"""
predictor.py
────────────
Loads the trained LSTM and serves real-time carrier predictions.

Public API (imported by agent.py and main.py):
  refresh_predictions(shipments)         → updates cache from live data
  get_predicted_reliability(carrier)     → float  (used by agent risk scorer)
  get_all_predictions()                  → dict   (used by /api/ml-predictions)
  get_forecast(carrier, days, shipments) → list   (used by /api/ml-forecast)

Place at:  backend/ml/predictor.py
"""

import json, numpy as np, os, sys
from datetime import datetime, timedelta

ML_DIR     = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ML_DIR, "models")
sys.path.insert(0, ML_DIR)

CARRIERS = ["DHL", "FedEx", "UPS", "BlueDart", "Maersk"]

# Lazy-loaded globals
_model   = None
_scaler  = None
_cols    = None
_seq_len = 7
_cache: dict = {}
_loaded = False

SERIES_PATH = os.path.join(
    os.path.dirname(ML_DIR), "maindata", "carrier_daily_series.json"
)

# Carrier fallback baselines (from real AtlasAI data)
_BASELINES = {"DHL": 0.87, "FedEx": 0.85, "UPS": 0.83, "BlueDart": 0.83, "Maersk": 0.85}


# ── Lazy load ───────────────────────────────────────────────────────────────

def _load():
    global _model, _scaler, _cols, _seq_len, _loaded
    from lstm_model import CarrierLSTM
    from data_prep  import Scaler, FEATURE_COLS, SEQ_LEN

    mp = os.path.join(MODELS_DIR, "carrier_lstm.npz")
    sp = os.path.join(MODELS_DIR, "scaler_params.json")

    if not os.path.exists(mp):
        raise FileNotFoundError(
            f"Model not found at {mp}.\nRun: python backend/ml/train.py"
        )

    _model = CarrierLSTM(n_features=len(FEATURE_COLS), h1=64, h2=32)
    _model.load(mp)
    _scaler  = Scaler.load(sp)
    _cols    = FEATURE_COLS
    _seq_len = SEQ_LEN
    _loaded  = True
    print("🧠 [LSTM Predictor] Model loaded.")


# ── Feature row builder ──────────────────────────────────────────────────────

def _row_to_vec(row: dict) -> list:
    return [float(row.get(c, 0.0)) for c in _cols]


# ── Run one inference step ───────────────────────────────────────────────────

def _infer(window: np.ndarray):
    """
    window: (seq_len, n_features) unscaled
    Returns: (pred_reliability, degradation_prob)
    """
    X_raw = window.reshape(-1, len(_cols))
    X_s   = _scaler.transform(X_raw).reshape(1, _seq_len, len(_cols))
    pr, pc = _model.forward(X_s, training=False)
    rel = float(pr[0]) * _scaler.rng[0] + _scaler.lo[0]
    rel = float(np.clip(rel, 0.50, 0.99))
    deg = float(pc[0])
    return rel, deg


# ── Build recent feature window from live shipments ──────────────────────────

def _live_window(carrier: str, shipments) -> list | None:
    """
    Builds last seq_len daily rows for carrier from a list of live shipment
    objects (Pydantic or dict). Returns None if insufficient history.
    """
    from collections import defaultdict
    by_date = defaultdict(list)

    for s in shipments:
        c = getattr(s, "carrier", None) or (s.get("carrier") if isinstance(s, dict) else None)
        if c != carrier:
            continue
        ts = getattr(s, "timestamp", None) or (s.get("timestamp") if isinstance(s, dict) else "")
        date = str(ts)[:10]
        by_date[date].append(s)

    if len(by_date) < _seq_len:
        return None

    def gf(s, f, default=0.0):
        v = getattr(s, f, None)
        if v is None and isinstance(s, dict): v = s.get(f)
        return float(v) if v is not None else default

    rows = []
    for date in sorted(by_date)[-_seq_len:]:
        bucket = by_date[date]
        n = len(bucket)
        rels   = [gf(s, "partner_reliability", 0.84) for s in bucket]
        delays = [gf(s, "delay_probability",   0.25) for s in bucket]
        costs  = [gf(s, "operational_cost",   3000)  for s in bucket]
        dists  = [gf(s, "distance_km",         500)  for s in bucket]
        stats  = [getattr(s, "status", None) or (s.get("status") if isinstance(s, dict) else "") for s in bucket]
        n_del  = sum(1 for st in stats if st == "Delayed")
        n_dlv  = sum(1 for st in stats if st == "Delivered")
        avg_r  = float(np.mean(rels))
        avg_d  = float(np.mean(delays))
        cpkm   = float(np.mean([c/max(d,1) for c,d in zip(costs,dists)]))
        # Rolling features
        past3  = [r["avg_reliability"] for r in rows[-3:]] or [avg_r]
        past7  = [r["avg_reliability"] for r in rows[-7:]] or [avg_r]
        rows.append({
            "avg_reliability":   avg_r,
            "avg_delay_prob":    avg_d,
            "delay_rate":        n_del/n,
            "on_time_rate":      n_dlv/n,
            "carrier_load_norm": n/35.0,
            "cost_per_km":       cpkm,
            "trend_3d":          avg_r - past3[0],
            "trend_7d":          avg_r - past7[0],
            "rolling_3d":        float(np.mean(past3)),
            "rolling_7d":        float(np.mean(past7)),
            "weekday":           datetime.strptime(date, "%Y-%m-%d").weekday(),
        })
    return rows if len(rows) >= _seq_len else None


def _stored_window(carrier: str) -> list | None:
    """Fall back to carrier_daily_series.json."""
    if not os.path.exists(SERIES_PATH):
        return None
    with open(SERIES_PATH) as f:
        all_series = json.load(f)
    rows = sorted(all_series.get(carrier, []), key=lambda r: r["date"])
    return rows[-_seq_len:] if len(rows) >= _seq_len else None


def _synthetic_window(carrier: str) -> list:
    """Last resort — plausible synthetic window."""
    base = _BASELINES.get(carrier, 0.84)
    rows, rel = [], base
    for i in range(_seq_len):
        rel = float(np.clip(rel + np.random.normal(0, 0.006), 0.65, 0.99))
        rows.append({
            "avg_reliability": rel, "avg_delay_prob": 1-rel+0.05,
            "delay_rate": max(0.05, 1-rel), "on_time_rate": max(0.2, rel-0.1),
            "carrier_load_norm": 0.85, "cost_per_km": 5.0,
            "trend_3d": 0.0, "trend_7d": 0.0,
            "rolling_3d": rel, "rolling_7d": rel, "weekday": i%7,
        })
    return rows


# ── Public API ───────────────────────────────────────────────────────────────

def refresh_predictions(shipments=None):
    """Re-run inference for all carriers. Call at start of each agent cycle."""
    global _cache
    if not _loaded: _load()

    new_cache = {}
    for carrier in CARRIERS:
        try:
            window = (
                (_live_window(carrier, shipments) if shipments else None)
                or _stored_window(carrier)
                or _synthetic_window(carrier)
            )
            mat = np.array([_row_to_vec(r) for r in window], dtype=np.float32)
            pred_rel, deg_prob = _infer(mat)
            curr_rel = float(window[-1]["avg_reliability"])
            trend    = pred_rel - curr_rel

            new_cache[carrier] = {
                "predicted_reliability":  round(pred_rel, 4),
                "degradation_probability":round(deg_prob,  4),
                "current_reliability":    round(curr_rel,  4),
                "trend":                  round(trend,     4),
                "is_degrading":           bool(trend < -0.015),
                "is_degraded":            bool(pred_rel < 0.80),
                "risk_flag": (
                    "🔴 HIGH"  if pred_rel < 0.72 else
                    "🟡 WATCH" if pred_rel < 0.82 else
                    "🟢 GOOD"
                ),
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"  ⚠️ [Predictor] {carrier}: {e}")
            new_cache[carrier] = {
                "predicted_reliability": _BASELINES.get(carrier, 0.84),
                "degradation_probability": 0.20,
                "current_reliability": _BASELINES.get(carrier, 0.84),
                "trend": 0.0, "is_degrading": False, "is_degraded": False,
                "risk_flag": "🟡 WATCH",
                "last_updated": datetime.now().isoformat(),
                "error": str(e),
            }

    _cache = new_cache
    carriers_flagged = sum(1 for v in _cache.values() if v["is_degraded"])
    print(f"🔮 [LSTM] Predictions refreshed — {carriers_flagged}/{len(CARRIERS)} carriers degraded.")
    return _cache


def get_predicted_reliability(carrier: str) -> float:
    """Used by agent.py auto_flag_at_risk() to replace static reliability."""
    if not _cache:
        try: refresh_predictions()
        except: return _BASELINES.get(carrier, 0.84)
    return _cache.get(carrier, {}).get("predicted_reliability", _BASELINES.get(carrier, 0.84))


def get_all_predictions() -> dict:
    if not _cache:
        try: refresh_predictions()
        except: return {}
    return _cache


def get_forecast(carrier: str, days: int = 3, shipments=None) -> list:
    """Autoregressive multi-step forecast."""
    if not _loaded: _load()
    window = (
        (_live_window(carrier, shipments) if shipments else None)
        or _stored_window(carrier)
        or _synthetic_window(carrier)
    )
    rows = [_row_to_vec(r) for r in window]
    forecasts = []

    for day_ahead in range(1, days+1):
        mat = np.array(rows[-_seq_len:], dtype=np.float32)
        pred_rel, deg_prob = _infer(mat)
        date = (datetime.now() + timedelta(days=day_ahead)).strftime("%Y-%m-%d")
        forecasts.append({
            "day": day_ahead, "date": date,
            "predicted_reliability":   round(pred_rel,  4),
            "degradation_probability": round(deg_prob,  4),
            "is_degraded": bool(pred_rel < 0.80),
            "risk_flag": (
                "🔴 HIGH"  if pred_rel < 0.72 else
                "🟡 WATCH" if pred_rel < 0.82 else
                "🟢 GOOD"
            ),
        })
        # Append predicted row (autoregressive — feed prediction back as input)
        last = dict(zip(_cols, rows[-1]))
        last["avg_reliability"] = pred_rel
        last["trend_3d"]  = pred_rel - float(rows[-3][_cols.index("avg_reliability")] if len(rows) >= 3 else pred_rel)
        last["rolling_3d"]= float(np.mean([rows[j][_cols.index("avg_reliability")] for j in range(-3, 0)]))
        rows.append([last.get(c, 0.0) for c in _cols])

    return forecasts


# ── CLI diagnostics ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔮 AtlasAI LSTM Predictor — Diagnostics")
    print("=" * 60)

    preds = refresh_predictions()
    print(f"\n{'Carrier':<12} {'Pred':>8} {'Curr':>8} {'Trend':>8} {'DegProb':>9} Flag")
    print("─" * 55)
    for c, p in preds.items():
        print(f"  {c:<10} {p['predicted_reliability']:>8.4f} {p['current_reliability']:>8.4f} "
              f"{p['trend']:>+8.4f} {p['degradation_probability']:>9.4f}  {p['risk_flag']}")

    print("\n📅 3-Day Forecast — UPS (most volatile carrier):")
    for f in get_forecast("UPS", days=3):
        print(f"  Day +{f['day']} ({f['date']})  rel={f['predicted_reliability']:.4f}  {f['risk_flag']}")

    print("\n✅ Predictor OK.")