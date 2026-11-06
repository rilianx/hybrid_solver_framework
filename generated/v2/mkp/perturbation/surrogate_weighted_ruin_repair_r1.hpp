// COMPONENT: {"name": "surrogate_weighted_ruin_repair", "slot": "perturbation", "params": {"sigma": {"type": "float", "range": [0.1, 2.0]}, "tight_power": {"type": "float", "range": [0.0, 4.0]}, "ruin_randomness": {"type": "float", "range": [0.0, 1.0]}}}
class SurrogateRuinRepair : public hsf::Perturbation<Model> {
    const Model& M;
    double sigma, tightPow, ruinRand;
    std::vector<double> used, u, key;
    std::vector<int> sel, cand;
    std::vector<char> banned;
    std::normal_distribution<double> nd{0.0, 1.0};

    bool fits(int j) const {
        const double* w = &M.wt[(size_t)j * M.m];
        for (int i = 0; i < M.m; ++i)
            if (used[i] + w[i] > M.capacity[i] + Model::EPS) return false;
        return true;
    }
    void addItem(int j) { const double* w = &M.wt[(size_t)j * M.m]; for (int i = 0; i < M.m; ++i) used[i] += w[i]; }
    void remItem(int j) { const double* w = &M.wt[(size_t)j * M.m]; for (int i = 0; i < M.m; ++i) used[i] -= w[i]; }
    bool overloaded() const {
        for (int i = 0; i < M.m; ++i) if (used[i] > M.capacity[i] + Model::EPS) return true;
        return false;
    }
    double surKey(int j) const {
        const double* w = &M.wt[(size_t)j * M.m];
        double d = 0;
        for (int i = 0; i < M.m; ++i) d += u[i] * w[i] / std::max(M.capacity[i], Model::EPS);
        return d > 1e-300 ? M.profit[j] / d : 1e300;
    }

public:
    SurrogateRuinRepair(const Model& model, double sg, double tp, double rr)
        : M(model), sigma(sg), tightPow(tp), ruinRand(rr) {
        used.assign(M.m, 0.0); u.assign(M.m, 1.0);
        key.assign(M.n, 0.0); banned.assign(M.n, 0);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol r = s;
        std::vector<int>& x = r[0];
        std::fill(used.begin(), used.end(), 0.0);
        sel.clear();
        for (int j = 0; j < M.n; ++j) if (x[j]) { addItem(j); sel.push_back(j); }
        // multiplicadores subrogados aleatorios, sesgados a recursos apretados
        for (int i = 0; i < M.m; ++i) {
            double load = M.capacity[i] > Model::EPS ? std::min(1.5, used[i] / M.capacity[i]) : 1.0;
            u[i] = std::pow(std::max(load, 0.05), tightPow) * std::exp(sigma * nd(rng.g));
        }
        for (int j = 0; j < M.n; ++j) key[j] = surKey(j);
        // reparar entrada infactible
        while (overloaded() && !sel.empty()) {
            size_t b = 0;
            for (size_t t = 1; t < sel.size(); ++t) if (key[sel[t]] < key[sel[b]]) b = t;
            int j = sel[b]; x[j] = 0; remItem(j); banned[j] = 1;
            sel[b] = sel.back(); sel.pop_back();
        }
        if (sel.empty()) {
            cand.clear();
            for (int j = 0; j < M.n; ++j) if (!x[j] && !banned[j] && fits(j)) cand.push_back(j);
            if (!cand.empty()) {
                int best = cand[0];
                for (int j : cand) if (key[j] > key[best]) best = j;
                if (rng.uniform() < ruinRand) best = cand[rng.below((int)cand.size())];
                x[best] = 1; addItem(best);
            }
            std::fill(banned.begin(), banned.end(), 0);
            return r;
        }
        int k = (int)std::lround(strength);
        if (k < 1) k = 1;
        if (k > (int)sel.size()) k = (int)sel.size();
        // ruina: los k peores según la métrica subrogada (con ruido de rango)
        for (int j : sel) key[j] = key[j] * std::exp(ruinRand * 2.0 * (rng.uniform() - 0.5) * 2.0);
        std::nth_element(sel.begin(), sel.begin() + (k - 1), sel.end(),
                         [&](int a, int b) { return key[a] < key[b]; });
        for (int t = 0; t < k; ++t) { int j = sel[t]; x[j] = 0; remItem(j); banned[j] = 1; }
        // reparación greedy subrogada
        cand.clear();
        for (int j = 0; j < M.n; ++j) if (!x[j] && !banned[j]) { cand.push_back(j); key[j] = surKey(j); }
        std::sort(cand.begin(), cand.end(), [&](int a, int b) {
            if (key[a] != key[b]) return key[a] > key[b];
            return a < b;
        });
        for (int j : cand) if (fits(j)) { x[j] = 1; addItem(j); }
        std::fill(banned.begin(), banned.end(), 0);
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sg = params.get("sigma", 0.6);
    double tp = params.get("tight_power", 1.5);
    double rr = params.get("ruin_randomness", 0.3);
    return std::make_unique<SurrogateRuinRepair>(model, sg, tp, rr);
}
