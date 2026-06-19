"""
SAKT -- Self-Attentive Knowledge Tracing (Pandey & Karypis 2019)
Q=KC_embed, K=V=interaction_embed, causal mask, output = sigmoid(1)
Mode: binary (BCE) | quality (MSE on quality_norm 0/0.5/1)
"""
import json, pickle
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import mean_squared_error, roc_auc_score
from torch.utils.data import DataLoader, Dataset


class SAKTDataset(Dataset):
    def __init__(self, seqs, n_kcs, mode='binary', max_len=200):
        self.seqs, self.n_kcs, self.mode, self.max_len = seqs, n_kcs, mode, max_len

    def __len__(self): return len(self.seqs)

    def __getitem__(self, idx):
        seq = self.seqs[idx]
        kc_seq, correct, q_norm = seq['kc_seq'], seq['correct_seq'], seq['quality_seq']
        T = min(len(kc_seq) - 1, self.max_len)
        if T <= 0:
            return torch.zeros(1, dtype=torch.long), torch.zeros(1, dtype=torch.long), torch.zeros(1), torch.zeros(1)
        # interaction index: correct -> kc_id, wrong -> kc_id + n_kcs
        inter = [kc_seq[t] if correct[t] >= 1 else kc_seq[t] + self.n_kcs for t in range(T)]
        inter_t = torch.tensor(inter, dtype=torch.long)
        kc_next = torch.tensor(kc_seq[1:T+1], dtype=torch.long)
        if self.mode == 'binary':
            y = torch.tensor([float(correct[t+1] >= 1) for t in range(T)], dtype=torch.float32)
        else:
            y = torch.tensor([float(q_norm[t+1]) for t in range(T)], dtype=torch.float32)
        return inter_t, kc_next, y, torch.ones(T)


def collate_fn(batch):
    ints, kcs, ys, masks = zip(*batch)
    max_T = max(x.shape[0] for x in ints)
    ip = torch.zeros(len(ints), max_T, dtype=torch.long)
    kp = torch.zeros(len(kcs), max_T, dtype=torch.long)
    yp = torch.zeros(len(ys), max_T)
    mp = torch.zeros(len(masks), max_T)
    for i, (it, k, y, m) in enumerate(zip(ints, kcs, ys, masks)):
        T = it.shape[0]
        ip[i,:T] = it; kp[i,:T] = k; yp[i,:T] = y; mp[i,:T] = m
    return ip, kp, yp, mp


class SAKTModel(nn.Module):
    def __init__(self, n_kcs, embed_dim=64, n_heads=4, n_layers=1, dropout=0.2, max_len=200):
        super().__init__()
        self.inter_embed = nn.Embedding(2*n_kcs + 1, embed_dim, padding_idx=0)
        self.kc_embed    = nn.Embedding(n_kcs, embed_dim)
        self.pos_embed   = nn.Embedding(max_len + 1, embed_dim)
        self.attn  = nn.ModuleList([nn.MultiheadAttention(embed_dim, n_heads, dropout=dropout, batch_first=True) for _ in range(n_layers)])
        self.ff    = nn.ModuleList([nn.Sequential(nn.Linear(embed_dim, embed_dim*2), nn.ReLU(), nn.Dropout(dropout), nn.Linear(embed_dim*2, embed_dim)) for _ in range(n_layers)])
        self.norm1 = nn.ModuleList([nn.LayerNorm(embed_dim) for _ in range(n_layers)])
        self.norm2 = nn.ModuleList([nn.LayerNorm(embed_dim) for _ in range(n_layers)])
        self.drop  = nn.Dropout(dropout)
        self.out   = nn.Linear(embed_dim, 1)

    def forward(self, inter_seq, kc_next):
        B, T = inter_seq.shape
        pos  = torch.arange(1, T+1, device=inter_seq.device).unsqueeze(0).expand(B, -1)
        causal = torch.triu(torch.ones(T, T, device=inter_seq.device), diagonal=1).bool()
        v = self.inter_embed(inter_seq) + self.pos_embed(pos)
        q = self.kc_embed(kc_next)
        h = v
        for attn, ff, n1, n2 in zip(self.attn, self.ff, self.norm1, self.norm2):
            ao, _ = attn(q, h, h, attn_mask=causal)
            q = n1(q + self.drop(ao))
            q = n2(q + self.drop(ff(q)))
        return torch.sigmoid(self.out(q)).squeeze(-1)


class SAKT:
    def __init__(self, n_kcs, mode='binary', embed_dim=64, n_heads=4, n_layers=1,
                 dropout=0.2, lr=1e-3, batch_size=64, epochs=30,
                 patience=5, max_len=200, device=None, seed=42):
        self.n_kcs, self.mode, self.embed_dim = n_kcs, mode, embed_dim
        self.n_heads, self.n_layers, self.dropout = n_heads, n_layers, dropout
        self.lr, self.batch_size, self.epochs = lr, batch_size, epochs
        self.patience, self.max_len, self.seed = patience, max_len, seed
        torch.manual_seed(seed); np.random.seed(seed)
        self.device = torch.device(device if device else ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.model = None
        self.history = {'train_loss': [], 'val_loss': [], 'val_auc': []}

    def _loader(self, seqs, shuffle=False):
        return DataLoader(SAKTDataset(seqs, self.n_kcs, self.mode, self.max_len),
                          batch_size=self.batch_size, shuffle=shuffle, collate_fn=collate_fn)

    def _loss(self, pred, target, mask):
        fn = nn.functional.binary_cross_entropy if self.mode == 'binary' else nn.functional.mse_loss
        return (fn(pred, target, reduction='none') * mask).sum() / mask.sum().clamp(min=1)

    def _epoch(self, loader, opt=None):
        self.model.train() if opt else self.model.eval()
        total, yt, yp = 0.0, [], []
        with torch.set_grad_enabled(opt is not None):
            for ints, kcs, ys, ms in loader:
                ints, kcs, ys, ms = ints.to(self.device), kcs.to(self.device), ys.to(self.device), ms.to(self.device)
                pred = self.model(ints, kcs)
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
        self.model = SAKTModel(self.n_kcs, self.embed_dim, self.n_heads, self.n_layers, self.dropout, self.max_len).to(self.device)
        opt   = torch.optim.Adam(self.model.parameters(), lr=self.lr)
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
            for ints, kcs, ys, ms in self._loader(seqs):
                pred = self.model(ints.to(self.device), kcs.to(self.device))
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
                    'config': {'n_kcs':self.n_kcs,'mode':self.mode,'embed_dim':self.embed_dim,
                               'n_heads':self.n_heads,'n_layers':self.n_layers,'dropout':self.dropout,'max_len':self.max_len},
                    'history': self.history}, path)
        print(f"SAKT saved -> {path}")

    def load(self, path):
        ckpt = torch.load(path, map_location=self.device, weights_only=False)
        c = ckpt['config']
        self.model = SAKTModel(c['n_kcs'], c['embed_dim'], c['n_heads'], c['n_layers'], c['dropout'], c['max_len']).to(self.device)
        self.model.load_state_dict(ckpt['state_dict'])
        self.history = ckpt.get('history', {})
        return self

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parents[1]
    with open(ROOT/'data'/'processed'/'metadata.json') as f: meta=json.load(f)
    with open(ROOT/'data'/'processed'/'train_seqs.pkl','rb') as f: train=pickle.load(f)
    with open(ROOT/'data'/'processed'/'val_seqs.pkl','rb') as f: val=pickle.load(f)
    for mode in ['binary','quality']:
        print(f"\n=== SAKT-{mode} ===")
        sakt = SAKT(n_kcs=meta['n_kcs'], mode=mode, epochs=5)
        sakt.fit(train, val)
        print(sakt.evaluate(val))
