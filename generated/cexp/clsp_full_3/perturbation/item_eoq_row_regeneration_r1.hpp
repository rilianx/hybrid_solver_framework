// COMPONENT: {"name": "item_eoq_row_regeneration", "slot": "perturbation", "params": {"items_per_strength": {"type": "int", "range": [1, 4]}, "cycle_noise": {"type": "float", "range": [0.0, 0.8]}, "greedy": {"type": "float", "range": [0.0, 1.0]}, "prune_prob": {"type": "float", "range": [0.0, 1.0]}}}
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

class EoqRowRegen : public hsf::Perturbation<Model> {
public:
    EoqRowRegen(const Model& m, int ips, double noise, double g, double pp)
        : m_(m), fx_(m), ips_(ips), noise_(noise), greedy_(g), prune_(pp) {
        baseCycle_.assign(m.n, (double)m.T);
        for (int i = 0; i < m.n; ++i) {
            double tot = 0.0;
            for (int t = 0; t < m.T; ++t) tot += m.d[i][t];
            double davg = m.T > 0 ? tot / m.T : 0.0;
            if (m.h[i] > 0 && davg > 0) baseCycle_[i] = std::sqrt(2.0 * m.s[i] / (m.h[i] * davg));
        }
        order_.resize(m.n);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        int k = (int)std::lround(std::max(1.0, strength) * ips_);
        k = std::max(1, std::min(k, n));
        std::iota(order_.begin(), order_.end(), 0);
        for (int r = 0; r < k; ++r) {
            int j = r + rng.below(n - r);
            std::swap(order_[r], order_[j]);
            int i = order_[r];
            double p = baseCycle_[i] * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
            int pi = (int)std::lround(p);
            pi = std::max(1, std::min(pi, T));
            std::vector<int>& row = y[i];
            std::fill(row.begin(), row.end(), 0);
            const std::vector<double>& di = m_.d[i];
            int t = 0;
            while (t < T) {
                int f = t;
                while (f < T && di[f] <= 0) ++f;
                if (f >= T) break;
                row[f] = 1;
                t = f + pi;
            }
        }
        return fx_.finish(std::move(y), s, rng, greedy_, prune_);
    }
private:
    const Model& m_;
    FlowFixer fx_;
    int ips_;
    double noise_, greedy_, prune_;
    std::vector<double> baseCycle_;
    std::vector<int> order_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ips = (int)params.get("items_per_strength", 1);
    double noise = params.get("cycle_noise", 0.4);
    double g = params.get("greedy", 0.7);
    double pp = params.get("prune_prob", 0.5);
    return std::make_unique<EoqRowRegen>(model, std::max(1, ips), noise, g, pp);
}
