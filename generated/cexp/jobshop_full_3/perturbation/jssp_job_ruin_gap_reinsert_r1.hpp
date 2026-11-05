// COMPONENT: {"name": "jssp_job_ruin_gap_reinsert", "slot": "perturbation", "params": {"jobs_base": {"type": "int", "range": [1, 6]}, "greed": {"type": "float", "range": [0.0, 1.0]}, "select": {"type": "cat", "values": ["random", "critical"]}}}
struct CoreR {
    using Sol = Model::Solution;
    const Model& md;
    int N, M, J;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    std::vector<std::pair<double,int>> heap;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit CoreR(const Model& m) : md(m), N(m.total_ops), M(m.m), J(m.n) {
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

class JobRuinGapReinsert : public hsf::Perturbation<Model> {
    CoreR c; int base; double greed; bool critSel;
    std::vector<char> removed;
    std::vector<int> pmp, pms, pindeg, pq, pidx, jobs, path;
    std::vector<long long> pst;
    std::vector<std::vector<int>> rows;
    std::vector<double> key;
public:
    JobRuinGapReinsert(const Model& m, int b, double g, bool cs) : c(m), base(b), greed(g), critSel(cs) {
        removed.assign(std::max(1, m.n), 0);
        int N = m.total_ops;
        pmp.assign(N, -1); pms.assign(N, -1); pindeg.assign(N, 0); pq.assign(N, 0); pidx.assign(N, 0);
        pst.assign(N, 0); key.assign(N, 0.0); rows.assign(m.m, {});
    }

    Model::Solution rebuild(const Model::Solution& s, int k, double gr, Rng& rng) {
        const Model& md = c.md;
        int N = c.N, M = c.M, J = c.J;
        std::fill(removed.begin(), removed.end(), 0);
        jobs.clear();
        if (critSel) {
            c.critical(rng, path);
            for (int o : path) {
                if ((int)jobs.size() >= k) break;
                if (rng.uniform() < 0.5) { int j = c.job[o]; if (!removed[j]) { removed[j] = 1; jobs.push_back(j); } }
            }
        }
        int guard = 0;
        while ((int)jobs.size() < k && guard < 20 * J + 20) {
            int j = rng.below(J); ++guard;
            if (!removed[j]) { removed[j] = 1; jobs.push_back(j); }
        }
        std::shuffle(jobs.begin(), jobs.end(), rng.g);
        // partial graph without removed jobs
        std::fill(pmp.begin(), pmp.end(), -1); std::fill(pms.begin(), pms.end(), -1);
        for (int i = 0; i < M; ++i) {
            rows[i].clear();
            for (int j : s[i]) if (!removed[j]) {
                int o = md.op_of[j][i];
                if (!rows[i].empty()) { int pr = rows[i].back(); pmp[o] = pr; pms[pr] = o; }
                pidx[o] = (int)rows[i].size();
                rows[i].push_back(o);
            }
        }
        int qh = 0, qt = 0;
        for (int o = 0; o < N; ++o) {
            pst[o] = 0;
            if (removed[c.job[o]]) { pindeg[o] = -1; continue; }
            pindeg[o] = (md.op_k[o] > 0 ? 1 : 0) + (pmp[o] >= 0 ? 1 : 0);
            if (pindeg[o] == 0) pq[qt++] = o;
        }
        while (qh < qt) {
            int o = pq[qh++]; long long e = pst[o] + md.op_proc[o];
            int a = md.op_next[o];
            if (a >= 0) { if (pst[a] < e) pst[a] = e; if (--pindeg[a] == 0) pq[qt++] = a; }
            int b = pms[o];
            if (b >= 0) { if (pst[b] < e) pst[b] = e; if (--pindeg[b] == 0) pq[qt++] = b; }
        }
        for (int o = 0; o < N; ++o) if (!removed[c.job[o]]) key[o] = (double)pst[o] + 1e-6 * pidx[o];
        // reinsert removed jobs op by op
        for (int j : jobs) {
            double r = 0.0, lastKey = -1e300;
            for (auto& pr : md.routes[j]) {
                int mi = pr.first;
                if (mi < 0 || mi >= (int)md.op_of[j].size()) continue;
                int o = md.op_of[j][mi];
                if (o < 0) continue;
                double p = (double)md.op_proc[o];
                double kk, stt;
                if (mi >= M) { stt = r; kk = r; }
                else {
                    auto& row = rows[mi];
                    int L = (int)row.size();
                    int choice = -1;
                    stt = r;
                    if (rng.uniform() < gr) {
                        double best = 1e300;
                        for (int pp = 0; pp <= L; ++pp) {
                            double prevEnd = pp > 0 ? (double)(pst[row[pp - 1]] + md.op_proc[row[pp - 1]]) : 0.0;
                            if (choice >= 0 && prevEnd >= best) break;
                            double t0 = std::max(r, prevEnd);
                            if (pp < L && t0 + p > (double)pst[row[pp]]) continue;
                            if (t0 < best) { best = t0; choice = pp; }
                        }
                        stt = best;
                    } else {
                        choice = rng.below(L + 1);
                        double prevEnd = choice > 0 ? (double)(pst[row[choice - 1]] + md.op_proc[row[choice - 1]]) : 0.0;
                        stt = std::max(r, prevEnd);
                    }
                    kk = stt;
                    if (choice >= 0 && choice < L) kk = std::min(kk, key[row[choice]] - 1e-4);
                }
                if (kk <= lastKey) kk = lastKey + 1e-7;
                key[o] = kk; lastKey = kk;
                r = stt + p;
            }
        }
        return c.dispatch(key);
    }

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (!c.check(s)) return c.repair(s, rng);
        if (c.N == 0 || c.J == 0) return s;
        double str = std::max(1.0, strength);
        int k = (int)std::lround(base * std::sqrt(str));
        k = std::max(1, std::min(c.J, k));
        double gr = greed;
        for (int attempt = 0; attempt < 5; ++attempt) {
            Model::Solution out = rebuild(s, k, gr, rng);
            if (out != s) return out;
            gr *= 0.5;
            k = std::min(c.J, k + 1);
        }
        Model::Solution cur = s;
        c.check(cur);
        c.any_swap(cur, rng);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int b = (int)params.get("jobs_base", 2);
    if (b < 1) b = 1;
    double g = params.get("greed", 0.7);
    bool cs = params.text("select", "critical") == "critical";
    return std::make_unique<JobRuinGapReinsert>(model, b, g, cs);
}
