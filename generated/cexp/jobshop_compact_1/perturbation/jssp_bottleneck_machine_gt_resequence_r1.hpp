// COMPONENT: {"name": "jssp_bottleneck_machine_gt_resequence", "slot": "perturbation", "params": {"machines_scale": {"type": "float", "range": [0.3, 2.0]}, "select_mode": {"type": "cat", "values": ["critical", "load", "random"]}, "greedy_prob": {"type": "float", "range": [0.0, 1.0]}}}
struct JCoreA {
    using Sol = Model::Solution;
    const Model& md;
    int n, m, N;
    std::vector<int> opJob, opMach, opPrev, opNext, opProc;
    std::vector<int> mp, ms, indeg, topo, pos;
    std::vector<long long> head, tail;
    explicit JCoreA(const Model& mod) : md(mod), n(mod.n), m(mod.m), N(mod.total_ops) {
        opJob.assign(N, -1); opMach.assign(N, -1); opPrev.assign(N, -1); opNext.assign(N, -1); opProc.assign(N, 0);
        for (int j = 0; j < n; ++j) {
            int prev = -1;
            for (const auto& pr : md.routes[j]) {
                int o = md.op_of[j][pr.first];
                opJob[o] = j; opMach[o] = pr.first; opProc[o] = pr.second; opPrev[o] = prev;
                if (prev >= 0) opNext[prev] = o;
                prev = o;
            }
        }
        mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0); pos.assign(N, 0);
        head.assign(N, 0); tail.assign(N, 0); topo.reserve(N);
    }
    bool load(const Sol& s) {
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        std::fill(indeg.begin(), indeg.end(), 0);
        if ((int)s.size() != m) return false;
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            int prev = -1;
            for (int j : s[i]) {
                if (j < 0 || j >= n) return false;
                int o = md.op_of[j][i];
                if (o < 0 || indeg[o]) return false;
                indeg[o] = 1;
                mp[o] = prev; if (prev >= 0) ms[prev] = o; prev = o; ++cnt;
            }
        }
        return cnt == N;
    }
    bool times() {
        topo.clear();
        for (int o = 0; o < N; ++o) {
            indeg[o] = (opPrev[o] >= 0) + (mp[o] >= 0);
            head[o] = 0;
            if (!indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h]; long long e = head[o] + opProc[o];
            int a = opNext[o];
            if (a >= 0) { if (head[a] < e) head[a] = e; if (--indeg[a] == 0) topo.push_back(a); }
            a = ms[o];
            if (a >= 0) { if (head[a] < e) head[a] = e; if (--indeg[a] == 0) topo.push_back(a); }
        }
        if ((int)topo.size() != N) return false;
        for (int t = 0; t < N; ++t) pos[topo[t]] = t;
        return true;
    }
    long long tails() {
        long long mk = 0;
        for (int t = N - 1; t >= 0; --t) {
            int o = topo[t]; long long q = 0;
            int a = opNext[o]; if (a >= 0) q = std::max(q, (long long)opProc[a] + tail[a]);
            a = ms[o]; if (a >= 0) q = std::max(q, (long long)opProc[a] + tail[a]);
            tail[o] = q; mk = std::max(mk, head[o] + opProc[o] + q);
        }
        return mk;
    }
    // swap of the machine arc with minimal topological span: always acyclic
    bool minspan_swap(Sol& cur) const {
        int best = std::numeric_limits<int>::max(), bi = -1, bt = -1;
        for (int i = 0; i < m; ++i)
            for (int t = 0; t + 1 < (int)cur[i].size(); ++t) {
                int u = md.op_of[cur[i][t]][i], v = md.op_of[cur[i][t + 1]][i];
                int d = pos[v] - pos[u];
                if (d < best) { best = d; bi = i; bt = t; }
            }
        if (bi < 0) return false;
        std::swap(cur[bi][bt], cur[bi][bt + 1]);
        return true;
    }
};

static int pick_weighted_a(const std::vector<double>& w, Rng& rng) {
    double tot = 0; for (double x : w) tot += x;
    if (tot <= 0) return -1;
    double x = rng.uniform() * tot; int last = -1;
    for (int i = 0; i < (int)w.size(); ++i) {
        if (w[i] <= 0) continue;
        last = i; x -= w[i];
        if (x < 0) return i;
    }
    return last;
}

class BottleneckMachineGtResequence : public hsf::Perturbation<Model> {
    JCoreA g; double scale; int mode; double greedy;
    std::vector<char> freeM;
    std::vector<double> w, tmp;
    std::vector<int> nk, ptr, cand;
    std::vector<long long> jr, avail, candEst;
public:
    BottleneckMachineGtResequence(const Model& md, double sc, int mo, double gp) : g(md), scale(sc), mode(mo), greedy(gp) {}

    Model::Solution build(const Model::Solution& s, double gp, Rng& rng) {
        const auto& R = g.md.routes;
        const int n = g.n, m = g.m;
        Model::Solution r(m);
        for (int i = 0; i < m && i < (int)s.size(); ++i) r[i].reserve(s[i].size());
        nk.assign(n, 0); ptr.assign(m, 0); jr.assign(n, 0); avail.assign(m, 0);
        int left = g.N;
        while (left > 0) {
            long long best = std::numeric_limits<long long>::max(); int bj = -1, ties = 0;
            for (int j = 0; j < n; ++j) {
                if (nk[j] >= (int)R[j].size()) continue;
                int i = R[j][nk[j]].first;
                if (!freeM[i]) {
                    if (i >= (int)s.size() || ptr[i] >= (int)s[i].size()) freeM[i] = 1;
                    else if (s[i][ptr[i]] != j) continue;
                }
                long long e = std::max(jr[j], avail[i]) + R[j][nk[j]].second;
                if (e < best) { best = e; bj = j; ties = 1; }
                else if (e == best && rng.below(++ties) == 0) bj = j;
            }
            if (bj < 0) { // only possible with an infeasible input: release blocking machines
                for (int j = 0; j < n; ++j) if (nk[j] < (int)R[j].size()) freeM[R[j][nk[j]].first] = 1;
                continue;
            }
            int mi = R[bj][nk[bj]].first, c = bj;
            if (freeM[mi]) {
                cand.clear(); candEst.clear();
                for (int j = 0; j < n; ++j) {
                    if (nk[j] >= (int)R[j].size() || R[j][nk[j]].first != mi) continue;
                    long long est = std::max(jr[j], avail[mi]);
                    if (est < best || j == bj) { cand.push_back(j); candEst.push_back(est); }
                }
                if (cand.size() > 1) {
                    if (rng.uniform() < gp) {
                        long long be = std::numeric_limits<long long>::max(); int t2 = 0;
                        for (size_t t = 0; t < cand.size(); ++t) {
                            if (candEst[t] < be) { be = candEst[t]; c = cand[t]; t2 = 1; }
                            else if (candEst[t] == be && rng.below(++t2) == 0) c = cand[t];
                        }
                    } else c = cand[rng.below((int)cand.size())];
                }
            }
            int p = R[c][nk[c]].second;
            long long st = std::max(jr[c], avail[mi]);
            jr[c] = avail[mi] = st + p;
            nk[c]++; r[mi].push_back(c);
            if (!freeM[mi]) ptr[mi]++;
            --left;
        }
        return r;
    }

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        const int M = g.m;
        bool ok = g.load(s) && g.times();
        if (!ok) { freeM.assign(M, 1); return build(s, 0.0, rng); }
        w.assign(M, 0.0);
        if (mode == 0) {
            long long mk = g.tails();
            for (int o = 0; o < g.N; ++o)
                if (g.head[o] + g.opProc[o] + g.tail[o] == mk) w[g.opMach[o]] += 1.0;
        }
        int nt = 0;
        for (int i = 0; i < M; ++i) {
            if (s[i].size() < 2) { w[i] = 0; continue; }
            ++nt;
            if (mode == 0) w[i] += 0.05;
            else if (mode == 1) {
                double ld = 1.0;
                for (int j : s[i]) ld += g.opProc[g.md.op_of[j][i]];
                w[i] = ld;
            } else w[i] = 1.0;
        }
        if (nt == 0) return s;
        int k = (int)std::lround(scale * strength);
        k = std::max(1, std::min(nt, k));
        for (int att = 0; att < 5; ++att) {
            freeM.assign(M, 0); tmp = w;
            for (int t = 0; t < k; ++t) {
                int i = pick_weighted_a(tmp, rng);
                if (i < 0) break;
                freeM[i] = 1; tmp[i] = 0;
            }
            Model::Solution r = build(s, greedy * std::pow(0.5, att), rng);
            if (r != s) return r;
            k = std::min(nt, k + 1);
        }
        Model::Solution cur = s;
        g.minspan_swap(cur);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("machines_scale", 0.7);
    std::string md = params.text("select_mode", "critical");
    int mo = md == "load" ? 1 : (md == "random" ? 2 : 0);
    double gp = params.get("greedy_prob", 0.5);
    return std::make_unique<BottleneckMachineGtResequence>(model, sc, mo, gp);
}
