// COMPONENT: {"name": "lr_index_greedy_rcl", "slot": "constructor", "params": {"first_rcl": {"type": "int", "range": [1, 10]}, "rcl_alpha": {"type": "float", "range": [0.0, 0.3]}}}
class LRIndexGreedy : public hsf::Constructor<Model> {
public:
    LRIndexGreedy(const Model& md, int firstRcl, double alpha)
        : M(md), firstRcl_(std::max(1, firstRcl)), alpha_(std::max(0.0, alpha)) {}

    Model::Solution build(Rng& rng) override {
        const int n = M.n, m = M.m;
        Model::Solution out(1);
        if (n <= 0) return out;
        if (m <= 0) {
            std::vector<int> p(n);
            std::iota(p.begin(), p.end(), 0);
            out[0] = p;
            return out;
        }
        std::vector<long long> C(m, 0), Cj(m), Ca(m);
        std::vector<double> sumRem(m, 0.0);
        for (int j = 0; j < n; ++j)
            for (int i = 0; i < m; ++i) sumRem[i] += (double)M.pj[(size_t)j * m + i];
        std::vector<int> rem(n);
        std::iota(rem.begin(), rem.end(), 0);
        std::vector<int> seq;
        seq.reserve(n);
        std::vector<double> idx;
        std::vector<int> order;
        const double denom = (double)std::max(1, n - 2);
        for (int k = 0; k < n; ++k) {
            int r = (int)rem.size();
            idx.assign(r, 0.0);
            for (int c = 0; c < r; ++c) {
                int j = rem[c];
                const long long* p = &M.pj[(size_t)j * m];
                Cj[0] = C[0] + p[0];
                double IT = 0.0;
                for (int i = 1; i < m; ++i) {
                    long long st = std::max(Cj[i - 1], C[i]);
                    if (Cj[i - 1] > C[i]) {
                        double w = (double)m / ((double)i + (double)k * (double)(m - i) / denom);
                        IT += w * (double)(Cj[i - 1] - C[i]);
                    }
                    Cj[i] = st + p[i];
                }
                double AT;
                if (r > 1) {
                    double inv = 1.0 / (double)(r - 1);
                    double ca = (double)Cj[0] + (sumRem[0] - (double)p[0]) * inv;
                    double prev = ca;
                    for (int i = 1; i < m; ++i) {
                        double a = (sumRem[i] - (double)p[i]) * inv;
                        prev = std::max(prev, (double)Cj[i]) + a;
                    }
                    AT = (double)Cj[m - 1] + prev;
                } else {
                    AT = (double)Cj[m - 1];
                }
                idx[c] = (double)std::max(0, n - k - 2) * IT + AT;
            }
            int pick;
            if (k == 0 && firstRcl_ > 1) {
                order.resize(r);
                std::iota(order.begin(), order.end(), 0);
                int t = std::min(firstRcl_, r);
                std::partial_sort(order.begin(), order.begin() + t, order.end(),
                                  [&](int a, int b) { return idx[a] < idx[b] || (idx[a] == idx[b] && a < b); });
                pick = order[rng.below(t)];
            } else {
                double mn = idx[0], mx = idx[0];
                for (int c = 1; c < r; ++c) { mn = std::min(mn, idx[c]); mx = std::max(mx, idx[c]); }
                double thr = mn + alpha_ * (mx - mn);
                int cnt = 0;
                for (int c = 0; c < r; ++c) if (idx[c] <= thr) ++cnt;
                int target = rng.below(std::max(1, cnt));
                pick = 0;
                for (int c = 0; c < r; ++c) if (idx[c] <= thr) { if (target == 0) { pick = c; break; } --target; }
            }
            int j = rem[pick];
            const long long* p = &M.pj[(size_t)j * m];
            C[0] += p[0];
            for (int i = 1; i < m; ++i) C[i] = std::max(C[i - 1], C[i]) + p[i];
            for (int i = 0; i < m; ++i) sumRem[i] -= (double)p[i];
            seq.push_back(j);
            rem[pick] = rem.back();
            rem.pop_back();
        }
        out[0] = std::move(seq);
        return out;
    }

private:
    const Model& M;
    int firstRcl_;
    double alpha_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int fr = (int)params.get("first_rcl", 3);
    double a = params.get("rcl_alpha", 0.05);
    return std::make_unique<LRIndexGreedy>(model, fr, a);
}
