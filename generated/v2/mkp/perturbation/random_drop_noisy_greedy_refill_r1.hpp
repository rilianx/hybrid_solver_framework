// COMPONENT: {"name": "random_drop_noisy_greedy_refill", "slot": "perturbation", "params": {"noise": {"type": "float", "range": [0.0, 1.5]}, "extra_drop_prob": {"type": "float", "range": [0.0, 0.5]}}}
class RandomDropNoisyRefill : public hsf::Perturbation<Model> {
    const Model& M;
    double noise, extraDrop;
    std::vector<double> ratio, used, key;
    std::vector<int> sel, cand;
    std::vector<char> banned;

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

public:
    RandomDropNoisyRefill(const Model& model, double nz, double ed)
        : M(model), noise(nz), extraDrop(ed) {
        ratio.assign(M.n, 0.0);
        for (int j = 0; j < M.n; ++j) {
            double d = 0;
            for (int i = 0; i < M.m; ++i) d += M.wt[(size_t)j * M.m + i] / std::max(M.capacity[i], Model::EPS);
            ratio[j] = d > 0 ? M.profit[j] / d : 1e300;
        }
        used.assign(M.m, 0.0);
        banned.assign(M.n, 0);
        key.assign(M.n, 0.0);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol r = s;
        std::vector<int>& x = r[0];
        std::fill(used.begin(), used.end(), 0.0);
        sel.clear();
        for (int j = 0; j < M.n; ++j) if (x[j]) { addItem(j); sel.push_back(j); }
        // reparar una entrada infactible (por si acaso): quitar el de peor razón
        while (overloaded() && !sel.empty()) {
            size_t b = 0;
            for (size_t t = 1; t < sel.size(); ++t) if (ratio[sel[t]] < ratio[sel[b]]) b = t;
            int j = sel[b]; x[j] = 0; remItem(j); banned[j] = 1;
            sel[b] = sel.back(); sel.pop_back();
        }
        if (sel.empty()) {
            cand.clear();
            for (int j = 0; j < M.n; ++j) if (!x[j] && !banned[j] && fits(j)) cand.push_back(j);
            if (!cand.empty()) { int j = cand[rng.below((int)cand.size())]; x[j] = 1; addItem(j); }
            std::fill(banned.begin(), banned.end(), 0);
            return r;
        }
        int k = (int)std::lround(strength);
        if (k < 1) k = 1;
        while (k < (int)sel.size() && rng.uniform() < extraDrop) ++k;
        if (k > (int)sel.size()) k = (int)sel.size();
        for (int t = 0; t < k; ++t) {
            int p = t + rng.below((int)sel.size() - t);
            std::swap(sel[t], sel[p]);
            int j = sel[t];
            x[j] = 0; remItem(j); banned[j] = 1;
        }
        cand.clear();
        for (int j = 0; j < M.n; ++j) {
            if (x[j] || banned[j]) continue;
            cand.push_back(j);
            key[j] = ratio[j] * std::exp(noise * (2.0 * rng.uniform() - 1.0));
        }
        std::sort(cand.begin(), cand.end(), [&](int a, int b) { return key[a] > key[b]; });
        for (int j : cand) if (fits(j)) { x[j] = 1; addItem(j); }
        std::fill(banned.begin(), banned.end(), 0);
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double nz = params.get("noise", 0.3);
    double ed = params.get("extra_drop_prob", 0.1);
    return std::make_unique<RandomDropNoisyRefill>(model, nz, ed);
}
