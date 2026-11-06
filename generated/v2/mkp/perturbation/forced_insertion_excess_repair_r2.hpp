// COMPONENT: {"name": "forced_insertion_excess_repair", "slot": "perturbation", "params": {"tournament": {"type": "int", "range": [1, 6]}, "allow_readd": {"type": "int", "range": [0, 1]}, "cluster_mult": {"type": "float", "range": [1.0, 3.0]}, "sim_noise": {"type": "float", "range": [0.0, 0.3]}}}
class ForcedInsertionRepair : public hsf::Perturbation<Model> {
    const Model& M;
    int tour;
    bool allowReadd;
    double clusterMult, simNoise;
    std::vector<double> ratio, used, fused, zero, nw;
    std::vector<int> order, cand, pool, sel, forcedList;
    std::vector<std::pair<double, int>> simv;
    std::vector<char> forced, removed;

    bool fitsIn(const std::vector<double>& U, int j) const {
        const double* w = &M.wt[(size_t)j * M.m];
        for (int i = 0; i < M.m; ++i)
            if (U[i] + w[i] > M.capacity[i] + Model::EPS) return false;
        return true;
    }
    static void addTo(std::vector<double>& U, const double* w, int m) { for (int i = 0; i < m; ++i) U[i] += w[i]; }
    static void subFrom(std::vector<double>& U, const double* w, int m) { for (int i = 0; i < m; ++i) U[i] -= w[i]; }
    bool overloaded() const {
        for (int i = 0; i < M.m; ++i) if (used[i] > M.capacity[i] + Model::EPS) return true;
        return false;
    }

public:
    ForcedInsertionRepair(const Model& model, int t, bool ar, double cm, double sn)
        : M(model), tour(std::max(1, t)), allowReadd(ar), clusterMult(std::max(1.0, cm)), simNoise(std::max(0.0, sn)) {
        const int m = M.m;
        ratio.assign(M.n, 0.0);
        nw.assign((size_t)M.n * m, 0.0);
        for (int j = 0; j < M.n; ++j) {
            double d = 0, nn = 0;
            for (int i = 0; i < m; ++i) {
                double v = M.wt[(size_t)j * m + i] / std::max(M.capacity[i], Model::EPS);
                d += v; nn += v * v;
                nw[(size_t)j * m + i] = v;
            }
            ratio[j] = d > 0 ? M.profit[j] / d : 1e300;
            nn = std::sqrt(nn);
            for (int i = 0; i < m; ++i) nw[(size_t)j * m + i] = nn > 0 ? nw[(size_t)j * m + i] / nn : 0.0;
        }
        order.resize(M.n);
        std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return ratio[a] > ratio[b]; });
        used.assign(m, 0.0); fused.assign(m, 0.0); zero.assign(m, 0.0);
        forced.assign(M.n, 0); removed.assign(M.n, 0);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol r = s;
        std::vector<int>& x = r[0];
        const int m = M.m;
        std::fill(used.begin(), used.end(), 0.0);
        std::fill(fused.begin(), fused.end(), 0.0);
        cand.clear();
        for (int j = 0; j < M.n; ++j) {
            if (x[j]) addTo(used, &M.wt[(size_t)j * m], m);
            else if (fitsIn(zero, j)) cand.push_back(j);
        }
        if (cand.empty()) {
            sel.clear();
            for (int j = 0; j < M.n; ++j) if (x[j]) sel.push_back(j);
            if (!sel.empty()) x[sel[rng.below((int)sel.size())]] = 0;
            return r;
        }
        // semilla: ítem bloqueado (no cabe en la capacidad residual), por torneo de ratio
        pool.clear();
        for (int j : cand) if (!fitsIn(used, j)) pool.push_back(j);
        const std::vector<int>& src = pool.empty() ? cand : pool;
        int seed = -1;
        for (int c = 0; c < tour; ++c) {
            int j = src[rng.below((int)src.size())];
            if (seed < 0 || ratio[j] > ratio[seed]) seed = j;
        }
        int k = (int)std::lround(std::max(1.0, strength) * clusterMult);
        if (k < 1) k = 1;
        forcedList.clear();
        forced[seed] = 1; forcedList.push_back(seed);
        addTo(fused, &M.wt[(size_t)seed * m], m);
        // clúster: no elegidos con perfil de consumo similar a la semilla
        if (k > 1) {
            simv.clear();
            const double* ns = &nw[(size_t)seed * m];
            for (int j : cand) {
                if (j == seed) continue;
                const double* nj = &nw[(size_t)j * m];
                double d = 0;
                for (int i = 0; i < m; ++i) d += ns[i] * nj[i];
                simv.emplace_back(d + simNoise * rng.uniform(), j);
            }
            size_t lim = std::min(simv.size(), (size_t)(3 * k));
            if (lim < simv.size())
                std::nth_element(simv.begin(), simv.begin() + lim, simv.end(),
                                 [](const std::pair<double, int>& a, const std::pair<double, int>& b) { return a.first > b.first; });
            std::sort(simv.begin(), simv.begin() + lim,
                      [](const std::pair<double, int>& a, const std::pair<double, int>& b) { return a.first > b.first; });
            for (size_t t = 0; t < lim && (int)forcedList.size() < k; ++t) {
                int j = simv[t].second;
                if (fitsIn(fused, j)) {
                    forced[j] = 1; forcedList.push_back(j);
                    addTo(fused, &M.wt[(size_t)j * m], m);
                }
            }
        }
        for (int j : forcedList) { x[j] = 1; addTo(used, &M.wt[(size_t)j * m], m); }
        // reparación: quitar no forzados con menor beneficio por aporte al exceso
        sel.clear();
        for (int j = 0; j < M.n; ++j) if (x[j] && !forced[j]) sel.push_back(j);
        while (overloaded() && !sel.empty()) {
            int bi = -1; double bs = 0;
            for (size_t t = 0; t < sel.size(); ++t) {
                int j = sel[t];
                const double* w = &M.wt[(size_t)j * m];
                double d = 0;
                for (int i = 0; i < m; ++i) {
                    double ex = used[i] - M.capacity[i];
                    if (ex > Model::EPS && w[i] > 0) {
                        double c = std::max(M.capacity[i], Model::EPS);
                        d += (ex / c) * (std::min(w[i], ex) / c + 1e-12);
                    }
                }
                if (d <= 0) continue;
                double sc = M.profit[j] / d;
                if (bi < 0 || sc < bs) { bi = (int)t; bs = sc; }
            }
            if (bi < 0) break;
            int j = sel[bi];
            x[j] = 0; removed[j] = 1;
            subFrom(used, &M.wt[(size_t)j * m], m);
            sel[bi] = sel.back(); sel.pop_back();
        }
        if (overloaded()) {
            // no se pudo reparar: deshacer forzados
            for (int j : forcedList) { x[j] = 0; subFrom(used, &M.wt[(size_t)j * m], m); }
        }
        // relleno greedy con el orden estático (sin readmitir los expulsados salvo allow_readd)
        for (int j : order) {
            if (x[j]) continue;
            if (removed[j] && !allowReadd) continue;
            if (fitsIn(used, j)) { x[j] = 1; addTo(used, &M.wt[(size_t)j * m], m); }
        }
        for (int j : forcedList) forced[j] = 0;
        std::fill(removed.begin(), removed.end(), 0);
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int t = (int)params.get("tournament", 2);
    bool ar = params.get("allow_readd", 0) > 0.5;
    double cm = params.get("cluster_mult", 1.5);
    double sn = params.get("sim_noise", 0.1);
    return std::make_unique<ForcedInsertionRepair>(model, t, ar, cm, sn);
}
