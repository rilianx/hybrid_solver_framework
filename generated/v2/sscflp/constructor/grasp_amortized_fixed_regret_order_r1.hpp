// COMPONENT: {"name": "grasp_amortized_fixed_regret_order", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 2.0]}, "rcl": {"type": "float", "range": [0.0, 0.3]}, "noise": {"type": "float", "range": [0.0, 1.0]}, "passes": {"type": "int", "range": [0, 4]}}}
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

class GraspAmortized : public hsf::Constructor<Model> {
public:
    GraspAmortized(const Model& m, double alpha, double rcl, double noise, int passes)
        : md(m), alpha_(alpha), rcl_(rcl), noise_(noise), passes_(passes) {
        F = (int)md.capacity.size();
        C = (int)md.demand.size();
        key.assign(C, 0.0);
        std::vector<double> reg(C, 0.0);
        double maxr = 0.0, maxd = 0.0;
        for (int j = 0; j < C; ++j) {
            double c1 = std::numeric_limits<double>::infinity(), c2 = c1;
            for (int i = 0; i < F; ++i) {
                double c = md.cost[i][j];
                if (c < c1) { c2 = c1; c1 = c; }
                else if (c < c2) c2 = c;
            }
            reg[j] = (F >= 2 && std::isfinite(c2)) ? (c2 - c1) : 0.0;
            maxr = std::max(maxr, reg[j]);
            maxd = std::max(maxd, md.demand[j]);
        }
        for (int j = 0; j < C; ++j)
            key[j] = (maxr > 0 ? reg[j] / maxr : 0.0) + (maxd > 0 ? md.demand[j] / maxd : 0.0);
        load.assign(F, 0.0); cnt.assign(F, 0); score.assign(F, 0.0);
    }

    Model::Solution build(Rng& rng) override {
        std::vector<std::pair<double, int>> ord(C);
        for (int j = 0; j < C; ++j) {
            double f = 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            ord[j] = {-(key[j] * f), j};
        }
        std::sort(ord.begin(), ord.end());
        std::fill(load.begin(), load.end(), 0.0);
        std::fill(cnt.begin(), cnt.end(), 0);
        std::vector<int> a(C, -1);
        const double INF = std::numeric_limits<double>::infinity();
        for (auto& pr : ord) {
            int j = pr.second;
            double d = md.demand[j];
            double best = INF;
            for (int i = 0; i < F; ++i) {
                if (load[i] + d <= md.capacity[i] + Model::EPS) {
                    double s = md.cost[i][j];
                    if (cnt[i] == 0) s += alpha_ * md.fixed[i] * d / std::max(md.capacity[i], 1e-12);
                    score[i] = s;
                    if (s < best) best = s;
                } else score[i] = INF;
            }
            if (!std::isfinite(best)) return md.trivial();
            double thr = best + rcl_ * std::abs(best) + 1e-12;
            int ncand = 0;
            for (int i = 0; i < F; ++i) if (score[i] <= thr) ++ncand;
            int k = rng.below(std::max(1, ncand));
            int chosen = -1;
            for (int i = 0; i < F; ++i) if (score[i] <= thr) { if (k == 0) { chosen = i; break; } --k; }
            if (chosen < 0) return md.trivial();
            a[j] = chosen; load[chosen] += d; cnt[chosen]++;
        }
        shift_polish(md, a, load, cnt, passes_);
        Model::Solution sol{a};
        if (!md.feasible(sol)) return md.trivial();
        return sol;
    }

private:
    const Model& md;
    double alpha_, rcl_, noise_;
    int passes_;
    int F = 0, C = 0;
    std::vector<double> key, load, score;
    std::vector<int> cnt;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = params.get("alpha", 1.0);
    double rcl = params.get("rcl", 0.05);
    double noise = params.get("noise", 0.3);
    int passes = (int)params.get("passes", 2);
    return std::unique_ptr<hsf::Constructor<Model>>(new GraspAmortized(model, alpha, rcl, noise, passes));
}
