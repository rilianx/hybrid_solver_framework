// COMPONENT: {"name": "randomized_add_open_then_regret_assign", "slot": "constructor", "params": {"slack": {"type": "float", "range": [1.0, 1.6]}, "topk": {"type": "int", "range": [1, 5]}, "noise": {"type": "float", "range": [0.0, 0.8]}, "passes": {"type": "int", "range": [0, 4]}}}
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

class AddOpenAssign : public hsf::Constructor<Model> {
public:
    AddOpenAssign(const Model& m, double slack, int topk, double noise, int passes)
        : md(m), slack_(slack), topk_(std::max(1, topk)), noise_(noise), passes_(passes) {
        F = (int)md.capacity.size();
        C = (int)md.demand.size();
        sumc.assign(F, 0.0);
        for (int i = 0; i < F; ++i)
            for (int j = 0; j < C; ++j) sumc[i] += md.cost[i][j];
        totDem = 0.0; maxd = 0.0;
        for (int j = 0; j < C; ++j) { totDem += md.demand[j]; maxd = std::max(maxd, md.demand[j]); }
    }

    Model::Solution build(Rng& rng) override {
        if (F == 0) return md.trivial();
        std::vector<char> open(F, 0);
        std::vector<double> dist(C);
        std::vector<std::pair<double, int>> cand;
        cand.reserve(F);
        // primer centro
        for (int i = 0; i < F; ++i) cand.push_back({md.fixed[i] + sumc[i], i});
        std::sort(cand.begin(), cand.end());
        int f0 = cand[rng.below(std::min(topk_, (int)cand.size()))].second;
        open[f0] = 1;
        double totCap = md.capacity[f0];
        for (int j = 0; j < C; ++j) dist[j] = md.cost[f0][j];
        // ADD
        while (true) {
            bool need = totCap < slack_ * totDem;
            cand.clear();
            for (int i = 0; i < F; ++i) {
                if (open[i]) continue;
                double sav = 0.0;
                const std::vector<double>& ci = md.cost[i];
                for (int j = 0; j < C; ++j) { double g = dist[j] - ci[j]; if (g > 0) sav += g; }
                double gain = sav - md.fixed[i];
                if (need) {
                    double capi = std::max(md.capacity[i], 1e-12);
                    cand.push_back({-gain / capi, i});
                } else if (gain > 1e-9) {
                    cand.push_back({-gain, i});
                }
            }
            if (cand.empty()) break;
            std::sort(cand.begin(), cand.end());
            int pick = cand[rng.below(std::min(topk_, (int)cand.size()))].second;
            open[pick] = 1;
            totCap += md.capacity[pick];
            for (int j = 0; j < C; ++j) dist[j] = std::min(dist[j], md.cost[pick][j]);
        }
        std::vector<int> O;
        for (int i = 0; i < F; ++i) if (open[i]) O.push_back(i);
        // orden por arrepentimiento entre abiertos
        std::vector<double> reg(C, 0.0);
        double maxr = 0.0;
        for (int j = 0; j < C; ++j) {
            double c1 = std::numeric_limits<double>::infinity(), c2 = c1;
            for (int i : O) {
                double c = md.cost[i][j];
                if (c < c1) { c2 = c1; c1 = c; } else if (c < c2) c2 = c;
            }
            reg[j] = (O.size() >= 2) ? (c2 - c1) : 0.0;
            maxr = std::max(maxr, reg[j]);
        }
        std::vector<std::pair<double, int>> ord(C);
        for (int j = 0; j < C; ++j) {
            double k = (maxr > 0 ? reg[j] / maxr : 0.0) + (maxd > 0 ? 1.5 * md.demand[j] / maxd : 0.0);
            ord[j] = {-(k * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0))), j};
        }
        std::sort(ord.begin(), ord.end());
        std::vector<double> load(F, 0.0);
        std::vector<int> cnt(F, 0), a(C, -1);
        for (auto& pr : ord) {
            int j = pr.second;
            double d = md.demand[j];
            int bi = -1; double bc = std::numeric_limits<double>::infinity();
            for (int i : O) {
                if (load[i] + d <= md.capacity[i] + Model::EPS && md.cost[i][j] < bc) { bc = md.cost[i][j]; bi = i; }
            }
            if (bi < 0) {
                for (int i = 0; i < F; ++i) {
                    if (open[i]) continue;
                    if (d <= md.capacity[i] + Model::EPS) {
                        double s = md.cost[i][j] + md.fixed[i];
                        if (s < bc) { bc = s; bi = i; }
                    }
                }
                if (bi < 0) return md.trivial();
                open[bi] = 1; O.push_back(bi);
            }
            a[j] = bi; load[bi] += d; cnt[bi]++;
        }
        shift_polish(md, a, load, cnt, passes_);
        Model::Solution sol{a};
        if (!md.feasible(sol)) return md.trivial();
        return sol;
    }

private:
    const Model& md;
    double slack_;
    int topk_;
    double noise_;
    int passes_;
    int F = 0, C = 0;
    double totDem = 0.0, maxd = 0.0;
    std::vector<double> sumc;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double slack = params.get("slack", 1.15);
    int topk = (int)params.get("topk", 2);
    double noise = params.get("noise", 0.2);
    int passes = (int)params.get("passes", 2);
    return std::unique_ptr<hsf::Constructor<Model>>(new AddOpenAssign(model, slack, topk, noise, passes));
}
