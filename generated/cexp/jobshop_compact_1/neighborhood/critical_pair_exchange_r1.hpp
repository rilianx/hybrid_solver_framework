// COMPONENT: {"name": "critical_pair_exchange", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [2, 15]}, "pair_mode": {"type": "cat", "values": ["one_critical", "both_critical"]}}}
struct JsState {
    const Model& M;
    int N = 0, MM = 0, T = 0;
    std::vector<int> jp, js, jobOf, pos, mp, ms, indeg, topo;
    std::vector<long long> p, r, q, sh, stl;
    std::vector<char> cr;
    Model::Solution cur;
    bool valid = false, feas = false;
    long long cmax = 0;
    double obj = 0;
    explicit JsState(const Model& m) : M(m) {
        N = m.n; MM = m.m; T = m.total_ops;
        jp.assign(T, -1); js.assign(T, -1); jobOf.assign(T, 0);
        pos.assign(T, 0); mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0);
        topo.reserve(T);
        p.assign(T, 0); r.assign(T, 0); q.assign(T, 0); sh.assign(T, 0); stl.assign(T, 0); cr.assign(T, 0);
        for (int j = 0; j < N; ++j) {
            const auto& rt = m.routes[j];
            int prev = -1; long long acc = 0;
            for (size_t k = 0; k < rt.size(); ++k) {
                int o = m.op_of[j][rt[k].first];
                jobOf[o] = j; p[o] = m.op_proc[o]; jp[o] = prev;
                if (prev >= 0) js[prev] = o;
                sh[o] = acc; acc += p[o]; prev = o;
            }
            long long t = 0;
            for (int k = (int)rt.size() - 1; k >= 0; --k) {
                int o = m.op_of[j][rt[k].first]; t += p[o]; stl[o] = t;
            }
        }
    }
    int opAt(const Model::Solution& s, int i, int k) const { return M.opflat[(size_t)i * N + s[i][k]]; }
    void ensure(const Model::Solution& s) {
        if (valid && s == cur) return;
        cur = s; valid = true; compute(s); obj = M.objective(s);
    }
    void compute(const Model::Solution& s) {
        std::fill(mp.begin(), mp.end(), -1);
        std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < MM && i < (int)s.size(); ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int o = opAt(s, i, k);
                pos[o] = k; mp[o] = prev;
                if (prev >= 0) ms[prev] = o;
                prev = o;
            }
        }
        topo.clear();
        for (int o = 0; o < T; ++o) {
            indeg[o] = (jp[o] >= 0) + (mp[o] >= 0);
            if (!indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = js[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            a = ms[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
        }
        feas = (int)topo.size() == T;
        if (!feas) {
            r = sh; q = stl; std::fill(cr.begin(), cr.end(), 0); cmax = 0; return;
        }
        cmax = 0;
        for (int o : topo) {
            long long st = 0;
            if (jp[o] >= 0) st = r[jp[o]] + p[jp[o]];
            if (mp[o] >= 0) st = std::max(st, r[mp[o]] + p[mp[o]]);
            r[o] = st; cmax = std::max(cmax, st + p[o]);
        }
        for (int h = T - 1; h >= 0; --h) {
            int o = topo[h];
            long long b = 0;
            if (js[o] >= 0) b = q[js[o]];
            if (ms[o] >= 0) b = std::max(b, q[ms[o]]);
            q[o] = p[o] + b;
            cr[o] = (r[o] + q[o] == cmax);
        }
    }
};

static Move mk3(int a, int b, int c) { Move m{}; m[0] = a; m[1] = b; m[2] = c; return m; }

class CriticalPairExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsState A;
    Sol work;
    int W;
    bool both;
    static void doSwap(Sol& t, const Move& m) {
        int i = m[0], a = m[1], b = m[2];
        if (i < 0 || i >= (int)t.size() || a == b) return;
        if (a < 0 || b < 0 || a >= (int)t[i].size() || b >= (int)t[i].size()) return;
        std::swap(t[i][a], t[i][b]);
    }
public:
    CriticalPairExchange(const Model& m, int w, bool b) : M(m), A(m), W(w), both(b) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        for (int i = 0; i < (int)s.size(); ++i) {
            int len = (int)s[i].size();
            for (int a = 0; a < len; ++a) {
                int u = A.opAt(s, i, a);
                int lim = std::min(len - 1, a + W);
                for (int b = a + 2; b <= lim; ++b) {
                    int v = A.opAt(s, i, b);
                    bool ok = !A.feas || (both ? (A.cr[u] && A.cr[v]) : (A.cr[u] || A.cr[v]));
                    if (ok) out.push_back(mk3(i, a, b));
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < (int)s.size(); ++i)
                for (int a = 0; a + 1 < (int)s[i].size(); ++a) out.push_back(mk3(i, a, a + 1));
        }
        if (out.empty()) out.push_back(mk3(0, 0, 0));
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s; doSwap(t, m); return t;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        work = s; doSwap(work, m);
        return M.objective(work) - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 6);
    if (w < 2) w = 2;
    bool both = params.text("pair_mode", "one_critical") == "both_critical";
    return std::unique_ptr<hsf::Neighborhood<Model>>(new CriticalPairExchange(model, w, both));
}
