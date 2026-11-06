// COMPONENT: {"name": "random_shift_swap_walk", "slot": "perturbation", "params": {"moves_per_strength": {"type": "int", "range": [1, 6]}, "swap_prob": {"type": "float", "range": [0.0, 1.0]}, "open_bias": {"type": "float", "range": [0.0, 1.0]}}}
struct WalkBase {
    const Model& M;
    int F, C;
    std::vector<double> load;
    std::vector<int> cnt;
    explicit WalkBase(const Model& m)
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

class RandomShiftSwapWalk : public hsf::Perturbation<Model> {
public:
    RandomShiftSwapWalk(const Model& m, int mps, double sp, double ob)
        : B(m), mps_(mps), swap_prob_(sp), open_bias_(ob) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (B.F == 0 || B.C == 0) return s;
        std::vector<int> a = B.init(s);
        const std::vector<int> orig = a;
        open_.clear();
        for (int i = 0; i < B.F; ++i) if (B.cnt[i] > 0) open_.push_back(i);
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * mps_));
        for (int t = 0; t < k; ++t) {
            bool ok = false;
            bool swap_first = rng.uniform() < swap_prob_;
            if (swap_first) ok = try_swap(a, rng);
            if (!ok) ok = try_relocate(a, rng);
            if (!ok && !swap_first) try_swap(a, rng);
        }
        if (a == orig) B.force_change(a, rng);
        return Sol{a};
    }

private:
    WalkBase B;
    int mps_;
    double swap_prob_, open_bias_;
    std::vector<int> open_;

    bool try_relocate(std::vector<int>& a, Rng& rng) {
        for (int tr = 0; tr < 16; ++tr) {
            int j = rng.below(B.C);
            int i = (!open_.empty() && rng.uniform() < open_bias_) ? open_[rng.below((int)open_.size())]
                                                                  : rng.below(B.F);
            if (i == a[j] || !B.fits(i, j)) continue;
            bool was_closed = B.cnt[i] == 0;
            B.unplace(a, j);
            B.place(a, j, i);
            if (was_closed) open_.push_back(i);
            return true;
        }
        return false;
    }
    bool try_swap(std::vector<int>& a, Rng& rng) {
        if (B.C < 2) return false;
        for (int tr = 0; tr < 16; ++tr) {
            int j1 = rng.below(B.C), j2 = rng.below(B.C);
            if (B.try_swap_pair(a, j1, j2)) return true;
        }
        return false;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int mps = (int)params.get("moves_per_strength", 2);
    double sp = params.get("swap_prob", 0.4);
    double ob = params.get("open_bias", 0.7);
    return std::make_unique<RandomShiftSwapWalk>(model, std::max(1, mps), sp, ob);
}
