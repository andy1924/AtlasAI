"""
data_prep.py
────────────
Loads carrier_daily_series.json, engineers features,
builds sliding-window sequences, normalizes, splits temporally.

LSTM input  → (batch, seq_len=7, n_features=11)
Target reg  → next-day avg_reliability  (scaled 0-1)
Target cls  → next-day is_degraded flag (binary)

Outputs saved to ml/models/:
  scaler_params.json   feature min/max for consistent inference scaling
  data_splits.npz      X_train, y_train, X_val, y_val, X_test, y_test

Place at:  backend/ml/data_prep.py
"""

import json, numpy as np, os

ML_DIR      = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR  = os.path.join(ML_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

SERIES_PATH = os.path.join(
    os.path.dirname(ML_DIR), "maindata", "carrier_daily_series.json"
)

SEQ_LEN    = 7      # Look back 7 days → predict day 8
VAL_FRAC   = 0.15
TEST_FRAC  = 0.10

# Order matters — model expects this exact column order at inference
FEATURE_COLS = [
    "avg_reliability",    # 0  core signal
    "avg_delay_prob",     # 1  inversely correlated
    "delay_rate",         # 2  fraction delayed today
    "on_time_rate",       # 3  fraction delivered
    "carrier_load_norm",  # 4  volume stress
    "cost_per_km",        # 5  efficiency proxy
    "trend_3d",           # 6  3-day direction
    "trend_7d",           # 7  7-day direction
    "rolling_3d",         # 8  short smooth
    "rolling_7d",         # 9  long smooth
    "weekday",            # 10 seasonality (0=Mon … 6=Sun)
]
N_FEATURES = len(FEATURE_COLS)   # 11


# ── Min-max scaler ───────────────────────────────────────────────────────────

class Scaler:
    def __init__(self):
        self.lo = self.hi = self.rng = None

    def fit(self, X):                       # X: (n, n_features)
        self.lo  = X.min(axis=0)
        self.hi  = X.max(axis=0)
        self.rng = np.where((self.hi - self.lo) < 1e-8, 1.0, self.hi - self.lo)
        return self

    def transform(self, X):
        return (X - self.lo) / self.rng

    def inverse_rel(self, y_scaled):        # Undo scaling on feature 0 (reliability)
        return y_scaled * self.rng[0] + self.lo[0]

    def save(self, path):
        with open(path, "w") as f:
            json.dump({
                "lo":   self.lo.tolist(),
                "hi":   self.hi.tolist(),
                "rng":  self.rng.tolist(),
                "cols": FEATURE_COLS,
                "seq_len": SEQ_LEN,
            }, f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f: d = json.load(f)
        s = cls()
        s.lo  = np.array(d["lo"])
        s.hi  = np.array(d["hi"])
        s.rng = np.array(d["rng"])
        return s


# ── Sequence builder ─────────────────────────────────────────────────────────

def make_sequences(rows, scaler):
    """
    rows: list of daily dicts for ONE carrier, sorted by date.
    Returns X (n, SEQ_LEN, N_FEATURES), y_reg (n,), y_cls (n,)
    """
    mat = np.array([[float(r.get(c, 0)) for c in FEATURE_COLS] for r in rows], dtype=np.float32)
    mat_s = scaler.transform(mat)

    X, y_reg, y_cls = [], [], []
    for i in range(len(mat_s) - SEQ_LEN):
        X.append(mat_s[i : i + SEQ_LEN])
        t = i + SEQ_LEN
        raw_rel = float(rows[t]["avg_reliability"])
        y_reg.append((raw_rel - scaler.lo[0]) / scaler.rng[0])
        y_cls.append(float(rows[t]["is_degraded"]))

    return (np.array(X, np.float32),
            np.array(y_reg, np.float32),
            np.array(y_cls, np.float32))


# ── Main pipeline ─────────────────────────────────────────────────────────────

def prepare():
    print("📦 Data Preparation Pipeline")
    print("─" * 50)

    if not os.path.exists(SERIES_PATH):
        raise FileNotFoundError(
            f"carrier_daily_series.json not found at:\n  {SERIES_PATH}\n"
            "Run maindata/extended_simulator.py first."
        )

    with open(SERIES_PATH) as f:
        all_series = json.load(f)

    carriers = list(all_series.keys())
    print(f"Carriers: {carriers}")
    for c, rows in all_series.items():
        print(f"  {c}: {len(rows)} daily rows  "
              f"degraded={sum(r['is_degraded'] for r in rows)}/{len(rows)}")

    # Fit scaler on ALL rows combined
    all_rows_mat = np.array(
        [[float(r.get(c, 0)) for c in FEATURE_COLS]
         for rows in all_series.values() for r in rows],
        dtype=np.float32
    )
    scaler = Scaler().fit(all_rows_mat)
    scaler.save(os.path.join(MODELS_DIR, "scaler_params.json"))
    print(f"\nScaler fitted on {len(all_rows_mat)} rows.")

    # Build sequences per carrier, then split temporally
    Xtr, yr_tr, yc_tr = [], [], []
    Xva, yr_va, yc_va = [], [], []
    Xte, yr_te, yc_te = [], [], []

    for carrier, rows in all_series.items():
        rows_sorted = sorted(rows, key=lambda r: r["date"])
        X, y_reg, y_cls = make_sequences(rows_sorted, scaler)
        n = len(X)
        nt = max(1, int(n * TEST_FRAC))
        nv = max(1, int(n * VAL_FRAC))
        nr = n - nt - nv
        Xtr.append(X[:nr]);         yr_tr.append(y_reg[:nr]);   yc_tr.append(y_cls[:nr])
        Xva.append(X[nr:nr+nv]);    yr_va.append(y_reg[nr:nr+nv]); yc_va.append(y_cls[nr:nr+nv])
        Xte.append(X[nr+nv:]);      yr_te.append(y_reg[nr+nv:]); yc_te.append(y_cls[nr+nv:])
        print(f"  {carrier}: {n} seqs → train={nr} val={nv} test={nt}")

    def cat(lst): return np.concatenate(lst, axis=0)
    X_tr, yr_tr, yc_tr = cat(Xtr), cat(yr_tr), cat(yc_tr)
    X_va, yr_va, yc_va = cat(Xva), cat(yr_va), cat(yc_va)
    X_te, yr_te, yc_te = cat(Xte), cat(yr_te), cat(yc_te)

    # Shuffle train only (never shuffle time-series val/test)
    idx = np.random.permutation(len(X_tr))
    X_tr, yr_tr, yc_tr = X_tr[idx], yr_tr[idx], yc_tr[idx]

    print(f"\nFinal shapes:")
    print(f"  Train: {X_tr.shape}  class balance: {yc_tr.mean()*100:.1f}% degraded")
    print(f"  Val:   {X_va.shape}  class balance: {yc_va.mean()*100:.1f}% degraded")
    print(f"  Test:  {X_te.shape}  class balance: {yc_te.mean()*100:.1f}% degraded")

    out = os.path.join(MODELS_DIR, "data_splits.npz")
    np.savez(out,
             X_train=X_tr,  y_reg_train=yr_tr, y_cls_train=yc_tr,
             X_val=X_va,    y_reg_val=yr_va,   y_cls_val=yc_va,
             X_test=X_te,   y_reg_test=yr_te,  y_cls_test=yc_te)
    print(f"\n✅ Splits saved → {out}")

    meta = {
        "feature_cols": FEATURE_COLS, "n_features": N_FEATURES,
        "seq_len": SEQ_LEN, "carriers": carriers,
    }
    with open(os.path.join(MODELS_DIR, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    return X_tr, yr_tr, yc_tr, X_va, yr_va, yc_va, scaler


if __name__ == "__main__":
    prepare()
    print("\n✅ Done. Run  python backend/ml/train.py  next.")