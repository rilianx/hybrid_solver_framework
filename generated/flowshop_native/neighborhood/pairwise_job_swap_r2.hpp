// COMPONENT: {"name": "pairwise_job_swap", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [0, 500]}}}
using Solution = Model::Solution;

struct EvalSw {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur;
    explicit EvalSw(const Model& x) : md(x), m(x.m) { cur.resize(x.m > 0 ? x.m : 1); }
    void prepare(const Solution& s) {
        const auto& v = s[0];
        if (has && v == seq) return;
        seq = v; has = true;
        feas = md.perm_violation(s) == 0.0;
        if (!feas) return;
        int L = (int)v.size();
        F.assign((size_t)(L + 1) * m, 0); pre.assign(L + 1, 0);
        for (int k = 0; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            const long long* p = &md.pj[(size_t)v[k] * m];
            r[0] = q[0] + p[0];
            for (int i = 1; i < m; ++i) { long long x = q[i], y = r[i - 1]; r[i] = (x > y ? x : y) + p[i]; }
            pre[k + 1] = pre[k] + r[m - 1];
        }
    }
    template <int M>
    static inline void step(long long* c, const long long* p, int mm) {
        const int m = M > 0 ? M : mm;
        c[0] += p[0];
        for (int i = 1; i < m; ++i) { long long x = c[i], y = c[i - 1]; c[i] = (x > y ? x : y) + p[i]; }
    }
    template <int M>
    static inline bool same(const long long* c, const long long* r, int mm) {
        const int m = M > 0 ? M : mm;
        if (c[m - 1] != r[m - 1]) return false;
        for (int i = 0; i < m - 1; ++i) if (c[i] != r[i]) return false;
        return true;
    }
    template <int M>
    long long swp(int a, int b) {
        const int mm = m;
        const int L = (int)seq.size();
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        long long loc[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : cur.data();
        const int mc = M > 0 ? M : mm;
        const long long* src = Fd + (size_t)a * mc;
        for (int i = 0; i < mc; ++i) c[i] = src[i];
        long long sum = pre[a];
        step<M>(c, pj + (size_t)q[b] * mc, mm); sum += c[mc - 1];
        for (int k = a + 1; k < b; ++k) { step<M>(c, pj + (size_t)q[k] * mc, mm); sum += c[mc - 1]; }
        step<M>(c, pj + (size_t)q[a] * mc, mm); sum += c[mc - 1];
        const long long tot = pre[L];
        if (same<M>(c, Fd + (size_t)(b + 1) * mc, mm)) return sum + tot - pre[b + 1];
        for (int k = b + 1; k < L; ++k) {
            step<M>(c, pj + (size_t)q[k] * mc, mm); sum += c[mc - 1];
            if (same<M>(c, Fd + (size_t)(k + 1) * mc, mm)) return sum + tot - pre[k + 1];
        }
        return sum;
    }
    long long swapEval(int a, int b) {
        switch (m) {
            case 5: return swp<5>(a, b);
            case 10: return swp<10>(a, b);
            case 15: return swp<15>(a, b);
            case 20: return swp<20>(a, b);
            default: return swp<0>(a, b);
        }
    }
};

class PairSwap : public hsf::Neighborhood<Model> {
    const Model& md; int window; EvalSw ev;
public:
    PairSwap(const Model& x, int w) : md(x), window(w), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        if (L > 1) out.reserve(out.size() + (size_t)L * (size_t)(L - 1) / 2);
        for (int i = 0; i < L; ++i)
            for (int j = i + 1; j < L; ++j) {
                if (window > 0 && j - i > window) break;
                out.push_back(Move{i, j, 0, 0, 0, 0, 0});
            }
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        std::swap(r[0][mv[0]], r[0][mv[1]]);
        return r;
    }
    double delta(const Solution& s, const Move& mv) override {
        if (s.empty() || md.m == 0 || s[0].size() < 2) return md.objective(apply(s, mv)) - md.objective(s);
        ev.prepare(s);
        if (!ev.feas) return md.objective(apply(s, mv)) - md.objective(s);
        int a = std::min(mv[0], mv[1]), b = std::max(mv[0], mv[1]);
        long long nf = ev.swapEval(a, b);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 0.0);
    return std::make_unique<PairSwap>(model, w);
}
