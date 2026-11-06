// COMPONENT: {"name": "neh_taillard_noisy_order", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 0.3]}, "tie_break": {"type": "cat", "values": ["random", "first"]}, "order": {"type": "cat", "values": ["sum", "sum_std"]}}}
class NehTaillardNoisy : public hsf::Constructor<Model> {
public:
    NehTaillardNoisy(const Model& md, double noise, bool rtie, bool sumstd)
        : M(md), noise_(noise), rtie_(rtie), sumstd_(sumstd) {
        int n = M.n, m = M.m;
        if (n > 0 && m > 0) {
            e_.assign((size_t)(n + 1) * m, 0);
            q_.assign((size_t)(n + 1) * m, 0);
            base_.assign(n, 0.0);
            for (int j = 0; j < n; ++j) {
                double s = 0, s2 = 0;
                for (int i = 0; i < m; ++i) { double v = (double)M.pt[(size_t)j * m + i]; s += v; s2 += v * v; }
                double key = s;
                if (sumstd_) {
                    double mean = s / m;
                    double var = std::max(0.0, s2 / m - mean * mean);
                    key = s + std::sqrt(var);
                }
                base_[j] = key;
            }
        }
    }

    Sol build(Rng& rng) override {
        int n = M.n, m = M.m;
        Sol sol(1);
        if (n <= 0) return sol;
        std::vector<int>& seq = sol[0];
        if (m <= 0) { seq.resize(n); std::iota(seq.begin(), seq.end(), 0); return sol; }

        std::vector<std::pair<double, double>> key(n);
        for (int j = 0; j < n; ++j) {
            double f = 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            key[j] = {base_[j] * f, rng.uniform()};
        }
        std::vector<int> order(n);
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            if (key[a].first != key[b].first) return key[a].first > key[b].first;
            return key[a].second < key[b].second;
        });

        seq.reserve(n);
        seq.push_back(order[0]);
        for (int t = 1; t < n; ++t) {
            int x = order[t];
            int k = (int)seq.size();
            // heads
            for (int i = 0; i < m; ++i) e_[i] = 0;
            for (int j = 0; j < k; ++j) {
                const long long* p = &M.pt[(size_t)seq[j] * m];
                long long* prow = &e_[(size_t)j * m];
                long long* row = &e_[(size_t)(j + 1) * m];
                long long left = 0;
                for (int i = 0; i < m; ++i) {
                    long long v = std::max(prow[i], left) + p[i];
                    row[i] = v; left = v;
                }
            }
            // tails
            for (int i = 0; i < m; ++i) q_[(size_t)k * m + i] = 0;
            for (int j = k - 1; j >= 0; --j) {
                const long long* p = &M.pt[(size_t)seq[j] * m];
                long long* nrow = &q_[(size_t)(j + 1) * m];
                long long* row = &q_[(size_t)j * m];
                long long right = 0;
                for (int i = m - 1; i >= 0; --i) {
                    long long v = std::max(nrow[i], right) + p[i];
                    row[i] = v; right = v;
                }
            }
            const long long* px = &M.pt[(size_t)x * m];
            long long best = std::numeric_limits<long long>::max();
            int bestPos = 0, ties = 0;
            for (int pos = 0; pos <= k; ++pos) {
                const long long* er = &e_[(size_t)pos * m];
                const long long* qr = &q_[(size_t)pos * m];
                long long f = 0, val = 0;
                for (int i = 0; i < m; ++i) {
                    f = std::max(f, er[i]) + px[i];
                    long long c = f + qr[i];
                    if (c > val) val = c;
                }
                if (val < best) { best = val; bestPos = pos; ties = 1; }
                else if (val == best && rtie_) {
                    ++ties;
                    if (rng.below(ties) == 0) bestPos = pos;
                }
            }
            seq.insert(seq.begin() + bestPos, x);
        }
        return sol;
    }

private:
    const Model& M;
    double noise_;
    bool rtie_, sumstd_;
    std::vector<long long> e_, q_;
    std::vector<double> base_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.05);
    bool rtie = params.text("tie_break", "random") == "random";
    bool sumstd = params.text("order", "sum") == "sum_std";
    return std::make_unique<NehTaillardNoisy>(model, noise, rtie, sumstd);
}
