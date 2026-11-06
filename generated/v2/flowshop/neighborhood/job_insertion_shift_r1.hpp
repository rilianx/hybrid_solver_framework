// COMPONENT: {"name": "job_insertion_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [0, 500]}}}
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

class JobInsertionShift : public hsf::Neighborhood<Model> {
    const Model& md;
    FlowCache fc;
    int window;
    std::unordered_set<long long> used;
    int win(int L) const { return (window <= 0 || window > L - 1) ? L - 1 : window; }
public:
    using Sol = Model::Solution;
    JobInsertionShift(const Model& m_, int w) : md(m_), fc(m_), window(w) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size(), w = win(L);
        for (int a = 0; a < L; ++a)
            for (int b = std::max(0, a - w); b <= std::min(L - 1, a + w); ++b) {
                if (b == a || b == a - 1) continue;
                Move mv{}; mv[0] = a; mv[1] = b; out.push_back(mv);
            }
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        std::vector<int>& v = r[0];
        int a = mv[0], b = mv[1], x = v[a];
        if (a < b) std::copy(v.begin() + a + 1, v.begin() + b + 1, v.begin() + a);
        else if (a > b) std::copy_backward(v.begin() + b, v.begin() + a, v.begin() + a + 1);
        v[b] = x;
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        if (!fc.ensure(s)) return md.objective(apply(s, mv)) - md.objective(s);
        const std::vector<int>& q = fc.seq;
        int a = mv[0], b = mv[1];
        if (a == b) return 0.0;
        long long nt;
        if (a < b) nt = fc.tail(a, b + 1, [&](int k) { return k < b ? q[k + 1] : (k == b ? q[a] : q[k]); });
        else nt = fc.tail(b, a + 1, [&](int k) { return k == b ? q[a] : (k <= a ? q[k - 1] : q[k]); });
        return (double)(nt - fc.F[fc.n]);
    }
    Move tabu_key(const Move& mv) override {
        Move r{};
        if (mv[1] == mv[0] + 1) { r[0] = mv[0]; r[1] = mv[1]; }
        else { r[0] = mv[1]; r[1] = mv[0]; }
        return r;
    }
    void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) override {
        out.clear();
        if (s.empty()) return;
        int L = (int)s[0].size();
        if (L < 2) return;
        int w = win(L);
        long long total = 0;
        for (int a = 0; a < L; ++a) {
            int lo = std::max(0, a - w), hi = std::min(L - 1, a + w);
            total += hi - lo; if (a - 1 >= lo) total -= 1;
        }
        if (k < 0 || k >= total || 2LL * k > total) { hsf::Neighborhood<Model>::sample(s, k, rng, out); return; }
        used.clear();
        while ((int)out.size() < k) {
            int a = rng.below(L), d = 1 + rng.below(w);
            int b = (rng.below(2) == 0) ? a + d : a - d;
            if (b < 0 || b >= L || b == a - 1) continue;
            if (!used.insert((long long)a * L + b).second) continue;
            Move mv{}; mv[0] = a; mv[1] = b; out.push_back(mv);
        }
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 0);
    return std::make_unique<JobInsertionShift>(model, w);
}
