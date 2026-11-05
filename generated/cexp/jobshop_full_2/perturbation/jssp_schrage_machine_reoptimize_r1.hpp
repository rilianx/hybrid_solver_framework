// COMPONENT: {"name": "jssp_schrage_machine_reoptimize", "slot": "perturbation", "params": {"machines_scale": {"type": "float", "range": [0.5, 3.0]}, "tail_noise": {"type": "float", "range": [0.0, 3.0]}, "critical_bias": {"type": "float", "range": [0.0, 1.0]}}}
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

class SchrageMachineReopt : public hsf::Perturbation<Model> {
    using Sol = Model::Solution;
    const Model& md;
    Core c; double scale, noise, cbias, avgp = 1.0;
    std::vector<int> topo, deg, path, cands, mlist, seq, oldrow;
    std::vector<long long> head, tail;
    std::vector<std::pair<long long,int>> byr;
public:
    SchrageMachineReopt(const Model& m, double sc, double nz, double cb) : md(m), c(m), scale(sc), noise(nz), cbias(cb) {
        int N = m.total_ops;
        topo.assign(N, 0); deg.assign(N, 0); head.assign(N, 0); tail.assign(N, 0);
        double sum = 0; for (int o = 0; o < N; ++o) sum += m.op_proc[o];
        avgp = N > 0 ? std::max(1.0, sum / N) : 1.0;
        for (int i = 0; i < m.m; ++i) if (m.machine_jobs[i].size() >= 2) mlist.push_back(i);
    }
    int pick(Rng& rng) {
        if (cbias > 0 && rng.uniform() < cbias) {
            c.critical(rng, path);
            cands.clear();
            for (int o : path) { int mi = c.mach[o]; if (mi < c.M && md.machine_jobs[mi].size() >= 2) cands.push_back(mi); }
            if (!cands.empty()) return cands[rng.below((int)cands.size())];
        }
        return mlist[rng.below((int)mlist.size())];
    }
    // 1 changed, 0 unchanged, -1 infeasible (reverted)
    int reopt(Sol& cur, int i, double amp, Rng& rng) {
        const int N = c.N;
        const int* PR = md.op_proc.data();
        int qh = 0, qt = 0;
        for (int o = 0; o < N; ++o) {
            deg[o] = (md.op_k[o] > 0 ? 1 : 0) + ((c.mp[o] >= 0 && c.mach[o] != i) ? 1 : 0);
            head[o] = 0;
            if (deg[o] == 0) topo[qt++] = o;
        }
        while (qh < qt) {
            int o = topo[qh++]; long long e = head[o] + PR[o];
            int a = md.op_next[o];
            if (a >= 0) { if (head[a] < e) head[a] = e; if (--deg[a] == 0) topo[qt++] = a; }
            if (c.mach[o] != i) { int b = c.ms[o]; if (b >= 0) { if (head[b] < e) head[b] = e; if (--deg[b] == 0) topo[qt++] = b; } }
        }
        if (qt != N) return 0;
        for (int k = N - 1; k >= 0; --k) {
            int o = topo[k]; long long t = 0;
            int a = md.op_next[o]; if (a >= 0) t = std::max(t, tail[a] + PR[a]);
            if (c.mach[o] != i) { int b = c.ms[o]; if (b >= 0) t = std::max(t, tail[b] + PR[b]); }
            tail[o] = t;
        }
        byr.clear();
        for (int j : cur[i]) { int o = md.op_of[j][i]; byr.push_back({head[o], o}); }
        if (byr.size() < 2) return 0;
        std::sort(byr.begin(), byr.end());
        std::priority_queue<std::pair<double,int>> heap;
        seq.clear();
        size_t k = 0; long long t = byr[0].first;
        while (seq.size() < byr.size()) {
            while (k < byr.size() && byr[k].first <= t) {
                int o = byr[k].second;
                heap.push({(double)tail[o] + amp * rng.uniform() - 1e-9 * (double)head[o], o});
                ++k;
            }
            if (heap.empty()) { t = byr[k].first; continue; }
            int o = heap.top().second; heap.pop();
            seq.push_back(c.job[o]);
            t += PR[o];
        }
        if (seq == cur[i]) return 0;
        oldrow = cur[i]; cur[i] = seq;
        if (c.check(cur)) return 1;
        cur[i] = oldrow; c.check(cur);
        return -1;
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol cur = s;
        if (!c.check(cur)) return c.repair(s, rng);
        if (mlist.empty()) return cur;
        double str = std::max(1.0, strength);
        int k = std::max(1, (int)std::lround(str * scale));
        k = std::min<int>(k, 2 * (int)mlist.size());
        double amp = noise * avgp * std::sqrt(str);
        for (int t = 0; t < k; ++t) {
            int i = pick(rng);
            int r = reopt(cur, i, amp, rng);
            if (r == -1) reopt(cur, i, 0.0, rng);
            else if (r == 0 && amp > 0) reopt(cur, i, 2.0 * amp, rng);
        }
        if (cur == s) { c.check(cur); c.any_swap(cur, rng); }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("machines_scale", 1.0);
    double nz = params.get("tail_noise", 0.5);
    double cb = params.get("critical_bias", 0.8);
    return std::make_unique<SchrageMachineReopt>(model, sc, nz, cb);
}
