// COMPONENT: {"name": "random_setup_flips_flow_repair", "slot": "perturbation", "params": {"flips_per_strength": {"type": "float", "range": [0.5, 4.0]}, "off_bias": {"type": "float", "range": [0.0, 1.0]}, "repair_iters": {"type": "int", "range": [20, 400]}}}
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
            int i = c / m_.T, t = c % m_.T;
            y[i][t] ^= 1;
            if (fix(y, rng, lim) && y != s) return y;
        }
        return s;
    }
private:
    const Model& m_;
    std::vector<std::vector<int>> dem_;
    std::vector<int> cand_, order_;
};

class RandomSetupFlips : public hsf::Perturbation<Model> {
public:
    RandomSetupFlips(const Model& m, double fps, double bias, int it)
        : m_(m), rep_(m), fps_(fps), bias_(bias), iters_(it) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (m_.n == 0 || m_.T == 0) return s;
        int N = m_.n * m_.T;
        int k = std::max(1, (int)std::lround(fps_ * std::max(1.0, strength)));
        k = std::min(k, N);
        for (int attempt = 0; attempt < 6; ++attempt) {
            Sol y = s;
            for (int c = 0; c < k; ++c) {
                int want = rng.uniform() < bias_ ? 1 : 0;  // value of cell to flip
                int cell = -1;
                for (int tr = 0; tr < 10; ++tr) {
                    int z = rng.below(N);
                    if (y[z / m_.T][z % m_.T] == want) { cell = z; break; }
                }
                if (cell < 0) cell = rng.below(N);
                y[cell / m_.T][cell % m_.T] ^= 1;
            }
            if (rep_.fix(y, rng, iters_) && y != s) return y;
            if (attempt >= 2) k = std::max(1, k / 2);
        }
        return rep_.fallback(s, rng, iters_);
    }
private:
    const Model& m_;
    FlowRepair rep_;
    double fps_, bias_;
    int iters_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double fps = params.get("flips_per_strength", 1.5);
    double bias = params.get("off_bias", 0.6);
    int it = (int)params.get("repair_iters", 100);
    return std::make_unique<RandomSetupFlips>(model, fps, bias, std::max(1, it));
}
