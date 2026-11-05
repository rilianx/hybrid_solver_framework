// COMPONENT: {"name": "dispatch_rule_window_resequence", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [3, 12]}, "rules": {"type": "cat", "values": ["all", "ready", "tail", "slack"]}}}
struct JsAnD {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnD(const Model& m) : M(m) {
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

class DispatchWindowResequence : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnD A;
    int W;
    std::vector<int> rules;
    std::vector<long long> sh, stl;
    std::vector<std::pair<long long, int>> buf;
    std::vector<int> seg, saved;
    std::vector<std::array<int, 2>> wins;

    long long key(int o, int rule) const {
        long long rd, tl;
        if (A.feas) {
            int jp = M.op_k[o] > 0 ? o - 1 : -1;
            rd = jp >= 0 ? A.r[jp] + M.op_proc[jp] : 0;
            tl = A.t[o];
        } else { rd = sh[o]; tl = stl[o]; }
        if (rule == 0) return rd;
        if (rule == 1) return -tl;
        return -(rd + tl);
    }
    // writes new order of row[a..b] into seg; returns whether it changed
    bool reseq(const std::vector<int>& row, int i, int a, int b, int rule) {
        buf.clear();
        const long long BIG = std::numeric_limits<long long>::max() / 4;
        for (int k = a; k <= b; ++k) {
            int j = row[k];
            long long kk = BIG;
            if (j >= 0 && j < M.n && i >= 0 && i < (int)M.op_of[j].size()) {
                int op = M.op_of[j][i];
                if (op >= 0) kk = key(op, rule);
            }
            buf.push_back({kk, k});
        }
        std::sort(buf.begin(), buf.end());
        seg.resize(b - a + 1);
        bool ch = false;
        for (int idx = 0; idx <= b - a; ++idx) {
            seg[idx] = row[buf[idx].second];
            if (buf[idx].second != a + idx) ch = true;
        }
        return ch;
    }
    bool validMove(const Sol& s, const Move& m) const {
        if (m[0] < 0 || m[0] >= (int)s.size() || m[0] >= M.m) return false;
        int L = (int)s[m[0]].size();
        return m[1] >= 0 && m[1] < m[2] && m[2] < L && m[3] >= 0 && m[3] <= 2;
    }
    void emitWindows(const Sol& s, int i, std::vector<Move>& out) {
        for (auto& w : wins)
            for (int rl : rules)
                if (reseq(s[i], i, w[0], w[1], rl)) out.push_back(Move{i, w[0], w[1], rl, 0, 0, 0});
    }
    void slidingAll(const Sol& s, std::vector<Move>& out, int len) {
        int lim = std::min((int)s.size(), M.m);
        for (int i = 0; i < lim; ++i) {
            int L = (int)s[i].size();
            if (L < 2) continue;
            int ln = std::min(len, L);
            wins.clear();
            for (int x = 0; x + ln - 1 < L; ++x) wins.push_back({x, x + ln - 1});
            emitWindows(s, i, out);
        }
    }
public:
    DispatchWindowResequence(const Model& m, int w, const std::string& rs) : M(m), A(m), W(w) {
        if (rs == "ready") rules = {0};
        else if (rs == "tail") rules = {1};
        else if (rs == "slack") rules = {2};
        else rules = {0, 1, 2};
        int T = M.total_ops;
        sh.assign(T, 0); stl.assign(T, 0);
        int id = 0;
        for (int j = 0; j < M.n; ++j) {
            int L = (int)M.routes[j].size();
            long long acc = 0;
            for (int k = 0; k < L; ++k) { sh[id + k] = acc; acc += M.op_proc[id + k]; }
            long long rem = 0;
            for (int k = L - 1; k >= 0; --k) { rem += M.op_proc[id + k]; stl[id + k] = rem; }
            id += L;
        }
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (A.feas) {
            for (int i = 0; i < M.m; ++i) {
                int L = (int)s[i].size();
                wins.clear();
                int a = 0;
                while (a < L) {
                    int b = a;
                    while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                    if (b > a) {
                        int lo = std::max(0, a - 1), hi = std::min(L - 1, b + 1);
                        wins.push_back({a, b});
                        wins.push_back({lo, b});
                        wins.push_back({a, hi});
                        wins.push_back({lo, hi});
                        if (L >= W)
                            for (int x = std::max(0, a - W + 1); x <= std::min(b, L - W); ++x)
                                wins.push_back({x, x + W - 1});
                    }
                    a = b + 1;
                }
                std::sort(wins.begin(), wins.end());
                wins.erase(std::unique(wins.begin(), wins.end()), wins.end());
                wins.erase(std::remove_if(wins.begin(), wins.end(),
                           [](const std::array<int, 2>& w) { return w[1] <= w[0]; }), wins.end());
                emitWindows(s, i, out);
            }
        }
        if (out.empty()) slidingAll(s, out, W);
        if (out.empty()) for (int len = 2; len < W && out.empty(); ++len) slidingAll(s, out, len);
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        if (!validMove(s, m)) return c;
        A.ensure(s);
        reseq(s[m[0]], m[0], m[1], m[2], m[3]);
        std::copy(seg.begin(), seg.end(), c[m[0]].begin() + m[1]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        if (!validMove(s, m)) return 0.0;
        A.ensure(s);
        auto& row = A.work[m[0]];
        if (!reseq(row, m[0], m[1], m[2], m[3])) return 0.0;
        saved.assign(row.begin() + m[1], row.begin() + m[2] + 1);
        std::copy(seg.begin(), seg.end(), row.begin() + m[1]);
        double o2 = M.objective(A.work);
        std::copy(saved.begin(), saved.end(), row.begin() + m[1]);
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 6.0);
    if (w < 3) w = 3;
    std::string rs = params.text("rules", "all");
    return std::make_unique<DispatchWindowResequence>(model, w, rs);
}
