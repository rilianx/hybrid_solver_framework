// COMPONENT: {"name": "facility_close_greedy_repair", "slot": "perturbation", "params": {"close_per_strength": {"type": "float", "range": [0.5, 3.0]}, "selection": {"type": "cat", "values": ["random", "expensive"]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "open_weight": {"type": "float", "range": [0.0, 1.5]}}}
struct CloseBase {
    const Model& M;
    int F, C;
    std::vector<double> load;
    std::vector<int> cnt;
    explicit CloseBase(const Model& m)
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

class FacilityCloseGreedyRepair : public hsf::Perturbation<Model> {
public:
    FacilityCloseGreedyRepair(const Model& m, double cps, bool expensive, double noise, double ow)
        : B(m), cps_(cps), expensive_(expensive), noise_(noise), ow_(ow), closed_(B.F, 0), w_(B.F, 0.0) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (B.F == 0 || B.C == 0) return s;
        std::vector<int> a = B.init(s);
        const std::vector<int> orig = a;
        open_.clear();
        for (int i = 0; i < B.F; ++i) if (B.cnt[i] > 0) open_.push_back(i);
        int maxk = (int)open_.size();
        if (maxk == B.F) maxk -= 1;
        if (maxk < 1) { B.force_change(a, rng); return Sol{a}; }
        int k = std::max(1, (int)std::floor(std::max(1.0, strength) * cps_ + 0.5));
        k = std::min(k, maxk);

        // choose facilities to close
        chosen_.clear();
        if (!expensive_) {
            for (int t = 0; t < k; ++t) {
                int r = t + rng.below((int)open_.size() - t);
                std::swap(open_[t], open_[r]);
                chosen_.push_back(open_[t]);
            }
        } else {
            std::fill(w_.begin(), w_.end(), 0.0);
            for (int j = 0; j < B.C; ++j) w_[a[j]] += B.M.cost[a[j]][j];
            for (int i : open_) w_[i] = (w_[i] + B.M.fixed[i]) / std::max(B.load[i], 1e-6) + 1e-12;
            for (int t = 0; t < k; ++t) {
                double tot = 0;
                for (int i : open_) tot += w_[i];
                double r = rng.uniform() * tot;
                int pick = -1;
                for (int i : open_) {
                    if (w_[i] <= 0) continue;
                    pick = i;
                    r -= w_[i];
                    if (r <= 0) break;
                }
                if (pick < 0) break;
                chosen_.push_back(pick);
                w_[pick] = 0.0;
            }
        }
        for (int i : chosen_) closed_[i] = 1;

        removed_.clear();
        for (int j = 0; j < B.C; ++j) if (closed_[a[j]]) { removed_.push_back(j); B.unplace(a, j); }
        std::shuffle(removed_.begin(), removed_.end(), rng.g);
        std::stable_sort(removed_.begin(), removed_.end(),
                         [&](int x, int y) { return B.M.demand[x] > B.M.demand[y]; });

        bool fail = false;
        for (int j : removed_) {
            int bi = pick_best(j, true, rng);
            if (bi < 0) bi = pick_best(j, false, rng);
            if (bi < 0) { fail = true; break; }
            B.place(a, j, bi);
        }
        for (int i : chosen_) closed_[i] = 0;
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
    CloseBase B;
    double cps_;
    bool expensive_;
    double noise_, ow_;
    std::vector<char> closed_;
    std::vector<double> w_;
    std::vector<int> open_, chosen_, removed_;

    int pick_best(int j, bool respect_closed, Rng& rng) {
        int bi = -1;
        double bs = std::numeric_limits<double>::infinity();
        for (int i = 0; i < B.F; ++i) {
            if (respect_closed && closed_[i]) continue;
            if (!B.fits(i, j)) continue;
            double sc = B.M.cost[i][j] + (B.cnt[i] == 0 ? ow_ * B.M.fixed[i] : 0.0);
            if (noise_ > 0) sc *= 1.0 + noise_ * rng.uniform();
            if (sc < bs) { bs = sc; bi = i; }
        }
        return bi;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double cps = params.get("close_per_strength", 1.0);
    bool exp = params.text("selection", "expensive") == "expensive";
    double noise = params.get("noise", 0.1);
    double ow = params.get("open_weight", 1.0);
    return std::make_unique<FacilityCloseGreedyRepair>(model, std::max(0.5, cps), exp, noise, ow);
}
