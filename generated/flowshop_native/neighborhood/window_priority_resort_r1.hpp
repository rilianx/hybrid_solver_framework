// COMPONENT: {"name": "window_priority_resort", "slot": "neighborhood", "params": {"len_frac": {"type": "float", "range": [0.02, 0.5]}, "min_len": {"type": "int", "range": [3, 10]}, "growth": {"type": "float", "range": [1.2, 2.5]}, "n_rules": {"type": "int", "range": [1, 3]}}}
using Solution = Model::Solution;

struct BaseEvB {
    const Model& md; int m;
    std::vector<int> seq; bool has = false, feas = false;
    std::vector<long long> F, pre, c;
    explicit BaseEvB(const Model& x) : md(x), m(x.m) { c.resize(x.m > 0 ? x.m : 1); }
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

class WindowResort : public hsf::Neighborhood<Model> {
    const Model& md; double frac; int minl; double growth; int nr; BaseEvB ev;
    std::vector<long long> key[3];
    std::vector<int> run, buf, lens;
    inline long long kof(int r, int j) const {
        return (j < 0 || j >= md.n) ? std::numeric_limits<long long>::max() : key[r][j];
    }
    void sortRange(int r, std::vector<int>::iterator b, std::vector<int>::iterator e) const {
        std::stable_sort(b, e, [&](int x, int y) { return kof(r, x) < kof(r, y); });
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
        run.assign((size_t)nr * L, 1);
        for (int r = 0; r < nr; ++r) {
            int* R = &run[(size_t)r * L];
            for (int i = L - 2; i >= 0; --i)
                R[i] = kof(r, q[i]) < kof(r, q[i + 1]) ? R[i + 1] + 1 : 1;
        }
        for (int i = 0; i < L; ++i)
            for (int l : lens) {
                if (i + l > L) break;
                for (int r = 0; r < nr; ++r)
                    if (run[(size_t)r * L + i] < l) out.push_back(Move{i, l, r, 0, 0, 0, 0});
            }
    }
    Solution apply(const Solution& s, const Move& mv) override {
        Solution r = s;
        auto& v = r[0];
        sortRange(mv[2], v.begin() + mv[0], v.begin() + mv[0] + mv[1]);
        return r;
    }
    double delta(const Solution& s, const Move& mv) override {
        if (!ev.prepare(s)) return md.objective(apply(s, mv)) - md.objective(s);
        int i = mv[0], l = mv[1], r = mv[2];
        buf.assign(ev.seq.begin() + i, ev.seq.begin() + i + l);
        sortRange(r, buf.begin(), buf.end());
        const int m = ev.m;
        long long* c = ev.c.data();
        const long long* st = &ev.F[(size_t)i * m];
        for (int k = 0; k < m; ++k) c[k] = st[k];
        long long sum = ev.pre[i];
        for (int j : buf) sum += ev.step(c, j);
        long long nf = ev.suffix(c, i + l, sum);
        return (double)(nf - ev.pre[ev.seq.size()]);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double f = params.get("len_frac", 0.1);
    int ml = (int)params.get("min_len", 3.0); if (ml < 2) ml = 2;
    double g = params.get("growth", 1.5); if (g < 1.05) g = 1.05;
    int k = (int)params.get("n_rules", 3.0); k = std::max(1, std::min(3, k));
    return std::make_unique<WindowResort>(model, f, ml, g, k);
}
