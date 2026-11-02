// COMPONENT: {"name": "neh_taillard_noisy", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 0.3]}, "tie_break": {"type": "cat", "values": ["first", "last", "random"]}}}
class NehTaillardNoisy : public hsf::Constructor<Model> {
public:
    NehTaillardNoisy(const Model& md, double noise, int tie) : M(md), noise_(noise), tie_(tie) {}
    Model::Solution build(Rng& rng) override {
        const int n = M.n, m = M.m;
        std::vector<int> seq;
        if (n == 0) return Model::Solution{seq};
        std::vector<int> order(n);
        std::vector<double> key(n);
        for (int j = 0; j < n; ++j) {
            order[j] = j;
            long long s = 0;
            for (int i = 0; i < m; ++i) s += M.pt[(size_t)j * m + i];
            double f = 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            key[j] = (double)s * f;
        }
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return key[a] > key[b]; });
        if (m == 0) return Model::Solution{order};
        E.assign((size_t)(n + 1) * m, 0);
        Q.assign((size_t)(n + 1) * m, 0);
        F.assign(m, 0);
        seq.reserve(n);
        for (int t = 0; t < n; ++t) {
            int job = order[t];
            int k = (int)seq.size();
            // heads: E row r = after first r jobs (row 0 zeros)
            for (int r = 0; r < k; ++r) {
                const long long* p = &M.pt[(size_t)seq[r] * m];
                long long* prev = &E[(size_t)r * m];
                long long* cur = &E[(size_t)(r + 1) * m];
                long long c = 0;
                for (int i = 0; i < m; ++i) {
                    c = std::max(c, prev[i]) + p[i];
                    cur[i] = c;
                }
            }
            // tails: Q row r = tail starting at position r (row k zeros)
            std::fill(Q.begin() + (size_t)k * m, Q.begin() + (size_t)(k + 1) * m, 0LL);
            for (int r = k - 1; r >= 0; --r) {
                const long long* p = &M.pt[(size_t)seq[r] * m];
                long long* nxt = &Q[(size_t)(r + 1) * m];
                long long* cur = &Q[(size_t)r * m];
                long long c = 0;
                for (int i = m - 1; i >= 0; --i) {
                    c = std::max(c, nxt[i]) + p[i];
                    cur[i] = c;
                }
            }
            const long long* pj = &M.pt[(size_t)job * m];
            long long best = std::numeric_limits<long long>::max();
            int bestPos = 0, ties = 0;
            for (int pos = 0; pos <= k; ++pos) {
                const long long* e = &E[(size_t)pos * m];
                const long long* q = &Q[(size_t)pos * m];
                long long c = 0, cmax = 0;
                for (int i = 0; i < m; ++i) {
                    c = std::max(c, e[i]) + pj[i];
                    cmax = std::max(cmax, c + q[i]);
                }
                if (cmax < best) { best = cmax; bestPos = pos; ties = 1; }
                else if (cmax == best) {
                    if (tie_ == 1) bestPos = pos;
                    else if (tie_ == 2) { ++ties; if (rng.below(ties) == 0) bestPos = pos; }
                }
            }
            seq.insert(seq.begin() + bestPos, job);
        }
        return Model::Solution{seq};
    }
private:
    const Model& M;
    double noise_;
    int tie_;
    std::vector<long long> E, Q, F;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.05);
    std::string tb = params.text("tie_break", "first");
    int tie = tb == "last" ? 1 : (tb == "random" ? 2 : 0);
    return std::make_unique<NehTaillardNoisy>(model, noise, tie);
}
