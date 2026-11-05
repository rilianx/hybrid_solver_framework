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
    std::vector<int> buf, saved, sj, sop, used, tmp, resFlat;
    std::vector<long long> sr, st, sp, wins;
public:
    PriorityRuleWindowResequence(const Model& m, int w, std::vector<int> rl) : M(m), A(m), maxW(w), rules(std::move(rl)) {
        int T = M.total_ops;
        h0.assign(T, 0); q0.assign(T, 0);
        for (int o = 0; o < T; ++o) h0[o] = M.op_k[o] == 0 ? 0 : h0[o - 1] + M.op_proc[o - 1];
        for (int o = T - 1; o >= 0; --o) { int nx = M.op_next[o]; q0[o] = nx < 0 ? 0 : q0[nx] + M.op_proc[nx]; }
    }
    // A must be the analysis of the solution whose machine i is being reordered
    void reorder(int* v, int len, int i, int rule) {
        sj.assign(len, 0); sop.assign(len, -1); sr.assign(len, 0); st.assign(len, 0); sp.assign(len, 0);
        for (int k = 0; k < len; ++k) {
            int j = v[k];
            sj[k] = j;
            if (j >= 0 && j < M.n && i < (int)M.op_of[j].size() && M.op_of[j][i] >= 0) {
                int op = M.op_of[j][i];
                sop[k] = op;
                if (A.feas) {
                    int jp = M.op_k[op] > 0 ? op - 1 : -1, nx = M.op_next[op];
                    sr[k] = jp >= 0 ? A.r[jp] + M.op_proc[jp] : 0;
                    st[k] = nx >= 0 ? A.t[nx] : 0;
                } else { sr[k] = h0[op]; st[k] = q0[op]; }
                sp[k] = M.op_proc[op];
            }
        }
        if (rule == 3) {
            // Schrage dispatch inside the window
            long long time = 0;
            if (A.feas && sop[0] >= 0) {
                int pm = A.mp[sop[0]];
                if (pm >= 0) time = A.r[pm] + M.op_proc[pm];
            }
            used.assign(len, 0); tmp.clear();
            int nvalid = 0;
            for (int k = 0; k < len; ++k) if (sop[k] >= 0) ++nvalid;
            for (int step = 0; step < nvalid; ++step) {
                int best = -1;
                for (int k = 0; k < len; ++k) {
                    if (used[k] || sop[k] < 0 || sr[k] > time) continue;
                    if (best < 0 || st[k] > st[best] || (st[k] == st[best] && sr[k] < sr[best])) best = k;
                }
                if (best < 0) {
                    for (int k = 0; k < len; ++k) {
                        if (used[k] || sop[k] < 0) continue;
                        if (best < 0 || sr[k] < sr[best] || (sr[k] == sr[best] && st[k] > st[best])) best = k;
                    }
                }
                used[best] = 1; tmp.push_back(sj[best]);
                time = std::max(time, sr[best]) + sp[best];
            }
            for (int k = 0; k < len; ++k) if (sop[k] < 0) tmp.push_back(sj[k]);
            for (int k = 0; k < len; ++k) v[k] = tmp[k];
            return;
        }
        items.clear();
        const long long BIG = std::numeric_limits<long long>::max() / 4;
        for (int k = 0; k < len; ++k) {
            long long k1 = BIG, k2 = BIG;
            if (sop[k] >= 0) {
                long long rel = sr[k], tl = st[k];
                if (rule == 0) { k1 = rel; k2 = -tl; }
                else if (rule == 1) { k1 = -tl; k2 = rel; }
                else { k1 = rel - tl; k2 = rel; }
            }
            items.push_back(Item{k1, k2, sj[k]});
        }
        std::stable_sort(items.begin(), items.end(), [](const Item& a, const Item& b) {
            if (a.k1 != b.k1) return a.k1 < b.k1;
            return a.k2 < b.k2;
        });
        for (int k = 0; k < len; ++k) v[k] = items[k].job;
    }
    // 0 = no change, 1 = single adjacent transposition, 2 = other change; result left in buf
    int changeKind(const Sol& s, int i, int lo, int hi, int rule) {
        int len = hi - lo + 1;
        buf.assign(s[i].begin() + lo, s[i].begin() + hi + 1);
        reorder(buf.data(), len, i, rule);
        int f = -1, l = -1;
        for (int k = 0; k < len; ++k) if (buf[k] != s[i][lo + k]) { if (f < 0) f = k; l = k; }
        if (f < 0) return 0;
        if (l == f + 1 && buf[f] == s[i][lo + l] && buf[l] == s[i][lo + f]) return 1;
        return 2;
    }
    void addWindow(const Sol& s, int i, int lo, int hi, std::vector<Move>& out, int minKind) {
        int len = hi - lo + 1;
        resFlat.clear();
        for (int rule : rules) {
            if (minKind == 0) { out.push_back(Move{i, lo, hi, rule, 0, 0, 0}); continue; }
            int kind = changeKind(s, i, lo, hi, rule);
            if (kind < minKind) continue;
            bool dup = false;
            for (size_t b = 0; b + len <= resFlat.size() && !dup; b += len)
                if (std::equal(buf.begin(), buf.begin() + len, resFlat.begin() + b)) dup = true;
            if (dup) continue;
            resFlat.insert(resFlat.end(), buf.begin(), buf.begin() + len);
            out.push_back(Move{i, lo, hi, rule, 0, 0, 0});
        }
    }
    void allWindows(const Sol& s, std::vector<Move>& out, int minKind) {
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            for (int lo = 0; lo + 1 < L; ++lo)
                for (int len = 2; len <= maxW && lo + len - 1 < L; ++len)
                    addWindow(s, i, lo, lo + len - 1, out, minKind);
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
                        for (int ml = 0; ml <= 2; ++ml)
                            for (int mr = 0; mr <= 2; ++mr) {
                                int lo = std::max(0, a - ml), hi = std::min(L - 1, b + mr);
                                if (hi - lo + 1 < 3) continue;
                                if (hi - lo + 1 > maxW) {
                                    int step = std::max(1, maxW / 2);
                                    for (int x = lo; x + maxW - 1 <= hi; x += step)
                                        wins.push_back((long long)x * 100000 + (x + maxW - 1));
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
                    addWindow(s, i, lo, hi, out, 2);
                }
            }
        }
        if (out.empty()) allWindows(s, out, 2);
        if (out.empty()) allWindows(s, out, 1);
        if (out.empty()) allWindows(s, out, 0);
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
    if (w < 3) w = 3;
    std::string r = params.text("rules", "all");
    std::vector<int> rl;
    if (r == "release") rl = {3, 0};
    else if (r == "tail") rl = {3, 1};
    else rl = {3, 0, 1, 2};
    return std::make_unique<PriorityRuleWindowResequence>(model, w, rl);
}
