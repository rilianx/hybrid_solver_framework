// COMPONENT: {"name": "block_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
using Solution = Model::Solution;

struct EvalRv {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    int dirty = -1;
    std::vector<long long> F, pre, cur, cur2;
    explicit EvalRv(const Model& x) : md(x), m(x.m) { cur.resize(x.m > 0 ? x.m : 1); cur2.resize(x.m > 0 ? x.m : 1); }
    void rebuild(int from) {
        const int L = (int)seq.size();
        const int* v = seq.data();
        for (int k = from; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            const long long* p = &md.pj[(size_t)v[k] * m];
            long long acc = q[0] + p[0]; r[0] = acc;
            for (int i = 1; i < m; ++i) { long long x = q[i]; acc = (x > acc ? x : acc) + p[i]; r[i] = acc; }
            pre[k + 1] = pre[k] + acc;
        }
    }
    void prepare(const Solution& s) {
        const auto& v = s[0];
        if (has && v == seq) {
            if (dirty >= 0) { if (feas) rebuild(dirty); dirty = -1; }
            return;
        }
        seq = v; has = true; dirty = -1;
        feas = md.perm_violation(s) == 0.0;
        if (!feas) return;
        int L = (int)v.size();
        F.assign((size_t)(L + 1) * m, 0); pre.assign(L + 1, 0);
        rebuild(0);
    }
    void onApply(const std::vector<int>& old, int a, int b) {
        if (!has || old.size() != seq.size() || old != seq) return;
        std::reverse(seq.begin() + a, seq.begin() + b + 1);
        if (dirty < 0 || a < dirty) dirty = a;
    }
    // procesa q[b], q[b-1], ..., q[a] sobre c; devuelve la suma de las terminaciones en la última máquina
    template <int M>
    inline long long block(long long* c, int a, int b) {
        const int mc = M > 0 ? M : m;
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        long long sum = 0;
        int k = b;
        for (; k - 3 >= a; k -= 4) {
            const long long* p1 = pj + (size_t)q[k] * mc;
            const long long* p2 = pj + (size_t)q[k - 1] * mc;
            const long long* p3 = pj + (size_t)q[k - 2] * mc;
            const long long* p4 = pj + (size_t)q[k - 3] * mc;
            long long r1 = c[0] + p1[0];
            long long r2 = r1 + p2[0];
            long long r3 = r2 + p3[0];
            long long r4 = r3 + p4[0];
            c[0] = r4;
            for (int i = 1; i < mc; ++i) {
                long long x = c[i];
                r1 = (x > r1 ? x : r1) + p1[i];
                r2 = (r1 > r2 ? r1 : r2) + p2[i];
                r3 = (r2 > r3 ? r2 : r3) + p3[i];
                r4 = (r3 > r4 ? r3 : r4) + p4[i];
                c[i] = r4;
            }
            sum += r1 + r2 + r3 + r4;
        }
        for (; k >= a; --k) {
            const long long* p = pj + (size_t)q[k] * mc;
            long long r = c[0] + p[0]; c[0] = r;
            for (int i = 1; i < mc; ++i) { long long x = c[i]; r = (x > r ? x : r) + p[i]; c[i] = r; }
            sum += r;
        }
        return sum;
    }
    // Procesa k0..k1-1 de a dos filas. Invariante: lo >= 1 y para j < lo, la fila actual vale F[fila][j].
    template <int M>
    inline long long run(long long*& c, long long*& e, int& lo, int k0, int k1, long long sum) {
        const int mc = M > 0 ? M : m;
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        int k = k0;
        for (; k + 1 < k1; k += 2) {
            const long long* p1 = pj + (size_t)q[k] * mc;
            const long long* p2 = pj + (size_t)q[k + 1] * mc;
            const long long* F1 = Fd + (size_t)(k + 1) * mc;
            const long long* F2 = F1 + mc;
            long long* A = c; long long* B = e;
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
            c = B; e = A;
            if (lo == mc) return sum + pre[k1] - pre[k + 2];
        }
        if (k < k1) {
            const long long* p = pj + (size_t)q[k] * mc;
            const long long* Fn = Fd + (size_t)(k + 1) * mc;
            const int i0 = lo;
            long long r;
            { long long x = c[i0], y = Fn[i0 - 1]; r = (x > y ? x : y) + p[i0]; c[i0] = r; }
            for (int j = i0 + 1; j < mc; ++j) { long long x = c[j]; r = (x > r ? x : r) + p[j]; c[j] = r; }
            sum += r;
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
            if (lo == mc) return sum + pre[k1] - pre[k + 1];
        }
        return sum;
    }
    template <int M>
    long long rev(int a, int b, bool est) {
        const int mc = M > 0 ? M : m;
        const int L = (int)seq.size();
        const long long* Fd = F.data();
        long long loc[M > 0 ? M : 1], loc2[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : cur.data();
        long long* e = M > 0 ? loc2 : cur2.data();
        const long long* src = Fd + (size_t)a * mc;
        for (int i = 0; i < mc; ++i) c[i] = src[i];
        long long sum = pre[a] + block<M>(c, a, b);
        const long long tot = pre[L];
        int lo = 0;
        {
            const long long* Fn = Fd + (size_t)(b + 1) * mc;
            while (lo < mc && c[lo] == Fn[lo]) ++lo;
        }
        if (lo == mc) return sum + tot - pre[b + 1];
        if (lo == 0) lo = 0;  // nunca ocurre: la máquina 0 siempre coincide
        if (!est) return run<M>(c, e, lo, b + 1, L, sum);
        const int kend = std::min(L, b + 6);
        sum = run<M>(c, e, lo, b + 1, kend, sum);
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
        if (L < 2) return;
        size_t cnt = 0;
        for (int i = 0; i < L; ++i) { int hi = std::min(L - 1, i + max_len - 1); if (hi > i) cnt += hi - i; }
        size_t base = out.size();
        out.resize(base + cnt);
        Move* p = out.data() + base;
        for (int i = 0; i < L; ++i) {
            int hi = std::min(L - 1, i + max_len - 1);
            for (int j = i + 1; j <= hi; ++j) {
                Move& mv = *p++;
                mv[0] = i; mv[1] = j;
            }
        }
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        int a = std::min(mv[0], mv[1]), b = std::max(mv[0], mv[1]);
        std::reverse(r[0].begin() + a, r[0].begin() + b + 1);
        ev.onApply(s[0], a, b);
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
