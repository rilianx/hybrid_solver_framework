// COMPONENT: {"name": "block_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
using Solution = Model::Solution;

struct EvalRv {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur;
    explicit EvalRv(const Model& x) : md(x), m(x.m) { cur.resize(x.m > 0 ? x.m : 1); }
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
    // Procesa k0..k1-1. Invariante: para j < lo, c[j] == F[fila][j] (no se guarda). Solo recalcula lo..m-1.
    template <int M>
    inline long long run(long long* c, int& lo, int k0, int k1, long long sum) {
        const int mc = M > 0 ? M : m;
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        for (int k = k0; k < k1; ++k) {
            const long long* p = pj + (size_t)q[k] * mc;
            const long long* Fn = Fd + (size_t)(k + 1) * mc;
            const int i0 = lo;
            if (i0 == 0) c[0] += p[0];
            else { long long x = c[i0], y = Fn[i0 - 1]; c[i0] = (x > y ? x : y) + p[i0]; }
            for (int j = i0 + 1; j < mc; ++j) { long long x = c[j], y = c[j - 1]; c[j] = (x > y ? x : y) + p[j]; }
            sum += c[mc - 1];
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 1];
        }
        return sum;
    }
    template <int M>
    long long rev(int a, int b, bool est) {
        const int mm = m;
        const int mc = M > 0 ? M : mm;
        const int L = (int)seq.size();
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        long long loc[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : cur.data();
        const long long* src = Fd + (size_t)a * mc;
        for (int i = 0; i < mc; ++i) c[i] = src[i];
        long long sum = pre[a];
        for (int k = b; k >= a; --k) { step<M>(c, pj + (size_t)q[k] * mc, mm); sum += c[mc - 1]; }
        const long long tot = pre[L];
        int lo = 0;
        {
            const long long* Fn = Fd + (size_t)(b + 1) * mc;
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
        }
        if (lo == mc) return sum + tot - pre[b + 1];
        if (!est) return run<M>(c, lo, b + 1, L, sum);
        const int kend = std::min(L, b + 6);
        sum = run<M>(c, lo, b + 1, kend, sum);
        sum += tot - pre[kend];
        if (lo < mc && kend < L) {
            long long diff = c[mc - 1] - Fd[(size_t)kend * mc + mc - 1];
            sum += diff * (long long)(L - kend);
        }
        return sum;
    }
    long long revEval(int a, int b, bool est = false) {
        switch (m) {
            case 5: return rev<5>(a, b, est);
            case 10: return rev<10>(a, b, est);
            case 15: return rev<15>(a, b, est);
            case 20: return rev<20>(a, b, est);
            default: return rev<0>(a, b, est);
        }
    }
};

class BlockReversal : public hsf::Neighborhood<Model> {
    const Model& md; int max_len; EvalRv ev;
public:
    BlockReversal(const Model& x, int ml) : md(x), max_len(ml), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        if (L > 1) {
            size_t cnt = 0;
            for (int i = 0; i < L; ++i) { int hi = std::min(L - 1, i + max_len - 1); if (hi > i) cnt += hi - i; }
            out.reserve(out.size() + cnt);
        }
        for (int i = 0; i < L; ++i)
            for (int j = i + 1; j < L && j - i + 1 <= max_len; ++j)
                out.push_back(Move{i, j, 0, 0, 0, 0, 0});
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        int a = std::min(mv[0], mv[1]), b = std::max(mv[0], mv[1]);
        std::reverse(r[0].begin() + a, r[0].begin() + b + 1);
        return r;
    }
    double delta(const Solution& s, const Move& mv) override {
        if (s.empty() || md.m == 0 || s[0].size() < 2) return md.objective(apply(s, mv)) - md.objective(s);
        ev.prepare(s);
        if (!ev.feas) return md.objective(apply(s, mv)) - md.objective(s);
        int a = std::min(mv[0], mv[1]), b = std::max(mv[0], mv[1]);
        long long nf = ev.revEval(a, b);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    bool has_estimate() const override { return true; }
    double estimate(const Solution& s, const Move& mv) override {
        if (s.empty() || md.m == 0 || s[0].size() < 2) return md.objective(apply(s, mv)) - md.objective(s);
        ev.prepare(s);
        if (!ev.feas) return md.objective(apply(s, mv)) - md.objective(s);
        int a = std::min(mv[0], mv[1]), b = std::max(mv[0], mv[1]);
        long long nf = ev.revEval(a, b, true);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ml = (int)params.get("max_len", 500.0);
    if (ml < 2) ml = 2;
    return std::make_unique<BlockReversal>(model, ml);
}
