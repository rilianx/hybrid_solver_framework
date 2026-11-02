// COMPONENT: {"name": "weighted_priority_sort_adjacent_sweep", "slot": "constructor", "params": {"slope": {"type": "float", "range": [-1.0, 3.0]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "sweeps": {"type": "int", "range": [0, 6]}}}
class PrioritySweep : public hsf::Constructor<Model> {
public:
    PrioritySweep(const Model& md, double slope, double noise, int sweeps)
        : md_(md), slope_(slope), noise_(noise), sweeps_(std::max(0, sweeps)) {}
    Model::Solution build(Rng& rng) override {
        const int n = md_.n, m = md_.m;
        if (n <= 0) return Model::Solution{std::vector<int>()};
        if (m <= 0) return md_.trivial();
        std::vector<std::pair<double, int>> key(n);
        for (int j = 0; j < n; ++j) {
            double s = 0;
            for (int i = 0; i < m; ++i) {
                double w = 1.0 + slope_ * (m > 1 ? (double)(m - 1 - i) / (m - 1) : 0.0);
                if (w < 0.05) w = 0.05;
                s += w * (double)md_.pj[(size_t)j * m + i];
            }
            s *= 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            key[j] = {s, j};
        }
        std::sort(key.begin(), key.end());
        std::vector<int> seq(n);
        for (int t = 0; t < n; ++t) seq[t] = key[t].second;
        std::vector<long long> C(m), A(m), B(m);
        for (int s = 0; s < sweeps_; ++s) {
            std::fill(C.begin(), C.end(), 0LL);
            bool changed = false;
            for (int t = 0; t + 1 < n; ++t) {
                int a = seq[t], b = seq[t + 1];
                A = C; add(A, a, m); long long fa = A[m - 1]; add(A, b, m); fa += A[m - 1];
                B = C; add(B, b, m); long long fb = B[m - 1]; add(B, a, m); fb += B[m - 1];
                if (fb < fa || (fb == fa && B[m - 1] < A[m - 1])) {
                    std::swap(seq[t], seq[t + 1]);
                    changed = true;
                }
                add(C, seq[t], m);
            }
            if (!changed) break;
        }
        return Model::Solution{seq};
    }
private:
    void add(std::vector<long long>& C, int j, int m) const {
        const long long* p = &md_.pj[(size_t)j * m];
        long long prev = 0;
        for (int i = 0; i < m; ++i) { C[i] = std::max(C[i], prev) + p[i]; prev = C[i]; }
    }
    const Model& md_;
    double slope_, noise_;
    int sweeps_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sl = params.get("slope", 0.5);
    double nz = params.get("noise", 0.1);
    int sw = (int)params.get("sweeps", 3);
    return std::make_unique<PrioritySweep>(model, sl, nz, sw);
}
