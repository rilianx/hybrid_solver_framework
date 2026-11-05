// COMPONENT: {"name": "job_shift_all_machines", "slot": "neighborhood", "params": {"max_shift": {"type": "int", "range": [2, 6]}, "where": {"type": "cat", "values": ["all_machines", "critical_machines"]}}}
struct JsInfoS {
    const Model& M;
    int N = 0, NM = 0, T = 0;
    std::vector<int> opJob, opMach, opProc, jPred, jSucc;
    std::vector<std::vector<int>> opOf;
    Model::Solution cur;
    bool valid = false, feas = false;
    double obj = 0;
    long long cmax = 0;
    std::vector<int> mp, ms, pos, indeg, topo;
    std::vector<long long> r, q;
    explicit JsInfoS(const Model& m) : M(m) {
        N = m.n; NM = m.m;
        opOf.assign(N, std::vector<int>(NM, -1));
        for (int j = 0; j < N; ++j) {
            int prev = -1;
            for (const auto& pr : m.routes[j]) {
                int id = T++;
                opJob.push_back(j); opMach.push_back(pr.first); opProc.push_back(pr.second);
                jPred.push_back(prev); jSucc.push_back(-1);
                if (prev >= 0) jSucc[prev] = id;
                if (pr.first >= 0 && pr.first < NM) opOf[j][pr.first] = id;
                prev = id;
            }
        }
        mp.assign(T, -1); ms.assign(T, -1); pos.assign(T, -1); indeg.assign(T, 0);
        r.assign(T, 0); q.assign(T, 0); topo.reserve(T);
    }
    void ensure(const Model::Solution& s) { if (!valid || s != cur) compute(s); }
    void compute(const Model::Solution& s) {
        cur = s; valid = true; obj = M.objective(s);
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1); std::fill(pos.begin(), pos.end(), -1);
        for (int i = 0; i < (int)s.size() && i < NM; ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int j = s[i][k]; if (j < 0 || j >= N) continue;
                int o = opOf[j][i]; if (o < 0) continue;
                pos[o] = k;
                if (prev >= 0) { mp[o] = prev; ms[prev] = o; }
                prev = o;
            }
        }
        for (int o = 0; o < T; ++o) indeg[o] = (jPred[o] >= 0) + (mp[o] >= 0);
        topo.clear();
        for (int o = 0; o < T; ++o) if (indeg[o] == 0) topo.push_back(o);
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = jSucc[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            int b = ms[o]; if (b >= 0 && --indeg[b] == 0) topo.push_back(b);
        }
        feas = (int)topo.size() == T;
        cmax = 0;
        if (feas) {
            for (int o : topo) {
                long long v = 0;
                if (jPred[o] >= 0) v = r[jPred[o]] + opProc[jPred[o]];
                if (mp[o] >= 0) v = std::max(v, r[mp[o]] + opProc[mp[o]]);
                r[o] = v; cmax = std::max(cmax, v + opProc[o]);
            }
            for (int h = T - 1; h >= 0; --h) {
                int o = topo[h]; long long v = 0;
                if (jSucc[o] >= 0) v = q[jSucc[o]] + opProc[jSucc[o]];
                if (ms[o] >= 0) v = std::max(v, q[ms[o]] + opProc[ms[o]]);
                q[o] = v;
            }
        } else {
            for (int o = 0; o < T; ++o) r[o] = jPred[o] >= 0 ? r[jPred[o]] + opProc[jPred[o]] : 0;
            for (int o = T - 1; o >= 0; --o) q[o] = jSucc[o] >= 0 ? q[jSucc[o]] + opProc[jSucc[o]] : 0;
            for (int o = 0; o < T; ++o) cmax = std::max(cmax, r[o] + opProc[o] + q[o]);
        }
    }
    bool crit(int o) const { return r[o] + opProc[o] + q[o] == cmax; }
};

static void move_elem_js(std::vector<int>& v, int from, int to) {
    if (from < to) std::rotate(v.begin() + from, v.begin() + from + 1, v.begin() + to + 1);
    else if (from > to) std::rotate(v.begin() + to, v.begin() + from, v.begin() + from + 1);
}

class JobShiftAllMachines : public hsf::Neighborhood<Model> {
    const Model& M;
    JsInfoS A;
    int K;
    bool critOnly;
    Sol work;

    bool eligible(int o) const { return !critOnly || !A.feas || A.crit(o); }

    void build(const Sol& s, const Move& mv, Sol& out) {
        if (critOnly) A.ensure(s);
        out = s;
        int j = mv[0], sh = mv[1];
        if (j < 0 || j >= A.N) return;
        for (int i = 0; i < (int)out.size() && i < A.NM; ++i) {
            int o = A.opOf[j][i];
            if (o < 0 || !eligible(o)) continue;
            auto& seq = out[i];
            int L = seq.size(), p = -1;
            for (int k = 0; k < L; ++k) if (seq[k] == j) { p = k; break; }
            if (p < 0) continue;
            int t = std::max(0, std::min(L - 1, p + sh));
            if (std::abs(t - p) < 2) continue;  // solo inserciones reales (no intercambios adyacentes)
            move_elem_js(seq, p, t);
        }
    }
public:
    JobShiftAllMachines(const Model& m, int k, bool c) : M(m), A(m), K(k), critOnly(c) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        for (int j = 0; j < A.N; ++j) {
            bool cand = !A.feas;
            if (!cand) for (int i = 0; i < A.NM; ++i) { int o = A.opOf[j][i]; if (o >= 0 && A.crit(o)) { cand = true; break; } }
            if (!cand) continue;
            for (int sh = -K; sh <= K; ++sh) {
                if (std::abs(sh) < 2) continue;
                bool changes = false;
                for (int i = 0; i < A.NM && i < (int)s.size() && !changes; ++i) {
                    int o = A.opOf[j][i];
                    if (o < 0 || !eligible(o) || A.pos[o] < 0) continue;
                    int L = s[i].size(), p = A.pos[o];
                    int t = std::max(0, std::min(L - 1, p + sh));
                    if (std::abs(t - p) >= 2) changes = true;
                }
                if (changes) { Move mv{}; mv[0] = j; mv[1] = sh; out.push_back(mv); }
            }
        }
        if (out.empty()) {
            for (int j = 0; j < A.N; ++j)
                for (int sh = -K; sh <= K; ++sh)
                    if (std::abs(sh) >= 2) { Move mv{}; mv[0] = j; mv[1] = sh; out.push_back(mv); }
        }
    }
    Sol apply(const Sol& s, const Move& m) override { Sol r; build(s, m, r); return r; }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        double base = A.obj;
        build(s, m, work);
        return M.objective(work) - base;
    }
    Move tabu_key(const Move& m) override { Move k{}; k[0] = m[0]; k[1] = -m[1]; return k; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("max_shift", 3);
    k = std::max(2, std::min(6, k));
    std::string w = params.text("where", "all_machines");
    return std::make_unique<JobShiftAllMachines>(model, k, w == "critical_machines");
}
