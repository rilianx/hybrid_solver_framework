// COMPONENT: {"name": "pivot_ruin_regret_recreate", "slot": "perturbation", "params": {"base_q": {"type": "int", "range": [2, 40]}, "recreate": {"type": "cat", "values": ["regret", "greedy_random"]}, "noise": {"type": "float", "range": [0.0, 0.3]}}}
struct RState {
    std::vector<int> asg;
    std::vector<double> load;
    std::vector<int> cnt;
};

static inline double rcst(const Model& M, int i, int j) { return M.cost[(size_t)i * M.m + j]; }

static void r_relocate(const Model& M, RState& st, int j, int i) {
    int a = st.asg[j];
    double d = M.demand[j];
    if (a >= 0) { st.load[a] -= d; st.cnt[a]--; }
    st.asg[j] = i;
    if (i >= 0) { st.load[i] += d; st.cnt[i]++; }
}

static void r_load(const Model& M, const Model::Solution& s, RState& st) {
    st.asg.assign(M.m, -1); st.load.assign(M.n, 0.0); st.cnt.assign(M.n, 0);
    for (int i = 0; i < (int)s.size() && i < M.n; ++i)
        for (int j : s[i])
            if (j >= 0 && j < M.m && st.asg[j] < 0) { st.asg[j] = i; st.load[i] += M.demand[j]; st.cnt[i]++; }
    for (int j = 0; j < M.m; ++j) {
        if (st.asg[j] >= 0) continue;
        int best = -1, anyb = -1; double bv = 1e300, av = 1e300;
        for (int i = 0; i < M.n; ++i) {
            double v = rcst(M, i, j);
            if (v < av) { av = v; anyb = i; }
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS && v < bv) { bv = v; best = i; }
        }
        if (best < 0) best = anyb;
        if (best >= 0) r_relocate(M, st, j, best);
    }
}

static Model::Solution r_build(const Model& M, const RState& st) {
    Model::Solution out(M.n);
    for (int j = 0; j < M.m; ++j) if (st.asg[j] >= 0) out[st.asg[j]].push_back(j);
    return out;
}

static bool r_force(const Model& M, RState& st, Rng& rng) {
    int n = M.n, m = M.m;
    if (m == 0 || n < 2) return false;
    for (int t = 0; t < 60; ++t) {
        int j = rng.below(m), i = rng.below(n);
        if (i == st.asg[j]) continue;
        if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) { r_relocate(M, st, j, i); return true; }
    }
    int j0 = rng.below(m), i0 = rng.below(n);
    for (int jj = 0; jj < m; ++jj) {
        int j = (j0 + jj) % m;
        for (int ii = 0; ii < n; ++ii) {
            int i = (i0 + ii) % n;
            if (i == st.asg[j]) continue;
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) { r_relocate(M, st, j, i); return true; }
        }
    }
    for (int jj = 0; jj < m; ++jj) {
        int j = (j0 + jj) % m, a = st.asg[j];
        for (int k = 0; k < m; ++k) {
            int b = st.asg[k];
            if (a == b || a < 0 || b < 0) continue;
            double dj = M.demand[j], dk = M.demand[k];
            if (st.load[a] - dj + dk <= M.capacity[a] + M.EPS && st.load[b] - dk + dj <= M.capacity[b] + M.EPS) {
                r_relocate(M, st, j, b); r_relocate(M, st, k, a); return true;
            }
        }
    }
    return false;
}

class PivotRuinRegretRecreate : public hsf::Perturbation<Model> {
public:
    PivotRuinRegretRecreate(const Model& m, int bq, bool regret, double nz)
        : M(m), base_q(bq), use_regret(regret), noise(nz) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        r_load(M, s, st);
        orig = st.asg;
        if (M.m > 0 && M.n > 1) {
            int q = std::max(2, (int)std::lround(base_q * std::max(1.0, strength)));
            q = std::min(q, M.m);
            int f = rng.below(M.n);
            idx.resize(M.m);
            std::iota(idx.begin(), idx.end(), 0);
            if (q < M.m)
                std::nth_element(idx.begin(), idx.begin() + q, idx.end(),
                                 [&](int a, int b) { return rcst(M, f, a) < rcst(M, f, b); });
            pend.assign(idx.begin(), idx.begin() + q);
            backup = st;
            for (int j : pend) r_relocate(M, st, j, -1);
            bool ok = use_regret ? recreate_regret(rng) : recreate_greedy(rng);
            if (!ok) st = backup;
            if (st.asg == orig) r_force(M, st, rng);
        }
        return r_build(M, st);
    }

private:
    inline double ins_cost(int i, int j, Rng& rng) {
        double v = rcst(M, i, j) + (st.cnt[i] == 0 ? M.fixed[i] : 0.0);
        if (noise > 0) v *= 1.0 + noise * rng.uniform();
        return v;
    }

    bool recreate_greedy(Rng& rng) {
        std::shuffle(pend.begin(), pend.end(), rng.g);
        for (int j : pend) {
            int best = -1; double bv = 1e300;
            for (int i = 0; i < M.n; ++i) {
                if (st.load[i] + M.demand[j] > M.capacity[i] + M.EPS) continue;
                double v = ins_cost(i, j, rng);
                if (v < bv) { bv = v; best = i; }
            }
            if (best < 0) return false;
            r_relocate(M, st, j, best);
        }
        return true;
    }

    bool recreate_regret(Rng& rng) {
        while (!pend.empty()) {
            int pickPos = -1, pickFac = -1;
            double pickReg = -1e300;
            for (int p = 0; p < (int)pend.size(); ++p) {
                int j = pend[p];
                double b1 = 1e300, b2 = 1e300; int f1 = -1;
                for (int i = 0; i < M.n; ++i) {
                    if (st.load[i] + M.demand[j] > M.capacity[i] + M.EPS) continue;
                    double v = ins_cost(i, j, rng);
                    if (v < b1) { b2 = b1; b1 = v; f1 = i; }
                    else if (v < b2) b2 = v;
                }
                if (f1 < 0) return false;
                double reg = (b2 >= 1e299) ? 1e200 + M.demand[j] : (b2 - b1);
                if (reg > pickReg) { pickReg = reg; pickPos = p; pickFac = f1; }
            }
            int j = pend[pickPos];
            r_relocate(M, st, j, pickFac);
            pend[pickPos] = pend.back();
            pend.pop_back();
        }
        return true;
    }

    const Model& M;
    int base_q;
    bool use_regret;
    double noise;
    RState st, backup;
    std::vector<int> orig, idx, pend;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int bq = std::max(2, std::min(40, (int)std::lround(params.get("base_q", 8))));
    bool regret = params.text("recreate", "regret") != "greedy_random";
    double nz = std::min(0.3, std::max(0.0, params.get("noise", 0.05)));
    return std::make_unique<PivotRuinRegretRecreate>(model, bq, regret, nz);
}
