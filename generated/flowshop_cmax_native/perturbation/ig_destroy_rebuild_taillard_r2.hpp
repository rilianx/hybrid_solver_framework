// COMPONENT: {"name": "ig_destroy_rebuild_taillard", "slot": "perturbation", "params": {"d_base": {"type": "int", "range": [1, 8]}, "d_max_frac": {"type": "float", "range": [0.05, 0.5]}}}
class IGDestroyRebuild : public hsf::Perturbation<Model> {
public:
    IGDestroyRebuild(const Model& M, int dBase, double dMaxFrac) : M_(M), dBase_(dBase), dMaxFrac_(dMaxFrac) {
        int n = M_.n, m = std::max(1, M_.m);
        e_.assign((size_t)(n + 2) * m, 0);
        q_.assign((size_t)(n + 2) * m, 0);
        zero_.assign(m, 0);
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
        removed_.clear();
        for (int t = 0; t < d; ++t) {
            int idx = rng.below((int)v.size());
            removed_.push_back(v[idx]);
            v.erase(v.begin() + idx);
        }
        int m = M_.m;
        size_t need = (size_t)(n + 2) * m;
        if (e_.size() < need) { e_.assign(need, 0); q_.assign(need, 0); }
        int k = (int)v.size();
        // full heads/tails once
        for (int i = 0; i < m; ++i) e_[i] = 0;
        heads(v, 1, k);
        for (int i = 0; i < m; ++i) q_[i] = 0;
        tails(v, 1, k);
        for (int idx = 0; idx < (int)removed_.size(); ++idx) {
            int job = removed_[idx];
            k = (int)v.size();
            int bestPos = evalBest(job, k, rng);
            v.insert(v.begin() + bestPos, job);
            if (idx + 1 < (int)removed_.size()) {
                heads(v, bestPos + 1, k + 1);
                tails(v, k - bestPos + 1, k + 1);
            }
        }
        ensureDifferent(s[0], v, rng);
        return out;
    }
private:
    const Model& M_;
    int dBase_;
    double dMaxFrac_;
    std::vector<long long> e_, q_, zero_;
    std::vector<int> removed_;

    inline const long long* row(int j) const {
        if (j < 0 || j >= M_.n) return zero_.data();
        return M_.pt.data() + (size_t)j * M_.m;
    }
    // e_ row r = heads after first r jobs; recompute rows from..to
    void heads(const std::vector<int>& seq, int from, int to) {
        int m = M_.m;
        long long* E = e_.data();
        for (int r = from; r <= to; ++r) {
            const long long* pj = row(seq[r - 1]);
            const long long* up = E + (size_t)(r - 1) * m;
            long long* cur = E + (size_t)r * m;
            long long c = up[0] + pj[0];
            cur[0] = c;
            for (int i = 1; i < m; ++i) {
                long long u = up[i];
                c = (u > c ? u : c) + pj[i];
                cur[i] = c;
            }
        }
    }
    // q_ row t = tails of the suffix of length t; sequence length = seq.size()
    void tails(const std::vector<int>& seq, int from, int to) {
        int m = M_.m;
        int K = (int)seq.size();
        long long* Q = q_.data();
        for (int t = from; t <= to; ++t) {
            const long long* pj = row(seq[K - t]);
            const long long* dn = Q + (size_t)(t - 1) * m;
            long long* cur = Q + (size_t)t * m;
            long long c = dn[m - 1] + pj[m - 1];
            cur[m - 1] = c;
            for (int i = m - 2; i >= 0; --i) {
                long long d = dn[i];
                c = (d > c ? d : c) + pj[i];
                cur[i] = c;
            }
        }
    }
    int evalBest(int job, int k, Rng& rng) {
        int m = M_.m;
        const long long* pj = row(job);
        const long long* E = e_.data();
        const long long* Q = q_.data();
        long long best = std::numeric_limits<long long>::max();
        int bestPos = 0, ties = 0;
        for (int pos = 0; pos <= k; ++pos) {
            const long long* h = E + (size_t)pos * m;
            const long long* q = Q + (size_t)(k - pos) * m;
            long long prev = 0, mk = 0;
            bool over = false;
            for (int i = 0; i < m; ++i) {
                long long hv = h[i];
                long long c = (hv > prev ? hv : prev) + pj[i];
                prev = c;
                long long tot = c + q[i];
                if (tot > mk) { mk = tot; if (mk > best) { over = true; break; } }
            }
            if (over) continue;
            if (mk < best) { best = mk; bestPos = pos; ties = 1; }
            else if (mk == best) { ++ties; if (rng.below(ties) == 0) bestPos = pos; }
        }
        return bestPos;
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
