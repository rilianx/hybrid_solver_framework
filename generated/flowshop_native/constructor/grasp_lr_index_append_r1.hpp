// COMPONENT: {"name": "grasp_lr_index_append", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 0.4]}, "idle_weight": {"type": "float", "range": [0.2, 3.0]}}}
class GraspLR : public hsf::Constructor<Model> {
public:
    GraspLR(const Model& md, double alpha, double iw) : md_(md), alpha_(alpha), iw_(iw) {}
    Model::Solution build(Rng& rng) override {
        const int n = md_.n, m = md_.m;
        if (n <= 0) return Model::Solution{std::vector<int>()};
        if (m <= 0) return md_.trivial();
        std::vector<int> rem(n);
        std::iota(rem.begin(), rem.end(), 0);
        std::vector<double> S(m, 0.0);
        for (int j = 0; j < n; ++j)
            for (int i = 0; i < m; ++i) S[i] += (double)md_.pj[(size_t)j * m + i];
        std::vector<long long> C(m, 0), cj(m);
        std::vector<double> val;
        std::vector<int> seq;
        seq.reserve(n);
        int k = 0;
        while (!rem.empty()) {
            int r = (int)rem.size();
            int pick = 0;
            if (r > 1) {
                val.assign(r, 0.0);
                double lo = std::numeric_limits<double>::infinity(), hi = -lo;
                double kf = (n > 2) ? (double)k / (double)(n - 2) : 0.0;
                double mult = std::max(0, n - k - 2) * iw_;
                for (int c = 0; c < r; ++c) {
                    const long long* p = &md_.pj[(size_t)rem[c] * m];
                    long long prev = 0;
                    double IT = 0.0;
                    for (int i = 0; i < m; ++i) {
                        if (i > 0 && prev > C[i]) {
                            double w = (double)m / (i + 1 + kf * (m - i - 1));
                            IT += w * (double)(prev - C[i]);
                        }
                        long long st = std::max(C[i], prev);
                        cj[i] = st + p[i];
                        prev = cj[i];
                    }
                    double a = 0.0;
                    for (int i = 0; i < m; ++i) {
                        double q = (S[i] - (double)p[i]) / (double)(r - 1);
                        a = std::max((double)cj[i], a) + q;
                    }
                    double AT = (double)cj[m - 1] + a;
                    val[c] = mult * IT + AT;
                    lo = std::min(lo, val[c]);
                    hi = std::max(hi, val[c]);
                }
                double thr = lo + alpha_ * (hi - lo);
                int cnt = 0;
                for (int c = 0; c < r; ++c) if (val[c] <= thr) ++cnt;
                int target = rng.below(std::max(cnt, 1));
                for (int c = 0; c < r; ++c)
                    if (val[c] <= thr) { if (target-- == 0) { pick = c; break; } }
            }
            int j = rem[pick];
            const long long* p = &md_.pj[(size_t)j * m];
            long long prev = 0;
            for (int i = 0; i < m; ++i) { C[i] = std::max(C[i], prev) + p[i]; prev = C[i]; S[i] -= (double)p[i]; }
            seq.push_back(j);
            rem[pick] = rem.back();
            rem.pop_back();
            ++k;
        }
        return Model::Solution{seq};
    }
private:
    const Model& md_;
    double alpha_, iw_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double a = params.get("alpha", 0.05);
    double w = params.get("idle_weight", 1.0);
    return std::make_unique<GraspLR>(model, a, w);
}
