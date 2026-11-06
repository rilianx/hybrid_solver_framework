// COMPONENT: {"name": "cluster_ruin_regret_recreate", "slot": "perturbation", "params": {"ruin_per_strength": {"type": "int", "range": [2, 20]}, "reference": {"type": "cat", "values": ["open_facility", "any_facility"]}, "insertion": {"type": "cat", "values": ["regret", "greedy_demand"]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "open_weight": {"type": "float", "range": [0.5, 1.5]}}}
struct RRBase {
    const Model& M;
    int F, C;
    std::vector<double> load;
    std::vector<int> cnt;
    explicit RRBase(const Model& m)
        : M(m), F((int)m.capacity.size()), C((int)m.demand.size()), load(F, 0.0), cnt(F, 0) {}
    bool fits(int i, int j) const { return load[i] + M.demand[j] <= M.capacity[i] + 1e-9; }
    void place(std::vector<int>& a, int j, int i) { a[j] = i; load[i] += M.demand[j]; cnt[i]++; }
    void unplace(std::vector<int>& a, int j) {
        int i = a[j];
        if (i >= 0) { load[i] -= M.demand[j]; cnt[i]--; }
        a[j] = -1;
    }
    void recompute(const std::vector<int>& a) {
        std::fill(load.begin(), load.end(), 0.0);
        std::fill(cnt.begin(), cnt.end(), 0);
        for (int j = 0; j < C; ++j) if (a[j] >= 0) { load[a[j]] += M.demand[j]; cnt[a[j]]++; }
    }
    std::vector<int> init(const Model::Solution& s) {
        std::vector<int> a = s.empty() ? std::vector<int>() : s[0];
        a.resize(C, -1);
        for (int j = 0; j < C; ++j) if (a[j] < 0 || a[j] >= F) a[j] = -1;
        recompute(a);
        for (int j = 0; j < C; ++j) if (a[j] < 0) {
            int bi = -1, bany = 0;
            for (int i = 0; i < F; ++i) {
                if (fits(i, j) && (bi < 0 || M.cost[i][j] < M.cost[bi][j])) bi = i;
                if (M.cost[i][j] < M.cost[bany][j]) bany = i;
            }
            place(a, j, bi >= 0 ? bi : bany);
        }
        return a;
    }
    bool try_swap_pair(std::vector<int>& a, int j1, int j2) {
        int f1 = a[j1], f2 = a[j2];
        if (f1 == f2) return false;
        double d1 = M.demand[j1], d2 = M.demand[j2];
        if (load[f1] - d1 + d2 <= M.capacity[f1] + 1e-9 && load[f2] - d2 + d1 <= M.capacity[f2] + 1e-9) {
            load[f1] += d2 - d1; load[f2] += d1 - d2;
            a[j1] = f2; a[j2] = f1;
            return true;
        }
        return false;
    }
    bool force_change(std::vector<int>& a, Rng& rng) {
        if (F < 2 || C < 1) return false;
        int j0 = rng.below(C), i0 = rng.below(F);
        for (int jj = 0; jj < C; ++jj) {
            int j = (j0 + jj) % C;
            for (int ii = 0; ii < F; ++ii) {
                int i = (i0 + ii) % F;
                if (i != a[j] && fits(i, j)) { unplace(a, j); place(a, j, i); return true; }
            }
        }
        for (int x = 0; x < C; ++x)
            for (int y = x + 1; y < C; ++y)
                if (try_swap_pair(a, (j0 + x) % C, (j0 + y) % C)) return true;
        return false;
    }
};

class ClusterRuinRegretRecreate : public hsf::Perturbation<Model> {
public:
    ClusterRuinRegretRecreate(const Model& m, int rps, bool ref_open, bool regret, double noise, double ow)
        : B(m), rps_(rps), ref_open_(ref_open), regret_(regret), noise_(noise), ow_(ow),
          idx_(B.C), b1_(B.C), b2_(B.C), i1_(B.C), i2_(B.C) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (B.F == 0 || B.C == 0) return s;
        std::vector<int> a = B.init(s);
        const std::vector<int> orig = a;
        if (B.F < 2) return Sol{a};

        int q = (int)std::lround(std::max(1.0, strength) * rps_);
        q = std::max(1, std::min(q, B.C));
        int r = ref_open_ ? a[rng.below(B.C)] : rng.below(B.F);

        std::iota(idx_.begin(), idx_.end(), 0);
        const auto& cr = B.M.cost[r];
        if (q < B.C)
            std::nth_element(idx_.begin(), idx_.begin() + q, idx_.end(),
                             [&](int x, int y) { return cr[x] < cr[y]; });
        P_.assign(idx_.begin(), idx_.begin() + q);
        for (int j : P_) B.unplace(a, j);
        for (int j : P_) eval(j);

        bool fail = false;
        while (!P_.empty()) {
            int bp = -1;
            double bk = -1.0;
            for (int p = 0; p < (int)P_.size(); ++p) {
                int j = P_[p];
                if (i1_[j] < 0) { fail = true; break; }
                double key;
                if (regret_) {
                    key = (i2_[j] < 0) ? 1e15 + B.M.demand[j] : (b2_[j] - b1_[j]);
                    if (i2_[j] >= 0 && noise_ > 0) key *= 1.0 + noise_ * rng.uniform();
                } else {
                    key = B.M.demand[j] * (1.0 + noise_ * rng.uniform());
                }
                if (key > bk) { bk = key; bp = p; }
            }
            if (fail || bp < 0) { fail = true; break; }
            int j = P_[bp];
            int i = i1_[j];
            B.place(a, j, i);
            P_[bp] = P_.back();
            P_.pop_back();
            for (int jj : P_) {
                if (i1_[jj] == i || i2_[jj] == i) { eval(jj); continue; }
                if (!B.fits(i, jj)) continue;
                double sc = score(i, jj);
                if (sc < b1_[jj]) { b2_[jj] = b1_[jj]; i2_[jj] = i1_[jj]; b1_[jj] = sc; i1_[jj] = i; }
                else if (sc < b2_[jj]) { b2_[jj] = sc; i2_[jj] = i; }
            }
        }
        if (fail) {
            a = orig;
            B.recompute(a);
            B.force_change(a, rng);
            return Sol{a};
        }
        if (a == orig) B.force_change(a, rng);
        return Sol{a};
    }

private:
    RRBase B;
    int rps_;
    bool ref_open_, regret_;
    double noise_, ow_;
    std::vector<int> idx_, P_;
    std::vector<double> b1_, b2_;
    std::vector<int> i1_, i2_;

    double score(int i, int j) const {
        return B.M.cost[i][j] + (B.cnt[i] == 0 ? ow_ * B.M.fixed[i] : 0.0);
    }
    void eval(int j) {
        const double INF = std::numeric_limits<double>::infinity();
        double v1 = INF, v2 = INF;
        int k1 = -1, k2 = -1;
        for (int i = 0; i < B.F; ++i) {
            if (!B.fits(i, j)) continue;
            double sc = score(i, j);
            if (sc < v1) { v2 = v1; k2 = k1; v1 = sc; k1 = i; }
            else if (sc < v2) { v2 = sc; k2 = i; }
        }
        b1_[j] = v1; b2_[j] = v2; i1_[j] = k1; i2_[j] = k2;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int rps = (int)params.get("ruin_per_strength", 5);
    bool ref_open = params.text("reference", "open_facility") == "open_facility";
    bool regret = params.text("insertion", "regret") == "regret";
    double noise = params.get("noise", 0.1);
    double ow = params.get("open_weight", 1.0);
    return std::make_unique<ClusterRuinRegretRecreate>(model, std::max(1, rps), ref_open, regret, noise, ow);
}
