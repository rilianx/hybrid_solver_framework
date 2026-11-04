// COMPONENT: {"name": "jssp_noisy_start_redispatch", "slot": "perturbation", "params": {"op_fraction": {"type": "float", "range": [0.02, 0.3]}, "noise_scale": {"type": "float", "range": [0.5, 5.0]}, "focus": {"type": "cat", "values": ["all", "critical"]}}}
struct CoreB {
    using Sol = Model::Solution;
    const Model& md;
    int N, M;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit CoreB(const Model& m) : md(m), N(m.total_ops), M(m.m) {
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

class NoisyStartRedispatch : public hsf::Perturbation<Model> {
    CoreB c; double frac0, noise; bool crit;
    double avgp = 1.0;
    std::vector<double> key;
    std::vector<int> path;
public:
    NoisyStartRedispatch(const Model& m, double f, double ns, bool cr) : c(m), frac0(f), noise(ns), crit(cr) {
        double sum = 0; for (int o = 0; o < m.total_ops; ++o) sum += m.op_proc[o];
        avgp = m.total_ops > 0 ? std::max(1.0, sum / m.total_ops) : 1.0;
        key.assign(m.total_ops, 0.0);
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (!c.check(s)) return c.repair(s, rng);
        int N = c.N;
        if (N == 0) return s;
        double str = std::max(1.0, strength);
        double amp = noise * avgp * std::sqrt(str);
        double frac = std::min(1.0, frac0 * str);
        if (crit) c.critical(rng, path);
        for (int attempt = 0; attempt < 6; ++attempt) {
            for (int o = 0; o < N; ++o) key[o] = (double)c.st[o] + 1e-6 * c.pos[o];
            int touched = 0;
            if (crit && path.size() > 1) {
                for (int o : path) if (rng.uniform() < 0.5) { key[o] += (2.0 * rng.uniform() - 1.0) * amp; ++touched; }
                int extra = (int)std::lround(frac * 0.25 * N);
                for (int e = 0; e < extra; ++e) { int o = rng.below(N); key[o] += (2.0 * rng.uniform() - 1.0) * amp; ++touched; }
            } else {
                for (int o = 0; o < N; ++o) if (rng.uniform() < frac) { key[o] += (2.0 * rng.uniform() - 1.0) * amp; ++touched; }
            }
            if (touched == 0) { int o = rng.below(N); key[o] += (2.0 * rng.uniform() - 1.0) * amp; }
            Model::Solution out = c.dispatch(key);
            if (out != s) return out;
            amp *= 2.0; frac = std::min(1.0, frac * 2.0);
        }
        Model::Solution cur = s;
        c.check(cur);
        c.any_swap(cur, rng);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double f = params.get("op_fraction", 0.08);
    double ns = params.get("noise_scale", 1.5);
    bool cr = params.text("focus", "all") == "critical";
    return std::make_unique<NoisyStartRedispatch>(model, f, ns, cr);
}
