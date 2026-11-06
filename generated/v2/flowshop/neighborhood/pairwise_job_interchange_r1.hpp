// COMPONENT: {"name": "pairwise_job_interchange", "slot": "neighborhood", "params": {"max_gap": {"type": "int", "range": [0, 500]}}}
class FlowCache {
public:
    const Model& md;
    int n, m;
    std::vector<int> seq;
    std::vector<long long> C, F, row;
    std::vector<char> seen;
    bool valid = false, fast = false;
    explicit FlowCache(const Model& md_) : md(md_), n(md_.n), m(md_.m) {}
    bool ensure(const Model::Solution& s) {
        if (s.size() != 1) return false;
        if (valid && s[0] == seq) return fast;
        seq = s[0]; valid = true; fast = false;
        if ((int)seq.size() != n || m <= 0 || n <= 0) return false;
        seen.assign(n, 0);
        for (int j : seq) { if (j < 0 || j >= n || seen[j]) return false; seen[j] = 1; }
        C.assign((size_t)(n + 1) * m, 0); F.assign(n + 1, 0);
        for (int k = 0; k < n; ++k) {
            const long long* p = &md.pj[(size_t)seq[k] * m];
            const long long* pr = &C[(size_t)k * m];
            long long* cr = &C[(size_t)(k + 1) * m];
            long long c = pr[0] + p[0]; cr[0] = c;
            for (int i = 1; i < m; ++i) { c = std::max(c, pr[i]) + p[i]; cr[i] = c; }
            F[k + 1] = F[k] + c;
        }
        fast = (md.objective(s) == (double)F[n]);
        return fast;
    }
    template <class G>
    long long tail(int st, int same_from, G job) {
        row.assign(C.begin() + (size_t)st * m, C.begin() + (size_t)(st + 1) * m);
        long long tot = F[st];
        for (int k = st; k < n; ++k) {
            const long long* p = &md.pj[(size_t)job(k) * m];
            long long c = row[0] + p[0]; row[0] = c;
            for (int i = 1; i < m; ++i) { c = std::max(c, row[i]) + p[i]; row[i] = c; }
            tot += c;
            if (k + 1 >= same_from && k + 1 < n) {
                const long long* o = &C[(size_t)(k + 1) * m];
                bool eq = true;
                for (int i = 0; i < m; ++i) if (o[i] != row[i]) { eq = false; break; }
                if (eq) return tot + (F[n] - F[k + 1]);
            }
        }
        return tot;
    }
};

class PairwiseJobInterchange : public hsf::Neighborhood<Model> {
    const Model& md;
    FlowCache fc;
    int max_gap;
    std::unordered_set<long long> used;
    int gap(int L) const { return (max_gap <= 0 || max_gap > L - 1) ? L - 1 : max_gap; }
public:
    using Sol = Model::Solution;
    PairwiseJobInterchange(const Model& m_, int g) : md(m_), fc(m_), max_gap(g) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size(), g = gap(L);
        for (int i = 0; i < L; ++i)
            for (int j = i + 1; j <= std::min(L - 1, i + g); ++j) {
                Move mv{}; mv[0] = i; mv[1] = j; out.push_back(mv);
            }
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        std::swap(r[0][mv[0]], r[0][mv[1]]);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        if (!fc.ensure(s)) return md.objective(apply(s, mv)) - md.objective(s);
        const std::vector<int>& q = fc.seq;
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i == j) return 0.0;
        long long nt = fc.tail(i, j + 1, [&](int k) { return k == i ? q[j] : (k == j ? q[i] : q[k]); });
        return (double)(nt - fc.F[fc.n]);
    }
    void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) override {
        out.clear();
        if (s.empty()) return;
        int L = (int)s[0].size();
        if (L < 2) return;
        int g = gap(L);
        long long total = 0;
        for (int i = 0; i < L; ++i) total += std::min(L - 1, i + g) - i;
        if (k < 0 || k >= total || 2LL * k > total) { hsf::Neighborhood<Model>::sample(s, k, rng, out); return; }
        used.clear();
        while ((int)out.size() < k) {
            int i = rng.below(L), j = i + 1 + rng.below(g);
            if (j >= L) continue;
            if (!used.insert((long long)i * L + j).second) continue;
            Move mv{}; mv[0] = i; mv[1] = j; out.push_back(mv);
        }
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int g = (int)params.get("max_gap", 0);
    return std::make_unique<PairwiseJobInterchange>(model, g);
}
