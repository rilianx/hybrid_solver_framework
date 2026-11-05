// COMPONENT: {"name": "job_priority_shift_all_machines", "slot": "neighborhood", "params": {"max_shift": {"type": "int", "range": [1, 8]}, "extremes": {"type": "cat", "values": ["yes", "no"]}, "focus": {"type": "cat", "values": ["critical", "all"]}}}
struct JsAnJ {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, pos, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnJ(const Model& m) : M(m) {
        int T = M.total_ops;
        mp.assign(T, -1); ms.assign(T, -1); pos.assign(T, 0); indeg.assign(T, 0);
        topo.assign(T, 0); seen.assign(T, 0); r.assign(T, 0); t.assign(T, 0);
        for (auto& v : M.machine_jobs) expected += (int)v.size();
    }
    void ensure(const Model::Solution& s) {
        if (valid && s == cur) return;
        cur = s; work = s; valid = true; compute(s);
    }
    void compute(const Model::Solution& s) {
        obj = M.objective(s);
        int T = M.total_ops;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        feas = ((int)s.size() == M.m);
        ++stamp;
        int present = 0;
        int lim = std::min((int)s.size(), M.m);
        for (int i = 0; i < lim; ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int j = s[i][k];
                if (j < 0 || j >= M.n || i >= (int)M.op_of[j].size() || M.op_of[j][i] < 0) { feas = false; continue; }
                int op = M.op_of[j][i];
                if (seen[op] == stamp) { feas = false; continue; }
                seen[op] = stamp; pos[op] = k; ++present;
                if (prev >= 0) { ms[prev] = op; mp[op] = prev; }
                prev = op;
            }
        }
        if (present != expected) feas = false;
        if (!feas) return;
        int qh = 0, qt = 0;
        for (int o = 0; o < T; ++o) {
            indeg[o] = (M.op_k[o] > 0 ? 1 : 0) + (mp[o] >= 0 ? 1 : 0);
            r[o] = 0;
            if (indeg[o] == 0) topo[qt++] = o;
        }
        cmax = 0;
        while (qh < qt) {
            int o = topo[qh++];
            long long e = r[o] + M.op_proc[o];
            if (e > cmax) cmax = e;
            int a = M.op_next[o];
            if (a >= 0) { if (r[a] < e) r[a] = e; if (--indeg[a] == 0) topo[qt++] = a; }
            int b = ms[o];
            if (b >= 0) { if (r[b] < e) r[b] = e; if (--indeg[b] == 0) topo[qt++] = b; }
        }
        if (qt < T) { feas = false; return; }
        for (int idx = T - 1; idx >= 0; --idx) {
            int o = topo[idx];
            long long best = 0;
            int a = M.op_next[o]; if (a >= 0) best = std::max(best, t[a]);
            int b = ms[o]; if (b >= 0) best = std::max(best, t[b]);
            t[o] = M.op_proc[o] + best;
        }
    }
    bool crit(int o) const { return r[o] + t[o] == cmax; }
};

static void shift_elem_j(std::vector<int>& v, int from, int to) {
    if (from < to) std::rotate(v.begin() + from, v.begin() + from + 1, v.begin() + to + 1);
    else if (from > to) std::rotate(v.begin() + to, v.begin() + from, v.begin() + from + 1);
}

class JobPriorityShift : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnJ A;
    int D;
    bool extremes, critOnly;
    std::vector<int> opJob;
    std::vector<char> jobSel;
    std::vector<std::array<int, 3>> undo;

    static int target(int p, int L, const Move& m) {
        if (m[1] == 1) return 0;
        if (m[1] == 2) return L - 1;
        int q = p + m[2];
        if (q < 0) q = 0;
        if (q > L - 1) q = L - 1;
        return q;
    }
    void doMove(Sol& c, const Move& m, std::vector<std::array<int, 3>>* rec) {
        int j = m[0];
        if (j < 0 || j >= M.n) return;
        for (auto& pr : M.routes[j]) {
            int mach = pr.first;
            if (mach < 0 || mach >= (int)c.size()) continue;
            auto& v = c[mach];
            int p = -1;
            for (int k = 0; k < (int)v.size(); ++k) if (v[k] == j) { p = k; break; }
            if (p < 0) continue;
            int q = target(p, (int)v.size(), m);
            if (q != p) {
                shift_elem_j(v, p, q);
                if (rec) rec->push_back({mach, p, q});
            }
        }
    }
    bool isNoop(const Sol& s, const Move& m) const {
        if (!A.feas) return false;
        int j = m[0];
        for (auto& pr : M.routes[j]) {
            int mach = pr.first;
            if (mach < 0 || mach >= M.m) continue;
            int o = M.op_of[j][mach];
            if (o < 0) continue;
            int p = A.pos[o];
            if (target(p, (int)s[mach].size(), m) != p) return false;
        }
        return true;
    }
    void genJob(const Sol& s, int j, std::vector<Move>& out) {
        for (int d = -D; d <= D; ++d) {
            if (d == 0) continue;
            Move mv{j, 0, d, 0, 0, 0, 0};
            if (!isNoop(s, mv)) out.push_back(mv);
        }
        if (extremes) {
            Move a{j, 1, 0, 0, 0, 0, 0}, b{j, 2, 0, 0, 0, 0, 0};
            if (!isNoop(s, a)) out.push_back(a);
            if (!isNoop(s, b)) out.push_back(b);
        }
    }
public:
    JobPriorityShift(const Model& m, int d, bool ex, bool co) : M(m), A(m), D(d), extremes(ex), critOnly(co) {
        opJob.assign(M.total_ops, 0);
        for (int j = 0; j < M.n; ++j)
            for (auto& pr : M.routes[j]) {
                if (pr.first < 0 || pr.first >= (int)M.op_of[j].size()) continue;
                int o = M.op_of[j][pr.first];
                if (o >= 0) opJob[o] = j;
            }
        jobSel.assign(M.n, 0);
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        std::fill(jobSel.begin(), jobSel.end(), 0);
        if (A.feas && critOnly) {
            for (int o = 0; o < M.total_ops; ++o) if (A.crit(o)) jobSel[opJob[o]] = 1;
        } else {
            std::fill(jobSel.begin(), jobSel.end(), 1);
        }
        for (int j = 0; j < M.n; ++j) if (jobSel[j]) genJob(s, j, out);
        if (out.empty())
            for (int j = 0; j < M.n; ++j) if (!jobSel[j]) genJob(s, j, out);
        if (out.empty()) out.push_back(Move{0, 0, 1, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        doMove(c, m, nullptr);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        undo.clear();
        doMove(A.work, m, &undo);
        if (undo.empty()) return 0.0;
        double o2 = M.objective(A.work);
        for (int k = (int)undo.size() - 1; k >= 0; --k)
            shift_elem_j(A.work[undo[k][0]], undo[k][2], undo[k][1]);
        return o2 - A.obj;
    }
    Move tabu_key(const Move& m) override {
        if (m[1] == 0) return Move{m[0], 0, -m[2], 0, 0, 0, 0};
        return m;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int d = (int)params.get("max_shift", 3.0);
    if (d < 1) d = 1;
    bool ex = params.text("extremes", "yes") == "yes";
    bool co = params.text("focus", "critical") == "critical";
    return std::make_unique<JobPriorityShift>(model, d, ex, co);
}
