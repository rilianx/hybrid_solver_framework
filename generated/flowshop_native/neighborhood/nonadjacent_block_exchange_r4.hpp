// COMPONENT: {"name": "nonadjacent_block_exchange", "slot": "neighborhood", "params": {"max_block": {"type": "int", "range": [2, 5]}, "win_frac": {"type": "float", "range": [0.01, 0.3]}, "min_win": {"type": "int", "range": [3, 40]}}}
using Solution = Model::Solution;

struct BaseEvC {
    const Model& md; int m; int kb;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur, cur2, cur3, cur4;
    std::vector<long long> tab, tsum;
    std::vector<unsigned> tgen;
    std::vector<int> thave;
    unsigned gen = 1;
    int ta = -1;
    BaseEvC(const Model& x, int maxb) : md(x), m(x.m), kb(maxb) {
        size_t s = x.m > 0 ? x.m : 1;
        cur.resize(s); cur2.resize(s); cur3.resize(s); cur4.resize(s);
    }
    bool prepare(const Solution& s) {
        if (s.empty() || m == 0) return false;
        const auto& v = s[0];
        if (has && v == seq) return feas;
        seq = v; has = true; ta = -1;
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
    static inline void step2(const long long* in, long long* o, const long long* p, int mm) {
        const int m = M > 0 ? M : mm;
        long long r = in[0] + p[0]; o[0] = r;
        for (int i = 1; i < m; ++i) { long long x = in[i]; r = (x > r ? x : r) + p[i]; o[i] = r; }
    }
    template <int M>
    inline long long blk(long long* c, int i0, int i1, long long sum) const {
        const int mc = M > 0 ? M : m;
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        int i = i0;
        for (; i + 3 < i1; i += 4) {
            const long long* p1 = pj + (size_t)q[i] * mc;
            const long long* p2 = pj + (size_t)q[i + 1] * mc;
            const long long* p3 = pj + (size_t)q[i + 2] * mc;
            const long long* p4 = pj + (size_t)q[i + 3] * mc;
            long long a = c[0] + p1[0];
            long long b = a + p2[0];
            long long g = b + p3[0];
            long long h = g + p4[0];
            c[0] = h;
            for (int j = 1; j < mc; ++j) {
                long long x = c[j]; a = (x > a ? x : a) + p1[j];
                b = (a > b ? a : b) + p2[j];
                g = (b > g ? b : g) + p3[j];
                h = (g > h ? g : h) + p4[j]; c[j] = h;
            }
            sum += a + b + g + h;
        }
        const int r = i1 - i;
        if (r == 3) {
            const long long* p1 = pj + (size_t)q[i] * mc;
            const long long* p2 = pj + (size_t)q[i + 1] * mc;
            const long long* p3 = pj + (size_t)q[i + 2] * mc;
            long long a = c[0] + p1[0];
            long long b = a + p2[0];
            long long g = b + p3[0];
            c[0] = g;
            for (int j = 1; j < mc; ++j) {
                long long x = c[j]; a = (x > a ? x : a) + p1[j];
                b = (a > b ? a : b) + p2[j];
                g = (b > g ? b : g) + p3[j]; c[j] = g;
            }
            sum += a + b + g;
        } else if (r == 2) {
            const long long* p1 = pj + (size_t)q[i] * mc;
            const long long* p2 = pj + (size_t)q[i + 1] * mc;
            long long a = c[0] + p1[0];
            long long b = a + p2[0];
            c[0] = b;
            for (int j = 1; j < mc; ++j) {
                long long x = c[j]; a = (x > a ? x : a) + p1[j];
                b = (a > b ? a : b) + p2[j]; c[j] = b;
            }
            sum += a + b;
        } else if (r == 1) {
            const long long* p = pj + (size_t)q[i] * mc;
            long long rr = c[0] + p[0]; c[0] = rr;
            for (int j = 1; j < mc; ++j) { long long x = c[j]; rr = (x > rr ? x : rr) + p[j]; c[j] = rr; }
            sum += rr;
        }
        return sum;
    }
    template <int M>
    inline long long b2state(int a, int b, int k2, long long* c) {
        const int mc = M > 0 ? M : m;
        const int boff = b - a;
        if (k2 > kb || k2 < 1 || boff < 0) {
            const long long* st = F.data() + (size_t)a * mc;
            for (int i = 0; i < mc; ++i) c[i] = st[i];
            return blk<M>(c, b, b + k2, pre[a]);
        }
        if (ta != a) {
            ta = a;
            if (++gen == 0) { std::fill(tgen.begin(), tgen.end(), 0u); gen = 1; }
        }
        if ((size_t)boff >= tgen.size()) {
            size_t ns = (size_t)boff + 1;
            tgen.resize(ns, 0u); thave.resize(ns, 0);
            tab.resize(ns * (size_t)kb * mc); tsum.resize(ns * (size_t)kb);
        }
        int h = tgen[boff] == gen ? thave[boff] : 0;
        tgen[boff] = gen;
        long long* base = tab.data() + (size_t)boff * kb * mc;
        long long* tsb = tsum.data() + (size_t)boff * kb;
        if (h < k2) {
            const int* q = seq.data();
            const long long* pj = md.pj.data();
            const long long* src; long long s;
            if (h == 0) { src = F.data() + (size_t)a * mc; s = pre[a]; }
            else { src = base + (size_t)(h - 1) * mc; s = tsb[h - 1]; }
            for (int kk = h; kk < k2; ++kk) {
                long long* dst = base + (size_t)kk * mc;
                step2<M>(src, dst, pj + (size_t)q[b + kk] * mc, m);
                s += dst[mc - 1];
                tsb[kk] = s;
                src = dst;
            }
            thave[boff] = k2;
        }
        const long long* st = base + (size_t)(k2 - 1) * mc;
        for (int i = 0; i < mc; ++i) c[i] = st[i];
        return tsb[k2 - 1];
    }
    template <int M>
    inline long long conv(long long* R, int kn, int k1, long long d, long long sum, bool fill) const {
        const int mc = M > 0 ? M : m;
        sum += pre[k1] - pre[kn] + d * (long long)(k1 - kn);
        if (fill) {
            const long long* Fe = F.data() + (size_t)k1 * mc;
            for (int j = 0; j < mc; ++j) R[j] = Fe[j] + d;
        }
        return sum;
    }
    // Procesa q[k0..k1-1] de a cuatro filas. Invariante: para j < lo, la fila actual vale F[k][j] + d (no guardado).
    template <int M>
    inline long long run(long long*& c, long long*& e1, long long*& e2, long long*& e3, int& lo, long long d,
                         int k0, int k1, long long sum, bool fill) {
        const int mc = M > 0 ? M : m;
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        int k = k0;
        for (; k + 3 < k1; k += 4) {
            const long long* p1 = pj + (size_t)q[k] * mc;
            const long long* p2 = pj + (size_t)q[k + 1] * mc;
            const long long* p3 = pj + (size_t)q[k + 2] * mc;
            const long long* p4 = pj + (size_t)q[k + 3] * mc;
            const long long* F1 = Fd + (size_t)(k + 1) * mc;
            const long long* F2 = F1 + mc;
            const long long* F3 = F2 + mc;
            const long long* F4 = F3 + mc;
            long long* A = c; long long* B = e1; long long* C = e2; long long* D = e3;
            const int i0 = lo;
            long long a, b, g, h;
            if (i0 == 0) {
                a = A[0] + p1[0]; A[0] = a;
                b = a + p2[0]; B[0] = b;
                g = b + p3[0]; C[0] = g;
                h = g + p4[0]; D[0] = h;
            } else {
                { long long x = A[i0], y = F1[i0 - 1] + d; a = (x > y ? x : y) + p1[i0]; A[i0] = a; }
                { long long y = F2[i0 - 1] + d; b = (a > y ? a : y) + p2[i0]; B[i0] = b; }
                { long long y = F3[i0 - 1] + d; g = (b > y ? b : y) + p3[i0]; C[i0] = g; }
                { long long y = F4[i0 - 1] + d; h = (g > y ? g : y) + p4[i0]; D[i0] = h; }
            }
            for (int j = i0 + 1; j < mc; ++j) {
                long long x = A[j]; a = (x > a ? x : a) + p1[j]; A[j] = a;
                b = (a > b ? a : b) + p2[j]; B[j] = b;
                g = (b > g ? b : g) + p3[j]; C[j] = g;
                h = (g > h ? g : h) + p4[j]; D[j] = h;
            }
            sum += a;
            while (lo < mc && A[lo] == F1[lo] + d) ++lo;
            if (lo == mc) return conv<M>(A, k + 1, k1, d, sum, fill);
            sum += b;
            while (lo < mc && B[lo] == F2[lo] + d) ++lo;
            if (lo == mc) { c = B; e1 = A; return conv<M>(B, k + 2, k1, d, sum, fill); }
            sum += g;
            while (lo < mc && C[lo] == F3[lo] + d) ++lo;
            if (lo == mc) { c = C; e2 = A; return conv<M>(C, k + 3, k1, d, sum, fill); }
            sum += h;
            while (lo < mc && D[lo] == F4[lo] + d) ++lo;
            c = D; e1 = A; e2 = B; e3 = C;
            if (lo == mc) return conv<M>(D, k + 4, k1, d, sum, fill);
        }
        if (k + 1 < k1) {
            const long long* p1 = pj + (size_t)q[k] * mc;
            const long long* p2 = pj + (size_t)q[k + 1] * mc;
            const long long* F1 = Fd + (size_t)(k + 1) * mc;
            const long long* F2 = F1 + mc;
            long long* A = c; long long* B = e1;
            const int i0 = lo;
            long long a, b;
            if (i0 == 0) {
                a = A[0] + p1[0]; A[0] = a;
                b = a + p2[0]; B[0] = b;
            } else {
                { long long x = A[i0], y = F1[i0 - 1] + d; a = (x > y ? x : y) + p1[i0]; A[i0] = a; }
                { long long y = F2[i0 - 1] + d; b = (a > y ? a : y) + p2[i0]; B[i0] = b; }
            }
            for (int j = i0 + 1; j < mc; ++j) {
                long long x = A[j]; a = (x > a ? x : a) + p1[j]; A[j] = a;
                b = (a > b ? a : b) + p2[j]; B[j] = b;
            }
            sum += a;
            while (lo < mc && A[lo] == F1[lo] + d) ++lo;
            if (lo == mc) return conv<M>(A, k + 1, k1, d, sum, fill);
            sum += b;
            while (lo < mc && B[lo] == F2[lo] + d) ++lo;
            c = B; e1 = A;
            if (lo == mc) return conv<M>(B, k + 2, k1, d, sum, fill);
            k += 2;
        }
        if (k < k1) {
            const long long* p = pj + (size_t)q[k] * mc;
            const long long* Fn = Fd + (size_t)(k + 1) * mc;
            const int i0 = lo;
            long long r;
            if (i0 == 0) { r = c[0] + p[0]; c[0] = r; }
            else { long long x = c[i0], y = Fn[i0 - 1] + d; r = (x > y ? x : y) + p[i0]; c[i0] = r; }
            for (int j = i0 + 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + p[j]; c[j] = r; }
            sum += r;
            while (lo < mc && c[lo] == Fn[lo] + d) ++lo;
            if (lo == mc) return conv<M>(c, k + 1, k1, d, sum, fill);
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
        const long long* Fd = F.data();
        long long loc[M > 0 ? M : 1], loc2[M > 0 ? M : 1], loc3[M > 0 ? M : 1], loc4[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : cur.data();
        long long* e1 = M > 0 ? loc2 : cur2.data();
        long long* e2 = M > 0 ? loc3 : cur3.data();
        long long* e3 = M > 0 ? loc4 : cur4.data();
        long long sum = b2state<M>(a, b, k2, c);
        const int m0 = a + k1;
        const long long* Fm = Fd + (size_t)m0 * mc;
        const long long d = c[0] - Fm[0];
        int lo = 0;
        while (lo < mc && c[lo] == Fm[lo] + d) ++lo;
        if (lo == mc) {
            sum += pre[b] - pre[m0] + d * (long long)(b - m0);
            const long long* Fe = Fd + (size_t)b * mc;
            for (int j = 0; j < mc; ++j) c[j] = Fe[j] + d;
        } else if (!est || b - m0 <= 4) {
            sum = run<M>(c, e1, e2, e3, lo, d, m0, b, sum, true);
        } else {
            const int kmid = m0 + 4;
            sum = run<M>(c, e1, e2, e3, lo, d, m0, kmid, sum, true);
            const long long* Fk = Fd + (size_t)kmid * mc;
            const long long* Fb = Fd + (size_t)b * mc;
            sum += pre[b] - pre[kmid] + (c[mc - 1] - Fk[mc - 1]) * (long long)(b - kmid);
            for (int j = 0; j < mc; ++j) c[j] = Fb[j] + (c[j] - Fk[j]);
        }
        sum = blk<M>(c, a, a + k1, sum);
        const int k0 = b + k2;
        const long long tot = pre[L];
        lo = 0;
        {
            const long long* Fn = Fd + (size_t)k0 * mc;
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
        }
        if (lo == mc) return sum + tot - pre[k0];
        if (!est) return run<M>(c, e1, e2, e3, lo, 0, k0, L, sum, false);
        const int kend = std::min(L, k0 + 5);
        sum = run<M>(c, e1, e2, e3, lo, 0, k0, kend, sum, false);
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
    BlockExchange(const Model& x, int b, double f, int mw) : md(x), maxb(b), frac(f), minw(mw), ev(x, b) {}
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
