// COMPONENT: {"name": "machine_resequence_heads_tails", "slot": "neighborhood", "params": {"rules": {"type": "cat", "values": ["all", "schrage"]}, "machines": {"type": "cat", "values": ["critical", "all"]}}}
struct JsInfoR {
    const Model& M;
    int N = 0, NM = 0, T = 0;
    std::vector<int> opJob, opMach, opProc, jPred, jSucc;
    std::vector<std::vector<int>> opOf;
    Model::Solution cur;
    bool valid = false, feas = false;
    double obj = 0;
    long long cmax = 0;
    std::vector<int> mp, ms, indeg, topo;
    std::vector<long long> r, q;
    explicit JsInfoR(const Model& m) : M(m) {
        N = m.n; NM = m.m;
        opOf.assign(N, std::vector<int>(NM, -1));
        for (int j = 0; j < N; ++j) {
            int prev = -1;
            for (const auto& pr : m.routes[j]) {
                int id = T++;
                opJob.push_back(j); opMach.push_back(pr.first); opProc.push_back(pr.second);
                jPred.push_back(prev); jSucc.push_back(-1);
                if (prev >= 0) jSucc[prev] = id;
                if (pr.first >= 0 && pr.first < NM) opOf[j][pr.first] = id;
                prev = id;
            }
        }
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0);
        r.assign(T, 0); q.assign(T, 0); topo.reserve(T);
    }
    void ensure(const Model::Solution& s) { if (!valid || s != cur) compute(s); }
    void compute(const Model::Solution& s) {
        cur = s; valid = true; obj = M.objective(s);
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < (int)s.size() && i < NM; ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int j = s[i][k]; if (j < 0 || j >= N) continue;
                int o = opOf[j][i]; if (o < 0) continue;
                if (prev >= 0) { mp[o] = prev; ms[prev] = o; }
                prev = o;
            }
        }
        for (int o = 0; o < T; ++o) indeg[o] = (jPred[o] >= 0) + (mp[o] >= 0);
        topo.clear();
        for (int o = 0; o < T; ++o) if (indeg[o] == 0) topo.push_back(o);
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = jSucc[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            int b = ms[o]; if (b >= 0 && --indeg[b] == 0) topo.push_back(b);
        }
        feas = (int)topo.size() == T;
        cmax = 0;
        if (feas) {
            for (int o : topo) {
                long long v = 0;
                if (jPred[o] >= 0) v = r[jPred[o]] + opProc[jPred[o]];
                if (mp[o] >= 0) v = std::max(v, r[mp[o]] + opProc[mp[o]]);
                r[o] = v; cmax = std::max(cmax, v + opProc[o]);
            }
            for (int h = T - 1; h >= 0; --h) {
                int o = topo[h]; long long v = 0;
                if (jSucc[o] >= 0) v = q[jSucc[o]] + opProc[jSucc[o]];
                if (ms[o] >= 0) v = std::max(v, q[ms[o]] + opProc[ms[o]]);
                q[o] = v;
            }
        } else {
            for (int o = 0; o < T; ++o) r[o] = jPred[o] >= 0 ? r[jPred[o]] + opProc[jPred[o]] : 0;
            for (int o = T - 1; o >= 0; --o) q[o] = jSucc[o] >= 0 ? q[jSucc[o]] + opProc[jSucc[o]] : 0;
            for (int o = 0; o < T; ++o) cmax = std::max(cmax, r[o] + opProc[o] + q[o]);
        }
    }
    bool crit(int o) const { return r[o] + opProc[o] + q[o] == cmax; }
};

class MachineResequenceHeadsTails : public hsf::Neighborhood<Model> {
    const Model& M;
    JsInfoR A;
    bool allRules, critMachines;
    Sol work;
    std::vector<long long> H, Tl, P;
    std::vector<int> idx, seqBuf;
    std::vector<char> used;

    // rule 0: Schrage (released op with largest job-tail); 1: ascending job-head; 2: descending job-tail
    void reseq(const Sol& s, int i, int rule, std::vector<int>& outSeq) {
        const std::vector<int>& seq = s[i];
        int L = seq.size();
        H.resize(L); Tl.resize(L); P.resize(L); idx.resize(L); outSeq.resize(L);
        for (int k = 0; k < L; ++k) {
            int o = A.opOf[seq[k]][i];
            int jp = A.jPred[o], js = A.jSucc[o];
            H[k] = jp >= 0 ? A.r[jp] + A.opProc[jp] : 0;
            Tl[k] = js >= 0 ? A.q[js] + A.opProc[js] : 0;
            P[k] = A.opProc[o];
            idx[k] = k;
        }
        if (rule == 1) {
            std::stable_sort(idx.begin(), idx.end(), [&](int a, int b) { return H[a] < H[b]; });
        } else if (rule == 2) {
            std::stable_sort(idx.begin(), idx.end(), [&](int a, int b) { return Tl[a] > Tl[b]; });
        } else {
            used.assign(L, 0);
            long long t = 0;
            int step = 0;
            while (step < L) {
                int best = -1;
                long long minH = std::numeric_limits<long long>::max();
                for (int k = 0; k < L; ++k) {
                    if (used[k]) continue;
                    if (H[k] <= t) {
                        if (best < 0 || Tl[k] > Tl[best] || (Tl[k] == Tl[best] && H[k] < H[best])) best = k;
                    } else if (H[k] < minH) minH = H[k];
                }
                if (best < 0) { t = minH; continue; }
                idx[step++] = best; used[best] = 1;
                t = std::max(t, H[best]) + P[best];
            }
        }
        for (int k = 0; k < L; ++k) outSeq[k] = seq[idx[k]];
    }

    void build(const Sol& s, const Move& mv, Sol& out) {
        A.ensure(s);
        out = s;
        int i = mv[0], rule = mv[1];
        if (i < 0 || i >= (int)s.size() || i >= A.NM) return;
        reseq(s, i, rule, seqBuf);
        out[i] = seqBuf;
    }

    void gen(const Sol& s, std::vector<Move>& out, bool onlyCrit) {
        int nr = allRules ? 3 : 1;
        for (int i = 0; i < (int)s.size() && i < A.NM; ++i) {
            if (s[i].size() < 2) continue;
            if (onlyCrit) {
                bool has = false;
                for (int j : s[i]) { int o = A.opOf[j][i]; if (o >= 0 && A.crit(o)) { has = true; break; } }
                if (!has) continue;
            }
            for (int rule = 0; rule < nr; ++rule) {
                reseq(s, i, rule, seqBuf);
                if (seqBuf != s[i]) { Move mv{}; mv[0] = i; mv[1] = rule; out.push_back(mv); }
            }
        }
    }
public:
    MachineResequenceHeadsTails(const Model& m, bool ar, bool cm) : M(m), A(m), allRules(ar), critMachines(cm) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        gen(s, out, critMachines && A.feas);
        if (out.empty() && critMachines && A.feas) gen(s, out, false);
        if (out.empty()) {
            bool save = allRules; allRules = true;
            gen(s, out, false);
            allRules = save;
        }
        if (out.empty()) { Move mv{}; out.push_back(mv); }
    }
    Sol apply(const Sol& s, const Move& m) override { Sol r; build(s, m, r); return r; }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        double base = A.obj;
        build(s, m, work);
        return M.objective(work) - base;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string rules = params.text("rules", "all");
    std::string mach = params.text("machines", "critical");
    return std::make_unique<MachineResequenceHeadsTails>(model, rules != "schrage", mach != "all");
}
