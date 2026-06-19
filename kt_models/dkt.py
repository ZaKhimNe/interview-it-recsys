"""
DKT -- Deep Knowledge Tracing (Piech et al. 2015)
LSTM, input = one-hot(2*n_kcs), output = sigmoid(n_kcs)
Mode: binary (BCE) | quality (MSE on quality_norm 0/0.5/1)
"""
import json, pickle
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import mean_squared_error, roc_auc_score
from torch.utils.data import DataLoader, Dataset


class KTDataset(Dataset):
    def __init__(self, seqs, n_kcs, mode='binary', max_len=200):
        self.seqs, self.n_kcs, self.mode, self.max_len = seqs, n_kcs, mode, max_len

    def __len__(self): return len(self.seqs)

    def __getitem__(self, idx):
        seq = self.seqs[idx]
        kc_seq, correct, q_norm = seq['kc_seq'], seq['correct_seq'], seq['quality_seq']
        T = min(len(kc_seq) - 1, self.max_len)
        if T <= 0:
            return torch.zeros(1, 2*self.n_kcs), torch.zeros(1), torch.zeros(1, dtype=torch.long), torch.zeros(1)
        x = torch.zeros(T, 2*self.n_kcs)
        for t in range(T):
            kc = kc_seq[t]
            x[t, kc if correct[t] >= 1 else kc + self.n_kcs] = 1.0
        if self.mode == 'binary':
            y = torch.tensor([float(correct[t+1] >= 1) for t in range(T)], dtype=torch.float32)
        else:
            y = torch.tensor([float(q_norm[t+1]) for t in range(T)], dtype=torch.float32)
        kc_next = torch.tensor(kc_seq[1:T+1], dtype=torch.long)
        return x, y, kc_next, torch.ones(T)


def collate_fn(batch):
    xs, ys, kcs, masks = zip(*batch)
    max_T = max(x.shape[0] for x in xs)
    n2 = xs[0].shape[1]
    xp = torch.zeros(len(xs), max_T, n2)
    yp = torch.zeros(len(ys), max_T)
    kp = torch.zeros(len(kcs), max_T, dtype=torch.long)
    mp = torch.zeros(len(masks), max_T)
    for i, (x, y, k, m) in enumerate(zip(xs, ys, kcs, masks)):
        T = x.shape[0]
        xp[i,:T] = x; yp[i,:T] = y; kp[i,:T] = k; mp[i,:T] = m
    return xp, yp, kp, mp


class DKTModel(nn.Module):
    def __init__(self, n_kcs, hidden=128, layers=1, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(2*n_kcs, hidden, layers, batch_first=True,
                            dropout=dropout if layers > 1 else 0.0)
        self.drop = nn.Dropout(dropout)
        self.fc   = nn.Linear(hidden, n_kcs)

    def forward(self, x):
        h, _ = self.lstm(x)
        return torch.sigmoid(self.fc(self.drop(h)))


class DKT:
    def __init__(self, n_kcs, mode='binary', hidden_size=128, n_layers=1,
                 dropout=0.2, lr=1e-3, batch_size=64, epochs=30,
                 patience=5, max_len=200, device=None, seed=42):
        self.n_kcs, self.mode, self.hidden_size = n_kcs, mode, hidden_size
        self.n_layers, self.dropout, self.lr = n_layers, dropout, lr
        self.batch_size, self.epochs, self.patience = batch_size, epochs, patience
        self.max_len, self.seed = max_len, seed
        torch.manual_seed(seed); np.random.seed(seed)
        self.device = torch.device(device if device else ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.model = None
        self.history = {'train_loss': [], 'val_loss': [], 'val_auc': []}

    def _loader(self, seqs, shuffle=False):
        return DataLoader(KTDataset(seqs, self.n_kcs, self.mode, self.max_len),
                          batch_size=self.batch_size, shuffle=shuffle, collate_fn=collate_fn)

    def _loss(self, pred, target, mask):
        fn = nn.functional.binary_cross_entropy if self.mode == 'binary' else nn.functional.mse_loss
        return (fn(pred, target, reduction='none') * mask).sum() / mask.sum().clamp(min=1)

    def _epoch(self, loader, opt=None):
        self.model.train() if opt else self.model.eval()
        total, yt, yp = 0.0, [], []
        with torch.set_grad_enabled(opt is not None):
            for xs, ys, kcs, ms in loader:
                xs, ys, kcs, ms = xs.to(self.device), ys.to(self.device), kcs.to(self.device), ms.to(self.device)
                out  = self.model(xs)
                pred = out.gather(2, kcs.unsqueeze(-1)).squeeze(-1)
                loss = self._loss(pred, ys, ms)
                total += loss.item()
                if opt:
                    opt.zero_grad(); loss.backward()
                    nn.utils.clip_grad_norm_(self.model.parameters(), 1.0); opt.step()
                m = ms.bool()
                yt.extend(ys[m].cpu().numpy().tolist())
                yp.extend(pred[m].detach().cpu().numpy().tolist())
        yt, yp = np.array(yt), np.array(yp)
        auc = 0.0
        try:
            yb = yt if self.mode == 'binary' else (yt >= 0.5).astype(int)
            if len(np.unique(yb)) > 1: auc = roc_auc_score(yb, yp)
        except: pass
        return total / len(loader), auc

    def fit(self, train_seqs, val_seqs, verbose=True):
        self.model = DKTModel(self.n_kcs, self.hidden_size, self.n_layers, self.dropout).to(self.device)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=2, factor=0.5)
        tl, vl = self._loader(train_seqs, True), self._loader(val_seqs)
        best_auc, best_state, no_imp = -1.0, None, 0
        for ep in range(1, self.epochs+1):
            tl_loss, _ = self._epoch(tl, opt)
            vl_loss, vauc = self._epoch(vl)
            sched.step(vl_loss)
            self.history['train_loss'].append(tl_loss)
            self.history['val_loss'].append(vl_loss)
            self.history['val_auc'].append(vauc)
            if verbose: print(f"  Epoch {ep:3d}/{self.epochs}  train={tl_loss:.4f}  val={vl_loss:.4f}  auc={vauc:.4f}")
            if vauc > best_auc:
                best_auc, best_state, no_imp = vauc, {k: v.clone() for k,v in self.model.state_dict().items()}, 0
            else:
                no_imp += 1
                if no_imp >= self.patience:
                    if verbose: print(f"  Early stop @ {ep}")
                    break
        if best_state: self.model.load_state_dict(best_state)
        return self

    def predict(self, seqs):
        assert self.model
        self.model.eval()
        yt, yp = [], []
        with torch.no_grad():
            for xs, ys, kcs, ms in self._loader(seqs):
                out  = self.model(xs.to(self.device))
                pred = out.gather(2, kcs.to(self.device).unsqueeze(-1)).squeeze(-1)
                m = ms.bool()
                yt.extend(ys[m].numpy().tolist())
                yp.extend(pred[m].cpu().numpy().tolist())
        return np.array(yt), np.array(yp)

    def evaluate(self, seqs):
        yt, yp = self.predict(seqs)
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))
        yb = yt if self.mode == 'binary' else (yt >= 0.5).astype(int)
        auc = roc_auc_score(yb, yp) if len(np.unique(yb)) > 1 else 0.0
        acc = float(np.mean((yp >= 0.5).astype(int) == yb.astype(int)))
        return {'auc': round(auc,4), 'rmse': round(rmse,4), 'acc': round(acc,4)}

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({'state_dict': self.model.state_dict(),
                    'config': {'n_kcs':self.n_kcs,'mode':self.mode,
                               'hidden_size':self.hidden_size,'n_layers':self.n_layers,'dropout':self.dropout},
                    'history': self.history}, path)
        print(f"DKT saved -> {path}")

    def load(self, path):
        ckpt = torch.load(path, map_location=self.device, weights_only=False)
        c = ckpt['config']
        self.model = DKTModel(c['n_kcs'], c['hidden_size'], c['n_layers'], c['dropout']).to(self.device)
        self.model.load_state_dict(ckpt['state_dict'])
        self.history = ckpt.get('history', {})
        return self

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parents[1]
    with open(ROOT/'data'/'processed'/'metadata.json') as f: meta=json.load(f)
    with open(ROOT/'data'/'processed'/'train_seqs.pkl','rb') as f: train=pickle.load(f)
    with open(ROOT/'data'/'processed'/'val_seqs.pkl','rb') as f: val=pickle.load(f)
    for mode in ['binary','quality']:
        print(f"\n=== DKT-{mode} ===")
        dkt = DKT(n_kcs=meta['n_kcs'], mode=mode, epochs=5)
        dkt.fit(train, val)
        print(dkt.evaluate(val))
