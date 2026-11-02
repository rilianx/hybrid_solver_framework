// COMPONENT: {"name": "window_priority_resort", "slot": "neighborhood", "params": {"len_frac": {"type": "float", "range": [0.02, 0.5]}, "min_len": {"type": "int", "range": [3, 10]}, "growth": {"type": "float", "range": [1.2, 2.5]}, "n_rules": {"type": "int", "range": [1, 3]}}}
using Solution = Model::Solution;

struct EvW {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur, cur2, cur3, cur4;
    explicit EvW(const Model& x) : md(x), m(x.m) {
        size_t mm = x.m > 0 ? x.m : 1;
        cur.resize(mm); cur2.resize(mm); cur3.resize(mm); cur4.resize(mm);
    }
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
    // la secuencia cambió solo en [st, st+l) (misma multiconjunto); actualiza F y pre
    void update(int st, int l, const std::vector<int>& nv) {
        for (int a = st; a < st + l; ++a) seq[a] = nv[a];
        const int L = (int)seq.size();
        for (int k = st; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            const long long* p = &md.pj[(size_t)seq[k] * m];
            long long acc = q[0] + p[0];
            bool same = r[0] == acc; r[0] = acc;
            for (int i = 1; i < m; ++i) {
                long long x = q[i]; acc = (x > acc ? x : acc) + p[i];
                same &= (r[i] == acc); r[i] = acc;
            }
            long long np = pre[k] + acc;
            if (same && k >= st + l) {
                long long diff = np - pre[k + 1];
                if (diff != 0) for (int t = k + 1; t <= L; ++t) pre[t] += diff;
                return;
            }
            pre[k + 1] = np;
        }
    }
    // Filas k0..k1-1. Invariante: para j < lo (lo >= 1), la fila actual vale F[fila][j].
    template <int M>
    inline long long run(long long*& c, long long*& e1, long long*& e2, long long*& e3, int& lo, int k0, int k1, long long sum) {
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
            { long long x = A[i0], y = F1[i0 - 1]; a = (x > y ? x : y) + p1[i0]; A[i0] = a; }
            { long long y = F2[i0 - 1]; b = (a > y ? a : y) + p2[i0]; B[i0] = b; }
            { long long y = F3[i0 - 1]; g = (b > y ? b : y) + p3[i0]; C[i0] = g; }
            { long long y = F4[i0 - 1]; h = (g > y ? g : y) + p4[i0]; D[i0] = h; }
            for (int j = i0 + 1; j < mc; ++j) {
                long long x = A[j]; a = (x > a ? x : a) + p1[j]; A[j] = a;
                b = (a > b ? a : b) + p2[j]; B[j] = b;
                g = (b > g ? b : g) + p3[j]; C[j] = g;
                h = (g > h ? g : h) + p4[j]; D[j] = h;
            }
            sum += a;
            while (lo < mc && A[lo] == F1[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 1];
            sum += b;
            while (lo < mc && B[lo] == F2[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 2];
            sum += g;
            while (lo < mc && C[lo] == F3[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 3];
            sum += h;
            while (lo < mc && D[lo] == F4[lo]) ++lo;
            c = D; e1 = A; e2 = B; e3 = C;
            if (lo == mc) return sum + pre[k1] - pre[k + 4];
        }
        for (; k + 1 < k1; k += 2) {
            const long long* p1 = pj + (size_t)q[k] * mc;
            const long long* p2 = pj + (size_t)q[k + 1] * mc;
            const long long* F1 = Fd + (size_t)(k + 1) * mc;
            const long long* F2 = F1 + mc;
            long long* A = c; long long* B = e1;
            const int i0 = lo;
            long long a, b;
            { long long x = A[i0], y = F1[i0 - 1]; a = (x > y ? x : y) + p1[i0]; A[i0] = a; }
            { long long y = F2[i0 - 1]; b = (a > y ? a : y) + p2[i0]; B[i0] = b; }
            for (int j = i0 + 1; j < mc; ++j) {
                long long x = A[j]; a = (x > a ? x : a) + p1[j]; A[j] = a;
                b = (a > b ? a : b) + p2[j]; B[j] = b;
            }
            sum += a;
            while (lo < mc && A[lo] == F1[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 1];
            sum += b;
            while (lo < mc && B[lo] == F2[lo]) ++lo;
            c = B; e1 = A;
            if (lo == mc) return sum + pre[k1] - pre[k + 2];
        }
        if (k < k1) {
            const long long* p = pj + (size_t)q[k] * mc;
            const long long* Fn = Fd + (size_t)(k + 1) * mc;
            const int i0 = lo;
            { long long x = c[i0], y = Fn[i0 - 1]; c[i0] = (x > y ? x : y) + p[i0]; }
            for (int j = i0 + 1; j < mc; ++j) { long long x = c[j], y = c[j - 1]; c[j] = (x > y ? x : y) + p[j]; }
            sum += c[mc - 1];
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 1];
        }
        return sum;
    }
    template <int M>
    long long win(int i, int l, const int* buf, bool est) {
        const int mc = M > 0 ? M : m;
        const int L = (int)seq.size();
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        int p = 0;
        while (p < l && buf[p] == q[i + p]) ++p;
        if (p == l) return pre[L];
        long long loc[4][M > 0 ? M : 1];
        long long* c = M > 0 ? loc[0] : cur.data();
        long long* e1 = M > 0 ? loc[1] : cur2.data();
        long long* e2 = M > 0 ? loc[2] : cur3.data();
        long long* e3 = M > 0 ? loc[3] : cur4.data();
        const long long* st = Fd + (size_t)(i + p) * mc;
        for (int j = 0; j < mc; ++j) c[j] = st[j];
        long long sum = pre[i + p];
        int t = p;
        for (; t + 3 < l; t += 4) {
            const long long* p1 = pj + (size_t)buf[t] * mc;
            const long long* p2 = pj + (size_t)buf[t + 1] * mc;
            const long long* p3 = pj + (size_t)buf[t + 2] * mc;
            const long long* p4 = pj + (size_t)buf[t + 3] * mc;
            long long a = c[0] + p1[0];
            long long b = a + p2[0];
            long long g = b + p3[0];
            long long h = g + p4[0];
            c[0] = h;
            for (int j = 1; j < mc; ++j) {
                long long x = c[j];
                a = (x > a ? x : a) + p1[j];
                b = (a > b ? a : b) + p2[j];
                g = (b > g ? b : g) + p3[j];
                h = (g > h ? g : h) + p4[j];
                c[j] = h;
            }
            sum += a + b + g + h;
        }
        for (; t + 1 < l; t += 2) {
            const long long* p1 = pj + (size_t)buf[t] * mc;
            const long long* p2 = pj + (size_t)buf[t + 1] * mc;
            long long a = c[0] + p1[0];
            long long b = a + p2[0];
            c[0] = b;
            for (int j = 1; j < mc; ++j) {
                long long x = c[j];
                a = (x > a ? x : a) + p1[j];
                b = (a > b ? a : b) + p2[j];
                c[j] = b;
            }
            sum += a + b;
        }
        if (t < l) {
            const long long* pp = pj + (size_t)buf[t] * mc;
            long long r = c[0] + pp[0]; c[0] = r;
            for (int j = 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + pp[j]; c[j] = r; }
            sum += r;
        }
        const int k0 = i + l;
        const long long* Fn = Fd + (size_t)k0 * mc;
        int lo = 0;
        while (lo < mc && c[lo] == Fn[lo]) ++lo;
        if (lo == mc) return sum + pre[L] - pre[k0];
        if (lo == 0) {  // no debería ocurrir (máquina 0 coincide), por seguridad
            long long r;
            if (k0 >= L) return sum;
            const long long* pp = pj + (size_t)q[k0] * mc;
            r = c[0] + pp[0]; c[0] = r;
            for (int j = 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + pp[j]; c[j] = r; }
            sum += r;
            const long long* Fm = Fd + (size_t)(k0 + 1) * mc;
            while (lo < mc && c[lo] == Fm[lo]) ++lo;
            if (lo == mc) return sum + pre[L] - pre[k0 + 1];
            if (lo == 0) {
                for (int k = k0 + 1; k < L; ++k) {
                    const long long* p2 = pj + (size_t)q[k] * mc;
                    r = c[0] + p2[0]; c[0] = r;
                    for (int j = 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + p2[j]; c[j] = r; }
                    sum += r;
                }
                return sum;
            }
            if (!est) return run<M>(c, e1, e2, e3, lo, k0 + 1, L, sum);
            const int kend = std::min(L, k0 + 6);
            sum = run<M>(c, e1, e2, e3, lo, k0 + 1, kend, sum);
            sum += pre[L] - pre[kend];
            if (lo < mc && kend < L) sum += (c[mc - 1] - Fd[(size_t)kend * mc + mc - 1]) * (long long)(L - kend);
            return sum;
        }
        if (!est) return run<M>(c, e1, e2, e3, lo, k0, L, sum);
        const int kend = std::min(L, k0 + 5);
        sum = run<M>(c, e1, e2, e3, lo, k0, kend, sum);
        sum += pre[L] - pre[kend];
        if (lo < mc && kend < L) sum += (c[mc - 1] - Fd[(size_t)kend * mc + mc - 1]) * (long long)(L - kend);
        return sum;
    }
    long long winEval(int i, int l, const int* buf, bool est) {
        switch (m) {
            case 5: return win<5>(i, l, buf, est);
            case 10: return win<10>(i, l, buf, est);
            case 15: return win<15>(i, l, buf, est);
            case 20: return win<20>(i, l, buf, est);
            default: return win<0>(i, l, buf, est);
        }
    }
};

class WindowResort : public hsf::Neighborhood<Model> {
    const Model& md; double frac; int minl; double growth; int nr; EvW ev;
    std::vector<long long> key[3];
    std::vector<int> rank[3], inv[3];
    std::vector<int> run, lens, wbuf, wtmp;
    std::vector<unsigned long long> bits;
    // ordena por rango (rangos distintos, válidos) sin comparaciones; deja bits en cero
    inline void sortWin(const int* R, const int* I, const int* src, int l, int* out) {
        unsigned long long* W = bits.data();
        int wlo = std::numeric_limits<int>::max(), whi = -1;
        for (int a = 0; a < l; ++a) {
            int x = R[src[a]], w = x >> 6;
            W[w] |= 1ull << (x & 63);
            wlo = w < wlo ? w : wlo; whi = w > whi ? w : whi;
        }
        int pos = 0;
        for (int w = wlo; w <= whi; ++w) {
            unsigned long long v = W[w];
            if (!v) continue;
            W[w] = 0;
            const int base = w << 6;
            while (v) { out[pos++] = I[base + __builtin_ctzll(v)]; v &= v - 1; }
        }
    }
    inline long long kof(int r, int j) const {
        return (j < 0 || j >= md.n) ? std::numeric_limits<long long>::max() : key[r][j];
    }
    void sortRange(int r, std::vector<int>::iterator b, std::vector<int>::iterator e) const {
        std::stable_sort(b, e, [&](int x, int y) { return kof(r, x) < kof(r, y); });
    }
    double eval(const Solution& s, const Move& mv, bool est) {
        if (!ev.prepare(s)) return md.objective(apply(s, mv)) - md.objective(s);
        int i = mv[0], l = mv[1], r = mv[2];
        const int* q = ev.seq.data();
        const int* R = rank[r].data();
        const int* I = inv[r].data();
        int* b = wbuf.data();
        sortWin(R, I, q + i, l, b);
        long long nf = ev.winEval(i, l, b, est);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
public:
    WindowResort(const Model& x, double f, int ml, double g, int k) : md(x), frac(f), minl(ml), growth(g), nr(k), ev(x) {
        int n = x.n, m = x.m;
        for (int r = 0; r < 3; ++r) key[r].assign(n, 0);
        for (int j = 0; j < n; ++j) {
            long long tot = 0, wf = 0;
            for (int i = 0; i < m; ++i) {
                long long p = x.pj[(size_t)j * m + i];
                tot += p; wf += (long long)(m - i) * p;
            }
            long long p0 = m > 0 ? x.pj[(size_t)j * m] : 0;
            key[0][j] = tot * (n + 1) + j;
            key[1][j] = wf * (n + 1) + j;
            key[2][j] = (p0 * (tot + 1) + tot) * (long long)(n + 1) + j;
        }
        for (int r = 0; r < 3; ++r) {
            inv[r].resize(n); rank[r].assign(n, 0);
            std::iota(inv[r].begin(), inv[r].end(), 0);
            const auto& K = key[r];
            std::stable_sort(inv[r].begin(), inv[r].end(), [&](int a, int b) { return K[a] < K[b]; });
            for (int t = 0; t < n; ++t) rank[r][inv[r][t]] = t;
        }
        wbuf.assign(n > 0 ? n : 1, 0);
        wtmp.assign(n > 0 ? n : 1, 0);
        bits.assign((size_t)((n > 0 ? n : 1) + 63) / 64 + 1, 0ull);
    }
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        const auto& q = s[0];
        int L = (int)q.size();
        if (L < 2) return;
        int maxl = std::max(std::min(minl, L), std::min(L, (int)std::ceil(frac * L)));
        lens.clear();
        for (int l = std::min(minl, L); l <= maxl;) {
            lens.push_back(l);
            int nl = (int)std::ceil(l * growth);
            l = std::max(l + 1, nl);
        }
        run.resize((size_t)nr * L);
        for (int r = 0; r < nr; ++r) {
            int* R = &run[(size_t)r * L];
            R[L - 1] = 1;
            long long kn = kof(r, q[L - 1]);
            for (int i = L - 2; i >= 0; --i) {
                long long kc = kof(r, q[i]);
                R[i] = kc < kn ? R[i + 1] + 1 : 1;
                kn = kc;
            }
        }
        const size_t base = out.size();
        const size_t bound = (size_t)L * lens.size() * (size_t)nr;
        out.resize(base + bound);
        Move* p = out.data() + base;
        const int* RN = run.data();
        const int nl = (int)lens.size();
        const int* LS = lens.data();
        for (int i = 0; i < L; ++i)
            for (int t = 0; t < nl; ++t) {
                const int l = LS[t];
                if (i + l > L) break;
                for (int r = 0; r < nr; ++r)
                    if (RN[(size_t)r * L + i] < l) {
                        Move& mv = *p++;
                        mv[0] = i; mv[1] = l; mv[2] = r; mv[3] = 0; mv[4] = 0; mv[5] = 0; mv[6] = 0;
                    }
            }
        out.resize((size_t)(p - out.data()));
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        auto& v = r[0];
        const int st = mv[0], l = mv[1], rr = mv[2];
        const int n = md.n;
        const int* R = rank[rr].data();
        const int* I = inv[rr].data();
        unsigned long long* W = bits.data();
        int wlo = std::numeric_limits<int>::max(), whi = -1;
        bool ok = true;
        for (int a = 0; a < l; ++a) {
            int j = v[st + a];
            if (j < 0 || j >= n) { ok = false; break; }
            int x = R[j], w = x >> 6;
            unsigned long long bt = 1ull << (x & 63);
            if (W[w] & bt) { ok = false; break; }
            W[w] |= bt;
            wlo = w < wlo ? w : wlo; whi = w > whi ? w : whi;
        }
        if (!ok) {
            for (int w = wlo; w <= whi; ++w) W[w] = 0;
            sortRange(rr, v.begin() + st, v.begin() + st + l);
            return r;
        }
        int pos = st;
        for (int w = wlo; w <= whi; ++w) {
            unsigned long long x = W[w];
            if (!x) continue;
            W[w] = 0;
            const int base = w << 6;
            while (x) { v[pos++] = I[base + __builtin_ctzll(x)]; x &= x - 1; }
        }
        if (ev.has && ev.feas && md.m > 0 && !s.empty() && s[0].size() == ev.seq.size() && s[0] == ev.seq)
            ev.update(st, l, v);
        return r;
    }
    double delta(const Solution& s, const Move& mv) override { return eval(s, mv, false); }
    bool has_estimate() const override { return true; }
    double estimate(const Solution& s, const Move& mv) override { return eval(s, mv, true); }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double f = params.get("len_frac", 0.1);
    int ml = (int)params.get("min_len", 3.0); if (ml < 2) ml = 2;
    double g = params.get("growth", 1.5); if (g < 1.05) g = 1.05;
    int k = (int)params.get("n_rules", 3.0); k = std::max(1, std::min(3, k));
    return std::make_unique<WindowResort>(model, f, ml, g, k);
}
