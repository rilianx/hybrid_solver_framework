// COMPONENT: {"name": "critical_block_insertion", "slot": "neighborhood", "params": {"mode": {"type": "cat", "values": ["block_ends", "block_all"]}, "window": {"type": "int", "range": [2, 20]}}}
struct JsAnalysisB {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnalysisB(const Model& m) : M(m) {
        int T = M.total_ops;
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0);
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
                seen[op] = stamp; ++present;
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
    bool critArc(int u, int v) const { return crit(u) && crit(v) && r[u] + M.op_proc[u] == r[v]; }
    int opAt(int i, int k) const { return M.op_of[cur[i][k]][i]; }
};

static void shift_elem(std::vector<int>& v, int from, int to) {
    if (from < to) std::rotate(v.begin() + from, v.begin() + from + 1, v.begin() + to + 1);
    else if (from > to) std::rotate(v.begin() + to, v.begin() + from, v.begin() + from + 1);
}

class CriticalBlockInsertion : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnalysisB A;
    bool allPos;
    int W;
public:
    CriticalBlockInsertion(const Model& m, bool ap, int w) : M(m), A(m), allPos(ap), W(w) {}
    void windowMoves(const Sol& s, std::vector<Move>& out) {
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            for (int f = 0; f < L; ++f)
                for (int to = std::max(0, f - W); to <= std::min(L - 1, f + W); ++to)
                    if (std::abs(to - f) >= 2) out.push_back(Move{i, f, to, 0, 0, 0, 0});
        }
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (!A.feas) { windowMoves(s, out); return; }
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            int a = 0;
            while (a < L) {
                int b = a;
                while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                if (b > a) {
                    int ext = allPos ? W : 1;
                    int lo = std::max(0, a - ext), hi = std::min(L - 1, b + ext);
                    for (int k = a; k <= b; ++k) {
                        if (allPos) {
                            for (int to = lo; to <= hi; ++to)
                                if (std::abs(to - k) >= 2) out.push_back(Move{i, k, to, 0, 0, 0, 0});
                        } else {
                            int tg[4] = {lo, a, b, hi};
                            for (int q = 0; q < 4; ++q) {
                                int to = tg[q];
                                bool dup = false;
                                for (int p = 0; p < q; ++p) if (tg[p] == to) dup = true;
                                if (!dup && std::abs(to - k) >= 2) out.push_back(Move{i, k, to, 0, 0, 0, 0});
                            }
                        }
                    }
                }
                a = b + 1;
            }
        }
        if (out.empty()) windowMoves(s, out);
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        shift_elem(c[m[0]], m[1], m[2]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        auto& v = A.work[m[0]];
        shift_elem(v, m[1], m[2]);
        double o2 = M.objective(A.work);
        shift_elem(v, m[2], m[1]);
        return o2 - A.obj;
    }
    Move tabu_key(const Move& m) override { return Move{m[0], m[2], m[1], 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool ap = params.text("mode", "block_ends") == "block_all";
    int w = (int)params.get("window", 6.0);
    if (w < 1) w = 1;
    return std::make_unique<CriticalBlockInsertion>(model, ap, w);
}
