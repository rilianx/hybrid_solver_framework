// COMPONENT: {"name": "jssp_job_ruin_reinsert", "slot": "perturbation", "params": {"jobs_scale": {"type": "float", "range": [0.3, 2.0]}, "random_pos_prob": {"type": "float", "range": [0.0, 1.0]}, "noise_scale": {"type": "float", "range": [0.0, 4.0]}, "job_pick": {"type": "cat", "values": ["critical", "random"]}}}
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

class JobRuinReinsert : public hsf::Perturbation<Model> {
    Core c;
    double jscale, rprob, noise; bool crit; double avgp = 1.0;
    std::vector<int> jstart, jlen, anc, stk, path, jobs, jmark, pool;
    std::vector<long long> st0;
    int astamp = 0, jstamp = 0;

    void pick_jobs(int k, bool usecrit, Rng& rng) {
        const int n = c.md.n;
        jobs.clear(); ++jstamp;
        if (usecrit && !path.empty()) {
            pool.clear();
            for (int o : path) { int j = c.job[o]; if (jmark[j] != jstamp) { jmark[j] = jstamp; pool.push_back(j); } }
            std::shuffle(pool.begin(), pool.end(), rng.g);
            ++jstamp;
            for (int j : pool) { if ((int)jobs.size() >= k) break; jobs.push_back(j); jmark[j] = jstamp; }
        }
        int guard = 0;
        while ((int)jobs.size() < k && guard < 50 * n + 100) {
            int j = rng.below(n); ++guard;
            if (jmark[j] != jstamp) { jmark[j] = jstamp; jobs.push_back(j); }
        }
    }

    void reinsert(Model::Solution& cur, int j, double rp, double amp, Rng& rng) {
        const int n = c.md.n;
        for (int t = 0; t < jlen[j]; ++t) {
            int o = jstart[j] + t, mi = c.mach[o];
            if (mi >= c.M) continue;
            auto& row = cur[mi];
            int idx = (int)(std::find(row.begin(), row.end(), j) - row.begin());
            if (idx >= (int)row.size()) continue;
            row.erase(row.begin() + idx);
            int u = c.mp[o], w = c.ms[o];
            if (u >= 0) c.ms[u] = w;
            if (w >= 0) c.mp[w] = u;
            c.mp[o] = -1; c.ms[o] = -1;
        }
        for (int t = 0; t < jlen[j]; ++t) {
            int o = jstart[j] + t, mi = c.mach[o];
            if (mi >= c.M) continue;
            auto& row = cur[mi];
            const int* rowop = c.md.opflat.data() + (size_t)mi * n;
            int lo = 0;
            if (t > 0) {
                if (astamp >= std::numeric_limits<int>::max() - 2) { std::fill(anc.begin(), anc.end(), 0); astamp = 0; }
                ++astamp;
                stk.clear(); stk.push_back(o - 1); anc[o - 1] = astamp;
                while (!stk.empty()) {
                    int x = stk.back(); stk.pop_back();
                    if (c.md.op_k[x] > 0 && anc[x - 1] != astamp) { anc[x - 1] = astamp; stk.push_back(x - 1); }
                    int y = c.mp[x];
                    if (y >= 0 && anc[y] != astamp) { anc[y] = astamp; stk.push_back(y); }
                }
                for (int idx = (int)row.size() - 1; idx >= 0; --idx)
                    if (anc[rowop[row[idx]]] == astamp) { lo = idx + 1; break; }
            }
            int sz = (int)row.size(), p = sz;
            if (rng.uniform() < rp) p = lo + rng.below(sz - lo + 1);
            else {
                double target = (double)st0[o] + (2.0 * rng.uniform() - 1.0) * amp;
                for (int idx = lo; idx < sz; ++idx)
                    if ((double)st0[rowop[row[idx]]] > target) { p = idx; break; }
            }
            row.insert(row.begin() + p, j);
            int u = p > 0 ? rowop[row[p - 1]] : -1;
            int w = p + 1 < (int)row.size() ? rowop[row[p + 1]] : -1;
            c.mp[o] = u; c.ms[o] = w;
            if (u >= 0) c.ms[u] = o;
            if (w >= 0) c.mp[w] = o;
        }
    }
public:
    JobRuinReinsert(const Model& m, double js, double rp, double ns, bool cr)
        : c(m), jscale(js), rprob(rp), noise(ns), crit(cr) {
        jstart.assign(m.n, 0); jlen.assign(m.n, 0);
        for (int j = 0; j < m.n; ++j) if (!m.routes[j].empty()) {
            int f = m.routes[j][0].first;
            if (f >= 0 && f < (int)m.op_of[j].size() && m.op_of[j][f] >= 0) {
                jstart[j] = m.op_of[j][f]; jlen[j] = (int)m.routes[j].size();
            }
        }
        anc.assign(std::max(1, c.N), 0); jmark.assign(std::max(1, m.n), 0);
        double sum = 0; for (int o = 0; o < m.total_ops; ++o) sum += m.op_proc[o];
        avgp = m.total_ops > 0 ? std::max(1.0, sum / m.total_ops) : 1.0;
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (!c.check(s)) return c.repair(s, rng);
        const int n = c.md.n;
        if (n == 0 || c.N == 0) return s;
        double str = std::max(1.0, strength);
        st0 = c.st;
        if (crit) c.critical(rng, path); else path.clear();
        int k = std::max(1, std::min(n, (int)std::lround(str * jscale)));
        double amp = noise * avgp * std::sqrt(str);
        for (int attempt = 0; attempt < 4; ++attempt) {
            pick_jobs(k, crit && attempt == 0, rng);
            Model::Solution cur = s;
            c.check(cur);
            double rp = attempt == 0 ? rprob : 1.0;
            for (int j : jobs) reinsert(cur, j, rp, amp, rng);
            if (cur != s && c.check(cur)) return cur;
        }
        Model::Solution cur = s;
        c.check(cur);
        c.any_swap(cur, rng);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double js = params.get("jobs_scale", 0.8);
    double rp = params.get("random_pos_prob", 0.3);
    double ns = params.get("noise_scale", 1.0);
    bool cr = params.text("job_pick", "critical") == "critical";
    return std::make_unique<JobRuinReinsert>(model, js, rp, ns, cr);
}
