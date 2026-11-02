// COMPONENT: {"name": "block_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
using Solution = Model::Solution;

struct EvalRv {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, cur;
    explicit EvalRv(const Model& x) : md(x), m(x.m) {}
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

class BlockReversal : public hsf::Neighborhood<Model> {
    const Model& md; int max_len; EvalRv ev;
public:
    BlockReversal(const Model& x, int ml) : md(x), max_len(ml), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
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
        const auto& q = ev.seq;
        long long nf = ev.suffix(a, b, [&](int k) { return (k >= a && k <= b) ? q[a + b - k] : q[k]; });
        return (double)(nf - ev.pre[q.size()]);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ml = (int)params.get("max_len", 500.0);
    if (ml < 2) ml = 2;
    return std::make_unique<BlockReversal>(model, ml);
}
