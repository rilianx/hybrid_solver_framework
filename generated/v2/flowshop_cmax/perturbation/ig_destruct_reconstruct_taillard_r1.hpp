// COMPONENT: {"name": "ig_destruct_reconstruct_taillard", "slot": "perturbation", "params": {"d_base": {"type": "int", "range": [1, 8]}, "d_per_strength": {"type": "float", "range": [0.0, 4.0]}, "tie_break": {"type": "cat", "values": ["first", "random"]}}}
class IGDestructReconstruct : public hsf::Perturbation<Model> {
public:
    IGDestructReconstruct(const Model& m, int db, double dps, bool rt)
        : M(m), dBase_(db), dPer_(dps), randTie_(rt) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        const int n = M.n, m = M.m;
        sanitize(s);
        Model::Solution out(1);
        if (n < 2) { out[0] = work_; return out; }
        int d = dBase_ + (int)std::floor(dPer_ * (std::max(1.0, strength) - 1.0));
        d = std::max(1, std::min(d, n - 1));
        // choose d distinct positions to remove
        idx_.resize(n);
        for (int i = 0; i < n; ++i) idx_[i] = i;
        mark_.assign(n, 0);
        removed_.clear();
        for (int t = 0; t < d; ++t) {
            int r = t + rng.below(n - t);
            std::swap(idx_[t], idx_[r]);
            mark_[idx_[t]] = 1;
            removed_.push_back(work_[idx_[t]]);
        }
        seq_.clear();
        for (int i = 0; i < n; ++i) if (!mark_[i]) seq_.push_back(work_[i]);
        E_.assign((size_t)(n + 1) * (m + 1), 0);
        Q_.assign((size_t)(n + 1) * (m + 1), 0);
        for (int job : removed_) insertBest(job, rng);
        out[0] = seq_;
        if (s.size() == 1 && s[0] == out[0]) {
            int a = rng.below(n);
            int b = rng.below(n - 1);
            if (b >= a) ++b;
            std::swap(out[0][a], out[0][b]);
        }
        return out;
    }

private:
    inline long long p(int job, int mach) const { return M.pt[(size_t)job * M.m + mach]; }

    void insertBest(int job, Rng& rng) {
        const int m = M.m, W = m + 1;
        const int k = (int)seq_.size();
        // heads: E[r][c], r = number of jobs scheduled, c = machine+1
        for (int r = 1; r <= k; ++r) {
            int jb = seq_[r - 1];
            long long* cur = &E_[(size_t)r * W];
            const long long* prv = &E_[(size_t)(r - 1) * W];
            cur[0] = 0;
            for (int i = 0; i < m; ++i)
                cur[i + 1] = std::max(prv[i + 1], cur[i]) + p(jb, i);
        }
        // tails: Q[pos][i], row k = 0, column m = 0
        for (int i = 0; i <= m; ++i) Q_[(size_t)k * W + i] = 0;
        for (int pos = k - 1; pos >= 0; --pos) {
            int jb = seq_[pos];
            long long* cur = &Q_[(size_t)pos * W];
            const long long* nxt = &Q_[(size_t)(pos + 1) * W];
            cur[m] = 0;
            for (int i = m - 1; i >= 0; --i)
                cur[i] = std::max(nxt[i], cur[i + 1]) + p(jb, i);
        }
        long long best = std::numeric_limits<long long>::max();
        int bestPos = 0, ties = 0;
        for (int pos = 0; pos <= k; ++pos) {
            const long long* e = &E_[(size_t)pos * W];
            const long long* q = &Q_[(size_t)pos * W];
            long long f = 0, mx = 0;
            for (int i = 0; i < m; ++i) {
                f = std::max(f, e[i + 1]) + p(job, i);
                long long v = f + q[i];
                if (v > mx) mx = v;
            }
            if (mx < best) { best = mx; bestPos = pos; ties = 1; }
            else if (mx == best && randTie_) {
                ++ties;
                if (rng.below(ties) == 0) bestPos = pos;
            }
        }
        seq_.insert(seq_.begin() + bestPos, job);
    }

    void sanitize(const Model::Solution& s) {
        const int n = M.n;
        work_.clear();
        seen_.assign(n, 0);
        if (!s.empty())
            for (int x : s[0])
                if (x >= 0 && x < n && !seen_[x]) { seen_[x] = 1; work_.push_back(x); }
        for (int j = 0; j < n; ++j) if (!seen_[j]) work_.push_back(j);
    }

    const Model& M;
    int dBase_;
    double dPer_;
    bool randTie_;
    std::vector<int> work_, seq_, removed_, idx_;
    std::vector<char> seen_, mark_;
    std::vector<long long> E_, Q_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int db = (int)params.get("d_base", 3);
    double dps = params.get("d_per_strength", 1.0);
    bool rt = params.text("tie_break", "random") == "random";
    return std::make_unique<IGDestructReconstruct>(model, db, dps, rt);
}
