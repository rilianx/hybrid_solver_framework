// COMPONENT: {"name": "nonadjacent_block_exchange", "slot": "neighborhood", "params": {"max_block": {"type": "int", "range": [2, 5]}, "win_frac": {"type": "float", "range": [0.01, 0.3]}, "min_win": {"type": "int", "range": [3, 40]}}}
using Solution = Model::Solution;

struct BaseEvC {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, c;
    explicit BaseEvC(const Model& x) : md(x), m(x.m) { c.resize(x.m > 0 ? x.m : 1); }
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
    inline long long step(long long* cc, int job) const {
        const long long* p = &md.pj[(size_t)job * m];
        long long r = cc[0] + p[0]; cc[0] = r;
        for (int i = 1; i < m; ++i) { long long x = cc[i]; r = (x > r ? x : r) + p[i]; cc[i] = r; }
        return r;
    }
    long long suffix(long long* cc, int k0, long long sum) const {
        const int L = (int)seq.size();
        const long long* Fd = F.data(); const long long* pj = md.pj.data(); const int* q = seq.data();
        const long long* Fk = Fd + (size_t)k0 * m;
        int lo = 0;
        while (lo < m && cc[lo] == Fk[lo]) ++lo;
        if (lo == m) return sum + pre[L] - pre[k0];
        for (int k = k0; k < L; ++k) {
            const long long* p = pj + (size_t)q[k] * m;
            const long long* Fn = Fd + (size_t)(k + 1) * m;
            long long r;
            if (lo == 0) { r = cc[0] + p[0]; cc[0] = r; }
            else { long long x = cc[lo], y = Fn[lo - 1]; r = (x > y ? x : y) + p[lo]; cc[lo] = r; }
            for (int j = lo + 1; j < m; ++j) { long long x = cc[j]; r = (x > r ? x : r) + p[j]; cc[j] = r; }
            sum += r;
            while (lo < m && cc[lo] == Fn[lo]) ++lo;
            if (lo == m) return sum + pre[L] - pre[k + 1];
        }
        return sum;
    }
};

class BlockExchange : public hsf::Neighborhood<Model> {
    const Model& md; int maxb; double frac; int minw; BaseEvC ev;
    std::vector<int> tmp;
public:
    BlockExchange(const Model& x, int b, double f, int mw) : md(x), maxb(b), frac(f), minw(mw), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        int w = std::max(minw, (int)std::ceil(frac * L));
        for (int a = 0; a < L; ++a)
            for (int k1 = 1; k1 <= maxb; ++k1) {
                int bhi = std::min(a + w, L - 1);
                for (int b = a + k1 + 1; b <= bhi; ++b)
                    for (int k2 = 1; k2 <= maxb && b + k2 <= L; ++k2) {
                        if (k1 == 1 && k2 == 1) continue;
                        out.push_back(Move{a, k1, b, k2, 0, 0, 0});
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
        int a = mv[0], k1 = mv[1], b = mv[2], k2 = mv[3];
        const int m = ev.m;
        const int* q = ev.seq.data();
        long long* c = ev.c.data();
        const long long* st = &ev.F[(size_t)a * m];
        for (int i = 0; i < m; ++i) c[i] = st[i];
        long long sum = ev.pre[a];
        for (int i = b; i < b + k2; ++i) sum += ev.step(c, q[i]);
        for (int i = a + k1; i < b; ++i) sum += ev.step(c, q[i]);
        for (int i = a; i < a + k1; ++i) sum += ev.step(c, q[i]);
        long long nf = ev.suffix(c, b + k2, sum);
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
