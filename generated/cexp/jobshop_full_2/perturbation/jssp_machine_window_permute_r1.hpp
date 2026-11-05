// COMPONENT: {"name": "jssp_machine_window_permute", "slot": "perturbation", "params": {"win_scale": {"type": "float", "range": [1.0, 4.0]}, "n_windows": {"type": "int", "range": [1, 4]}, "machine_pick": {"type": "cat", "values": ["critical", "load", "uniform"]}, "window_op": {"type": "cat", "values": ["shuffle", "reverse"]}}}
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
        if (stamp > 2000000000) { std::fill(mark.begin(), mark.end(), 0); stamp = 0; }
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
        for (int t = 0; t < lim; ++t) { auto c = cand[rng.below((int)cand.size())]; if (try_swap(cur, c.first, c.second)) return true; }
        std::shuffle(cand.begin(), cand.end(), rng.g);
        for (auto& c : cand) if (try_swap(cur, c.first, c.second)) return true;
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

class MachineWindowPermute : public hsf::Perturbation<Model> {
    using Sol = Model::Solution;
    const Model& md;
    Core c; double wscale; int nwin, pickMode, opMode;
    std::vector<double> key, mcum;
    std::vector<int> path, cands, mlist, win, orig;
    std::vector<long long> starts;
public:
    MachineWindowPermute(const Model& m, double ws, int nw, int pm, int om)
        : md(m), c(m), wscale(ws), nwin(nw), pickMode(pm), opMode(om) {
        key.assign(m.total_ops, 0.0);
        double acc = 0;
        for (int i = 0; i < m.m; ++i) if (m.machine_jobs[i].size() >= 2) {
            mlist.push_back(i);
            double load = 0;
            for (int j : m.machine_jobs[i]) { int o = m.op_of[j][i]; if (o >= 0) load += m.op_proc[o]; }
            acc += std::max(1e-9, load);
            mcum.push_back(acc);
        }
    }
    int pick_machine(Rng& rng, int& anchor) {
        anchor = -1;
        if (pickMode == 0) {
            c.critical(rng, path);
            cands.clear();
            for (int o : path) { int mi = c.mach[o]; if (mi < c.M && md.machine_jobs[mi].size() >= 2) cands.push_back(o); }
            if (!cands.empty()) { int o = cands[rng.below((int)cands.size())]; anchor = c.pos[o]; return c.mach[o]; }
        } else if (pickMode == 1) {
            double r = rng.uniform() * mcum.back();
            int k = (int)(std::lower_bound(mcum.begin(), mcum.end(), r) - mcum.begin());
            if (k >= (int)mlist.size()) k = (int)mlist.size() - 1;
            return mlist[k];
        }
        return mlist[rng.below((int)mlist.size())];
    }
    void one_window(Sol& cur, double str, Rng& rng) {
        int anchor;
        int i = pick_machine(rng, anchor);
        int L = (int)cur[i].size();
        int w = (int)std::lround(1.0 + str * wscale);
        w = std::max(2, std::min(w, L));
        int a = anchor >= 0 ? anchor - rng.below(w) : rng.below(L - w + 1);
        a = std::max(0, std::min(a, L - w));
        for (int o = 0; o < c.N; ++o) key[o] = (double)c.st[o];
        starts.resize(w);
        orig.assign(cur[i].begin() + a, cur[i].begin() + a + w);
        for (int t = 0; t < w; ++t) starts[t] = c.st[md.op_of[orig[t]][i]];
        win = orig;
        if (opMode == 1) std::reverse(win.begin(), win.end());
        else {
            std::shuffle(win.begin(), win.end(), rng.g);
            if (win == orig) std::reverse(win.begin(), win.end());
        }
        std::copy(win.begin(), win.end(), cur[i].begin() + a);
        if (c.check(cur)) return;
        for (int t = 0; t < w; ++t) {
            int o = md.op_of[win[t]][i];
            key[o] = (double)starts[t] + 1e-6 * t;
        }
        cur = c.dispatch(key);
        c.check(cur);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol cur = s;
        if (!c.check(cur)) return c.repair(s, rng);
        if (mlist.empty()) return cur;
        double str = std::max(1.0, strength);
        for (int t = 0; t < nwin; ++t) one_window(cur, str, rng);
        if (cur == s) { c.check(cur); c.any_swap(cur, rng); }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ws = params.get("win_scale", 2.0);
    int nw = (int)params.get("n_windows", 1);
    if (nw < 1) nw = 1;
    std::string mp = params.text("machine_pick", "critical");
    int pm = mp == "load" ? 1 : (mp == "uniform" ? 2 : 0);
    int om = params.text("window_op", "shuffle") == "reverse" ? 1 : 0;
    return std::make_unique<MachineWindowPermute>(model, ws, nw, pm, om);
}
