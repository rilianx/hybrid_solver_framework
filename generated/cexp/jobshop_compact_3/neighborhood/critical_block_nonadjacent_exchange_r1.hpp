// COMPONENT: {"name": "critical_block_nonadjacent_exchange", "slot": "neighborhood", "params": {"mode": {"type": "cat", "values": ["end_to_any", "any_pair"]}, "max_dist": {"type": "int", "range": [2, 30]}}}
struct JsCoreX {
    const Model& M;
    int n, m, T;
    std::vector<int> jp, jn;
    std::vector<long long> p;
    Model::Solution cur;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0; long long version = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, q;
    int stamp = 0;
    explicit JsCoreX(const Model& md) : M(md), n(md.n), m(md.m), T(md.total_ops) {
        jp.assign(T, -1); jn.assign(T, -1); p.assign(T, 0);
        for (int j = 0; j < n; ++j) {
            const auto& R = M.routes[j]; int prev = -1;
            for (size_t k = 0; k < R.size(); ++k) {
                int o = M.op_of[j][R[k].first];
                p[o] = R[k].second; jp[o] = prev; if (prev >= 0) jn[prev] = o; prev = o;
            }
        }
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0); seen.assign(T, 0);
        r.assign(T, 0); q.assign(T, 0); topo.reserve(T);
    }
    int op(int i, int j) const { return (i >= 0 && i < m && j >= 0 && j < n) ? M.opflat[(size_t)i * n + j] : -1; }
    void ensure(const Model::Solution& s) { if (!valid || s != cur) compute(s); }
    void compute(const Model::Solution& s) {
        cur = s; valid = true; ++version; obj = M.objective(s); feas = false; cmax = 0;
        ++stamp;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        if ((int)s.size() != m) return;
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            const auto& seq = s[i];
            for (int k = 0; k < (int)seq.size(); ++k) {
                int o = op(i, seq[k]);
                if (o < 0 || seen[o] == stamp) return;
                seen[o] = stamp; ++cnt;
                if (k > 0) { int pr = op(i, seq[k - 1]); mp[o] = pr; ms[pr] = o; }
            }
        }
        if (cnt != T) return;
        topo.clear();
        for (int o = 0; o < T; ++o) { indeg[o] = (jp[o] >= 0) + (mp[o] >= 0); if (!indeg[o]) topo.push_back(o); }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = jn[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            int b = ms[o]; if (b >= 0 && --indeg[b] == 0) topo.push_back(b);
        }
        if ((int)topo.size() != T) return;
        for (int o : topo) {
            long long a = 0;
            if (jp[o] >= 0) a = r[jp[o]] + p[jp[o]];
            if (mp[o] >= 0) a = std::max(a, r[mp[o]] + p[mp[o]]);
            r[o] = a; cmax = std::max(cmax, a + p[o]);
        }
        for (int h = T - 1; h >= 0; --h) {
            int o = topo[h]; long long b = 0;
            if (jn[o] >= 0) b = q[jn[o]] + p[jn[o]];
            if (ms[o] >= 0) b = std::max(b, q[ms[o]] + p[ms[o]]);
            q[o] = b;
        }
        feas = true;
    }
    bool critArc(int u, int v) const { return r[u] + p[u] == r[v] && r[v] + p[v] + q[v] == cmax; }
};

class CriticalBlockNonadjacentExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsCoreX A;
    bool anyPair;
    int D;
    Sol work; long long workVer = -1;

    void addBlock(int i, int a, int b, std::vector<Move>& out) {
        if (b - a < 2) return;
        if (anyPair) {
            for (int x = a; x <= b; ++x)
                for (int y = x + 2; y <= std::min(b, x + D); ++y) out.push_back(Move{i, x, y, 0, 0, 0, 0});
            return;
        }
        for (int x = a + 2; x <= std::min(b, a + D); ++x) out.push_back(Move{i, a, x, 0, 0, 0, 0});
        for (int x = std::max(a, b - D); x <= b - 2; ++x) {
            if (x == a && b - a <= D) continue;  // (a,b) ya agregado
            out.push_back(Move{i, x, b, 0, 0, 0, 0});
        }
    }
public:
    CriticalBlockNonadjacentExchange(const Model& md, bool ap, int d) : M(md), A(md), anyPair(ap), D(std::max(2, d)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        int mm = std::min(A.m, (int)s.size());
        if (A.feas) {
            for (int i = 0; i < mm; ++i) {
                const auto& seq = s[i];
                int L = (int)seq.size(), k = 0;
                while (k < L - 1) {
                    int u = A.op(i, seq[k]), v = A.op(i, seq[k + 1]);
                    if (u >= 0 && v >= 0 && A.critArc(u, v)) {
                        int a = k;
                        while (k < L - 1) {
                            int uu = A.op(i, seq[k]), vv = A.op(i, seq[k + 1]);
                            if (uu < 0 || vv < 0 || !A.critArc(uu, vv)) break;
                            ++k;
                        }
                        addBlock(i, a, k, out);
                    } else ++k;
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < mm; ++i) {
                int L = (int)s[i].size();
                for (int x = 0; x < L; ++x)
                    for (int y = x + 2; y < std::min(L, x + D + 1); ++y) out.push_back(Move{i, x, y, 0, 0, 0, 0});
            }
        }
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        int i = mv[0];
        if (i >= 0 && i < (int)r.size()) {
            int L = (int)r[i].size();
            if (mv[1] >= 0 && mv[1] < L && mv[2] >= 0 && mv[2] < L) std::swap(r[i][mv[1]], r[i][mv[2]]);
        }
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        A.ensure(s);
        int i = mv[0];
        if (i < 0 || i >= (int)s.size()) return 0.0;
        int L = (int)s[i].size();
        if (mv[1] < 0 || mv[1] >= L || mv[2] < 0 || mv[2] >= L || mv[1] == mv[2]) return 0.0;
        if (workVer != A.version) { work = s; workVer = A.version; }
        std::swap(work[i][mv[1]], work[i][mv[2]]);
        double v = M.objective(work);
        std::swap(work[i][mv[1]], work[i][mv[2]]);
        return v - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool ap = params.text("mode", "end_to_any") == "any_pair";
    int d = (int)params.get("max_dist", 8);
    return std::make_unique<CriticalBlockNonadjacentExchange>(model, ap, d);
}
