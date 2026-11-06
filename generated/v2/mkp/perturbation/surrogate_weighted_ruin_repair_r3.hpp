// COMPONENT: {"name": "surrogate_weighted_ruin_repair", "slot": "perturbation", "params": {"sigma": {"type": "float", "range": [0.1, 2.0]}, "tight_power": {"type": "float", "range": [0.0, 4.0]}, "align_prob": {"type": "float", "range": [0.0, 1.0]}, "core_mult": {"type": "float", "range": [0.5, 4.0]}}}
class SurrogateRuinRepair : public hsf::Perturbation<Model> {
    const Model& M;
    double sigma, tightPow, alignProb, coreMult;
    std::vector<double> used, u, key, sw, over;
    std::vector<int> sel, order, core;
    std::vector<char> banned, forced;
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
    double relief(int j) const {
        const double* w = &M.wt[(size_t)j * M.m];
        double r = 0;
        for (int i = 0; i < M.m; ++i)
            if (over[i] > 0 && w[i] > 0)
                r += std::min(w[i], over[i]) / std::max(M.capacity[i], Model::EPS);
        return r;
    }
    void computeOver() {
        for (int i = 0; i < M.m; ++i) {
            double o = used[i] - M.capacity[i];
            over[i] = o > Model::EPS ? o : 0.0;
        }
    }
    // expulsión dirigida a la sobrecarga; prefiere no tocar los forzados
    void ejectUntilFeasible(std::vector<int>& x) {
        while (overloaded() && !sel.empty()) {
            computeOver();
            int bestT = -1; double bestS = 1e300;
            for (int pass = 0; pass < 2 && bestT < 0; ++pass) {
                for (size_t t = 0; t < sel.size(); ++t) {
                    int j = sel[t];
                    if ((pass == 0) == (bool)forced[j]) continue;
                    double rl = relief(j);
                    if (rl <= 1e-15) continue;
                    double sc = M.profit[j] / rl;
                    if (sc < bestS) { bestS = sc; bestT = (int)t; }
                }
            }
            if (bestT < 0) break;
            int j = sel[bestT];
            x[j] = 0; remItem(j); banned[j] = 1;
            sel[bestT] = sel.back(); sel.pop_back();
        }
    }

public:
    SurrogateRuinRepair(const Model& model, double sg, double tp, double ap, double cm)
        : M(model), sigma(sg), tightPow(tp), alignProb(ap), coreMult(cm) {
        used.assign(M.m, 0.0); u.assign(M.m, 1.0); over.assign(M.m, 0.0);
        key.assign(M.n, 0.0); sw.assign(M.n, 0.0);
        banned.assign(M.n, 0); forced.assign(M.n, 0);
        order.resize(M.n);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol r = s;
        std::vector<int>& x = r[0];
        const int n = M.n;
        std::fill(used.begin(), used.end(), 0.0);
        for (int j = 0; j < n; ++j) if (x[j]) addItem(j);

        // multiplicadores subrogados aleatorios, sesgados a recursos apretados
        double capS = 0;
        for (int i = 0; i < M.m; ++i) {
            double load = M.capacity[i] > Model::EPS ? std::min(1.5, used[i] / M.capacity[i]) : 1.0;
            u[i] = std::pow(std::max(load, 0.05), tightPow) * std::exp(sigma * nd(rng.g));
            capS += u[i];
        }
        for (int j = 0; j < n; ++j) {
            const double* w = &M.wt[(size_t)j * M.m];
            double d = 0;
            for (int i = 0; i < M.m; ++i) d += u[i] * w[i] / std::max(M.capacity[i], Model::EPS);
            sw[j] = d;
            key[j] = d > 1e-300 ? M.profit[j] / d : 1e300;
        }
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            if (key[a] != key[b]) return key[a] > key[b];
            return a < b;
        });

        // punto de corte de la mochila subrogada (relajación de una restricción)
        int brk = n;
        double acc = 0;
        for (int t = 0; t < n; ++t) {
            acc += sw[order[t]];
            if (acc > capS + Model::EPS) { brk = t; break; }
        }
        int k = (int)std::lround(strength);
        if (k < 1) k = 1;
        int half = std::max(1, (int)std::lround(coreMult * k));
        int lo = std::max(0, brk - half), hi = std::min(n, brk + half);

        // alineación fuera del núcleo con el orden subrogado
        for (int t = 0; t < lo; ++t) {
            int j = order[t];
            if (!x[j] && rng.uniform() < alignProb) { x[j] = 1; forced[j] = 1; }
        }
        for (int t = hi; t < n; ++t) {
            int j = order[t];
            if (x[j] && rng.uniform() < alignProb) { x[j] = 0; banned[j] = 1; }
        }
        // inversiones aleatorias dentro del núcleo
        core.assign(order.begin() + lo, order.begin() + hi);
        int cs = (int)core.size();
        int kk = std::min(k, cs);
        for (int t = 0; t < kk; ++t) {
            int q = t + rng.below(cs - t);
            std::swap(core[t], core[q]);
            int j = core[t];
            x[j] ^= 1;
            if (x[j]) forced[j] = 1; else banned[j] = 1;
        }

        // reconstruir carga y reparar
        std::fill(used.begin(), used.end(), 0.0);
        sel.clear();
        for (int j = 0; j < n; ++j) if (x[j]) { addItem(j); sel.push_back(j); }
        ejectUntilFeasible(x);

        // relleno en orden subrogado (sin reintroducir lo expulsado/apagado)
        for (int t = 0; t < n; ++t) {
            int j = order[t];
            if (!x[j] && !banned[j] && fits(j)) { x[j] = 1; addItem(j); }
        }
        std::fill(banned.begin(), banned.end(), 0);
        std::fill(forced.begin(), forced.end(), 0);
        return r;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sg = params.get("sigma", 0.6);
    double tp = params.get("tight_power", 1.5);
    double ap = params.get("align_prob", 0.5);
    double cm = params.get("core_mult", 1.5);
    return std::make_unique<SurrogateRuinRepair>(model, sg, tp, ap, cm);
}
