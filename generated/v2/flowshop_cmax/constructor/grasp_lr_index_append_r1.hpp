// COMPONENT: {"name": "grasp_lr_index_append", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 0.4]}, "at_weight": {"type": "float", "range": [0.0, 2.0]}}}
class GraspLR : public hsf::Constructor<Model> {
public:
    GraspLR(const Model& md, double alpha, double atw) : M(md), alpha_(alpha), atw_(atw) {}

    Sol build(Rng& rng) override {
        int n = M.n, m = M.m;
        Sol sol(1);
        if (n <= 0) return sol;
        std::vector<int>& seq = sol[0];
        seq.reserve(n);
        if (m <= 0) { seq.resize(n); std::iota(seq.begin(), seq.end(), 0); return sol; }

        C_.assign(m, 0);
        S_.assign(m, 0.0);
        rem_.resize(n);
        std::iota(rem_.begin(), rem_.end(), 0);
        for (int j = 0; j < n; ++j)
            for (int i = 0; i < m; ++i) S_[i] += (double)M.pt[(size_t)j * m + i];
        w_.assign(m, 0.0);
        idx_.resize(n);

        double denomN = (double)std::max(1, n - 2);
        for (int k = 0; k < n; ++k) {
            int r = (int)rem_.size();
            if (r == 1) { appendJob(rem_[0]); seq.push_back(rem_[0]); rem_.pop_back(); break; }
            for (int i = 1; i < m; ++i) {
                double ii = (double)(i + 1);
                w_[i] = (double)m / (ii + (double)k * ((double)m - ii) / denomN);
            }
            double itCoef = (double)std::max(0, n - k - 2);
            double lo = std::numeric_limits<double>::infinity(), hi = -lo;
            for (int t = 0; t < r; ++t) {
                int j = rem_[t];
                const long long* p = &M.pt[(size_t)j * m];
                double invR = 1.0 / (double)(r - 1);
                double cnPrev = 0, caPrev = 0, it = 0;
                for (int i = 0; i < m; ++i) {
                    double ci = (double)C_[i];
                    if (i > 0 && cnPrev > ci) it += w_[i] * (cnPrev - ci);
                    double cn = std::max(cnPrev, ci) + (double)p[i];
                    double ap = (S_[i] - (double)p[i]) * invR;
                    double ca = std::max(caPrev, cn) + ap;
                    cnPrev = cn; caPrev = ca;
                }
                double at = cnPrev + caPrev;
                double v = itCoef * it + atw_ * at;
                idx_[t] = v;
                if (v < lo) lo = v;
                if (v > hi) hi = v;
            }
            double thr = lo + alpha_ * (hi - lo);
            int chosen = -1, cntc = 0;
            for (int t = 0; t < r; ++t) {
                if (idx_[t] <= thr + 1e-12) {
                    ++cntc;
                    if (rng.below(cntc) == 0) chosen = t;
                }
            }
            if (chosen < 0) chosen = 0;
            int j = rem_[chosen];
            appendJob(j);
            seq.push_back(j);
            const long long* p = &M.pt[(size_t)j * m];
            for (int i = 0; i < m; ++i) S_[i] -= (double)p[i];
            rem_[chosen] = rem_.back();
            rem_.pop_back();
        }
        return sol;
    }

private:
    void appendJob(int j) {
        int m = M.m;
        const long long* p = &M.pt[(size_t)j * m];
        long long left = 0;
        for (int i = 0; i < m; ++i) {
            long long v = std::max(C_[i], left) + p[i];
            C_[i] = v; left = v;
        }
    }

    const Model& M;
    double alpha_, atw_;
    std::vector<long long> C_;
    std::vector<double> S_, w_, idx_;
    std::vector<int> rem_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = params.get("alpha", 0.1);
    double atw = params.get("at_weight", 1.0);
    return std::make_unique<GraspLR>(model, alpha, atw);
}
