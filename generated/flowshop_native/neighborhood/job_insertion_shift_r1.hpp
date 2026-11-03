// COMPONENT: {"name": "job_insertion_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [0, 500]}}}
using Solution = Model::Solution;

struct EvalIns {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur;
    explicit EvalIns(const Model& x) : md(x), m(x.m) {}
    void prepare(const Solution& s) {
        const auto& v = s[0];
        if (has && v == seq) return;
        seq = v; has = true;
        feas = md.perm_violation(s) == 0.0;
        int L = (int)v.size();
        F.assign((size_t)(L + 1) * m, 0); pre.assign(L + 1, 0);
        for (int k = 0; k < L; ++k) {
            long long* r = &F[(size_t)(k + 1) * m]; const long long* q = &F[(size_t)k * m];
            int j = v[k];
            if (j < 0 || j >= md.n) { std::copy(q, q + m, r); pre[k + 1] = pre[k]; continue; }
            const long long* p = &md.pj[(size_t)j * m];
            r[0] = q[0] + p[0];
            for (int i = 1; i < m; ++i) r[i] = std::max(q[i], r[i - 1]) + p[i];
            pre[k + 1] = pre[k] + r[m - 1];
        }
    }
    template <class G> long long suffix(int a, int hi, G g) {
        int L = (int)seq.size();
        cur.assign(F.begin() + (size_t)a * m, F.begin() + (size_t)(a + 1) * m);
        long long sum = pre[a];
        for (int k = a; k < L; ++k) {
            int j = g(k);
            if (j >= 0 && j < md.n) {
                const long long* p = &md.pj[(size_t)j * m];
                cur[0] += p[0];
                for (int i = 1; i < m; ++i) cur[i] = std::max(cur[i], cur[i - 1]) + p[i];
                sum += cur[m - 1];
            }
            if (k >= hi && std::equal(cur.begin(), cur.end(), F.begin() + (size_t)(k + 1) * m))
                return sum + pre[L] - pre[k + 1];
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
        int f = mv[0], t = mv[1];
        const auto& q = ev.seq;
        long long nf;
        if (f < t) nf = ev.suffix(f, t, [&](int k) { return k < t ? (k >= f ? q[k + 1] : q[k]) : (k == t ? q[f] : q[k]); });
        else nf = ev.suffix(t, f, [&](int k) { return k == t ? q[f] : (k > t && k <= f ? q[k - 1] : q[k]); });
        return (double)(nf - ev.pre[q.size()]);
    }
    Move tabu_key(const Move& mv) override { return Move{mv[1], mv[0], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 0.0);
    return std::make_unique<JobInsertion>(model, w);
}
