// COMPONENT: {"name": "block_relocation_oropt_window", "slot": "neighborhood", "params": {"max_block": {"type": "int", "range": [2, 6]}, "win_frac": {"type": "float", "range": [0.01, 0.5]}, "min_win": {"type": "int", "range": [1, 50]}}}
using Solution = Model::Solution;

struct BaseEvA {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false; unsigned ver = 0;
    std::vector<long long> F, pre, c;
    explicit BaseEvA(const Model& x) : md(x), m(x.m) { c.resize(x.m > 0 ? x.m : 1); }
    bool prepare(const Solution& s) {
        if (s.empty() || m == 0) return false;
        const auto& v = s[0];
        if (has && v == seq) return feas;
        seq = v; has = true; ++ver;
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
};

class BlockRelocate : public hsf::Neighborhood<Model> {
    const Model& md; int maxb; double frac; int minw; BaseEvA ev;
    std::vector<long long> SR, SRs; int ca = -1, cl = -1, sl = -1; unsigned cver = 0;
    int win(int L) const { int w = (int)std::ceil(frac * L); return std::max(minw, w); }

    template <int M>
    static inline long long step(long long* c, const long long* p, int mm) {
        const int m = M > 0 ? M : mm;
        long long r = c[0] + p[0]; c[0] = r;
        for (int i = 1; i < m; ++i) { long long x = c[i]; r = (x > r ? x : r) + p[i]; c[i] = r; }
        return r;
    }

    template <int M>
    void ensure(int a, int len, int t) {
        const int mc = M > 0 ? M : ev.m; const int L = (int)ev.seq.size();
        if ((int)SRs.size() < L + 1) { SR.resize((size_t)(L + 1) * mc); SRs.resize(L + 1); }
        if (ca != a || cl != len || cver != ev.ver) {
            ca = a; cl = len; cver = ev.ver;
            const long long* src = &ev.F[(size_t)a * mc];
            long long* dst = &SR[(size_t)a * mc];
            for (int i = 0; i < mc; ++i) dst[i] = src[i];
            SRs[a] = ev.pre[a]; sl = a;
        }
        const long long* pj = md.pj.data();
        long long* Sd = SR.data();
        while (sl < t) {
            const long long* in = Sd + (size_t)sl * mc;
            long long* o = Sd + (size_t)(sl + 1) * mc;
            const long long* p = pj + (size_t)ev.seq[sl + len] * mc;
            long long acc = in[0] + p[0]; o[0] = acc;
            for (int i = 1; i < mc; ++i) { long long x = in[i]; acc = (x > acc ? x : acc) + p[i]; o[i] = acc; }
            SRs[sl + 1] = SRs[sl] + acc;
            ++sl;
        }
    }

    // Procesa q[k0..k1-1]; invariante: para j < lo, c[j] = F[k][j] + d.
    template <int M>
    inline long long run(long long* c, int& lo, long long d, int k0, int k1, long long sum, bool fill) {
        const int mc = M > 0 ? M : ev.m;
        const int* q = ev.seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = ev.F.data();
        const long long* pre = ev.pre.data();
        if (lo == mc) {
            sum += pre[k1] - pre[k0] + d * (long long)(k1 - k0);
            if (fill) {
                const long long* Fe = Fd + (size_t)k1 * mc;
                for (int j = 0; j < mc; ++j) c[j] = Fe[j] + d;
            }
            return sum;
        }
        for (int k = k0; k < k1; ++k) {
            const long long* p = pj + (size_t)q[k] * mc;
            const long long* Fn = Fd + (size_t)(k + 1) * mc;
            const int i0 = lo;
            long long r;
            if (i0 == 0) { r = c[0] + p[0]; c[0] = r; }
            else { long long x = c[i0], y = Fn[i0 - 1] + d; r = (x > y ? x : y) + p[i0]; c[i0] = r; }
            for (int j = i0 + 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + p[j]; c[j] = r; }
            sum += r;
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
    long long evalT(int a, int len, int t, bool est) {
        const int mm = ev.m;
        const int mc = M > 0 ? M : mm;
        const int L = (int)ev.seq.size();
        const int* q = ev.seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = ev.F.data();
        const long long* pre = ev.pre.data();
        long long loc[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : ev.c.data();
        long long sum; int lo, k0;
        if (t > a) {
            if ((ca == a && cl == len && cver == ev.ver) || t == a + 1) {
                ensure<M>(a, len, t);
                const long long* st = SR.data() + (size_t)t * mc;
                for (int i = 0; i < mc; ++i) c[i] = st[i];
                sum = SRs[t];
            } else {
                const long long* st = Fd + (size_t)a * mc;
                for (int i = 0; i < mc; ++i) c[i] = st[i];
                sum = pre[a];
                long long d = 0;
                for (int i = 0; i < len; ++i) d -= pj[(size_t)q[a + i] * mc];
                lo = 0;
                const long long* Fn = Fd + (size_t)(a + len) * mc;
                while (lo < mc && c[lo] == Fn[lo] + d) ++lo;
                sum = run<M>(c, lo, d, a + len, t + len, sum, true);
            }
            for (int i = 0; i < len; ++i) sum += step<M>(c, pj + (size_t)q[a + i] * mc, mm);
            k0 = t + len;
        } else {
            const long long* st = Fd + (size_t)t * mc;
            for (int i = 0; i < mc; ++i) c[i] = st[i];
            sum = pre[t];
            long long d = 0;
            for (int i = 0; i < len; ++i) {
                const long long* p = pj + (size_t)q[a + i] * mc;
                sum += step<M>(c, p, mm);
                d += p[0];
            }
            lo = 0;
            while (lo < mc && c[lo] == st[lo] + d) ++lo;
            sum = run<M>(c, lo, d, t, a, sum, true);
            k0 = a + len;
        }
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
    long long eval(int a, int len, int t, bool est) {
        switch (ev.m) {
            case 5: return evalT<5>(a, len, t, est);
            case 10: return evalT<10>(a, len, t, est);
            case 15: return evalT<15>(a, len, t, est);
            case 20: return evalT<20>(a, len, t, est);
            default: return evalT<0>(a, len, t, est);
        }
    }
public:
    BlockRelocate(const Model& x, int b, double f, int mw) : md(x), maxb(b), frac(f), minw(mw), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        int w = win(L);
        size_t cnt = 0;
        for (int a = 0; a < L; ++a)
            for (int len = 2; len <= maxb && a + len <= L; ++len) {
                int lo = std::max(0, a - w), hi = std::min(L - len, a + w);
                if (hi > lo) cnt += (size_t)(hi - lo);
            }
        size_t base = out.size();
        out.resize(base + cnt);
        Move* p = out.data() + base;
        for (int a = 0; a < L; ++a)
            for (int len = 2; len <= maxb && a + len <= L; ++len) {
                int lo = std::max(0, a - w), hi = std::min(L - len, a + w);
                for (int t = lo; t <= hi; ++t) {
                    if (t == a) continue;
                    Move& mv = *p++;
                    mv[0] = a; mv[1] = len; mv[2] = t;
                }
            }
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        auto& v = r[0];
        int a = mv[0], len = mv[1], t = mv[2];
        if (t > a) std::rotate(v.begin() + a, v.begin() + a + len, v.begin() + t + len);
        else if (t < a) std::rotate(v.begin() + t, v.begin() + a, v.begin() + a + len);
        return r;
    }
    double delta(const Solution& s, const Move& mv) override {
        if (!ev.prepare(s)) return md.objective(apply(s, mv)) - md.objective(s);
        long long nf = eval(mv[0], mv[1], mv[2], false);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    bool has_estimate() const override { return true; }
    double estimate(const Solution& s, const Move& mv) override {
        if (!ev.prepare(s)) return md.objective(apply(s, mv)) - md.objective(s);
        long long nf = eval(mv[0], mv[1], mv[2], true);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    Move tabu_key(const Move& mv) override { return Move{mv[2], mv[1], mv[0], 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int b = (int)params.get("max_block", 3.0); if (b < 2) b = 2;
    double f = params.get("win_frac", 0.05);
    int mw = (int)params.get("min_win", 5.0); if (mw < 1) mw = 1;
    return std::make_unique<BlockRelocate>(model, b, f, mw);
}
