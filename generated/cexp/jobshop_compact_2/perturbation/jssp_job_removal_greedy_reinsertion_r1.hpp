// COMPONENT: {"name": "jssp_job_removal_greedy_reinsertion", "slot": "perturbation", "params": {"jobs_scale": {"type": "float", "range": [0.5, 3.0]}, "rcl_alpha": {"type": "float", "range": [0.0, 1.0]}, "focus": {"type": "cat", "values": ["critical", "random"]}}}
struct JCore {
    using Sol = Model::Solution;
    const Model& md;
    int N, M, NJ;
    std::vector<int> opjob, opmach, jpred, jsucc, proc, jfirst;
    std::vector<std::vector<int>> seq;
    std::vector<int> mp, ms, pos, indeg, topo, mark, nxt, cand;
    std::vector<char> absent;
    std::vector<long long> head, tail;
    std::vector<double> prio;
    long long mk = 0; int endop = -1; int stamp = 0;
    double avgp = 1.0;

    explicit JCore(const Model& m) : md(m), N(m.total_ops), M(m.m), NJ(m.n) {
        opjob.assign(N, -1); opmach.assign(N, 0); jpred.assign(N, -1); jsucc.assign(N, -1);
        proc.assign(N, 0); jfirst.assign(NJ, -1);
        mp.assign(N, -1); ms.assign(N, -1); pos.assign(N, 0); indeg.assign(N, 0);
        topo.reserve(N); mark.assign(N, 0); absent.assign(N, 0); head.assign(N, 0); tail.assign(N, 0);
        seq.assign(M, {});
        long long tot = 0;
        for (int j = 0; j < NJ; ++j) {
            int prev = -1;
            for (size_t k = 0; k < m.routes[j].size(); ++k) {
                int mc = m.routes[j][k].first;
                int o = m.op_of[j][mc];
                if (o < 0) continue;
                opjob[o] = j; opmach[o] = mc; proc[o] = m.routes[j][k].second; tot += proc[o];
                jpred[o] = prev;
                if (prev >= 0) jsucc[prev] = o; else jfirst[j] = o;
                prev = o;
            }
        }
        avgp = N > 0 ? std::max(1.0, (double)tot / N) : 1.0;
    }
    void load(const Sol& s) {
        ++stamp;
        for (int i = 0; i < M; ++i) {
            seq[i].clear();
            if (i < (int)s.size())
                for (int j : s[i]) {
                    if (j < 0 || j >= NJ) continue;
                    int o = md.op_of[j][i];
                    if (o < 0 || mark[o] == stamp) continue;
                    mark[o] = stamp; seq[i].push_back(o);
                }
        }
        for (int o = 0; o < N; ++o) if (mark[o] != stamp) seq[opmach[o]].push_back(o);
        std::fill(absent.begin(), absent.end(), 0);
    }
    void links() {
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < M; ++i) {
            int pr = -1;
            for (size_t k = 0; k < seq[i].size(); ++k) {
                int o = seq[i][k]; pos[o] = (int)k; mp[o] = pr;
                if (pr >= 0) ms[pr] = o;
                pr = o;
            }
        }
    }
    bool times() {
        topo.clear(); int present = 0;
        for (int o = 0; o < N; ++o) {
            if (absent[o]) continue;
            ++present;
            indeg[o] = (jpred[o] >= 0 && !absent[jpred[o]]) + (mp[o] >= 0);
            head[o] = 0;
            if (!indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h]; long long f = head[o] + proc[o];
            int a = jsucc[o];
            if (a >= 0 && !absent[a]) { if (head[a] < f) head[a] = f; if (--indeg[a] == 0) topo.push_back(a); }
            int b = ms[o];
            if (b >= 0) { if (head[b] < f) head[b] = f; if (--indeg[b] == 0) topo.push_back(b); }
        }
        if ((int)topo.size() != present) return false;
        mk = 0; endop = -1;
        for (int h = (int)topo.size() - 1; h >= 0; --h) {
            int o = topo[h]; long long t = 0;
            int a = jsucc[o]; if (a >= 0 && !absent[a]) t = std::max(t, tail[a] + proc[a]);
            int b = ms[o]; if (b >= 0) t = std::max(t, tail[b] + proc[b]);
            tail[o] = t;
            long long f = head[o] + proc[o];
            if (endop < 0 || f > mk) { mk = f; endop = o; }
        }
        return true;
    }
    void critical(std::vector<int>& path) {
        path.clear(); int o = endop;
        while (o >= 0) {
            path.push_back(o);
            int a = jpred[o], b = mp[o], nx = -1;
            if (b >= 0 && head[b] + proc[b] == head[o]) nx = b;
            else if (a >= 0 && !absent[a] && head[a] + proc[a] == head[o]) nx = a;
            o = nx;
        }
    }
    Sol toSol() const {
        Sol r(M);
        for (int i = 0; i < M; ++i) { r[i].reserve(seq[i].size()); for (int o : seq[i]) r[i].push_back(opjob[o]); }
        return r;
    }
    void rebuild_by_priority(const std::vector<double>& pr) {
        for (int i = 0; i < M; ++i) seq[i].clear();
        nxt = jfirst;
        for (int step = 0; step < N; ++step) {
            int bj = -1; double bv = std::numeric_limits<double>::infinity();
            for (int j = 0; j < NJ; ++j) { int o = nxt[j]; if (o >= 0 && pr[o] < bv) { bv = pr[o]; bj = j; } }
            if (bj < 0) break;
            int o = nxt[bj]; seq[opmach[o]].push_back(o); nxt[bj] = jsucc[o];
        }
    }
    bool ensure(const Sol& s) {
        load(s); links();
        if (times()) return true;
        prio.assign(N, 0.0);
        for (int i = 0; i < M; ++i) {
            double L = (double)std::max<size_t>(1, seq[i].size());
            for (size_t k = 0; k < seq[i].size(); ++k) prio[seq[i][k]] = (k + 0.5) / L;
        }
        rebuild_by_priority(prio); links(); times();
        return false;
    }
    bool try_adj(int u) {
        int i = opmach[u], k = pos[u];
        if (k + 1 >= (int)seq[i].size()) return false;
        std::swap(seq[i][k], seq[i][k + 1]); links();
        if (times()) return true;
        std::swap(seq[i][k], seq[i][k + 1]); links(); times();
        return false;
    }
    bool force_change(Rng& rng) {
        cand.clear();
        for (int o = 0; o < N; ++o) { int b = ms[o]; if (b >= 0 && head[o] + proc[o] == head[b]) cand.push_back(o); }
        int C = (int)cand.size();
        for (int t = 0; t < C && t < 8; ++t) {
            int idx = t + rng.below(C - t); std::swap(cand[t], cand[idx]);
            if (try_adj(cand[t])) return true;
        }
        cand.clear();
        for (int o = 0; o < N; ++o) if (ms[o] >= 0) cand.push_back(o);
        C = (int)cand.size();
        if (C == 0) return false;
        int st0 = rng.below(C);
        for (int t = 0; t < C; ++t) if (try_adj(cand[(st0 + t) % C])) return true;
        return false;
    }
};

class JobReinsertion : public hsf::Perturbation<Model> {
    JCore c; double scale, alpha; bool crit;
    std::vector<int> path, bfs, jo;
    std::vector<long long> rem, cost;
    std::vector<char> jmark;

    int pick_job(Rng& rng) {
        if (crit) {
            c.critical(path);
            for (int t = 0; t < 8 && !path.empty(); ++t) {
                int j = c.opjob[path[rng.below((int)path.size())]];
                if (j >= 0 && !jmark[j]) return j;
            }
        }
        int st0 = rng.below(c.NJ);
        for (int t = 0; t < c.NJ; ++t) { int j = (st0 + t) % c.NJ; if (!jmark[j]) return j; }
        return -1;
    }
    void reinsert(int j, Rng& rng) {
        jo.clear();
        for (int o = c.jfirst[j]; o >= 0; o = c.jsucc[o]) jo.push_back(o);
        int K = (int)jo.size();
        if (K == 0) return;
        rem.assign(K, 0);
        for (int k = K - 2; k >= 0; --k) rem[k] = rem[k + 1] + c.proc[jo[k + 1]];
        for (int o : jo) {
            auto& sq = c.seq[c.opmach[o]];
            auto it = std::find(sq.begin(), sq.end(), o);
            if (it != sq.end()) sq.erase(it);
            c.absent[o] = 1;
        }
        for (int k = 0; k < K; ++k) {
            int v = jo[k];
            c.links(); c.times();
            int i = c.opmach[v]; auto& sq = c.seq[i]; int L = (int)sq.size();
            int lend = 0; long long rp = 0; int pv = c.jpred[v];
            if (pv >= 0) {
                rp = c.head[pv] + c.proc[pv];
                ++c.stamp; bfs.clear(); bfs.push_back(pv); c.mark[pv] = c.stamp;
                for (size_t h = 0; h < bfs.size(); ++h) {
                    int o = bfs[h];
                    int u = c.jpred[o];
                    if (u >= 0 && !c.absent[u] && c.mark[u] != c.stamp) { c.mark[u] = c.stamp; bfs.push_back(u); }
                    u = c.mp[o];
                    if (u >= 0 && c.mark[u] != c.stamp) { c.mark[u] = c.stamp; bfs.push_back(u); }
                }
                for (int idx = L - 1; idx >= 0; --idx) if (c.mark[sq[idx]] == c.stamp) { lend = idx + 1; break; }
            }
            cost.assign(L + 1, 0);
            long long best = std::numeric_limits<long long>::max(), worst = std::numeric_limits<long long>::min();
            for (int p = lend; p <= L; ++p) {
                long long ra = p > 0 ? c.head[sq[p - 1]] + c.proc[sq[p - 1]] : 0;
                long long qb = p < L ? c.proc[sq[p]] + c.tail[sq[p]] : 0;
                long long e = std::max(rp, ra) + c.proc[v] + std::max(qb, rem[k]);
                cost[p] = e; best = std::min(best, e); worst = std::max(worst, e);
            }
            double thr = (double)best + alpha * (double)(worst - best) + 1e-9;
            int cnt = 0, chosen = lend;
            for (int p = lend; p <= L; ++p)
                if ((double)cost[p] <= thr) { ++cnt; if (rng.below(cnt) == 0) chosen = p; }
            sq.insert(sq.begin() + chosen, v);
            c.absent[v] = 0;
        }
        c.links(); c.times();
    }
public:
    JobReinsertion(const Model& m, double sc, double al, bool cr) : c(m), scale(sc), alpha(al), crit(cr) {}
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (c.N == 0 || c.M == 0 || c.NJ == 0) return s;
        c.ensure(s);
        jmark.assign(c.NJ, 0);
        int k = (int)std::lround(scale * std::max(1.0, strength));
        k = std::max(1, std::min(k, c.NJ));
        for (int it = 0; it < k; ++it) {
            int j = pick_job(rng);
            if (j < 0) break;
            jmark[j] = 1;
            reinsert(j, rng);
        }
        if (!c.times()) c.ensure(s);
        Model::Solution r = c.toSol();
        if (r == s && c.force_change(rng)) r = c.toSol();
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("jobs_scale", 1.0);
    double al = params.get("rcl_alpha", 0.3);
    bool cr = params.text("focus", "critical") == "critical";
    return std::make_unique<JobReinsertion>(model, sc, al, cr);
}
