// COMPONENT: {"name": "priority_rule_window_resequence", "slot": "neighborhood", "params": {"max_window": {"type": "int", "range": [3, 12]}, "rules": {"type": "cat", "values": ["all", "release", "tail"]}}}
struct JsAnR {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnR(const Model& m) : M(m) {
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

class PriorityRuleWindowResequence : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnR A;
    int maxW;
    std::vector<int> rules;
    std::vector<long long> h0, q0;
    struct Item { long long k1, k2; int job; };
    std::vector<Item> items;
    std::vector<int> buf, saved;
    std::vector<long long> wins;
public:
    PriorityRuleWindowResequence(const Model& m, int w, std::vector<int> rl) : M(m), A(m), maxW(w), rules(std::move(rl)) {
        int T = M.total_ops;
        h0.assign(T, 0); q0.assign(T, 0);
        for (int o = 0; o < T; ++o) h0[o] = M.op_k[o] == 0 ? 0 : h0[o - 1] + M.op_proc[o - 1];
        for (int o = T - 1; o >= 0; --o) { int nx = M.op_next[o]; q0[o] = nx < 0 ? 0 : q0[nx] + M.op_proc[nx]; }
    }
    // A must be the analysis of the solution whose machine i is being reordered
    void reorder(int* v, int len, int i, int rule) {
        items.clear();
        const long long BIG = std::numeric_limits<long long>::max() / 4;
        for (int k = 0; k < len; ++k) {
            int j = v[k];
            long long k1 = BIG, k2 = BIG;
            if (j >= 0 && j < M.n && i < (int)M.op_of[j].size() && M.op_of[j][i] >= 0) {
                int op = M.op_of[j][i];
                long long rel, tl;
                if (A.feas) {
                    int jp = M.op_k[op] > 0 ? op - 1 : -1, nx = M.op_next[op];
                    rel = jp >= 0 ? A.r[jp] + M.op_proc[jp] : 0;
                    tl = nx >= 0 ? A.t[nx] : 0;
                } else { rel = h0[op]; tl = q0[op]; }
                if (rule == 0) { k1 = rel; k2 = -tl; }
                else if (rule == 1) { k1 = -tl; k2 = rel; }
                else { k1 = rel - tl; k2 = rel; }
            }
            items.push_back(Item{k1, k2, j});
        }
        std::stable_sort(items.begin(), items.end(), [](const Item& a, const Item& b) {
            if (a.k1 != b.k1) return a.k1 < b.k1;
            return a.k2 < b.k2;
        });
        for (int k = 0; k < len; ++k) v[k] = items[k].job;
    }
    bool changes(const Sol& s, int i, int lo, int hi, int rule) {
        int len = hi - lo + 1;
        buf.assign(s[i].begin() + lo, s[i].begin() + hi + 1);
        reorder(buf.data(), len, i, rule);
        for (int k = 0; k < len; ++k) if (buf[k] != s[i][lo + k]) return true;
        return false;
    }
    void allWindows(const Sol& s, std::vector<Move>& out, bool filter) {
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            for (int lo = 0; lo + 1 < L; ++lo)
                for (int len = 2; len <= maxW && lo + len - 1 < L; ++len)
                    for (int rule : rules)
                        if (!filter || changes(s, i, lo, lo + len - 1, rule))
                            out.push_back(Move{i, lo, lo + len - 1, rule, 0, 0, 0});
        }
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (A.feas) {
            for (int i = 0; i < (int)s.size(); ++i) {
                int L = (int)s[i].size();
                wins.clear();
                int a = 0;
                while (a < L) {
                    int b = a;
                    while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                    if (b > a) {
                        int los[2] = {a, std::max(0, a - 1)}, his[2] = {b, std::min(L - 1, b + 1)};
                        for (int x = 0; x < 2; ++x)
                            for (int y = 0; y < 2; ++y) {
                                int lo = los[x], hi = his[y];
                                if (hi - lo + 1 > maxW) {
                                    wins.push_back((long long)lo * 100000 + (lo + maxW - 1));
                                    wins.push_back((long long)(hi - maxW + 1) * 100000 + hi);
                                } else wins.push_back((long long)lo * 100000 + hi);
                            }
                    }
                    a = b + 1;
                }
                std::sort(wins.begin(), wins.end());
                wins.erase(std::unique(wins.begin(), wins.end()), wins.end());
                for (long long w : wins) {
                    int lo = (int)(w / 100000), hi = (int)(w % 100000);
                    for (int rule : rules)
                        if (changes(s, i, lo, hi, rule)) out.push_back(Move{i, lo, hi, rule, 0, 0, 0});
                }
            }
        }
        if (out.empty()) allWindows(s, out, true);
        if (out.empty()) allWindows(s, out, false);
    }
    Sol apply(const Sol& s, const Move& m) override {
        A.ensure(s);
        Sol c = s;
        reorder(c[m[0]].data() + m[1], m[2] - m[1] + 1, m[0], m[3]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        auto& v = A.work[m[0]];
        int len = m[2] - m[1] + 1;
        saved.assign(v.begin() + m[1], v.begin() + m[2] + 1);
        reorder(v.data() + m[1], len, m[0], m[3]);
        double o2 = M.objective(A.work);
        std::copy(saved.begin(), saved.end(), v.begin() + m[1]);
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("max_window", 6.0);
    if (w < 2) w = 2;
    std::string r = params.text("rules", "all");
    std::vector<int> rl;
    if (r == "release") rl = {0};
    else if (r == "tail") rl = {1};
    else rl = {0, 1, 2};
    return std::make_unique<PriorityRuleWindowResequence>(model, w, rl);
}
