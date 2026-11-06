// COMPONENT: {"name": "facility_star_packing_greedy", "slot": "constructor", "params": {"rcl_k": {"type": "int", "range": [1, 5]}, "ratio_mode": {"type": "cat", "values": ["per_customer", "per_demand"]}, "passes": {"type": "int", "range": [0, 4]}}}
static void shift_polish(const Model& md, std::vector<int>& a, std::vector<double>& load,
                         std::vector<int>& cnt, int passes) {
    const int F = (int)md.capacity.size(), C = (int)md.demand.size();
    for (int p = 0; p < passes; ++p) {
        bool imp = false;
        for (int j = 0; j < C; ++j) {
            int i0 = a[j];
            double d = md.demand[j];
            double base = md.cost[i0][j] + (cnt[i0] == 1 ? md.fixed[i0] : 0.0);
            int bi = -1;
            double bd = -1e-9 * (1.0 + std::abs(base));
            for (int i = 0; i < F; ++i) {
                if (i == i0 || cnt[i] == 0) continue;
                if (load[i] + d > md.capacity[i] + Model::EPS) continue;
                double delta = md.cost[i][j] - base;
                if (delta < bd) { bd = delta; bi = i; }
            }
            if (bi >= 0) {
                load[i0] -= d; cnt[i0]--;
                load[bi] += d; cnt[bi]++;
                a[j] = bi; imp = true;
            }
        }
        if (!imp) break;
    }
}

class StarPacking : public hsf::Constructor<Model> {
public:
    StarPacking(const Model& m, int rclk, bool perDemand, int passes)
        : md(m), rclk_(std::max(1, rclk)), perDemand_(perDemand), passes_(passes) {
        F = (int)md.capacity.size();
        C = (int)md.demand.size();
        lists.assign(F, std::vector<int>(C));
        for (int i = 0; i < F; ++i) {
            std::vector<int>& L = lists[i];
            std::iota(L.begin(), L.end(), 0);
            const std::vector<double>& ci = md.cost[i];
            if (perDemand_) {
                std::sort(L.begin(), L.end(), [&](int x, int y) {
                    double ax = ci[x] / std::max(md.demand[x], 1e-12), ay = ci[y] / std::max(md.demand[y], 1e-12);
                    if (ax != ay) return ax < ay;
                    return x < y;
                });
            } else {
                std::sort(L.begin(), L.end(), [&](int x, int y) {
                    if (ci[x] != ci[y]) return ci[x] < ci[y];
                    return x < y;
                });
            }
        }
    }

    Model::Solution build(Rng& rng) override {
        std::vector<int> a(C, -1);
        std::vector<double> load(F, 0.0);
        std::vector<int> cnt(F, 0);
        std::vector<char> open(F, 0);
        std::vector<int> bestLen(F, 0);
        std::vector<std::pair<double, int>> cand;
        cand.reserve(F);
        int remaining = C;
        while (remaining > 0) {
            cand.clear();
            for (int i = 0; i < F; ++i) {
                if (open[i]) continue;
                const std::vector<int>& L = lists[i];
                double capLeft = md.capacity[i], sum = md.fixed[i], den = 0.0;
                double br = std::numeric_limits<double>::infinity();
                int bl = -1, taken = 0;
                for (int p = 0; p < C; ++p) {
                    int j = L[p];
                    if (a[j] >= 0) continue;
                    double d = md.demand[j];
                    if (d > capLeft + Model::EPS) continue;
                    capLeft -= d;
                    sum += md.cost[i][j];
                    den += perDemand_ ? d : 1.0;
                    ++taken;
                    double r = sum / std::max(den, 1e-12);
                    if (r < br) { br = r; bl = p; }
                    if (taken >= remaining) break;
                }
                if (bl >= 0) { bestLen[i] = bl; cand.push_back({br, i}); }
            }
            if (cand.empty()) break;
            int k = std::min(rclk_, (int)cand.size());
            std::partial_sort(cand.begin(), cand.begin() + k, cand.end());
            int i = cand[rng.below(k)].second;
            open[i] = 1;
            const std::vector<int>& L = lists[i];
            double capLeft = md.capacity[i];
            for (int p = 0; p <= bestLen[i]; ++p) {
                int j = L[p];
                if (a[j] >= 0) continue;
                double d = md.demand[j];
                if (d > capLeft + Model::EPS) continue;
                capLeft -= d;
                a[j] = i; load[i] += d; cnt[i]++; --remaining;
            }
        }
        if (remaining > 0) {
            for (int j = 0; j < C; ++j) {
                if (a[j] >= 0) continue;
                double d = md.demand[j];
                int bi = -1; double bc = std::numeric_limits<double>::infinity();
                for (int i = 0; i < F; ++i) {
                    if (load[i] + d > md.capacity[i] + Model::EPS) continue;
                    double c = md.cost[i][j] + (cnt[i] == 0 ? md.fixed[i] : 0.0);
                    if (c < bc) { bc = c; bi = i; }
                }
                if (bi < 0) return md.trivial();
                a[j] = bi; load[bi] += d; cnt[bi]++;
            }
        }
        shift_polish(md, a, load, cnt, passes_);
        Model::Solution sol{a};
        if (!md.feasible(sol)) return md.trivial();
        return sol;
    }

private:
    const Model& md;
    int rclk_;
    bool perDemand_;
    int passes_;
    int F = 0, C = 0;
    std::vector<std::vector<int>> lists;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int rclk = (int)params.get("rcl_k", 2);
    std::string mode = params.text("ratio_mode", "per_customer");
    int passes = (int)params.get("passes", 2);
    return std::unique_ptr<hsf::Constructor<Model>>(new StarPacking(model, rclk, mode == "per_demand", passes));
}
