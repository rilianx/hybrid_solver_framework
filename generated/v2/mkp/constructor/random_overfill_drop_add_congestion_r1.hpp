// COMPONENT: {"name": "random_overfill_drop_add_congestion", "slot": "constructor", "params": {"init_density": {"type": "float", "range": [0.3, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.3]}}}
class DropAddCongestion : public hsf::Constructor<Model> {
public:
    DropAddCongestion(const Model& md, double dens, double noise) : M(md), dens_(dens), noise_(noise) {
        n = M.n; m = M.m;
        std::vector<double> invcap(m), mu(m, 0.0);
        for (int i = 0; i < m; ++i) invcap[i] = 1.0 / std::max(M.capacity[i], 1e-9);
        for (int j = 0; j < n; ++j)
            for (int i = 0; i < m; ++i) mu[i] += M.wt[(size_t)j * m + i] * invcap[i];
        double mx = 0.0;
        for (int i = 0; i < m; ++i) mx = std::max(mx, mu[i]);
        for (int i = 0; i < m; ++i) mu[i] = (mx > 0 ? mu[i] / mx : 1.0) + 1e-3;  // congestion weight
        base.resize(n);
        for (int j = 0; j < n; ++j) {
            double d = 0.0;
            for (int i = 0; i < m; ++i) d += mu[i] * M.wt[(size_t)j * m + i] * invcap[i];
            base[j] = (d <= 1e-300) ? 1e300 : M.profit[j] / d;
        }
        score.resize(n); order.resize(n); used.resize(m);
    }
    Solution build(Rng& rng) override {
        Solution s(1, std::vector<int>(n, 0));
        std::vector<int>& x = s[0];
        for (int j = 0; j < n; ++j) {
            double f = 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            score[j] = base[j] >= 1e299 ? base[j] : base[j] * f;
        }
        std::fill(used.begin(), used.end(), 0.0);
        for (int j = 0; j < n; ++j) {
            bool take = M.profit[j] >= 0 && rng.uniform() < dens_;
            if (take) {
                x[j] = 1;
                const double* w = &M.wt[(size_t)j * m];
                for (int i = 0; i < m; ++i) used[i] += w[i];
            }
        }
        int viol = 0;
        for (int i = 0; i < m; ++i) if (used[i] > M.capacity[i] + Model::EPS) ++viol;
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int p, int q) {
            if (score[p] != score[q]) return score[p] > score[q];
            return p < q;
        });
        // DROP: worst ratio first, only items touching a violated resource
        for (int p = n - 1; p >= 0 && viol > 0; --p) {
            int j = order[p];
            if (!x[j]) continue;
            const double* w = &M.wt[(size_t)j * m];
            bool touches = false;
            for (int i = 0; i < m; ++i)
                if (w[i] > 0 && used[i] > M.capacity[i] + Model::EPS) { touches = true; break; }
            if (!touches) continue;
            x[j] = 0;
            for (int i = 0; i < m; ++i) {
                bool was = used[i] > M.capacity[i] + Model::EPS;
                used[i] -= w[i];
                if (was && used[i] <= M.capacity[i] + Model::EPS) --viol;
            }
        }
        if (viol > 0) return M.trivial();
        // ADD: best ratio first
        for (int p = 0; p < n; ++p) {
            int j = order[p];
            if (x[j] || M.profit[j] < 0) continue;
            const double* w = &M.wt[(size_t)j * m];
            bool ok = true;
            for (int i = 0; i < m; ++i) if (used[i] + w[i] > M.capacity[i] + Model::EPS) { ok = false; break; }
            if (!ok) continue;
            x[j] = 1;
            for (int i = 0; i < m; ++i) used[i] += w[i];
        }
        if (!M.feasible(s)) return M.trivial();
        return s;
    }
private:
    const Model& M;
    int n, m;
    double dens_, noise_;
    std::vector<double> base, score, used;
    std::vector<int> order;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double dens = params.get("init_density", 0.7);
    double noise = params.get("noise", 0.1);
    return std::make_unique<DropAddCongestion>(model, dens, noise);
}
