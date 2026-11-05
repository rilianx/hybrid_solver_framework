// COMPONENT: {"name": "window_ruin_silver_meal_rebuild", "slot": "perturbation", "params": {"len_factor": {"type": "float", "range": [1.0, 4.0]}, "item_frac": {"type": "float", "range": [0.05, 0.5]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "cap_frac": {"type": "float", "range": [0.3, 1.0]}, "attempts": {"type": "int", "range": [2, 12]}}}
using Sol = Model::Solution;

static Sol fallbackFlipRR(const Model& m, const Sol& s, Rng& rng) {
    int n = m.n, T = m.T, N = n * T;
    if (N == 0) return s;
    std::vector<int> idx(N);
    std::iota(idx.begin(), idx.end(), 0);
    std::shuffle(idx.begin(), idx.end(), rng.g);
    Sol y = s;
    for (int c : idx) {
        int i = c / T, t = c % T;
        y[i][t] = 1 - y[i][t];
        if (m.feasible(y)) return y;
        y[i][t] = 1 - y[i][t];
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    y[idx[0] / T][idx[0] % T] = 1 - y[idx[0] / T][idx[0] % T];
    return y;
}

class WindowRuinSilverMeal : public hsf::Perturbation<Model> {
    const Model& m;
    double lenFactor, itemFrac, noise, capFrac;
    int attempts;
    std::vector<int> items;
public:
    WindowRuinSilverMeal(const Model& model, double lf, double fr, double nz, double cf, int at)
        : m(model), lenFactor(lf), itemFrac(fr), noise(nz), capFrac(cf), attempts(at) {
        items.resize(m.n);
    }

    void rebuildItem(Sol& y, const Sol& s, int i, int a, int b, Rng& rng) {
        int T = m.T;
        // extender hasta el período anterior al siguiente setup original tras b
        int e = T - 1;
        for (int t = b + 1; t < T; ++t) if (s[i][t]) { e = t - 1; break; }
        for (int t = a; t <= e; ++t) y[i][t] = 0;
        double sc = m.s[i] * (1.0 + noise * (2.0 * rng.uniform() - 1.0));
        sc = std::max(sc, 1e-9);
        int p = a;
        while (p <= e) {
            while (p <= e && m.d[i][p] <= 1e-12) ++p;
            if (p > e) break;
            y[i][p] = 1;
            double total = sc, lot = m.d[i][p];
            double lim = capFrac * (m.cap[p] - m.st[i]);
            int q = p;
            while (q + 1 <= e) {
                double dq = m.d[i][q + 1];
                double nt = total + m.h[i] * (double)(q + 1 - p) * dq;
                if (dq > 1e-12 && lot + dq > lim) break;
                if (nt / (double)(q + 2 - p) > total / (double)(q + 1 - p)) break;
                total = nt; lot += dq; ++q;
            }
            p = q + 1;
        }
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = m.n, T = m.T;
        if (n == 0 || T == 0) return s;
        double str = std::max(1.0, strength);
        for (int at = 0; at < attempts; ++at) {
            int L = std::min(T, std::max(2, (int)std::lround(str * lenFactor)));
            int a = rng.below(T - L + 1);
            int b = a + L - 1;
            int k = std::max(1, std::min(n, (int)std::lround(itemFrac * n * std::sqrt(str))));
            std::iota(items.begin(), items.end(), 0);
            for (int j = 0; j < k; ++j) {
                int r = j + rng.below(n - j);
                std::swap(items[j], items[r]);
            }
            Sol y = s;
            for (int j = 0; j < k; ++j) rebuildItem(y, s, items[j], a, b, rng);
            if (y == s) continue;
            if (m.feasible(y)) return y;
            // reparación: revertir ítems en orden inverso hasta lograr factibilidad
            for (int j = k - 1; j >= 1; --j) {
                y[items[j]] = s[items[j]];
                if (y == s) break;
                if (m.feasible(y)) return y;
            }
        }
        return fallbackFlipRR(m, s, rng);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double lf = params.get("len_factor", 2.0);
    double fr = params.get("item_frac", 0.2);
    double nz = params.get("noise", 0.2);
    double cf = params.get("cap_frac", 0.8);
    int at = (int)params.get("attempts", 6);
    return std::make_unique<WindowRuinSilverMeal>(model, lf, fr, nz, cf, std::max(1, at));
}
