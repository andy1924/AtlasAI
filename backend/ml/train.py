"""
train.py
────────
End-to-end training script.  Run this once to produce carrier_lstm.npz.

Steps:
  1. Check data splits exist  (run data_prep.py if not)
  2. Load splits + scaler
  3. Train CarrierLSTM
  4. Evaluate on held-out test set
  5. Save trained model

Place at:  backend/ml/train.py
Run:       python backend/ml/train.py
"""

import numpy as np
import json
import os
import sys

ML_DIR     = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ML_DIR, "models")
sys.path.insert(0, ML_DIR)

from data_prep   import prepare, Scaler, FEATURE_COLS
from lstm_model  import CarrierLSTM, train, evaluate


def main():
    print("=" * 65)
    print("  AtlasAI LSTM — Carrier Reliability Prediction")
    print("  Architecture: LSTM(64) → LSTM(32) → Dense(16) → [Reg, Cls]")
    print("=" * 65)

    splits_path = os.path.join(MODELS_DIR, "data_splits.npz")
    scaler_path = os.path.join(MODELS_DIR, "scaler_params.json")

    # ── Step 1: Prepare data if not already done ──────────────────
    if not os.path.exists(splits_path):
        print("\n[1/4] data_splits.npz not found — running data_prep...")
        prepare()
    else:
        print("\n[1/4] data_splits.npz found ✅")

    # ── Step 2: Load splits ───────────────────────────────────────
    print("[2/4] Loading splits and scaler...")
    d = np.load(splits_path)
    X_tr  = d["X_train"];  yr_tr = d["y_reg_train"]; yc_tr = d["y_cls_train"]
    X_va  = d["X_val"];    yr_va = d["y_reg_val"];   yc_va = d["y_cls_val"]
    X_te  = d["X_test"];   yr_te = d["y_reg_test"];  yc_te = d["y_cls_test"]
    scaler = Scaler.load(scaler_path)

    n_features = X_tr.shape[2]
    print(f"  X_train={X_tr.shape}  X_val={X_va.shape}  X_test={X_te.shape}")
    print(f"  Features: {n_features}  ({FEATURE_COLS})")
    print(f"  Train class balance: {yc_tr.mean()*100:.1f}% degraded")

    # ── Step 3: Build + train model ───────────────────────────────
    print("\n[3/4] Building CarrierLSTM...")
    model = CarrierLSTM(n_features=n_features, h1=64, h2=32, drop=0.25)

    model = train(
        model, X_tr, yr_tr, yc_tr,
               X_va, yr_va, yc_va,
        epochs=100, bs=32, patience=15,
    )

    # ── Step 4: Evaluate ──────────────────────────────────────────
    print("\n[4/4] Evaluating on held-out test set...")
    metrics = evaluate(model, X_te, yr_te, yc_te, scaler)

    # ── Step 5: Save ──────────────────────────────────────────────
    model_path = os.path.join(MODELS_DIR, "carrier_lstm.npz")
    model.save(model_path)
    print(f"\n💾 Model saved → {model_path}")

    size_kb = os.path.getsize(model_path) / 1024
    print(f"   File size: {size_kb:.1f} KB")
    print(f"   Parameters: ~{(64*(11+64+1)*4 + 32*(64+32+1)*4 + 16*32 + 1*16 + 1*16)//1000}K")

    print("\n" + "="*65)
    print("  TRAINING COMPLETE")
    print(f"  MAE  (reliability prediction): {metrics['mae']:.4f}")
    print(f"  F1   (degradation detection):  {metrics['f1']:.3f}")
    print(f"  Acc  (degradation detection):  {metrics['accuracy']:.3f}")
    print("="*65)
    print("\n✅ Run  python backend/ml/predictor.py  to test inference.")


if __name__ == "__main__":
    main()