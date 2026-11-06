// COMPONENT: {"name": "forced_insertion_excess_repair", "slot": "perturbation", "params": {"tournament": {"type": "int", "range": [1, 6]}, "allow_readd": {"type": "int", "range": [0, 1]}}}
class ForcedInsertionRepair : public hsf::Perturbation<Model> {
    const Model& M;
    int tour;
    bool allowReadd;
    std::vector<double> ratio, used, fused;
    std::vector<int> order, cand, sel;
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
    ForcedInsertionRepair(const Model& model, int t, bool ar) : M(model), tour(std::max(1, t)), allowReadd(ar) {
        ratio.assign(M.n, 0.0);
        for (int j = 0; j < M.n; ++j) {
            double d = 0;
            for (int i = 0; i < M.m; ++i) d += M.wt[(size_t)j * M.m + i] / std::max(M.capacity[i], Model::EPS);
            ratio[j] = d > 0 ? M.profit[j] / d : 1e300;
        }
        order.resize(M.n);
        std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return ratio[a] > ratio[b]; });
        used.assign(M.m, 0.0); fused.assign(M.m, 0.0);
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
            else cand.push_back(j);
        }
        int k = (int)std::lround(strength);
        if (k < 1) k = 1;
        // selección por torneo de ítems a forzar (el conjunto forzado debe caber solo)
        for (size_t t = 0; t < cand.size(); ++t) {
            size_t p = t + (size_t)rng.below((int)(cand.size() - t));
            std::swap(cand[t], cand[p]);
        }
        std::vector<int> forcedList;
        size_t pos = 0;
        while ((int)forcedList.size() < k && pos < cand.size()) {
            int best = -1;
            for (int c = 0; c < tour && pos < cand.size(); ++c) {
                int j = cand[pos++];
                if (fitsIn(fused, j) && (best < 0 || ratio[j] > ratio[best])) best = j;
            }
            if (best >= 0) {
                forced[best] = 1; forcedList.push_back(best);
                addTo(fused, &M.wt[(size_t)best * m], m);
            }
        }
        if (forcedList.empty()) {
            // nada entra: alternativa, sacar un elegido al azar
            sel.clear();
            for (int j = 0; j < M.n; ++j) if (x[j]) sel.push_back(j);
            if (!sel.empty()) x[sel[rng.below((int)sel.size())]] = 0;
            return r;
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
        // relleno greedy con el orden estático
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
    return std::make_unique<ForcedInsertionRepair>(model, t, ar);
}
