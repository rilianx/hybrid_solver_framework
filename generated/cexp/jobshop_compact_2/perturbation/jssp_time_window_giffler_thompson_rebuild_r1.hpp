// COMPONENT: {"name": "jssp_time_window_giffler_thompson_rebuild", "slot": "perturbation", "params": {"window_frac": {"type": "float", "range": [0.03, 0.5]}, "rule": {"type": "cat", "values": ["random", "mwr", "spt"]}}}
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

class WindowGifflerThompson : public hsf::Perturbation<Model> {
    JCore c; double wfrac; int rule;
    std::vector<int> nx, conf;
    std::vector<long long> jr, mr, remw, ces;
    std::vector<double> w;
    std::vector<std::vector<int>> ns;
public:
    WindowGifflerThompson(const Model& m, double wf, int r) : c(m), wfrac(wf), rule(r) {
        remw.assign(c.N, 0);
        std::vector<int> tmp;
        for (int j = 0; j < c.NJ; ++j) {
            tmp.clear();
            for (int o = c.jfirst[j]; o >= 0; o = c.jsucc[o]) tmp.push_back(o);
            long long acc = 0;
            for (int k = (int)tmp.size() - 1; k >= 0; --k) { acc += c.proc[tmp[k]]; remw[tmp[k]] = acc; }
        }
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (c.N == 0 || c.M == 0 || c.NJ == 0) return s;
        c.ensure(s);  // c.pos = rank in the (feasible) reference order
        double mk = (double)c.mk;
        double W = std::min(1.0, wfrac * std::max(1.0, strength)) * mk;
        double t0 = rng.uniform() * std::max(0.0, mk - W), t1 = t0 + W;
        ns.assign(c.M, {});
        for (int i = 0; i < c.M; ++i) ns[i].reserve(c.seq[i].size());
        nx = c.jfirst; jr.assign(c.NJ, 0); mr.assign(c.M, 0);
        for (int step = 0; step < c.N; ++step) {
            long long bec = std::numeric_limits<long long>::max(); int bo = -1;
            for (int j = 0; j < c.NJ; ++j) {
                int o = nx[j]; if (o < 0) continue;
                long long es = std::max(jr[j], mr[c.opmach[o]]);
                long long ec = es + c.proc[o];
                if (ec < bec) { bec = ec; bo = o; }
            }
            if (bo < 0) break;
            int mm = c.opmach[bo];
            conf.clear(); ces.clear();
            long long mines = std::numeric_limits<long long>::max();
            for (int j = 0; j < c.NJ; ++j) {
                int o = nx[j]; if (o < 0 || c.opmach[o] != mm) continue;
                long long es = std::max(jr[j], mr[mm]);
                if (es < bec || o == bo) { conf.push_back(o); ces.push_back(es); mines = std::min(mines, es); }
            }
            int ch = conf[0];
            if (conf.size() > 1 && (double)mines >= t0 && (double)mines <= t1) {
                w.resize(conf.size()); double tot = 0;
                for (size_t q = 0; q < conf.size(); ++q) {
                    int o = conf[q];
                    double wt = rule == 1 ? (double)remw[o] + 1e-9 : (rule == 2 ? 1.0 / (1.0 + c.proc[o]) : 1.0);
                    w[q] = wt; tot += wt;
                }
                double r = rng.uniform() * tot; ch = conf.back();
                for (size_t q = 0; q < conf.size(); ++q) { r -= w[q]; if (r <= 0) { ch = conf[q]; break; } }
            } else {
                for (int o : conf) if (c.pos[o] < c.pos[ch]) ch = o;
            }
            int jj = c.opjob[ch];
            long long f = std::max(jr[jj], mr[mm]) + c.proc[ch];
            jr[jj] = f; mr[mm] = f;
            ns[mm].push_back(ch);
            nx[jj] = c.jsucc[ch];
        }
        c.seq.swap(ns);
        c.links();
        c.times();
        Model::Solution r = c.toSol();
        if (r == s && c.force_change(rng)) r = c.toSol();
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double wf = params.get("window_frac", 0.12);
    std::string r = params.text("rule", "random");
    int rule = r == "mwr" ? 1 : (r == "spt" ? 2 : 0);
    return std::make_unique<WindowGifflerThompson>(model, wf, rule);
}
