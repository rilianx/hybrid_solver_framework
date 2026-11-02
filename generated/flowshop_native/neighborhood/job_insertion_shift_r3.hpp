// COMPONENT: {"name": "job_insertion_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [0, 500]}}}
using Solution = Model::Solution;

struct EvalIns {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, S, Ssum, cur;
    int sf = -1, slen = -1;
    explicit EvalIns(const Model& x) : md(x), m(x.m) { cur.resize(x.m > 0 ? x.m : 1); }
    void prepare(const Solution& s) {
        const auto& v = s[0];
        if (has && v == seq) return;
        seq = v; has = true; sf = -1; slen = -1;
        feas = md.perm_violation(s) == 0.0;
        if (!feas) return;
        int L = (int)v.size();
        F.assign((size_t)(L + 1) * m, 0); pre.assign(L + 1, 0);
        S.resize((size_t)(L + 1) * m); Ssum.resize(L + 1);
        for (int k = 0; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            const long long* p = &md.pj[(size_t)v[k] * m];
            r[0] = q[0] + p[0];
            for (int i = 1; i < m; ++i) { long long a = q[i], b = r[i - 1]; r[i] = (a > b ? a : b) + p[i]; }
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
    static inline void step2(const long long* in, long long* o, const long long* p, int mm) {
        const int m = M > 0 ? M : mm;
        o[0] = in[0] + p[0];
        for (int i = 1; i < m; ++i) { long long x = in[i], y = o[i - 1]; o[i] = (x > y ? x : y) + p[i]; }
    }
    template <int M>
    static inline bool same(const long long* c, const long long* r, int mm) {
        const int m = M > 0 ? M : mm;
        if (c[m - 1] != r[m - 1]) return false;
        for (int i = 0; i < m - 1; ++i) if (c[i] != r[i]) return false;
        return true;
    }
    template <int M>
    void ensureS(int f, int t) {
        const int mc = M > 0 ? M : m;
        if (sf != f) {
            sf = f; slen = f;
            const long long* src = F.data() + (size_t)f * mc;
            long long* dst = S.data() + (size_t)f * mc;
            for (int i = 0; i < mc; ++i) dst[i] = src[i];
            Ssum[f] = pre[f];
        }
        if (slen < t) {
            const long long* pj = md.pj.data();
            const int* q = seq.data();
            long long* Sd = S.data();
            long long acc = Ssum[slen];
            while (slen < t) {
                int k = slen + 1;
                long long* o = Sd + (size_t)k * mc;
                step2<M>(Sd + (size_t)slen * mc, o, pj + (size_t)q[k] * mc, m);
                acc += o[mc - 1];
                Ssum[k] = acc;
                slen = k;
            }
        }
    }
    template <int M>
    long long ins(int f, int t) {
        const int mm = m;
        const int mc = M > 0 ? M : mm;
        const int L = (int)seq.size();
        const int* q = seq.data();
        const long long* pj = md.pj.data();
        const long long* Fd = F.data();
        long long loc[M > 0 ? M : 1];
        long long* c = M > 0 ? loc : cur.data();
        const long long tot = pre[L];
        long long sum;
        int k0;
        if (f < t) {
            ensureS<M>(f, t);
            const long long* st = S.data() + (size_t)t * mc;
            for (int i = 0; i < mc; ++i) c[i] = st[i];
            sum = Ssum[t];
            step<M>(c, pj + (size_t)q[f] * mc, mm);
            sum += c[mc - 1];
            if (same<M>(c, Fd + (size_t)(t + 1) * mc, mm)) return sum + tot - pre[t + 1];
            k0 = t + 1;
        } else {
            const long long* st = Fd + (size_t)t * mc;
            for (int i = 0; i < mc; ++i) c[i] = st[i];
            sum = pre[t];
            step<M>(c, pj + (size_t)q[f] * mc, mm);
            sum += c[mc - 1];
            for (int k = t; k < f; ++k) {
                step<M>(c, pj + (size_t)q[k] * mc, mm);
                sum += c[mc - 1];
            }
            if (same<M>(c, Fd + (size_t)(f + 1) * mc, mm)) return sum + tot - pre[f + 1];
            k0 = f + 1;
        }
        for (int k = k0; k < L; ++k) {
            step<M>(c, pj + (size_t)q[k] * mc, mm);
            sum += c[mc - 1];
            if (same<M>(c, Fd + (size_t)(k + 1) * mc, mm)) return sum + tot - pre[k + 1];
        }
        return sum;
    }
    long long insEval(int f, int t) {
        switch (m) {
            case 5: return ins<5>(f, t);
            case 10: return ins<10>(f, t);
            case 15: return ins<15>(f, t);
            case 20: return ins<20>(f, t);
            default: return ins<0>(f, t);
        }
    }
};

class JobInsertion : public hsf::Neighborhood<Model> {
    const Model& md; int window; EvalIns ev;
public:
    JobInsertion(const Model& x, int w) : md(x), window(w), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        out.reserve(out.size() + (size_t)L * (size_t)L);
        for (int f = 0; f < L; ++f) {
            int lo = 0, hi = L - 1;
            if (window > 0) { lo = std::max(0, f - window); hi = std::min(L - 1, f + window); }
            for (int t = lo; t <= hi; ++t) {
                if (t == f || t == f - 1) continue;  // f->f-1 equivale a (f-1)->f
                out.push_back(Move{f, t, 0, 0, 0, 0, 0});
            }
        }
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        auto& v = r[0]; int f = mv[0], t = mv[1];
        int job = v[f];
        if (f < t) std::copy(v.begin() + f + 1, v.begin() + t + 1, v.begin() + f);
        else std::copy_backward(v.begin() + t, v.begin() + f, v.begin() + f + 1);
        v[t] = job;
        return r;
    }
    double delta(const Solution& s, const Move& mv) override {
        if (s.empty() || md.m == 0 || s[0].size() < 2) return md.objective(apply(s, mv)) - md.objective(s);
        ev.prepare(s);
        if (!ev.feas) return md.objective(apply(s, mv)) - md.objective(s);
        long long nf = ev.insEval(mv[0], mv[1]);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    Move tabu_key(const Move& mv) override { return Move{mv[1], mv[0], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 0.0);
    return std::make_unique<JobInsertion>(model, w);
}
