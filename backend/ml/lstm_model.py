"""
lstm_model.py
─────────────
Pure NumPy LSTM — zero external ML dependencies.
Equivalent in architecture to a Keras LSTM model.

Architecture
  Input  (batch, 7, 11)
    → LSTM Layer 1  hidden=64  return_sequences=True
    → Dropout 0.25
    → LSTM Layer 2  hidden=32
    → Dropout 0.25
    → Dense(16, tanh)
    → Head A: Dense(1, sigmoid)  →  predicted_reliability  [regression]
    → Head B: Dense(1, sigmoid)  →  degradation_prob       [classification]

Loss  =  0.65 × MSE(reliability)  +  0.35 × BCE(is_degraded)
Optimizer: Adam  lr=0.001  β1=0.9  β2=0.999
Epochs: 100  Batch: 32  Early-stop patience: 15

Place at:  backend/ml/lstm_model.py
"""

import numpy as np

np.random.seed(42)


# ═══════════════════════════════════════════════════════════════
# ACTIVATIONS
# ═══════════════════════════════════════════════════════════════

def _sig(x):
    x = np.clip(x, -500, 500)
    return np.where(x >= 0, 1/(1+np.exp(-x)), np.exp(x)/(1+np.exp(x)))

def _tanh(x):  return np.tanh(np.clip(x, -500, 500))
def _dsig(s):  return s * (1 - s)
def _dtanh(t): return 1.0 - t*t


# ═══════════════════════════════════════════════════════════════
# LSTM LAYER
# Processes a full (batch, seq_len, input_size) tensor
# ═══════════════════════════════════════════════════════════════

class LSTM:
    def __init__(self, in_size, hid_size, return_seq=False):
        self.H = hid_size
        self.I = in_size
        self.return_seq = return_seq

        # All 4 gates packed into one matrix: [I+H, 4H]
        # Order: forget | input | cell | output
        sc = np.sqrt(2.0 / (in_size + hid_size))
        self.W = np.random.randn(in_size + hid_size, 4 * hid_size).astype(np.float32) * sc
        self.b = np.zeros(4 * hid_size, dtype=np.float32)

        # Adam moments
        self.mW = np.zeros_like(self.W); self.vW = np.zeros_like(self.W)
        self.mb = np.zeros_like(self.b); self.vb = np.zeros_like(self.b)

    # ── Forward ──────────────────────────────────────────────────
    def forward(self, X, drop_masks=None):
        """X: (B, T, I)  →  out: (B, T, H) or (B, H)"""
        B, T, _ = X.shape
        H = self.H
        h = np.zeros((B, H), np.float32)
        c = np.zeros((B, H), np.float32)
        self._caches = []
        hs = []

        for t in range(T):
            xh   = np.concatenate([X[:, t], h], axis=1)      # (B, I+H)
            raw  = xh @ self.W + self.b                        # (B, 4H)
            f    = _sig( raw[:, 0*H:1*H])
            i_   = _sig( raw[:, 1*H:2*H])
            g    = _tanh(raw[:, 2*H:3*H])
            o    = _sig( raw[:, 3*H:4*H])
            c    = f*c + i_*g
            tc   = _tanh(c)
            h    = o * tc
            if drop_masks is not None and drop_masks[t] is not None:
                h = h * drop_masks[t]
            self._caches.append((X[:, t], h if drop_masks is None else h/max(drop_masks[t].mean(),1e-6),
                                 c, f, i_, g, o, tc, xh))
            # Store pre-dropout h for backprop cache
            hs.append(h)

        self._all_h = np.stack(hs, axis=1)   # (B, T, H)
        self._last_h = h; self._last_c = c
        return self._all_h if self.return_seq else h

    # ── Backward ─────────────────────────────────────────────────
    def backward(self, dout, drop_masks=None):
        """dout: (B,T,H) or (B,H)  →  dX: (B,T,I)"""
        T = len(self._caches)
        B = dout.shape[0]
        H = self.H

        if not self.return_seq:
            dh_t = np.zeros((B, T, H), np.float32)
            dh_t[:, -1] = dout
        else:
            dh_t = dout

        dX     = np.zeros((B, T, self.I), np.float32)
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)
        dh_n   = np.zeros((B, H), np.float32)
        dc_n   = np.zeros((B, H), np.float32)

        for t in reversed(range(T)):
            xt, ht, ct, f, i_, g, o, tc, xh = self._caches[t]
            # Previous cell state (c at t-1)
            ct_prev = self._caches[t-1][2] if t > 0 else np.zeros_like(ct)

            dh  = dh_t[:, t] + dh_n
            if drop_masks is not None and drop_masks[t] is not None:
                dh = dh * drop_masks[t]

            do  = dh * tc
            dtc = dh * o
            dc  = dtc * _dtanh(tc) + dc_n
            df  = dc * ct_prev
            di_ = dc * g
            dg  = dc * i_
            dc_n = dc * f

            dg_raw  = dg  * _dtanh(g)
            df_raw  = df  * _dsig(f)
            di_raw  = di_ * _dsig(i_)
            do_raw  = do  * _dsig(o)

            dgate = np.concatenate([df_raw, di_raw, dg_raw, do_raw], axis=1)  # (B,4H)
            self.dW += np.clip(xh.T @ dgate, -5, 5)
            self.db += np.clip(dgate.sum(0),  -5, 5)
            dxh  = dgate @ self.W.T
            dX[:, t]  = dxh[:, :self.I]
            dh_n      = dxh[:, self.I:]

        return dX


# ═══════════════════════════════════════════════════════════════
# DENSE LAYER
# ═══════════════════════════════════════════════════════════════

class Dense:
    def __init__(self, in_size, out_size, act="tanh"):
        sc = np.sqrt(2.0 / in_size)
        self.W  = np.random.randn(in_size, out_size).astype(np.float32) * sc
        self.b  = np.zeros(out_size, np.float32)
        self.act = act
        self.mW = np.zeros_like(self.W); self.vW = np.zeros_like(self.W)
        self.mb = np.zeros_like(self.b); self.vb = np.zeros_like(self.b)

    def forward(self, x):
        self._x = x
        z = x @ self.W + self.b
        if   self.act == "tanh":    self._out = _tanh(z)
        elif self.act == "sigmoid": self._out = _sig(z)
        else:                       self._out = z
        return self._out

    def backward(self, dout):
        if   self.act == "tanh":    dz = dout * _dtanh(self._out)
        elif self.act == "sigmoid": dz = dout * _dsig(self._out)
        else:                       dz = dout
        self.dW = np.clip(self._x.T @ dz, -5, 5)
        self.db = np.clip(dz.sum(0),       -5, 5)
        return dz @ self.W.T


# ═══════════════════════════════════════════════════════════════
# ADAM UPDATE  (shared helper)
# ═══════════════════════════════════════════════════════════════

def _adam(layer, t, lr=0.001, b1=0.9, b2=0.999, eps=1e-8):
    for pn, dpn, mn, vn in [("W","dW","mW","vW"),("b","db","mb","vb")]:
        p  = getattr(layer, pn);  dp = getattr(layer, dpn)
        m  = getattr(layer, mn);  v  = getattr(layer, vn)
        m  = b1*m + (1-b1)*dp
        v  = b2*v + (1-b2)*dp**2
        p -= lr * (m/(1-b1**t)) / (np.sqrt(v/(1-b2**t)) + eps)
        setattr(layer, pn, p); setattr(layer, mn, m); setattr(layer, vn, v)


# ═══════════════════════════════════════════════════════════════
# CARRIER LSTM MODEL
# ═══════════════════════════════════════════════════════════════

class CarrierLSTM:
    def __init__(self, n_features=11, h1=64, h2=32, drop=0.25):
        self.lstm1   = LSTM(n_features, h1, return_seq=True)
        self.lstm2   = LSTM(h1, h2,         return_seq=False)
        self.dense   = Dense(h2, 16,  "tanh")
        self.head_r  = Dense(16,  1,  "sigmoid")   # Reliability regression
        self.head_c  = Dense(16,  1,  "sigmoid")   # Degradation classification
        self.drop    = drop
        self.t       = 0                            # Adam step counter
        self.tr_loss = []
        self.va_loss = []

    # ── Dropout masks ────────────────────────────────────────────
    def _masks(self, B, T, H, training):
        if not training or self.drop == 0:
            return None
        scale = 1.0 / (1.0 - self.drop)
        return [
            (np.random.rand(B, H) > self.drop).astype(np.float32) * scale
            for _ in range(T)
        ]

    # ── Forward ──────────────────────────────────────────────────
    def forward(self, X, training=False):
        B, T, _ = X.shape
        m1 = self._masks(B, T, self.lstm1.H, training)
        o1 = self.lstm1.forward(X,  drop_masks=m1)      # (B, T, 64)
        m2 = self._masks(B, 1, self.lstm2.H, training)
        o2_raw = self.lstm2.forward(o1)                   # (B, 32)
        if training and m2:
            self._m2 = m2[0]; o2 = o2_raw * m2[0]
        else:
            self._m2 = None;  o2 = o2_raw
        self._o1_masks = m1; self._o2_raw = o2_raw
        d  = self.dense.forward(o2)
        pr = self.head_r.forward(d).squeeze(-1)           # (B,)
        pc = self.head_c.forward(d).squeeze(-1)           # (B,)
        return pr, pc

    # ── Loss ─────────────────────────────────────────────────────
    def loss(self, pr, pc, yr, yc, alpha=0.65):
        mse = float(np.mean((pr - yr)**2))
        bce = float(-np.mean(yc*np.log(pc+1e-7) + (1-yc)*np.log(1-pc+1e-7)))
        return alpha*mse + (1-alpha)*bce, mse, bce

    # ── Backward ─────────────────────────────────────────────────
    def backward(self, pr, pc, yr, yc, alpha=0.65):
        B = len(yr)
        dr = 2*alpha*(pr - yr)/B
        dc = (1-alpha)*((pc - yc)/np.clip(pc*(1-pc), 1e-7, None))/B
        dc = np.clip(dc, -5, 5)
        dd_r = self.head_r.backward(dr.reshape(-1, 1))
        dd_c = self.head_c.backward(dc.reshape(-1, 1))
        dd   = dd_r + dd_c
        do2  = self.dense.backward(dd)
        if self._m2 is not None:
            do2 = do2 * self._m2
        do1 = self.lstm2.backward(do2)
        self.lstm1.backward(do1, self._o1_masks)

    # ── Weight update ────────────────────────────────────────────
    def step(self):
        self.t += 1
        for layer in [self.lstm1, self.lstm2, self.dense, self.head_r, self.head_c]:
            _adam(layer, self.t)

    # ── Serialise ────────────────────────────────────────────────
    def save(self, path):
        np.savez(path,
            l1W=self.lstm1.W,   l1b=self.lstm1.b,
            l2W=self.lstm2.W,   l2b=self.lstm2.b,
            dW=self.dense.W,    db=self.dense.b,
            hrW=self.head_r.W,  hrb=self.head_r.b,
            hcW=self.head_c.W,  hcb=self.head_c.b,
            tr_loss=np.array(self.tr_loss),
            va_loss=np.array(self.va_loss),
        )

    def load(self, path):
        d = np.load(path)
        self.lstm1.W  = d["l1W"]; self.lstm1.b  = d["l1b"]
        self.lstm2.W  = d["l2W"]; self.lstm2.b  = d["l2b"]
        self.dense.W  = d["dW"];  self.dense.b  = d["db"]
        self.head_r.W = d["hrW"]; self.head_r.b = d["hrb"]
        self.head_c.W = d["hcW"]; self.head_c.b = d["hcb"]
        if "tr_loss" in d:
            self.tr_loss = d["tr_loss"].tolist()
            self.va_loss = d["va_loss"].tolist()


# ═══════════════════════════════════════════════════════════════
# TRAINING LOOP
# ═══════════════════════════════════════════════════════════════

def train(model, X_tr, yr_tr, yc_tr, X_va, yr_va, yc_va,
          epochs=100, bs=32, patience=15):

    n = len(X_tr)
    best_val  = float("inf")
    best_path = "/tmp/_atlasai_best.npz"
    wait = 0

    print(f"\n🚀 Training  train={n}  val={len(X_va)}  epochs={epochs}  batch={bs}")
    print("─"*65)
    fmt = "  Ep {:3d}/{} | tr={:.5f}  va={:.5f}  mse={:.5f}  bce={:.5f}  p={}/{}"

    for ep in range(1, epochs+1):
        idx = np.random.permutation(n)
        Xs  = X_tr[idx]; yrs = yr_tr[idx]; ycs = yc_tr[idx]
        batch_losses = []

        for s in range(0, n, bs):
            Xb = Xs[s:s+bs]; yrb = yrs[s:s+bs]; ycb = ycs[s:s+bs]
            pr, pc = model.forward(Xb, training=True)
            l, _, _ = model.loss(pr, pc, yrb, ycb)
            model.backward(pr, pc, yrb, ycb)
            model.step()
            batch_losses.append(l)

        tr_l = float(np.mean(batch_losses))

        pr_v, pc_v = model.forward(X_va, training=False)
        va_l, va_mse, va_bce = model.loss(pr_v, pc_v, yr_va, yc_va)
        va_l = float(va_l)

        model.tr_loss.append(tr_l)
        model.va_loss.append(va_l)

        if va_l < best_val - 1e-5:
            best_val = va_l; wait = 0
            model.save(best_path)
        else:
            wait += 1

        if ep % 10 == 0 or ep == 1:
            print(fmt.format(ep, epochs, tr_l, va_l, va_mse, va_bce, wait, patience))

        if wait >= patience:
            print(f"\n⏹  Early stop  ep={ep}  best_val={best_val:.5f}")
            break

    import os
    if os.path.exists(best_path):
        model.load(best_path)
        os.remove(best_path)
    print(f"\n✅ Training done.  best_val_loss={best_val:.5f}")
    return model


# ═══════════════════════════════════════════════════════════════
# EVALUATION
# ═══════════════════════════════════════════════════════════════

def evaluate(model, X_te, yr_te, yc_te, scaler):
    import json, os
    pr, pc = model.forward(X_te, training=False)

    pred_rel = pr * scaler.rng[0] + scaler.lo[0]
    true_rel = yr_te * scaler.rng[0] + scaler.lo[0]

    mae  = float(np.mean(np.abs(pred_rel - true_rel)))
    rmse = float(np.sqrt(np.mean((pred_rel - true_rel)**2)))

    pred_bin = (pc >= 0.5).astype(int)
    true_bin = yc_te.astype(int)
    acc  = float(np.mean(pred_bin == true_bin))
    tp   = int(np.sum((pred_bin==1)&(true_bin==1)))
    fp   = int(np.sum((pred_bin==1)&(true_bin==0)))
    fn   = int(np.sum((pred_bin==0)&(true_bin==1)))
    prec = tp / max(tp+fp, 1)
    rec  = tp / max(tp+fn, 1)
    f1   = 2*prec*rec / max(prec+rec, 1e-8)

    print("\n📊 Test-set evaluation")
    print("─"*40)
    print(f"  Regression  — MAE={mae:.4f}  RMSE={rmse:.4f}")
    print(f"  Classification — Acc={acc:.3f}  Prec={prec:.3f}  Rec={rec:.3f}  F1={f1:.3f}")

    metrics = dict(mae=mae, rmse=rmse, accuracy=acc,
                   precision=prec, recall=rec, f1=f1,
                   test_n=len(X_te))

    MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    with open(os.path.join(MODELS_DIR, "eval_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    return metrics