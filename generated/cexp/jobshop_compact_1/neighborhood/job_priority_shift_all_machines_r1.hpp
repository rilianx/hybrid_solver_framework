// COMPONENT: {"name": "job_priority_shift_all_machines", "slot": "neighborhood", "params": {"max_shift": {"type": "int", "range": [1, 8]}, "scope": {"type": "cat", "values": ["critical_jobs", "all_jobs"]}}}
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

class JobPriorityShift : public hsf::Neighborhood<Model> {
    const Model& M;
    JsState A;
    Sol work;
    int D;
    bool critOnly;
    void shiftJob(Sol& t, const Move& mv) const {
        int j = mv[0], dir = mv[1], d = mv[2];
        if (j < 0 || j >= M.n || d <= 0 || (dir != 1 && dir != -1)) return;
        const auto& rt = M.routes[j];
        for (size_t k = 0; k < rt.size(); ++k) {
            int i = rt[k].first;
            if (i < 0 || i >= (int)t.size()) continue;
            auto& v = t[i];
            int len = (int)v.size();
            int p = (int)(std::find(v.begin(), v.end(), j) - v.begin());
            if (p >= len) continue;
            int to = p + dir * d;
            if (to < 0) to = 0;
            if (to > len - 1) to = len - 1;
            if (to < p) std::rotate(v.begin() + to, v.begin() + p, v.begin() + p + 1);
            else if (to > p) std::rotate(v.begin() + p, v.begin() + p + 1, v.begin() + to + 1);
        }
    }
public:
    JobPriorityShift(const Model& m, int d, bool c) : M(m), A(m), D(d), critOnly(c) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        bool useCrit = critOnly && A.feas;
        for (int j = 0; j < M.n; ++j) {
            const auto& rt = M.routes[j];
            bool hasCrit = !useCrit;
            int roomL = 0, roomR = 0;
            for (size_t k = 0; k < rt.size(); ++k) {
                int i = rt[k].first;
                int o = M.op_of[j][i];
                if (o < 0) continue;
                if (A.cr[o]) hasCrit = true;
                int len = (int)s[i].size();
                roomL = std::max(roomL, A.pos[o]);
                roomR = std::max(roomR, len - 1 - A.pos[o]);
            }
            if (!hasCrit) continue;
            for (int d = 1; d <= std::min(D, roomL); ++d) out.push_back(mk3(j, -1, d));
            for (int d = 1; d <= std::min(D, roomR); ++d) out.push_back(mk3(j, 1, d));
        }
        if (out.empty()) {
            for (int j = 0; j < M.n; ++j) { out.push_back(mk3(j, -1, 1)); out.push_back(mk3(j, 1, 1)); }
        }
        if (out.empty()) out.push_back(mk3(0, 1, 0));
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s; shiftJob(t, m); return t;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        work = s; shiftJob(work, m);
        return M.objective(work) - A.obj;
    }
    Move tabu_key(const Move& m) override { return mk3(m[0], -m[1], m[2]); }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int d = (int)params.get("max_shift", 2);
    if (d < 1) d = 1;
    bool c = params.text("scope", "critical_jobs") == "critical_jobs";
    return std::unique_ptr<hsf::Neighborhood<Model>>(new JobPriorityShift(model, d, c));
}
