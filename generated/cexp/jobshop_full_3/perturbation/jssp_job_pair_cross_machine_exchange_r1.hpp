// COMPONENT: {"name": "jssp_job_pair_cross_machine_exchange", "slot": "perturbation", "params": {"pair_radius": {"type": "int", "range": [1, 8]}, "machine_frac": {"type": "float", "range": [0.05, 1.0]}, "seed": {"type": "cat", "values": ["critical", "uniform"]}}}
struct CoreP {
    using Sol = Model::Solution;
    const Model& md;
    int N, M, J;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    std::vector<std::pair<double,int>> heap;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit CoreP(const Model& m) : md(m), N(m.total_ops), M(m.m), J(m.n) {
        job.assign(N, 0); mach.assign(N, M);
        for (int j = 0; j < J; ++j) for (auto& pr : m.routes[j]) {
            int mi = pr.first;
            if (mi < 0 || mi >= (int)m.op_of[j].size()) continue;
            int o = m.op_of[j][mi];
            if (o >= 0) { job[o] = j; mach[o] = mi; }
        }
        mp.assign(N, -1); ms.assign(N, -1); pos.assign(N, 0); indeg.assign(N, 0); q.assign(N, 0);
        st.assign(N, 0); mark.assign(std::max(1, J), 0);
    }
    bool load(const Sol& s) {
        if ((int)s.size() != M) return false;
        if (stamp > std::numeric_limits<int>::max() - 4 * (M + 2)) { std::fill(mark.begin(), mark.end(), 0); stamp = 0; }
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < M; ++i) {
            if (s[i].size() != md.machine_jobs[i].size()) return false;
            ++stamp; int prev = -1;
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= J || i >= (int)md.op_of[j].size()) return false;
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
        heap.clear();
        auto cmp = std::greater<std::pair<double,int>>();
        for (int o = 0; o < N; ++o) if (md.op_k[o] == 0) { heap.push_back({key[o], o}); std::push_heap(heap.begin(), heap.end(), cmp); }
        while (!heap.empty()) {
            std::pop_heap(heap.begin(), heap.end(), cmp);
            int o = heap.back().second; heap.pop_back();
            if (mach[o] < M) out[mach[o]].push_back(job[o]);
            int nx = md.op_next[o];
            if (nx >= 0) { heap.push_back({key[nx], nx}); std::push_heap(heap.begin(), heap.end(), cmp); }
        }
        return out;
    }
    Sol repair(const Sol& s, Rng& rng) {
        std::vector<double> key(N);
        for (int o = 0; o < N; ++o) key[o] = rng.uniform() * (double)std::max(1, J);
        for (int i = 0; i < std::min<int>(M, (int)s.size()); ++i)
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= J || i >= (int)md.op_of[j].size()) continue;
                int op = md.op_of[j][i]; if (op >= 0) key[op] = idx + 0.5 * rng.uniform();
            }
        return dispatch(key);
    }
};

class JobPairCrossMachineExchange : public hsf::Perturbation<Model> {
    CoreP c; int radius; double frac; bool critSeed;
    std::vector<int> elig, path, critops, shared;
public:
    JobPairCrossMachineExchange(const Model& m, int r, double f, bool cs) : c(m), radius(r), frac(f), critSeed(cs) {
        for (int i = 0; i < m.m; ++i) if (m.machine_jobs[i].size() >= 2) elig.push_back(i);
    }

    void pick_pair(const Model::Solution& cur, Rng& rng, int& j1, int& j2, int& seedm) {
        int mi = -1, p = -1;
        if (critSeed) {
            c.critical(rng, path);
            critops.clear();
            for (int o : path) if (c.mach[o] < c.M && cur[c.mach[o]].size() >= 2) critops.push_back(o);
            if (!critops.empty()) { int o = critops[rng.below((int)critops.size())]; mi = c.mach[o]; p = c.pos[o]; }
        }
        if (mi < 0) { mi = elig[rng.below((int)elig.size())]; p = rng.below((int)cur[mi].size()); }
        int L = (int)cur[mi].size();
        int d = 1 + rng.below(std::max(1, radius));
        int qq = rng.below(2) ? p + d : p - d;
        if (qq < 0 || qq >= L) qq = (qq < 0) ? p + d : p - d;
        qq = std::max(0, std::min(L - 1, qq));
        if (qq == p) qq = (p + 1 < L) ? p + 1 : p - 1;
        j1 = cur[mi][p]; j2 = cur[mi][qq]; seedm = mi;
    }

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        const Model& md = c.md;
        Model::Solution cur = s;
        if (!c.check(cur)) return c.repair(s, rng);
        if (elig.empty()) return s;
        double str = std::max(1.0, strength);
        for (int attempt = 0; attempt < 6; ++attempt) {
            int j1, j2, seedm;
            pick_pair(cur, rng, j1, j2, seedm);
            if (j1 == j2) continue;
            shared.clear();
            for (int i = 0; i < c.M; ++i) {
                if (i == seedm) continue;
                if (i >= (int)md.op_of[j1].size() || i >= (int)md.op_of[j2].size()) continue;
                if (md.op_of[j1][i] >= 0 && md.op_of[j2][i] >= 0) shared.push_back(i);
            }
            std::shuffle(shared.begin(), shared.end(), rng.g);
            shared.insert(shared.begin(), seedm);
            int S = (int)shared.size();
            int target = (int)std::lround(frac * S * std::sqrt(str));
            target = std::max(1, std::min(S, target));
            int succ = 0;
            for (int t = 0; t < S && succ < target; ++t) {
                int i = shared[t];
                int pa = c.pos[md.op_of[j1][i]], pb = c.pos[md.op_of[j2][i]];
                std::swap(cur[i][pa], cur[i][pb]);
                if (c.check(cur)) { ++succ; }
                else { std::swap(cur[i][pa], cur[i][pb]); c.check(cur); }
            }
            if (succ > 0) break;
        }
        if (cur == s) { c.check(cur); c.any_swap(cur, rng); }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int r = (int)params.get("pair_radius", 3);
    if (r < 1) r = 1;
    double f = params.get("machine_frac", 0.3);
    bool cs = params.text("seed", "critical") == "critical";
    return std::make_unique<JobPairCrossMachineExchange>(model, r, f, cs);
}
