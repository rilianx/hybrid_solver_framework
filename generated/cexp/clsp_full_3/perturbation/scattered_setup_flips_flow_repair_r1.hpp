// COMPONENT: {"name": "scattered_setup_flips_flow_repair", "slot": "perturbation", "params": {"flips_per_strength": {"type": "int", "range": [1, 6]}, "remove_prob": {"type": "float", "range": [0.2, 0.9]}, "greedy": {"type": "float", "range": [0.0, 1.0]}, "prune_prob": {"type": "float", "range": [0.0, 1.0]}}}
class FlowFixer {
public:
    using Sol = Model::Solution;
    explicit FlowFixer(const Model& m) : m_(m) {}
    bool feasible(const Sol& y) { double u, h; m_.solveFlow(y, u, h); return u <= 1e-6; }
    double slack(int t) const { return m_.E[m_.srcEdge[t]].cap; }
    double prodFlow(int i, int t) const { return m_.E[m_.prodEdge[i][t] + 1].cap; }
    bool unmetAt(int i, int t) const {
        int id = m_.sinkEdge[(size_t)i * m_.T + t];
        return id >= 0 && m_.E[id].cap > 1e-6;
    }
    int pruneIdle(Sol& y) {
        int c = 0;
        for (int i = 0; i < m_.n; ++i)
            for (int t = 0; t < m_.T; ++t)
                if (y[i][t] && prodFlow(i, t) <= 1e-9) { y[i][t] = 0; ++c; }
        return c;
    }
    bool repair(Sol& y, Rng& rng, double greedy) {
        const int n = m_.n, T = m_.T;
        int maxIter = 2 * n * T + 10;
        for (int it = 0; it < maxIter; ++it) {
            double u, h; m_.solveFlow(y, u, h);
            if (u <= 1e-6) return true;
            pts_.clear();
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t)
                    if (unmetAt(i, t)) { pts_.push_back({i, t}); break; }
            if (pts_.empty()) return false;
            auto pr = pts_[rng.below((int)pts_.size())];
            int i = pr.first, t = pr.second;
            cand_.clear();
            for (int tp = t; tp >= 0; --tp)
                if (!y[i][tp] && slack(tp) > m_.st[i] + 1e-9) cand_.push_back(tp);
            if (!cand_.empty()) {
                int tp = (rng.uniform() < greedy) ? cand_[0]
                         : cand_[rng.below(std::min<int>((int)cand_.size(), 4))];
                y[i][tp] = 1;
                continue;
            }
            if (pruneIdle(y) > 0) continue;
            int best = -1; double bs = -1e300;
            for (int tp = t; tp >= 0; --tp)
                if (!y[i][tp] && slack(tp) > bs) { bs = slack(tp); best = tp; }
            if (best < 0) return false;
            y[i][best] = 1;
        }
        return feasible(y);
    }
    Sol fallback(const Sol& s, Rng& rng) {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        if (feasible(s)) {
            cells_.clear();
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t)
                    if (s[i][t] && prodFlow(i, t) <= 1e-9) cells_.push_back(i * T + t);
            if (!cells_.empty()) {
                int c = cells_[rng.below((int)cells_.size())];
                y[c / T][c % T] = 0;
                if (feasible(y)) return y;
                y = s;
            }
            feasible(s);
            cells_.clear();
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t)
                    if (!s[i][t] && slack(t) > m_.st[i] + 1e-9) cells_.push_back(i * T + t);
            if (!cells_.empty()) {
                int c = cells_[rng.below((int)cells_.size())];
                y[c / T][c % T] = 1;
                if (feasible(y)) return y;
                y = s;
            }
        }
        cells_.resize((size_t)n * T);
        std::iota(cells_.begin(), cells_.end(), 0);
        std::shuffle(cells_.begin(), cells_.end(), rng.g);
        for (int c : cells_) {
            int i = c / T, t = c % T;
            y[i][t] = y[i][t] ? 0 : 1;
            if (feasible(y)) return y;
            y[i][t] = s[i][t];
        }
        Sol tr = m_.trivial();
        if (tr != s && feasible(tr)) return tr;
        y = s; y[0][0] = y[0][0] ? 0 : 1;
        return y;
    }
    Sol finish(Sol y, const Sol& s, Rng& rng, double greedy, double pruneProb) {
        if (repair(y, rng, greedy)) {
            if (rng.uniform() < pruneProb) {
                Sol z = y;
                if (pruneIdle(z) > 0 && feasible(z) && z != s) y.swap(z);
            }
            if (y != s) return y;
        }
        return fallback(s, rng);
    }
private:
    const Model& m_;
    std::vector<std::pair<int, int>> pts_;
    std::vector<int> cand_, cells_;
};

class ScatteredFlips : public hsf::Perturbation<Model> {
public:
    ScatteredFlips(const Model& m, int fps, double rp, double g, double pp)
        : m_(m), fx_(m), fps_(fps), removeProb_(rp), greedy_(g), prune_(pp) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        int k = (int)std::lround(std::max(1.0, strength) * fps_);
        k = std::max(1, std::min(k, n * T));
        active_.clear(); idle_.clear();
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < T; ++t) (s[i][t] ? active_ : idle_).push_back(i * T + t);
        for (int r = 0; r < k; ++r) {
            bool rem = !active_.empty() && (idle_.empty() || rng.uniform() < removeProb_);
            std::vector<int>& L = rem ? active_ : idle_;
            if (L.empty()) break;
            int j = rng.below((int)L.size());
            int c = L[j]; L[j] = L.back(); L.pop_back();
            y[c / T][c % T] = rem ? 0 : 1;
        }
        return fx_.finish(std::move(y), s, rng, greedy_, prune_);
    }
private:
    const Model& m_;
    FlowFixer fx_;
    int fps_;
    double removeProb_, greedy_, prune_;
    std::vector<int> active_, idle_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int fps = (int)params.get("flips_per_strength", 2);
    double rp = params.get("remove_prob", 0.6);
    double g = params.get("greedy", 0.7);
    double pp = params.get("prune_prob", 0.8);
    return std::make_unique<ScatteredFlips>(model, std::max(1, fps), rp, g, pp);
}
