// COMPONENT: {"name": "grasp_topk_jittered_ratio", "slot": "constructor", "params": {"rcl_size": {"type": "int", "range": [1, 8]}, "weight_jitter": {"type": "float", "range": [0.0, 0.5]}}}
class GraspTopKRatio : public hsf::Constructor<Model> {
public:
    GraspTopKRatio(const Model& md, int k, double jit) : M(md), k_(std::max(1, k)), jit_(jit) {
        n = M.n; m = M.m;
        invcap.resize(m);
        for (int i = 0; i < m; ++i) invcap[i] = 1.0 / std::max(M.capacity[i], 1e-9);
        omega.resize(m); resid.resize(m); score.resize(n);
        nxt.resize(n + 2); prv.resize(n + 2); picks.reserve(k_);
        order.resize(n);
    }
    Solution build(Rng& rng) override {
        for (int i = 0; i < m; ++i) omega[i] = invcap[i] * (1.0 + jit_ * (2.0 * rng.uniform() - 1.0));
        for (int j = 0; j < n; ++j) {
            double d = 0.0;
            const double* w = &M.wt[(size_t)j * m];
            for (int i = 0; i < m; ++i) d += omega[i] * w[i];
            score[j] = (d <= 1e-15) ? 1e300 : M.profit[j] / d;
        }
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            if (score[a] != score[b]) return score[a] > score[b];
            return a < b;
        });
        // linked list over positions: node p+1 for order[p]; 0 = head sentinel, n+1 = tail sentinel
        const int H = 0, T = n + 1;
        int last = H;
        for (int p = 0; p < n; ++p) {
            if (M.profit[order[p]] < 0) continue;
            nxt[last] = p + 1; prv[p + 1] = last; last = p + 1;
        }
        nxt[last] = T; prv[T] = last;
        for (int i = 0; i < m; ++i) resid[i] = M.capacity[i];
        Solution s(1, std::vector<int>(n, 0));
        while (true) {
            picks.clear();
            int node = nxt[H];
            while (node != T && (int)picks.size() < k_) {
                int nn = nxt[node];
                int j = order[node - 1];
                if (fits(j)) picks.push_back(node);
                else unlink(node);
                node = nn;
            }
            if (picks.empty()) break;
            int chosen = picks[rng.below((int)picks.size())];
            int j = order[chosen - 1];
            unlink(chosen);
            s[0][j] = 1;
            const double* w = &M.wt[(size_t)j * m];
            for (int i = 0; i < m; ++i) resid[i] -= w[i];
        }
        if (!M.feasible(s)) return M.trivial();
        return s;
    }
private:
    bool fits(int j) const {
        const double* w = &M.wt[(size_t)j * m];
        for (int i = 0; i < m; ++i) if (w[i] > resid[i] + Model::EPS) return false;
        return true;
    }
    void unlink(int node) { int a = prv[node], b = nxt[node]; nxt[a] = b; prv[b] = a; }
    const Model& M;
    int n, m, k_;
    double jit_;
    std::vector<double> invcap, omega, resid, score;
    std::vector<int> nxt, prv, picks, order;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("rcl_size", 3);
    double jit = params.get("weight_jitter", 0.2);
    return std::make_unique<GraspTopKRatio>(model, k, jit);
}
