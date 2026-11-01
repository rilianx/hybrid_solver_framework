// COMPONENT: {"name": "lot_shift_merge_swap_repair", "slot": "perturbation", "params": {"moves_per_strength": {"type": "float", "range": [0.5, 4.0]}, "p_shift": {"type": "float", "range": [0.0, 1.0]}, "p_merge": {"type": "float", "range": [0.0, 1.0]}, "repair_iters": {"type": "int", "range": [20, 400]}}}
using Sol = Model::Solution;

class FlowRepair {
public:
    explicit FlowRepair(const Model& m) : m_(m) {
        dem_.assign(m.n, std::vector<int>(m.T, -1));
        for (int i = 0; i < m.n; ++i)
            for (int t = 0; t < m.T; ++t) {
                int u = m.itemNode(i, t);
                for (int id : m.adj[u])
                    if ((id & 1) == 0 && m.E0[id].to == m.SNK) dem_[i][t] = id;
            }
    }
    bool fix(Sol& y, Rng& rng, int maxIt) {
        double unmet, hold;
        for (int it = 0; it <= maxIt; ++it) {
            m_.solveFlow(y, unmet, hold);
            if (unmet <= 1e-6) return true;
            if (it == maxIt) break;
            cand_.clear();
            for (int i = 0; i < m_.n; ++i)
                for (int t = 0; t < m_.T; ++t) {
                    int id = dem_[i][t];
                    if (id >= 0 && m_.E[id].cap > 1e-6) cand_.push_back(i * m_.T + t);
                }
            if (cand_.empty()) return false;
            bool done = false;
            for (int tries = 0; tries < (int)cand_.size() && !done; ++tries) {
                int c = cand_[rng.below((int)cand_.size())];
                int i = c / m_.T, t = c % m_.T;
                bool rnd = rng.uniform() < 0.25;
                int best = -1; double bs = -std::numeric_limits<double>::infinity();
                for (int tt = 0; tt <= t; ++tt) {
                    if (y[i][tt]) continue;
                    double sc = rnd ? rng.uniform()
                                    : m_.E[m_.srcEdge[tt]].cap - m_.st[i] - 1e-6 * (t - tt);
                    if (sc > bs) { bs = sc; best = tt; }
                }
                if (best >= 0) { y[i][best] = 1; done = true; }
            }
            if (!done) return false;
        }
        return false;
    }
    Sol fallback(const Sol& s, Rng& rng, int iters) {
        int N = m_.n * m_.T;
        order_.resize(N);
        std::iota(order_.begin(), order_.end(), 0);
        std::shuffle(order_.begin(), order_.end(), rng.g);
        int lim = std::max(1, std::min(iters, 10));
        for (int c : order_) {
            Sol y = s;
            y[c / m_.T][c % m_.T] ^= 1;
            if (fix(y, rng, lim) && y != s) return y;
        }
        return s;
    }
private:
    const Model& m_;
    std::vector<std::vector<int>> dem_;
    std::vector<int> cand_, order_;
};

class LotShiftMergeSwap : public hsf::Perturbation<Model> {
public:
    LotShiftMergeSwap(const Model& m, double mps, double ps, double pm, int it)
        : m_(m), rep_(m), mps_(mps), it_(it) {
        double sw = std::max(0.0, 1.0 - ps - pm);
        double tot = ps + pm + sw;
        if (tot <= 0) { ps = pm = sw = 1.0; tot = 3.0; }
        ps_ = ps / tot; pm_ = pm / tot;
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (m_.n == 0 || m_.T == 0) return s;
        int k = std::max(1, (int)std::lround(mps_ * std::max(1.0, strength)));
        for (int attempt = 0; attempt < 6; ++attempt) {
            Sol y = s;
            for (int c = 0; c < k; ++c) oneMove(y, rng);
            if (rep_.fix(y, rng, it_) && y != s) return y;
            if (attempt >= 2) k = std::max(1, k / 2);
        }
        return rep_.fallback(s, rng, it_);
    }
private:
    void oneMove(Sol& y, Rng& rng) {
        int T = m_.T;
        double r = rng.uniform();
        int i = rng.below(m_.n);
        setups_.clear();
        for (int t = 0; t < T; ++t) if (y[i][t]) setups_.push_back(t);
        if (setups_.empty()) { y[i][rng.below(T)] = 1; return; }
        if (r < ps_) {  // shift a setup to neighbouring free period
            int t = setups_[rng.below((int)setups_.size())];
            int dir = rng.below(2) ? 1 : -1;
            int t2 = t + dir;
            if (t2 < 0 || t2 >= T || y[i][t2]) { t2 = t - dir; }
            if (t2 >= 0 && t2 < T && !y[i][t2]) { y[i][t] = 0; y[i][t2] = 1; }
            else y[i][t] = 0;
        } else if (r < ps_ + pm_) {  // merge: drop a non-first setup (lot absorbed earlier)
            if (setups_.size() >= 2) y[i][setups_[1 + rng.below((int)setups_.size() - 1)]] = 0;
            else {
                int t = rng.below(T);
                y[i][t] ^= 1;
            }
        } else {  // swap capacity between items in a period
            int t = setups_[rng.below((int)setups_.size())];
            int j = -1;
            for (int tr = 0; tr < 10; ++tr) {
                int z = rng.below(m_.n);
                if (z != i && !y[z][t]) { j = z; break; }
            }
            y[i][t] = 0;
            if (j >= 0) y[j][t] = 1;
        }
    }
    const Model& m_;
    FlowRepair rep_;
    double mps_, ps_, pm_;
    int it_;
    std::vector<int> setups_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double mps = params.get("moves_per_strength", 1.5);
    double ps = params.get("p_shift", 0.4);
    double pm = params.get("p_merge", 0.35);
    int it = (int)params.get("repair_iters", 100);
    return std::make_unique<LotShiftMergeSwap>(model, mps, ps, pm, std::max(1, it));
}
