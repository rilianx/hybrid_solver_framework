// COMPONENT: {"name": "job_insertion_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [0, 500]}}}
using Solution = Model::Solution;

struct EvalIns {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, S, Ssum, cur;
    int sf = -1, slen = -1;
    explicit EvalIns(const Model& x) : md(x), m(x.m) {}
    static inline void step(const long long* in, long long* out, const long long* p, int m) {
        out[0] = in[0] + p[0];
        for (int i = 1; i < m; ++i) { long long a = in[i], b = out[i - 1]; out[i] = (a > b ? a : b) + p[i]; }
    }
    void prepare(const Solution& s) {
        const auto& v = s[0];
        if (has && v == seq) return;
        seq = v; has = true; sf = -1; slen = -1;
        feas = md.perm_violation(s) == 0.0;
        if (!feas) return;
        int L = (int)v.size();
        F.assign((size_t)(L + 1) * m, 0); pre.assign(L + 1, 0);
        S.resize((size_t)(L + 1) * m); Ssum.resize(L + 1); cur.resize(m);
        for (int k = 0; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            step(q, r, &md.pj[(size_t)v[k] * m], m);
            pre[k + 1] = pre[k] + r[m - 1];
        }
    }
    inline bool same(const long long* c, int k1) const {
        const long long* r = &F[(size_t)k1 * m];
        if (c[m - 1] != r[m - 1]) return false;
        for (int i = 0; i < m - 1; ++i) if (c[i] != r[i]) return false;
        return true;
    }
    void ensureS(int f, int t) {
        if (sf != f) {
            sf = f; slen = f;
            std::copy(F.begin() + (size_t)f * m, F.begin() + (size_t)(f + 1) * m, S.begin() + (size_t)f * m);
            Ssum[f] = pre[f];
        }
        while (slen < t) {
            int k = slen + 1;
            long long* o = &S[(size_t)k * m];
            step(&S[(size_t)slen * m], o, &md.pj[(size_t)seq[k] * m], m);
            Ssum[k] = Ssum[slen] + o[m - 1];
            slen = k;
        }
    }
    long long ins(int f, int t) {
        int L = (int)seq.size();
        const int* q = seq.data();
        long long* c = cur.data();
        const long long* pj = md.pj.data();
        long long sum;
        int k0;
        if (f < t) {
            ensureS(f, t);
            const long long* st = &S[(size_t)t * m];
            sum = Ssum[t];
            step(st, c, pj + (size_t)q[f] * m, m);
            sum += c[m - 1];
            if (same(c, t + 1)) return sum + pre[L] - pre[t + 1];
            k0 = t + 1;
        } else {
            sum = pre[t];
            step(&F[(size_t)t * m], c, pj + (size_t)q[f] * m, m);
            sum += c[m - 1];
            for (int k = t; k < f; ++k) {
                step(c, c, pj + (size_t)q[k] * m, m);
                sum += c[m - 1];
            }
            if (same(c, f + 1)) return sum + pre[L] - pre[f + 1];
            k0 = f + 1;
        }
        for (int k = k0; k < L; ++k) {
            step(c, c, pj + (size_t)q[k] * m, m);
            sum += c[m - 1];
            if (same(c, k + 1)) return sum + pre[L] - pre[k + 1];
        }
        return sum;
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
        for (int f = 0; f < L; ++f)
            for (int t = 0; t < L; ++t) {
                if (t == f || t == f - 1) continue;  // f->f-1 equivale a (f-1)->f
                if (window > 0 && std::abs(t - f) > window) continue;
                out.push_back(Move{f, t, 0, 0, 0, 0, 0});
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
        long long nf = ev.ins(mv[0], mv[1]);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
    Move tabu_key(const Move& mv) override { return Move{mv[1], mv[0], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 0.0);
    return std::make_unique<JobInsertion>(model, w);
}
