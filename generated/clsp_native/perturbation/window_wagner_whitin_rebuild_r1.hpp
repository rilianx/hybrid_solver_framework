// COMPONENT: {"name": "window_wagner_whitin_rebuild", "slot": "perturbation", "params": {"window_base": {"type": "int", "range": [2, 12]}, "window_per_strength": {"type": "float", "range": [0.5, 4.0]}, "item_frac": {"type": "float", "range": [0.05, 1.0]}, "cost_noise": {"type": "float", "range": [0.0, 0.9]}, "repair_iters": {"type": "int", "range": [20, 400]}}}
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

class WindowWWRebuild : public hsf::Perturbation<Model> {
public:
    WindowWWRebuild(const Model& m, int wb, double wps, double frac, double noise, int it)
        : m_(m), rep_(m), wb_(wb), wps_(wps), frac_(frac), noise_(noise), it_(it) {
        items_.resize(m.n);
        std::iota(items_.begin(), items_.end(), 0);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (m_.n == 0 || m_.T == 0) return s;
        int T = m_.T;
        double str = std::max(1.0, strength);
        for (int attempt = 0; attempt < 6; ++attempt) {
            int L = std::min(T, std::max(1, wb_ + (int)std::lround(wps_ * str) + attempt));
            int a = rng.below(T - L + 1), b = a + L - 1;
            int ni = std::max(1, std::min(m_.n, (int)std::lround(frac_ * m_.n * std::min(str, 3.0) / 1.5)));
            std::shuffle(items_.begin(), items_.end(), rng.g);
            Sol y = s;
            for (int q = 0; q < ni; ++q) rebuild(y, items_[q], a, b, rng);
            if (y == s) {  // force diversity inside the window
                int i = items_[0];
                y[i][a + rng.below(L)] ^= 1;
            }
            if (rep_.fix(y, rng, it_) && y != s) return y;
        }
        return rep_.fallback(s, rng, it_);
    }
private:
    void rebuild(Sol& y, int i, int a, int b, Rng& rng) {
        int L = b - a + 1;
        double sc = m_.s[i] * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
        double h = m_.h[i];
        const auto& d = m_.d[i];
        f_.assign(L + 1, 0.0);
        ch_.assign(L + 1, -1);
        for (int k = 1; k <= L; ++k) {
            int t = a + k - 1;
            double best = std::numeric_limits<double>::infinity(); int arg = -1;
            if (d[t] <= 0) { best = f_[k - 1]; arg = -1; }
            double c = 0.0, sd = 0.0;
            for (int j = t; j >= a; --j) {
                c += h * sd;
                double v = f_[j - a] + sc + c;
                if (v < best - 1e-12) { best = v; arg = j; }
                sd += d[j];
            }
            f_[k] = best; ch_[k] = arg;
        }
        for (int t = a; t <= b; ++t) y[i][t] = 0;
        int k = L;
        while (k > 0) {
            int j = ch_[k];
            if (j < 0) { --k; continue; }
            y[i][j] = 1;
            k = j - a;
        }
    }
    const Model& m_;
    FlowRepair rep_;
    int wb_;
    double wps_, frac_, noise_;
    int it_;
    std::vector<int> items_, ch_;
    std::vector<double> f_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int wb = (int)params.get("window_base", 4);
    double wps = params.get("window_per_strength", 1.5);
    double frac = params.get("item_frac", 0.3);
    double noise = params.get("cost_noise", 0.4);
    int it = (int)params.get("repair_iters", 100);
    return std::make_unique<WindowWWRebuild>(model, std::max(1, wb), wps, frac, noise, std::max(1, it));
}
