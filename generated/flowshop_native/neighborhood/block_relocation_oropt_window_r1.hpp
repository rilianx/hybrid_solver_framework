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

class BlockRelocate : public hsf::Neighborhood<Model> {
    const Model& md; int maxb; double frac; int minw; BaseEvA ev;
    std::vector<long long> SR, SRs; int ca = -1, cl = -1, sl = -1; unsigned cver = 0;
    int win(int L) const { int w = (int)std::ceil(frac * L); return std::max(minw, w); }
    void ensure(int a, int len, int t) {
        const int m = ev.m; const int L = (int)ev.seq.size();
        if ((int)SRs.size() < L + 1) { SR.resize((size_t)(L + 1) * m); SRs.resize(L + 1); }
        if (ca != a || cl != len || cver != ev.ver) {
            ca = a; cl = len; cver = ev.ver;
            const long long* src = &ev.F[(size_t)a * m];
            long long* dst = &SR[(size_t)a * m];
            for (int i = 0; i < m; ++i) dst[i] = src[i];
            SRs[a] = ev.pre[a]; sl = a;
        }
        const long long* pj = md.pj.data();
        while (sl < t) {
            const long long* in = &SR[(size_t)sl * m];
            long long* o = &SR[(size_t)(sl + 1) * m];
            const long long* p = pj + (size_t)ev.seq[sl + len] * m;
            long long acc = in[0] + p[0]; o[0] = acc;
            for (int i = 1; i < m; ++i) { long long x = in[i]; acc = (x > acc ? x : acc) + p[i]; o[i] = acc; }
            SRs[sl + 1] = SRs[sl] + acc;
            ++sl;
        }
    }
    long long eval(int a, int len, int t) {
        const int m = ev.m;
        long long* c = ev.c.data();
        long long sum;
        if (t > a) {
            ensure(a, len, t);
            const long long* st = &SR[(size_t)t * m];
            for (int i = 0; i < m; ++i) c[i] = st[i];
            sum = SRs[t];
            for (int i = 0; i < len; ++i) sum += ev.step(c, ev.seq[a + i]);
            return ev.suffix(c, t + len, sum);
        }
        const long long* st = &ev.F[(size_t)t * m];
        for (int i = 0; i < m; ++i) c[i] = st[i];
        sum = ev.pre[t];
        for (int i = 0; i < len; ++i) sum += ev.step(c, ev.seq[a + i]);
        for (int k = t; k < a; ++k) sum += ev.step(c, ev.seq[k]);
        return ev.suffix(c, a + len, sum);
    }
public:
    BlockRelocate(const Model& x, int b, double f, int mw) : md(x), maxb(b), frac(f), minw(mw), ev(x) {}
    void moves(const Solution& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        int w = win(L);
        for (int a = 0; a < L; ++a)
            for (int len = 2; len <= maxb && a + len <= L; ++len) {
                int lo = std::max(0, a - w), hi = std::min(L - len, a + w);
                for (int t = lo; t <= hi; ++t) {
                    if (t == a) continue;
                    out.push_back(Move{a, len, t, 0, 0, 0, 0});
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
        long long nf = eval(mv[0], mv[1], mv[2]);
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
