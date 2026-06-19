"""
BKT -- Bayesian Knowledge Tracing (Corbett & Anderson 1994)
4 params per KC: P_L0, P_T, P_S, P_G
Fitted via L-BFGS-B on negative log-likelihood.
"""
import json, pickle
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from sklearn.metrics import mean_squared_error, roc_auc_score

EPS = 1e-6

class BKT:
    def __init__(self, n_kcs: int, seed: int = 42):
        self.n_kcs = n_kcs
        self.seed  = seed
        self.params = None   # (n_kcs, 4) in logit space

    @staticmethod
    def _sig(x):
        return 1.0 / (1.0 + np.exp(-x))

    def _unpack(self, theta):
        return tuple(self._sig(theta[i]) for i in range(4))

    def _nll_kc(self, theta, sequences_kc):
        P_L0, P_T, P_S, P_G = self._unpack(theta)
        loss, n = 0.0, 0
        for corr_list in sequences_kc:
            p_L = P_L0
            for correct in corr_list:
                p_c = np.clip(p_L*(1-P_S) + (1-p_L)*P_G, EPS, 1-EPS)
                y   = int(correct >= 1)
                loss -= y*np.log(p_c) + (1-y)*np.log(1-p_c)
                n   += 1
                p_Lg = (p_L*(1-P_S)/p_c) if y else (p_L*P_S/(1-p_c))
                p_Lg = np.clip(p_Lg, EPS, 1-EPS)
                p_L  = p_Lg + (1-p_Lg)*P_T
        return loss / max(n, 1)

    def fit(self, train_seqs, verbose=True):
        rng = np.random.default_rng(self.seed)
        self.params = np.zeros((self.n_kcs, 4))
        kc_data = {k: [] for k in range(self.n_kcs)}
        for seq in train_seqs:
            tmp = {}
            for kc, c in zip(seq['kc_seq'], seq['correct_seq']):
                tmp.setdefault(kc, []).append(c)
            for kc, lst in tmp.items():
                kc_data[kc].append(lst)
        for kc_id in range(self.n_kcs):
            seqs_kc = kc_data[kc_id]
            if not seqs_kc:
                continue
            theta0 = rng.uniform(-1, 1, size=4)
            res = minimize(self._nll_kc, theta0, args=(seqs_kc,),
                           method='L-BFGS-B', options={'maxiter':200})
            self.params[kc_id] = res.x
            if verbose:
                L0,T,S,G = self._unpack(res.x)
                print(f"  KC {kc_id:2d}: L0={L0:.3f} T={T:.3f} S={S:.3f} G={G:.3f} nll={res.fun:.4f}")
        return self

    def predict(self, seqs):
        assert self.params is not None
        y_true, y_pred = [], []
        for seq in seqs:
            p_L = {k: self._sig(self.params[k][0]) for k in range(self.n_kcs)}
            for kc, correct in zip(seq['kc_seq'], seq['correct_seq']):
                L0,T,S,G = self._unpack(self.params[kc])
                p_c = np.clip(p_L[kc]*(1-S) + (1-p_L[kc])*G, EPS, 1-EPS)
                y_pred.append(p_c)
                y   = int(correct >= 1)
                y_true.append(y)
                p_Lg = (p_L[kc]*(1-S)/p_c) if y else (p_L[kc]*S/(1-p_c))
                p_Lg = np.clip(p_Lg, EPS, 1-EPS)
                p_L[kc] = p_Lg + (1-p_Lg)*T
        return np.array(y_true), np.array(y_pred)

    def evaluate(self, seqs):
        y_true, y_pred = self.predict(seqs)
        auc  = roc_auc_score(y_true, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        acc  = float(np.mean((y_pred >= 0.5).astype(int) == y_true))
        return {'auc': round(auc,4), 'rmse': round(rmse,4), 'acc': round(acc,4)}

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.save(path, self.params)
        print(f"BKT saved -> {path}")

    def load(self, path):
        self.params = np.load(path)
        return self

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parents[1]
    with open(ROOT/'data'/'processed'/'metadata.json') as f: meta=json.load(f)
    with open(ROOT/'data'/'processed'/'train_seqs.pkl','rb') as f: train=pickle.load(f)
    with open(ROOT/'data'/'processed'/'val_seqs.pkl','rb') as f: val=pickle.load(f)
    bkt = BKT(n_kcs=meta['n_kcs'])
    bkt.fit(train)
    print(bkt.evaluate(val))
