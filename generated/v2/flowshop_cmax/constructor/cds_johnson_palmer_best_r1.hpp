// COMPONENT: {"name": "cds_johnson_palmer_best", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 0.25]}, "max_surrogates": {"type": "int", "range": [1, 60]}, "use_palmer": {"type": "cat", "values": ["yes", "no"]}}}
class CdsJohnson : public hsf::Constructor<Model> {
public:
    CdsJohnson(const Model& md, double noise, int maxs, bool palmer)
        : M(md), noise_(noise), maxs_(std::max(1, maxs)), palmer_(palmer) {}

    Sol build(Rng& rng) override {
        int n = M.n, m = M.m;
        Sol sol(1);
        if (n <= 0) return sol;
        std::vector<int>& best = sol[0];
        best.resize(n);
        std::iota(best.begin(), best.end(), 0);
        if (m <= 1) {
            for (int i = n - 1; i > 0; --i) std::swap(best[i], best[rng.below(i + 1)]);
            return sol;
        }
        C_.assign(m, 0);
        a_.assign(n, 0.0); b_.assign(n, 0.0); tk_.assign(n, 0.0);
        cand_.resize(n);
        long long bestMk = std::numeric_limits<long long>::max();

        // surrogate indices k in [1, m-1]
        std::vector<int> ks;
        int total = m - 1;
        if (total <= maxs_) { for (int k = 1; k <= total; ++k) ks.push_back(k); }
        else {
            for (int s = 0; s < maxs_; ++s) {
                int k = 1 + (int)std::llround((double)s * (total - 1) / std::max(1, maxs_ - 1));
                if (ks.empty() || ks.back() != k) ks.push_back(k);
            }
        }

        for (int k : ks) {
            for (int j = 0; j < n; ++j) {
                const long long* p = &M.pt[(size_t)j * m];
                double a = 0, b = 0;
                for (int i = 0; i < k; ++i) a += (double)p[i];
                for (int i = m - k; i < m; ++i) b += (double)p[i];
                a_[j] = a * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
                b_[j] = b * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
                tk_[j] = rng.uniform();
            }
            johnson(n);
            long long mk = makespan(cand_);
            if (mk < bestMk) { bestMk = mk; best = cand_; }
        }

        if (palmer_) {
            for (int j = 0; j < n; ++j) {
                const long long* p = &M.pt[(size_t)j * m];
                double sl = 0;
                for (int i = 0; i < m; ++i) sl += (double)(2 * i - m + 1) * (double)p[i];
                a_[j] = sl * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
                tk_[j] = rng.uniform();
            }
            std::iota(cand_.begin(), cand_.end(), 0);
            std::sort(cand_.begin(), cand_.end(), [&](int x, int y) {
                if (a_[x] != a_[y]) return a_[x] > a_[y];
                return tk_[x] < tk_[y];
            });
            long long mk = makespan(cand_);
            if (mk < bestMk) { bestMk = mk; best = cand_; }
        }
        return sol;
    }

private:
    void johnson(int n) {
        std::vector<int>& s1 = s1_; std::vector<int>& s2 = s2_;
        s1.clear(); s2.clear();
        for (int j = 0; j < n; ++j) (a_[j] < b_[j] ? s1 : s2).push_back(j);
        std::sort(s1.begin(), s1.end(), [&](int x, int y) {
            if (a_[x] != a_[y]) return a_[x] < a_[y];
            return tk_[x] < tk_[y];
        });
        std::sort(s2.begin(), s2.end(), [&](int x, int y) {
            if (b_[x] != b_[y]) return b_[x] > b_[y];
            return tk_[x] < tk_[y];
        });
        int t = 0;
        for (int j : s1) cand_[t++] = j;
        for (int j : s2) cand_[t++] = j;
    }

    long long makespan(const std::vector<int>& seq) {
        int m = M.m;
        std::fill(C_.begin(), C_.end(), 0);
        for (int j : seq) {
            const long long* p = &M.pt[(size_t)j * m];
            long long left = 0;
            for (int i = 0; i < m; ++i) {
                long long v = std::max(C_[i], left) + p[i];
                C_[i] = v; left = v;
            }
        }
        return C_[m - 1];
    }

    const Model& M;
    double noise_;
    int maxs_;
    bool palmer_;
    std::vector<long long> C_;
    std::vector<double> a_, b_, tk_;
    std::vector<int> cand_, s1_, s2_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.03);
    int maxs = (int)params.get("max_surrogates", 20);
    bool palmer = params.text("use_palmer", "yes") == "yes";
    return std::make_unique<CdsJohnson>(model, noise, maxs, palmer);
}
