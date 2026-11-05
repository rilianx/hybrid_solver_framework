// COMPONENT: {"name": "jssp_machine_window_reshuffle", "slot": "perturbation", "params": {"window_len": {"type": "int", "range": [3, 10]}, "windows_scale": {"type": "float", "range": [0.3, 2.0]}, "machine_pick": {"type": "cat", "values": ["critical", "random"]}}}
struct Core {
    using Sol = Model::Solution;
    const Model& md;
    int N, M;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit Core(const Model& m) : md(m), N(m.total_ops), M(m.m) {
        job.assign(N, 0); mach.assign(N, 0);
        for (int j = 0; j < m.n; ++j) for (auto& pr : m.routes[j]) {
            if (pr.first < 0 || pr.first >= (int)m.op_of[j].size()) continue;
            int o = m.op_of[j][pr.first]; if (o >= 0) { job[o] = j; mach[o] = pr.first; }
        }
        mp.assign(N, -1); ms.assign(N, -1); pos.assign(N, 0); indeg.assign(N, 0); q.assign(N, 0);
        st.assign(N, 0); mark.assign(m.n, 0);
    }
    bool load(const Sol& s) {
        if ((int)s.size() != M) return false;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < M; ++i) {
            if (s[i].size() != md.machine_jobs[i].size()) return false;
            ++stamp; int prev = -1;
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= md.n || i >= (int)md.op_of[j].size()) return false;
                int op = md.op_of[j][i];
                if (op < 0 || mark[j] == stamp) return false;
                mark[j] = stamp; pos[op] = idx;
                if (prev >= 0) { ms[prev] = op; mp[op] = prev; }
                prev = op;
            }
        }
        return true;
    }
    bool times() {
        int qh = 0, qt = 0;
        for (int o = 0; o < N; ++o) {
            indeg[o] = (md.op_k[o] > 0 ? 1 : 0) + (mp[o] >= 0 ? 1 : 0); st[o] = 0;
            if (indeg[o] == 0) q[qt++] = o;
        }
        mk = 0; endop = -1;
        while (qh < qt) {
            int o = q[qh++]; long long e = st[o] + md.op_proc[o];
            if (endop < 0 || e > mk) { mk = e; endop = o; }
            int a = md.op_next[o];
            if (a >= 0) { if (st[a] < e) st[a] = e; if (--indeg[a] == 0) q[qt++] = a; }
            int b = ms[o];
            if (b >= 0) { if (st[b] < e) st[b] = e; if (--indeg[b] == 0) q[qt++] = b; }
        }
        return qt == N;
    }
    bool check(const Sol& s) { return load(s) && times(); }
    void critical(Rng& rng, std::vector<int>& path) {
        path.clear(); int o = endop;
        while (o >= 0) {
            path.push_back(o);
            int jp = md.op_k[o] > 0 ? o - 1 : -1, mq = mp[o];
            bool tj = jp >= 0 && st[jp] + md.op_proc[jp] == st[o];
            bool tm = mq >= 0 && st[mq] + md.op_proc[mq] == st[o];
            if (tj && tm) o = rng.below(2) ? jp : mq; else if (tj) o = jp; else if (tm) o = mq; else o = -1;
        }
        std::reverse(path.begin(), path.end());
    }
    bool try_swap(Sol& cur, int mi, int pi) {
        std::swap(cur[mi][pi], cur[mi][pi + 1]);
        if (check(cur)) return true;
        std::swap(cur[mi][pi], cur[mi][pi + 1]);
        check(cur);
        return false;
    }
    bool any_swap(Sol& cur, Rng& rng) {
        cand.clear();
        for (int i = 0; i < M; ++i) for (int p = 0; p + 1 < (int)cur[i].size(); ++p) cand.push_back({i, p});
        if (cand.empty()) return false;
        int lim = std::min<int>(20, (int)cand.size());
        for (int t = 0; t < lim; ++t) { auto cc = cand[rng.below((int)cand.size())]; if (try_swap(cur, cc.first, cc.second)) return true; }
        std::shuffle(cand.begin(), cand.end(), rng.g);
        for (auto& cc : cand) if (try_swap(cur, cc.first, cc.second)) return true;
        return false;
    }
    Sol dispatch(const std::vector<double>& key) {
        Sol out(M);
        for (int i = 0; i < M; ++i) out[i].reserve(md.machine_jobs[i].size());
        std::priority_queue<std::pair<double,int>, std::vector<std::pair<double,int>>, std::greater<std::pair<double,int>>> h;
        for (int o = 0; o < N; ++o) if (md.op_k[o] == 0) h.push({key[o], o});
        while (!h.empty()) {
            int o = h.top().second; h.pop();
            if (mach[o] < M) out[mach[o]].push_back(job[o]);
            if (md.op_next[o] >= 0) h.push({key[md.op_next[o]], md.op_next[o]});
        }
        return out;
    }
    Sol repair(const Sol& s, Rng& rng) {
        std::vector<double> key(N);
        for (int o = 0; o < N; ++o) key[o] = rng.uniform() * (double)std::max(1, md.n);
        for (int i = 0; i < std::min<int>(M, (int)s.size()); ++i)
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= md.n || i >= (int)md.op_of[j].size()) continue;
                int op = md.op_of[j][i]; if (op >= 0) key[op] = idx + 0.5 * rng.uniform();
            }
        return dispatch(key);
    }
};

class MachineWindowReshuffle : public hsf::Perturbation<Model> {
    Core c;
    int wlen; double wscale; bool crit;
    std::vector<int> path, W, inwin, vis, stk, npred, cnt, avail, order, oldseg, rows;
    std::vector<char> adj;
    int vstamp = 0;

    bool pick(const Model::Solution& cur, int L, Rng& rng, int fixed, int& mi, int& start, int& Le) {
        if (crit) {
            c.critical(rng, path);
            for (int t = 0; t < 12 && !path.empty(); ++t) {
                int o = path[rng.below((int)path.size())];
                int m = c.mach[o];
                if (m >= c.M) continue;
                if (fixed >= 0 && m != fixed) continue;
                int sz = (int)cur[m].size();
                if (sz < 2) continue;
                mi = m; Le = std::min(L, sz);
                start = c.pos[o] - rng.below(Le);
                start = std::max(0, std::min(start, sz - Le));
                return true;
            }
        }
        if (fixed >= 0) {
            mi = fixed;
        } else {
            if (rows.empty()) return false;
            mi = rows[rng.below((int)rows.size())];
        }
        int sz = (int)cur[mi].size();
        if (sz < 2) return false;
        Le = std::min(L, sz);
        start = rng.below(sz - Le + 1);
        return true;
    }

    bool reshuffle(Model::Solution& cur, int mi, int start, int Le, Rng& rng) {
        auto& row = cur[mi];
        const int n = c.md.n;
        const int* rowop = c.md.opflat.data() + (size_t)mi * n;
        W.clear();
        long long maxst = 0;
        for (int t = 0; t < Le; ++t) {
            int o = rowop[row[start + t]];
            W.push_back(o); inwin[o] = t; maxst = std::max(maxst, c.st[o]);
        }
        adj.assign((size_t)Le * Le, 0);
        npred.assign(Le, 0);
        for (int a = 0; a < Le; ++a) {
            if (vstamp >= std::numeric_limits<int>::max() - 2) { std::fill(vis.begin(), vis.end(), 0); vstamp = 0; }
            ++vstamp;
            stk.clear(); stk.push_back(W[a]); vis[W[a]] = vstamp;
            while (!stk.empty()) {
                int x = stk.back(); stk.pop_back();
                int succ[2] = { c.md.op_next[x], inwin[x] >= 0 ? -1 : c.ms[x] };
                for (int y : succ) {
                    if (y < 0 || vis[y] == vstamp) continue;
                    if (c.st[y] > maxst) continue;
                    vis[y] = vstamp;
                    int b = inwin[y];
                    if (b >= 0 && !adj[(size_t)a * Le + b]) { adj[(size_t)a * Le + b] = 1; ++npred[b]; }
                    stk.push_back(y);
                }
            }
        }
        for (int o : W) inwin[o] = -1;
        bool changed = false;
        for (int attempt = 0; attempt < 5 && !changed; ++attempt) {
            cnt = npred; avail.clear(); order.clear();
            for (int b = 0; b < Le; ++b) if (cnt[b] == 0) avail.push_back(b);
            while (!avail.empty()) {
                int k = rng.below((int)avail.size());
                int b = avail[k]; avail[k] = avail.back(); avail.pop_back();
                order.push_back(b);
                for (int d = 0; d < Le; ++d) if (adj[(size_t)b * Le + d] && --cnt[d] == 0) avail.push_back(d);
            }
            if ((int)order.size() != Le) return false;
            for (int t = 0; t < Le; ++t) if (order[t] != t) { changed = true; break; }
        }
        if (!changed) return false;
        oldseg.assign(row.begin() + start, row.begin() + start + Le);
        for (int t = 0; t < Le; ++t) row[start + t] = c.job[W[order[t]]];
        if (c.check(cur)) return true;
        for (int t = 0; t < Le; ++t) row[start + t] = oldseg[t];
        c.check(cur);
        return false;
    }
public:
    MachineWindowReshuffle(const Model& m, int wl, double ws, bool cr) : c(m), wlen(wl), wscale(ws), crit(cr) {
        inwin.assign(std::max(1, c.N), -1); vis.assign(std::max(1, c.N), 0);
        for (int i = 0; i < m.m; ++i) if (m.machine_jobs[i].size() >= 2) rows.push_back(i);
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (!c.check(s)) return c.repair(s, rng);
        double str = std::max(1.0, strength);
        int L = std::max(2, wlen + (int)std::floor(std::sqrt(str)) - 1);
        int windows = std::max(1, (int)std::lround(std::sqrt(str) * wscale));
        Model::Solution cur = s;
        int done = 0, fixed = -1;
        for (int t = 0; t < windows * 3 + 3 && done < windows; ++t) {
            int mi, start, Le;
            if (!pick(cur, L, rng, fixed, mi, start, Le)) break;
            if (fixed < 0) fixed = mi;  // una sola máquina por perturbación
            if (Le < 2) continue;
            if (reshuffle(cur, mi, start, Le, rng)) ++done;
        }
        if (cur == s) { c.check(cur); c.any_swap(cur, rng); }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int wl = (int)params.get("window_len", 5);
    if (wl < 2) wl = 2;
    double ws = params.get("windows_scale", 0.7);
    bool cr = params.text("machine_pick", "critical") == "critical";
    return std::make_unique<MachineWindowReshuffle>(model, wl, ws, cr);
}
