// COMPONENT: {"name": "jssp_job_ruin_gt_rebuild", "slot": "perturbation", "params": {"jobs_scale": {"type": "float", "range": [0.5, 3.0]}, "delay_ratio": {"type": "float", "range": [0.0, 1.0]}, "critical_bias": {"type": "float", "range": [0.0, 1.0]}, "ruined_priority": {"type": "cat", "values": ["random", "first", "last"]}}}
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

class JobRuinGTRebuild : public hsf::Perturbation<Model> {
    using Sol = Model::Solution;
    const Model& md;
    Core c; double scale, delta, cbias; int rmode;
    std::vector<int> jfirst, nxt, path;
    std::vector<char> ruined;
    std::vector<long long> jready, mready, est;
    std::vector<double> prio;
public:
    JobRuinGTRebuild(const Model& m, double sc, double dl, double cb, int rm)
        : md(m), c(m), scale(sc), delta(dl), cbias(cb), rmode(rm) {
        int n = m.n;
        jfirst.assign(n, -1);
        for (int j = 0; j < n; ++j) if (!m.routes[j].empty()) {
            int mf = m.routes[j][0].first;
            if (mf >= 0 && mf < (int)m.op_of[j].size()) jfirst[j] = m.op_of[j][mf];
        }
        nxt.assign(n, -1); ruined.assign(n, 0); jready.assign(n, 0); est.assign(n, 0);
        mready.assign(std::max(1, m.m), 0); prio.assign(m.total_ops, 0.0);
    }
    Sol gt() {
        const int M = c.M, n = md.n;
        const int* PR = md.op_proc.data();
        Sol out(M);
        for (int i = 0; i < M; ++i) out[i].reserve(md.machine_jobs[i].size());
        int left = 0;
        for (int j = 0; j < n; ++j) { nxt[j] = jfirst[j]; jready[j] = 0; }
        for (int o = 0; o < c.N; ++o) (void)o;
        left = c.N;
        std::fill(mready.begin(), mready.end(), 0);
        const long long INF = std::numeric_limits<long long>::max();
        while (left > 0) {
            int bj = -1; long long bc = INF;
            for (int j = 0; j < n; ++j) {
                int o = nxt[j]; if (o < 0) continue;
                int mi = c.mach[o];
                long long e = jready[j];
                if (mi < M && mready[mi] > e) e = mready[mi];
                est[j] = e;
                long long cc = e + PR[o];
                if (cc < bc) { bc = cc; bj = j; }
            }
            if (bj < 0) break;
            int mi = c.mach[nxt[bj]];
            int pick = bj;
            if (mi < M) {
                long long smin = INF;
                for (int j = 0; j < n; ++j) { int o = nxt[j]; if (o >= 0 && c.mach[o] == mi && est[j] < smin) smin = est[j]; }
                double thr = (double)smin + delta * (double)(bc - smin);
                double bp = std::numeric_limits<double>::infinity();
                for (int j = 0; j < n; ++j) {
                    int o = nxt[j];
                    if (o < 0 || c.mach[o] != mi) continue;
                    if (est[j] < bc && (double)est[j] <= thr && prio[o] < bp) { bp = prio[o]; pick = j; }
                }
            }
            int po = nxt[pick];
            long long e = est[pick] + PR[po];
            jready[pick] = e;
            if (mi < M) { mready[mi] = e; out[mi].push_back(pick); }
            nxt[pick] = md.op_next[po];
            --left;
        }
        return out;
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol cur = s;
        if (!c.check(cur)) return c.repair(s, rng);
        const int n = md.n, N = c.N;
        if (n == 0 || N == 0) return cur;
        double str = std::max(1.0, strength);
        int k = std::max(1, std::min(n, (int)std::lround(str * scale)));
        double mk = (double)std::max(1LL, c.mk);
        c.critical(rng, path);
        for (int attempt = 0; attempt < 5; ++attempt) {
            std::fill(ruined.begin(), ruined.end(), 0);
            int chosen = 0, guard = 0;
            while (chosen < k && guard < 8 * n + 16) {
                ++guard;
                int j = (!path.empty() && rng.uniform() < cbias) ? c.job[path[rng.below((int)path.size())]] : rng.below(n);
                if (!ruined[j]) { ruined[j] = 1; ++chosen; }
            }
            for (int j = 0; j < n && chosen < k; ++j) if (!ruined[j]) { ruined[j] = 1; ++chosen; }
            for (int o = 0; o < N; ++o) {
                if (ruined[c.job[o]]) {
                    double u = rng.uniform();
                    prio[o] = rmode == 0 ? u * mk : (rmode == 1 ? -1.0 - u : mk + 1.0 + u);
                } else prio[o] = (double)c.st[o];
            }
            Sol out = gt();
            if (out != s) return out;
            k = std::min(n, k + 1);
        }
        c.check(cur);
        c.any_swap(cur, rng);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("jobs_scale", 1.0);
    double dl = params.get("delay_ratio", 0.7);
    double cb = params.get("critical_bias", 0.6);
    std::string rp = params.text("ruined_priority", "random");
    int rm = rp == "first" ? 1 : (rp == "last" ? 2 : 0);
    return std::make_unique<JobRuinGTRebuild>(model, sc, dl, cb, rm);
}
