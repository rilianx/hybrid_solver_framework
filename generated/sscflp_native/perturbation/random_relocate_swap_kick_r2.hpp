// COMPONENT: {"name": "random_relocate_swap_kick", "slot": "perturbation", "params": {"swap_prob": {"type": "float", "range": [0.0, 1.0]}, "moves_per_strength": {"type": "int", "range": [1, 4]}, "open_bias": {"type": "float", "range": [0.0, 1.0]}}}
struct KState {
    std::vector<int> asg;
    std::vector<double> load;
    std::vector<int> cnt;
};

static inline double kc(const Model& M, int i, int j) { return M.cost[(size_t)i * M.m + j]; }

static void k_relocate(const Model& M, KState& st, int j, int i) {
    int a = st.asg[j];
    double d = M.demand[j];
    if (a >= 0) { st.load[a] -= d; st.cnt[a]--; }
    st.asg[j] = i; st.load[i] += d; st.cnt[i]++;
}

static void k_load(const Model& M, const Model::Solution& s, KState& st) {
    st.asg.assign(M.m, -1); st.load.assign(M.n, 0.0); st.cnt.assign(M.n, 0);
    for (int i = 0; i < (int)s.size() && i < M.n; ++i)
        for (int j : s[i])
            if (j >= 0 && j < M.m && st.asg[j] < 0) { st.asg[j] = i; st.load[i] += M.demand[j]; st.cnt[i]++; }
    for (int j = 0; j < M.m; ++j) {
        if (st.asg[j] >= 0) continue;
        int best = -1, anyb = -1; double bv = 1e300, av = 1e300;
        for (int i = 0; i < M.n; ++i) {
            double v = kc(M, i, j);
            if (v < av) { av = v; anyb = i; }
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS && v < bv) { bv = v; best = i; }
        }
        if (best < 0) best = anyb;
        if (best >= 0) k_relocate(M, st, j, best);
    }
}

static Model::Solution k_build(const Model& M, const KState& st, const Model::Solution& s, std::vector<char>& seen) {
    Model::Solution out(M.n);
    seen.assign(M.m, 0);
    for (int i = 0; i < (int)s.size() && i < M.n; ++i)
        for (int j : s[i])
            if (j >= 0 && j < M.m && !seen[j] && st.asg[j] == i) { out[i].push_back(j); seen[j] = 1; }
    for (int j = 0; j < M.m; ++j) if (!seen[j] && st.asg[j] >= 0) out[st.asg[j]].push_back(j);
    return out;
}

static bool k_force(const Model& M, KState& st, Rng& rng) {
    int n = M.n, m = M.m;
    if (m == 0 || n < 2) return false;
    for (int t = 0; t < 60; ++t) {
        int j = rng.below(m), i = rng.below(n);
        if (i == st.asg[j]) continue;
        if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) { k_relocate(M, st, j, i); return true; }
    }
    int j0 = rng.below(m), i0 = rng.below(n);
    for (int jj = 0; jj < m; ++jj) {
        int j = (j0 + jj) % m;
        for (int ii = 0; ii < n; ++ii) {
            int i = (i0 + ii) % n;
            if (i == st.asg[j]) continue;
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) { k_relocate(M, st, j, i); return true; }
        }
    }
    for (int jj = 0; jj < m; ++jj) {
        int j = (j0 + jj) % m, a = st.asg[j];
        for (int k = 0; k < m; ++k) {
            int b = st.asg[k];
            if (a == b || a < 0 || b < 0) continue;
            double dj = M.demand[j], dk = M.demand[k];
            if (st.load[a] - dj + dk <= M.capacity[a] + M.EPS && st.load[b] - dk + dj <= M.capacity[b] + M.EPS) {
                k_relocate(M, st, j, b); k_relocate(M, st, k, a); return true;
            }
        }
    }
    return false;
}

class RandomRelocateSwapKick : public hsf::Perturbation<Model> {
public:
    RandomRelocateSwapKick(const Model& m, double sp, int mps, double ob)
        : M(m), swap_prob(sp), mps(mps), open_bias(ob) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        k_load(M, s, st);
        orig = st.asg;
        touched.assign(M.m, 0);
        if (M.m > 0 && M.n > 1) {
            int k = std::max(1, (int)std::lround(std::max(1.0, strength) * mps));
            for (int r = 0; r < k; ++r) {
                bool done = false;
                if (rng.uniform() < swap_prob) done = try_swap(rng);
                if (!done) done = try_relocate(rng);
                if (!done) try_swap(rng);
            }
            if (st.asg == orig) k_force(M, st, rng);
        }
        return k_build(M, st, s, seen);
    }

private:
    bool try_relocate(Rng& rng) {
        for (int t = 0; t < 40; ++t) {
            int j = rng.below(M.m), i = rng.below(M.n);
            if (i == st.asg[j]) continue;
            if (touched[j] && t < 30) continue;
            if (st.cnt[i] == 0 && rng.uniform() < open_bias) continue;
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) {
                k_relocate(M, st, j, i); touched[j] = 1; return true;
            }
        }
        return false;
    }
    bool try_swap(Rng& rng) {
        for (int t = 0; t < 40; ++t) {
            int j = rng.below(M.m), k = rng.below(M.m);
            int a = st.asg[j], b = st.asg[k];
            if (a == b || a < 0 || b < 0) continue;
            if ((touched[j] || touched[k]) && t < 30) continue;
            double dj = M.demand[j], dk = M.demand[k];
            if (st.load[a] - dj + dk <= M.capacity[a] + M.EPS && st.load[b] - dk + dj <= M.capacity[b] + M.EPS) {
                k_relocate(M, st, j, b); k_relocate(M, st, k, a);
                touched[j] = 1; touched[k] = 1; return true;
            }
        }
        return false;
    }

    std::vector<char> touched, seen;
    const Model& M;
    double swap_prob;
    int mps;
    double open_bias;
    KState st;
    std::vector<int> orig;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sp = std::min(1.0, std::max(0.0, params.get("swap_prob", 0.3)));
    int mps = std::max(1, std::min(4, (int)std::lround(params.get("moves_per_strength", 2))));
    double ob = std::min(1.0, std::max(0.0, params.get("open_bias", 0.7)));
    return std::make_unique<RandomRelocateSwapKick>(model, sp, mps, ob);
}
