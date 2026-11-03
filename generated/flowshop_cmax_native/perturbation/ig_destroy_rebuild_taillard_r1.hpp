// COMPONENT: {"name": "ig_destroy_rebuild_taillard", "slot": "perturbation", "params": {"d_base": {"type": "int", "range": [1, 8]}, "d_max_frac": {"type": "float", "range": [0.05, 0.5]}}}
class IGDestroyRebuild : public hsf::Perturbation<Model> {
public:
    IGDestroyRebuild(const Model& M, int dBase, double dMaxFrac) : M_(M), dBase_(dBase), dMaxFrac_(dMaxFrac) {
        int n = M_.n, m = std::max(1, M_.m);
        e_.assign((size_t)(n + 1) * m, 0);
        q_.assign((size_t)(n + 2) * m, 0);
        f_.assign(m, 0);
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        Model::Solution out = s;
        if (out.empty()) return out;
        std::vector<int>& v = out[0];
        int n = (int)v.size();
        if (n < 2 || M_.m == 0) return out;
        int dmax = std::max(1, std::min(n - 1, (int)std::lround(dMaxFrac_ * n)));
        int d = (int)std::lround(dBase_ * std::max(1.0, strength));
        d = std::max(1, std::min(d, dmax));
        // destrucción: elegir d posiciones distintas
        removed_.clear();
        for (int t = 0; t < d; ++t) {
            int idx = rng.below((int)v.size());
            removed_.push_back(v[idx]);
            v.erase(v.begin() + idx);
        }
        // reconstrucción
        for (int j : removed_) insertBest(v, j, rng);
        ensureDifferent(s[0], v, rng);
        return out;
    }
private:
    const Model& M_;
    int dBase_;
    double dMaxFrac_;
    std::vector<long long> e_, q_, f_;
    std::vector<int> removed_;

    long long p(int j, int i) const {
        if (j < 0 || j >= M_.n) return 0;
        return M_.pt[(size_t)j * M_.m + i];
    }
    void insertBest(std::vector<int>& seq, int job, Rng& rng) {
        int k = (int)seq.size(), m = M_.m;
        // heads
        for (int i = 0; i < m; ++i) e_[i] = 0;
        for (int r = 1; r <= k; ++r) {
            long long prev = 0;
            int jj = seq[r - 1];
            for (int i = 0; i < m; ++i) {
                long long up = e_[(size_t)(r - 1) * m + i];
                long long c = (up > prev ? up : prev) + p(jj, i);
                e_[(size_t)r * m + i] = c;
                prev = c;
            }
        }
        // tails
        for (int i = 0; i < m; ++i) q_[(size_t)k * m + i] = 0;
        for (int r = k - 1; r >= 0; --r) {
            long long nxt = 0;
            int jj = seq[r];
            for (int i = m - 1; i >= 0; --i) {
                long long dn = q_[(size_t)(r + 1) * m + i];
                long long c = (dn > nxt ? dn : nxt) + p(jj, i);
                q_[(size_t)r * m + i] = c;
                nxt = c;
            }
        }
        long long best = std::numeric_limits<long long>::max();
        int bestPos = 0, ties = 0;
        for (int pos = 0; pos <= k; ++pos) {
            long long prev = 0, mk = 0;
            for (int i = 0; i < m; ++i) {
                long long h = e_[(size_t)pos * m + i];
                long long c = (h > prev ? h : prev) + p(job, i);
                prev = c;
                long long tot = c + q_[(size_t)pos * m + i];
                if (tot > mk) mk = tot;
            }
            if (mk < best) { best = mk; bestPos = pos; ties = 1; }
            else if (mk == best) { ++ties; if (rng.below(ties) == 0) bestPos = pos; }
        }
        seq.insert(seq.begin() + bestPos, job);
    }
    static void ensureDifferent(const std::vector<int>& orig, std::vector<int>& v, Rng& rng) {
        if (orig != v) return;
        int n = (int)v.size();
        for (int tries = 0; tries < 64; ++tries) {
            int a = rng.below(n), b = rng.below(n);
            if (v[a] != v[b]) { std::swap(v[a], v[b]); return; }
        }
        for (int a = 0; a + 1 < n; ++a)
            if (v[a] != v[a + 1]) { std::swap(v[a], v[a + 1]); return; }
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int dBase = (int)params.get("d_base", 4.0);
    double frac = params.get("d_max_frac", 0.3);
    return std::make_unique<IGDestroyRebuild>(model, dBase, frac);
}
