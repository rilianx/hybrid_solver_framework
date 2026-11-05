// COMPONENT: {"name": "jssp_bottleneck_machine_schrage_resequence", "slot": "perturbation", "params": {"machines_scale": {"type": "float", "range": [0.5, 3.0]}, "noise": {"type": "float", "range": [0.0, 4.0]}, "pick": {"type": "cat", "values": ["critical", "load", "random"]}}}
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

class SchrageResequence : public hsf::Perturbation<Model> {
    JCore c; double scale, noise; int mode;
    std::vector<int> path, tpos, ops, order, eligible, tpv, idxv;
    std::vector<long long> rr, qq;
    std::vector<double> loads;
    std::vector<char> done;

    int pick(Rng& rng) {
        eligible.clear();
        for (int i = 0; i < c.M; ++i) if (c.seq[i].size() >= 2) eligible.push_back(i);
        if (eligible.empty()) return -1;
        if (mode == 0) {
            c.critical(path);
            if (!path.empty())
                for (int t = 0; t < 16; ++t) {
                    int o = path[rng.below((int)path.size())];
                    if (c.seq[c.opmach[o]].size() >= 2) return c.opmach[o];
                }
        } else if (mode == 1) {
            loads.assign(eligible.size(), 0.0); double tot = 0;
            for (size_t e = 0; e < eligible.size(); ++e) {
                for (int o : c.seq[eligible[e]]) loads[e] += c.proc[o] + 1e-9;
                tot += loads[e];
            }
            double r = rng.uniform() * tot;
            for (size_t e = 0; e < eligible.size(); ++e) { r -= loads[e]; if (r <= 0) return eligible[e]; }
            return eligible.back();
        }
        return eligible[rng.below((int)eligible.size())];
    }
    void reseq(int i, Rng& rng) {
        auto& sq = c.seq[i]; int L = (int)sq.size();
        if (L < 2) return;
        ops.assign(sq.begin(), sq.end());
        for (int o : ops) { c.mp[o] = -1; c.ms[o] = -1; }
        c.times();  // acyclic: arcs only removed
        for (size_t h = 0; h < c.topo.size(); ++h) tpos[c.topo[h]] = (int)h;
        rr.resize(L); qq.resize(L); tpv.resize(L);
        long long t = std::numeric_limits<long long>::max();
        for (int k = 0; k < L; ++k) {
            rr[k] = c.head[ops[k]]; qq[k] = c.tail[ops[k]]; tpv[k] = tpos[ops[k]];
            t = std::min(t, rr[k]);
        }
        done.assign(L, 0); order.clear();
        double amp = noise * c.avgp;
        while ((int)order.size() < L) {
            int best = -1; double bk = 0; long long minr = std::numeric_limits<long long>::max();
            for (int k = 0; k < L; ++k) {
                if (done[k]) continue;
                if (rr[k] <= t) {
                    double key = (double)qq[k] + (amp > 0 ? amp * (2.0 * rng.uniform() - 1.0) : 0.0);
                    if (best < 0 || key > bk || (key == bk && tpv[k] < tpv[best])) { best = k; bk = key; }
                } else minr = std::min(minr, rr[k]);
            }
            if (best < 0) { t = minr; continue; }
            done[best] = 1; order.push_back(ops[best]); t += c.proc[ops[best]];
        }
        for (int k = 0; k < L; ++k) sq[k] = order[k];
        c.links();
        if (!c.times()) {
            idxv.resize(L); std::iota(idxv.begin(), idxv.end(), 0);
            std::sort(idxv.begin(), idxv.end(), [&](int a, int b) {
                if (rr[a] != rr[b]) return rr[a] < rr[b];
                return tpv[a] < tpv[b];
            });
            for (int k = 0; k < L; ++k) sq[k] = ops[idxv[k]];
            c.links(); c.times();
        }
    }
public:
    SchrageResequence(const Model& m, double sc, double nz, int md_) : c(m), scale(sc), noise(nz), mode(md_) {
        tpos.assign(c.N, 0);
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (c.N == 0 || c.M == 0) return s;
        c.ensure(s);
        int k = (int)std::lround(scale * std::max(1.0, strength));
        k = std::max(1, std::min(k, c.M));
        for (int it = 0; it < k; ++it) { int i = pick(rng); if (i < 0) break; reseq(i, rng); }
        Model::Solution r = c.toSol();
        if (r == s && c.force_change(rng)) r = c.toSol();
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("machines_scale", 1.0);
    double nz = params.get("noise", 1.0);
    std::string p = params.text("pick", "critical");
    int mode = p == "load" ? 1 : (p == "random" ? 2 : 0);
    return std::make_unique<SchrageResequence>(model, sc, nz, mode);
}
