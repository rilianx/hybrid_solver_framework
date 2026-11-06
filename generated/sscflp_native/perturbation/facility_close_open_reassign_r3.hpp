// COMPONENT: {"name": "facility_close_open_reassign", "slot": "perturbation", "params": {"open_prob": {"type": "float", "range": [0.0, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.5]}}}
struct FState {
    std::vector<int> asg;
    std::vector<double> load;
    std::vector<int> cnt;
};

static inline double fcst(const Model& M, int i, int j) { return M.cost[(size_t)i * M.m + j]; }

static void f_relocate(const Model& M, FState& st, int j, int i) {
    int a = st.asg[j];
    double d = M.demand[j];
    if (a >= 0) { st.load[a] -= d; st.cnt[a]--; }
    st.asg[j] = i;
    if (i >= 0) { st.load[i] += d; st.cnt[i]++; }
}

static void f_load(const Model& M, const Model::Solution& s, FState& st) {
    st.asg.assign(M.m, -1); st.load.assign(M.n, 0.0); st.cnt.assign(M.n, 0);
    for (int i = 0; i < (int)s.size() && i < M.n; ++i)
        for (int j : s[i])
            if (j >= 0 && j < M.m && st.asg[j] < 0) { st.asg[j] = i; st.load[i] += M.demand[j]; st.cnt[i]++; }
    for (int j = 0; j < M.m; ++j) {
        if (st.asg[j] >= 0) continue;
        int best = -1, anyb = -1; double bv = 1e300, av = 1e300;
        for (int i = 0; i < M.n; ++i) {
            double v = fcst(M, i, j);
            if (v < av) { av = v; anyb = i; }
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS && v < bv) { bv = v; best = i; }
        }
        if (best < 0) best = anyb;
        if (best >= 0) f_relocate(M, st, j, best);
    }
}

static Model::Solution f_build(const Model& M, const FState& st) {
    Model::Solution out(M.n);
    for (int j = 0; j < M.m; ++j) if (st.asg[j] >= 0) out[st.asg[j]].push_back(j);
    return out;
}

static bool f_force(const Model& M, FState& st, Rng& rng) {
    int n = M.n, m = M.m;
    if (m == 0 || n < 2) return false;
    for (int t = 0; t < 60; ++t) {
        int j = rng.below(m), i = rng.below(n);
        if (i == st.asg[j]) continue;
        if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) { f_relocate(M, st, j, i); return true; }
    }
    int j0 = rng.below(m), i0 = rng.below(n);
    for (int jj = 0; jj < m; ++jj) {
        int j = (j0 + jj) % m;
        for (int ii = 0; ii < n; ++ii) {
            int i = (i0 + ii) % n;
            if (i == st.asg[j]) continue;
            if (st.load[i] + M.demand[j] <= M.capacity[i] + M.EPS) { f_relocate(M, st, j, i); return true; }
        }
    }
    for (int jj = 0; jj < m; ++jj) {
        int j = (j0 + jj) % m, a = st.asg[j];
        for (int k = 0; k < m; ++k) {
            int b = st.asg[k];
            if (a == b || a < 0 || b < 0) continue;
            double dj = M.demand[j], dk = M.demand[k];
            if (st.load[a] - dj + dk <= M.capacity[a] + M.EPS && st.load[b] - dk + dj <= M.capacity[b] + M.EPS) {
                f_relocate(M, st, j, b); f_relocate(M, st, k, a); return true;
            }
        }
    }
    return false;
}

class FacilityCloseOpenReassign : public hsf::Perturbation<Model> {
public:
    FacilityCloseOpenReassign(const Model& m, double op, double nz) : M(m), open_prob(op), noise(nz) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        f_load(M, s, st);
        orig = st.asg;
        lockF.assign(M.n, 0);
        diff = 0;
        if (M.m > 0 && M.n > 1) {
            int openF = 0;
            for (int i = 0; i < M.n; ++i) if (st.cnt[i] > 0) ++openF;
            double base = std::max(1.0, (double)M.m / (double)std::max(1, openF));
            double sg = std::max(0.0, strength);
            long tg = std::lround(std::max(1.0, sg) * base);
            target = (int)std::max(1L, std::min((long)M.m, tg));
            int rounds = std::max(1, (int)std::lround(sg));
            int maxAtt = 3 * rounds + 20, att = 0;
            while (diff < target && att < maxAtt) {
                ++att;
                bool ok;
                if (rng.uniform() < open_prob) { ok = open_move(rng); if (!ok) ok = close_move(rng); }
                else { ok = close_move(rng); if (!ok) ok = open_move(rng); }
            }
            if (diff == 0) f_force(M, st, rng);
        }
        return f_build(M, st);
    }

private:
    bool open_move(Rng& rng) {
        int f = -1;
        for (int t = 0; t < 30; ++t) { int i = rng.below(M.n); if (st.cnt[i] == 0 && !lockF[i]) { f = i; break; } }
        if (f < 0) return false;
        cand.clear();
        for (int j = 0; j < M.m; ++j) {
            int a = st.asg[j];
            if (a == f || a < 0) continue;
            if (a != orig[j]) continue;
            double sav = fcst(M, a, j) - fcst(M, f, j);
            if (st.cnt[a] == 1) sav += M.fixed[a];
            sav += noise * (rng.uniform() - 0.5) * (std::fabs(sav) + 1.0);
            cand.push_back({sav, j});
        }
        std::sort(cand.begin(), cand.end(), [](const std::pair<double,int>& x, const std::pair<double,int>& y) { return x.first > y.first; });
        int moved = 0;
        int cap = std::max(1, target - diff);
        for (auto& p : cand) {
            if (moved >= cap) break;
            if (moved > 0 && p.first <= 0) break;
            int j = p.second;
            if (st.load[f] + M.demand[j] <= M.capacity[f] + M.EPS) { mv(j, f); ++moved; }
        }
        if (moved > 0) lockF[f] = 1;
        return moved > 0;
    }

    bool close_move(Rng& rng) {
        int f = -1;
        for (int t = 0; t < 30; ++t) { int i = rng.below(M.n); if (st.cnt[i] > 0 && !lockF[i]) { f = i; break; } }
        if (f < 0) return false;
        backup = st;
        int bdiff = diff;
        custs.clear();
        for (int j = 0; j < M.m; ++j) if (st.asg[j] == f) custs.push_back(j);
        for (int j : custs) mv(j, -1);
        std::sort(custs.begin(), custs.end(), [&](int a, int b) { return M.demand[a] > M.demand[b]; });
        for (int j : custs) {
            int best = -1, bestO = -1; double bv = 1e300;
            int avoid = (orig[j] != f) ? orig[j] : -1;
            for (int i = 0; i < M.n; ++i) {
                if (i == f) continue;
                if (st.load[i] + M.demand[j] > M.capacity[i] + M.EPS) continue;
                if (i == avoid) { bestO = i; continue; }
                double v = fcst(M, i, j) + (st.cnt[i] == 0 ? M.fixed[i] : 0.0);
                if (noise > 0) v *= 1.0 + noise * rng.uniform();
                if (v < bv) { bv = v; best = i; }
            }
            if (best < 0) best = bestO;
            if (best < 0) { st = backup; diff = bdiff; return false; }
            mv(j, best);
        }
        lockF[f] = 1;
        return true;
    }

    void mv(int j, int i) {
        int before = (st.asg[j] != orig[j]) ? 1 : 0;
        f_relocate(M, st, j, i);
        int after = (i != orig[j]) ? 1 : 0;
        diff += after - before;
    }

    const Model& M;
    double open_prob, noise;
    int diff = 0, target = 1;
    FState st, backup;
    std::vector<int> orig, custs;
    std::vector<char> lockF;
    std::vector<std::pair<double,int>> cand;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double op = std::min(1.0, std::max(0.0, params.get("open_prob", 0.35)));
    double nz = std::min(0.5, std::max(0.0, params.get("noise", 0.1)));
    return std::make_unique<FacilityCloseOpenReassign>(model, op, nz);
}
