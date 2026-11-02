// COMPONENT: {"name": "cds_johnson_palmer", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 0.2]}, "include_palmer": {"type": "int", "range": [0, 1]}}}
class CdsJohnsonPalmer : public hsf::Constructor<Model> {
public:
    CdsJohnsonPalmer(const Model& md, double noise, int palmer) : M(md), noise_(noise), palmer_(palmer) {}
    Model::Solution build(Rng& rng) override {
        const int n = M.n, m = M.m;
        std::vector<int> best(n);
        for (int j = 0; j < n; ++j) best[j] = j;
        if (n == 0 || m == 0) return Model::Solution{best};
        C.assign(m, 0);
        long long bestC = std::numeric_limits<long long>::max();
        std::vector<double> a(n, 0.0), b(n, 0.0);
        std::vector<int> s1, s2, seq;
        s1.reserve(n); s2.reserve(n); seq.reserve(n);
        for (int kk = 1; kk <= std::max(1, m - 1); ++kk) {
            for (int j = 0; j < n; ++j) {
                const long long* p = &M.pt[(size_t)j * m];
                double sa = 0, sb = 0;
                for (int i = 0; i < std::min(kk, m); ++i) sa += (double)p[i];
                for (int i = std::max(0, m - kk); i < m; ++i) sb += (double)p[i];
                a[j] = sa * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
                b[j] = sb * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
            }
            s1.clear(); s2.clear();
            for (int j = 0; j < n; ++j) (a[j] < b[j] ? s1 : s2).push_back(j);
            std::stable_sort(s1.begin(), s1.end(), [&](int x, int y) { return a[x] < a[y]; });
            std::stable_sort(s2.begin(), s2.end(), [&](int x, int y) { return b[x] > b[y]; });
            seq = s1;
            seq.insert(seq.end(), s2.begin(), s2.end());
            long long c = eval(seq);
            if (c < bestC) { bestC = c; best = seq; }
        }
        if (palmer_) {
            std::vector<double> slope(n, 0.0);
            for (int j = 0; j < n; ++j) {
                const long long* p = &M.pt[(size_t)j * m];
                double s = 0;
                for (int i = 0; i < m; ++i) s += (double)(2 * i - m + 1) * (double)p[i];
                slope[j] = s * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
            }
            seq.resize(n);
            for (int j = 0; j < n; ++j) seq[j] = j;
            std::stable_sort(seq.begin(), seq.end(), [&](int x, int y) { return slope[x] > slope[y]; });
            long long c = eval(seq);
            if (c < bestC) { bestC = c; best = seq; }
        }
        return Model::Solution{best};
    }
private:
    long long eval(const std::vector<int>& seq) {
        const int m = M.m;
        std::fill(C.begin(), C.end(), 0LL);
        for (int j : seq) {
            const long long* p = &M.pt[(size_t)j * m];
            long long c = 0;
            for (int i = 0; i < m; ++i) { c = std::max(c, C[i]) + p[i]; C[i] = c; }
        }
        return C[m - 1];
    }
    const Model& M;
    double noise_;
    int palmer_;
    std::vector<long long> C;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.0);
    int palmer = (int)params.get("include_palmer", 1);
    return std::make_unique<CdsJohnsonPalmer>(model, noise, palmer);
}
