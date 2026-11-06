// COMPONENT: {"name": "lagrangian_dual_ratio_greedy", "slot": "constructor", "params": {"iters": {"type": "int", "range": [20, 300]}, "theta": {"type": "float", "range": [0.1, 2.0]}, "score_noise": {"type": "float", "range": [0.0, 0.3]}}}
class LagrangianDualGreedy : public hsf::Constructor<Model> {
public:
    using Solution = Model::Solution;
    LagrangianDualGreedy(const Model& md, int iters, double theta, double noise)
        : M(md), noise_(noise) {
        n = M.n; m = M.m;
        a.assign((size_t)n * m, 0.0);
        for (int j = 0; j < n; ++j)
            for (int i = 0; i < m; ++i)
                a[(size_t)j * m + i] = M.wt[(size_t)j * m + i] / std::max(M.capacity[i], 1e-9);
        order.resize(n); score.resize(n); resid.resize(m);
        computeMultipliers(std::max(1, iters), theta);
        base.resize(n);
        double mean = 0.0;
        for (int i = 0; i < m; ++i) mean += lam[i];
        mean = (m > 0 ? mean / m : 0.0);
        double eps = 1e-3 * mean + 1e-12;
        for (int j = 0; j < n; ++j) {
            double d = 0.0;
            for (int i = 0; i < m; ++i) d += (lam[i] + eps) * a[(size_t)j * m + i];
            base[j] = (d <= 1e-300) ? 1e300 : M.profit[j] / d;
        }
    }
    Solution build(Rng& rng) override {
        for (int j = 0; j < n; ++j) {
            double f = 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            score[j] = base[j] >= 1e299 ? base[j] : base[j] * f;
        }
        Solution s(1, std::vector<int>(n, 0));
        greedy(s[0]);
        if (!M.feasible(s)) return M.trivial();
        return s;
    }
private:
    double greedy(std::vector<int>& x) {
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int p, int q) {
            if (score[p] != score[q]) return score[p] > score[q];
            return p < q;
        });
        for (int i = 0; i < m; ++i) resid[i] = M.capacity[i];
        double tot = 0.0;
        for (int j : order) {
            if (M.profit[j] < 0) continue;
            const double* w = &M.wt[(size_t)j * m];
            bool ok = true;
            for (int i = 0; i < m; ++i) if (w[i] > resid[i] + Model::EPS) { ok = false; break; }
            if (!ok) continue;
            x[j] = 1; tot += M.profit[j];
            for (int i = 0; i < m; ++i) resid[i] -= w[i];
        }
        return tot;
    }
    double heuristicFrom(const std::vector<double>& l) {
        for (int j = 0; j < n; ++j) {
            double d = 0.0;
            for (int i = 0; i < m; ++i) d += (l[i] + 1e-9) * a[(size_t)j * m + i];
            score[j] = (d <= 1e-300) ? 1e300 : M.profit[j] / d;
        }
        std::vector<int> x(n, 0);
        return greedy(x);
    }
    void computeMultipliers(int iters, double theta) {
        lam.assign(m, 0.0);
        double sp = 0.0, sa = 0.0;
        for (int j = 0; j < n; ++j) { if (M.profit[j] > 0) sp += M.profit[j]; }
        for (double v : a) sa += v;
        double init = sa > 1e-15 ? sp / sa : 0.0;
        for (int i = 0; i < m; ++i) lam[i] = init;
        std::vector<double> ones(m, 1.0);
        double LB = heuristicFrom(ones);
        std::vector<double> best = lam, g(m);
        double bestL = std::numeric_limits<double>::infinity();
        int noImp = 0;
        for (int t = 0; t < iters; ++t) {
            double L = 0.0;
            for (int i = 0; i < m; ++i) { L += lam[i]; g[i] = 1.0; }
            for (int j = 0; j < n; ++j) {
                const double* aj = &a[(size_t)j * m];
                double rc = M.profit[j];
                for (int i = 0; i < m; ++i) rc -= lam[i] * aj[i];
                if (rc > 0) {
                    L += rc;
                    for (int i = 0; i < m; ++i) g[i] -= aj[i];
                }
            }
            if (L < bestL - 1e-12) { bestL = L; best = lam; noImp = 0; }
            else if (++noImp >= 15) { theta *= 0.5; noImp = 0; }
            if (t % 5 == 4) LB = std::max(LB, heuristicFrom(lam));
            double norm = 0.0;
            for (int i = 0; i < m; ++i) {
                double gi = (lam[i] <= 0 && g[i] > 0) ? 0.0 : g[i];
                norm += gi * gi;
            }
            if (norm < 1e-18) break;
            double gap = std::max(L - LB, 1e-6 * std::fabs(L) + 1e-9);
            double step = theta * gap / norm;
            for (int i = 0; i < m; ++i) lam[i] = std::max(0.0, lam[i] - step * g[i]);
            if (theta < 1e-6) break;
        }
        lam = best;
    }
    const Model& M;
    int n, m;
    double noise_;
    std::vector<double> a, lam, base, score, resid;
    std::vector<int> order;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int iters = (int)params.get("iters", 100);
    double theta = params.get("theta", 1.0);
    double noise = params.get("score_noise", 0.05);
    return std::make_unique<LagrangianDualGreedy>(model, iters, theta, noise);
}
