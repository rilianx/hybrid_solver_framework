// COMPONENT: {"name": "nonadjacent_block_exchange", "slot": "neighborhood", "params": {"max_block": {"type": "int", "range": [2, 5]}, "win_frac": {"type": "float", "range": [0.01, 0.3]}, "min_win": {"type": "int", "range": [3, 40]}}}
using Solution = Model::Solution;

struct BaseEvC {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur;
    explicit BaseEvC(const Model& x) : md(x), m(x.m) { cur.resize(x.m > 0 ? x.m : 1); }
    bool prepare(const Solution& s) {
        if (s.empty() || m == 0) return false;
        const auto& v = s[0];
        if (has && v == seq) return feas;
        seq = v; has = true;
        feas = md.perm_violation(s) == 0.0 && v.size() >= 2;
        if (!feas) return false;
        int L = (int)v.size();
        F.assign((size_t)(L + 1) * m, 0); pre.assign(L + 1, 0);
        for (int k = 0; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            const long long* p = &md.pj[(size_t)v[k] * m];
            long long acc = q[0] + p[0]; r[0] = acc;
            for (int i = 1; i < m; ++i) { long long x = q[i]; acc = (x > acc ? x : acc) + p[i]; r[i] = acc; }
            pre[k + 1] = pre[k] + acc;
        }
        return true;
    }
    template <int M>
    static inline void step(long long* c, const long long* p, int mm) {
        const int m = M > 0 ? M : mm;
        long long r = c[0] + p[0]; c[0] = r;
        for (int i = 1; i < m; ++i) { long long x = c[i]; r = (x > r ? x : r) + p[i]; c[i] = r; }
    }
    // Procesa q[k0..k1-1]. Invariante: para j < lo, c[j] = F[k][j] + d (no guardado).
    template <int M>
    inline long long run(long long* c, int& lo, long long d, int k0, int k1, long long sum, bool fill) {
        const int mc = M > 0 ? M : m;
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        for (int k = k0; k < k1; ++k) {
            const long long* p = pj + (size_t)q[k] * mc;
            const long long* Fn = Fd + (size_t)(k + 1) * mc;
            const int i0 = lo;
            long long r;
            if (i0 == 0) { r = c[0] + p[0]; c[0] = r; }
            else { long long x = c[i0], y = Fn[i0 - 1] + d; r = (x > y ? x : y) + p[i0]; c[i0] = r; }
            for (int j = i0 + 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + p[j]; c[j] = r; }
            sum += c[mc - 1];
            while (lo < mc && c[lo] == Fn[lo] + d) ++lo;
            if (lo == mc) {
                sum += pre[k1] - pre[k + 1] + d * (long long)(k1 - k - 1);
                if (fill) {
                    const long long* Fe = Fd + (size_t)k1 * mc;
                    for (int j = 0; j < mc; ++j) c[j] = Fe[j] + d;
                }
                return sum;
            }
        }
        if (fill) {
            const long long* Fe = Fd + (size_t)k1 * mc;
            for (int j = 0; j < lo; ++j) c[j] = Fe[j] + d;
        }
        return sum;
    }
    template <int M>
    long long ex(int a, int k1, int b, int k2, bool est) {
        const int mm = m;
        const int mc = M > 0 ? M : mm;
        const int L = (int)seq.size();
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        long long loc[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : cur.data();
        const long long* st = Fd + (size_t)a * mc;
        for (int i = 0; i < mc; ++i) c[i] = st[i];
        long long sum = pre[a];
        for (int i = b; i < b + k2; ++i) { step<M>(c, pj + (size_t)q[i] * mc, mm); sum += c[mc - 1]; }
        const int m0 = a + k1;
        const long long* Fm = Fd + (size_t)m0 * mc;
        const long long d = c[0] - Fm[0];
        int lo = 0;
        while (lo < mc && c[lo] == Fm[lo] + d) ++lo;
        if (lo == mc) {
            sum += pre[b] - pre[m0] + d * (long long)(b - m0);
            const long long* Fe = Fd + (size_t)b * mc;
            for (int j = 0; j < mc; ++j) c[j] = Fe[j] + d;
        } else {
            sum = run<M>(c, lo, d, m0, b, sum, true);
        }
        for (int i = a; i < a + k1; ++i) { step<M>(c, pj + (size_t)q[i] * mc, mm); sum += c[mc - 1]; }
        const int k0 = b + k2;
        const long long tot = pre[L];
        lo = 0;
        {
            const long long* Fn = Fd + (size_t)k0 * mc;
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
        }
        if (lo == mc) return sum + tot - pre[k0];
        if (!est) return run<M>(c, lo, 0, k0, L, sum, false);
        const int kend = std::min(L, k0 + 5);
        sum = run<M>(c, lo, 0, k0, kend, sum, false);
        sum += tot - pre[kend];
        if (lo < mc && kend < L) {
            long long diff = c[mc - 1] - Fd[(size_t)kend * mc + mc - 1];
            sum += diff * (long long)(L - kend);
        }
        return sum;
    }
    long long eval(int a, int k1, int b, int k2, bool est) {
        switch (m) {
            case 5: return ex<5>(a, k1, b, k2, est);
            case 10: return ex<10>(a, k1, b, k2, est);
            case 15: return ex<15>(a, k1, b, k2, est);
            case 20: return ex<20>(a, k1, b, k2, est);
            default: return ex<0>(a, k1, b, k2, est);
        }
    }
};

class BlockExchange : public hsf::Neighborhood<Model> {
    const Model& md; int maxb; double frac; int minw; BaseEvC ev;
public:
    BlockExchange(const Model& x, int b, double f, int mw) : md(x), maxb(b), frac(f), minw(mw), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        int w = std::max(minw, (int)std::ceil(frac * L));
        size_t cnt = 0;
        for (int a = 0; a < L; ++a)
            for (int k1 = 1; k1 <= maxb; ++k1) {
                int bhi = std::min(a + w, L - 1);
                for (int b = a + k1 + 1; b <= bhi; ++b) {
                    int n2 = std::min(maxb, L - b);
                    if (n2 <= 0) continue;
                    if (k1 == 1) --n2;
                    cnt += (size_t)n2;
                }
            }
        size_t base = out.size();
        out.resize(base + cnt);
        Move* p = out.data() + base;
        for (int a = 0; a < L; ++a)
            for (int k1 = 1; k1 <= maxb; ++k1) {
                int bhi = std::min(a + w, L - 1);
                for (int b = a + k1 + 1; b <= bhi; ++b)
                    for (int k2 = 1; k2 <= maxb && b + k2 <= L; ++k2) {
                        if (k1 == 1 && k2 == 1) continue;
                        Move& mv = *p++;
                        mv[0] = a; mv[1] = k1; mv[2] = b; mv[3] = k2;
                    }
            }
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        auto& v = r[0];
        const auto& o = s[0];
        int a = mv[0], k1 = mv[1], b = mv[2], k2 = mv[3];
        int pos = a;
        for (int i = b; i < b + k2; ++i) v[pos++] = o[i];
        for (int i = a + k1; i < b; ++i) v[pos++] = o[i];
        for (int i = a; i < a + k1; ++i) v[pos++] = o[i];
        return r;
    }
    double delta(const Solution& s, const Move& mv) override {
        if (!ev.prepare(s)) return md.objective(apply(s, mv)) - md.objective(s);
        long long nf = ev.eval(mv[0], mv[1], mv[2], mv[3], false);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    bool has_estimate() const override { return true; }
    double estimate(const Solution& s, const Move& mv) override {
        if (!ev.prepare(s)) return md.objective(apply(s, mv)) - md.objective(s);
        long long nf = ev.eval(mv[0], mv[1], mv[2], mv[3], true);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    Move tabu_key(const Move& mv) override {
        int a = mv[0], k1 = mv[1], b = mv[2], k2 = mv[3];
        return Move{a, k2, a + k2 + (b - a - k1), k1, 0, 0, 0};
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int b = (int)params.get("max_block", 3.0); if (b < 2) b = 2;
    double f = params.get("win_frac", 0.04);
    int mw = (int)params.get("min_win", 6.0); if (mw < 3) mw = 3;
    return std::make_unique<BlockExchange>(model, b, f, mw);
}
