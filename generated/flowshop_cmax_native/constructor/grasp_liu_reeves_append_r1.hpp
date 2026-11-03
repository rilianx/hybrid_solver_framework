// COMPONENT: {"name": "grasp_liu_reeves_append", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 0.5]}, "starts": {"type": "int", "range": [1, 8]}}}
class GraspLiuReeves : public hsf::Constructor<Model> {
public:
    GraspLiuReeves(const Model& md, double alpha, int starts) : M(md), alpha_(alpha), starts_(starts) {}
    Model::Solution build(Rng& rng) override {
        const int n = M.n, m = M.m;
        std::vector<int> best;
        if (n == 0) return Model::Solution{best};
        if (m == 0) { best.resize(n); for (int j = 0; j < n; ++j) best[j] = j; return Model::Solution{best}; }
        long long bestC = std::numeric_limits<long long>::max();
        for (int s = 0; s < starts_; ++s) {
            long long c;
            std::vector<int> seq = one(rng, c);
            if (c < bestC) { bestC = c; best.swap(seq); }
        }
        return Model::Solution{best};
    }
private:
    std::vector<int> one(Rng& rng, long long& cmaxOut) {
        const int n = M.n, m = M.m;
        std::vector<int> rem(n);
        for (int j = 0; j < n; ++j) rem[j] = j;
        std::vector<long long> C(m, 0), Cj(m);
        std::vector<double> remSum(m, 0.0), A(m), idx(n);
        for (int j = 0; j < n; ++j)
            for (int i = 0; i < m; ++i) remSum[i] += (double)M.pt[(size_t)j * m + i];
        std::vector<int> seq;
        seq.reserve(n);
        double nd = std::max(1, n - 2);
        for (int k = 0; k < n; ++k) {
            int r = (int)rem.size();
            double lo = 1e300, hi = -1e300;
            for (int t = 0; t < r; ++t) {
                int j = rem[t];
                const long long* p = &M.pt[(size_t)j * m];
                long long c = 0;
                double IT = 0.0;
                for (int i = 0; i < m; ++i) {
                    if (i > 0) {
                        long long gap = c - C[i];
                        if (gap > 0) IT += (double)m * gap / ((i + 1) + k * (double)(m - i - 1) / nd);
                    }
                    c = std::max(c, C[i]) + p[i];
                    Cj[i] = c;
                }
                double AT = 0.0;
                if (r > 1) {
                    double a = 0.0;
                    for (int i = 0; i < m; ++i) {
                        double pa = (remSum[i] - (double)p[i]) / (r - 1);
                        a = std::max(a, (double)Cj[i]) + pa;
                        AT += a;
                    }
                }
                double v = (double)(n - k - 2) * IT + AT;
                idx[t] = v;
                lo = std::min(lo, v); hi = std::max(hi, v);
            }
            double thr = lo + alpha_ * (hi - lo);
            int cnt = 0, pick = 0;
            for (int t = 0; t < r; ++t)
                if (idx[t] <= thr) { ++cnt; if (rng.below(cnt) == 0) pick = t; }
            int j = rem[pick];
            const long long* p = &M.pt[(size_t)j * m];
            long long c = 0;
            for (int i = 0; i < m; ++i) { c = std::max(c, C[i]) + p[i]; C[i] = c; remSum[i] -= (double)p[i]; }
            seq.push_back(j);
            rem[pick] = rem.back(); rem.pop_back();
        }
        cmaxOut = C[m - 1];
        return seq;
    }
    const Model& M;
    double alpha_;
    int starts_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = params.get("alpha", 0.1);
    int starts = std::max(1, (int)params.get("starts", 2));
    return std::make_unique<GraspLiuReeves>(model, alpha, starts);
}
