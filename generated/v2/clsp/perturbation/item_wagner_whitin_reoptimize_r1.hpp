// COMPONENT: {"name": "item_wagner_whitin_reoptimize", "slot": "perturbation", "params": {"items_per_strength": {"type": "float", "range": [0.5, 3.0]}, "cost_noise": {"type": "float", "range": [0.0, 0.8]}, "p_forbid": {"type": "float", "range": [0.0, 1.0]}}}
using Sol = Model::Solution;

static const double kEps = 1e-6;

static double shortfallOf(const Model& m, const Sol& s) {
    double a = 0, b = 0, c = 0;
    m.evaluate(s, a, b, c);
    return c;
}

static Sol fallbackDistinct(const Model& m, const Sol& s, double base, Rng& rng) {
    int n = m.n, P = m.P;
    Sol c = s;
    if (n <= 0 || P <= 0) return c;
    std::vector<int> cells(n * P);
    std::iota(cells.begin(), cells.end(), 0);
    std::shuffle(cells.begin(), cells.end(), rng.g);
    for (int id : cells) {
        int i = id / P, t = id % P;
        c[i][t] ^= 1;
        if (shortfallOf(m, c) <= base + kEps) return c;
        c[i][t] ^= 1;
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    c[0][0] ^= 1;
    return c;
}

class ItemWagnerWhitinReoptimize : public hsf::Perturbation<Model> {
    const Model& m;
    double perStr, noise, pForbid;
    std::vector<double> f;
    std::vector<int> from;
    std::vector<char> forb;
    std::vector<int> order, ones;

    // uncapacitated lot sizing for item i with setup cost sc; returns false if infeasible
    bool ww(int i, double sc, std::vector<int>& row) {
        int P = m.P;
        const double INF = std::numeric_limits<double>::infinity();
        f.assign(P + 1, INF);
        from.assign(P + 1, -2);
        f[0] = 0.0;
        double hh = m.h[i];
        for (int t = 1; t <= P; ++t) {
            if (m.d[i][t - 1] <= 0.0 && f[t - 1] < INF) { f[t] = f[t - 1]; from[t] = -1; }
            double hold = 0.0, D = 0.0;
            for (int j = t - 1; j >= 0; --j) {
                if (j < t - 1) { D += m.d[i][j + 1]; hold += hh * D; }
                if (!forb[j] && f[j] < INF) {
                    double c = f[j] + sc + hold;
                    if (c < f[t] - 1e-12) { f[t] = c; from[t] = j; }
                }
            }
        }
        if (!(f[P] < INF)) return false;
        row.assign(P, 0);
        int t = P;
        while (t > 0) {
            int j = from[t];
            if (j == -1) { --t; continue; }
            if (j < 0) return false;
            row[j] = 1;
            t = j;
        }
        return true;
    }

public:
    ItemWagnerWhitinReoptimize(const Model& model, double ps, double nz, double pf)
        : m(model), perStr(ps), noise(nz), pForbid(pf) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = m.n, P = m.P;
        if (n <= 0 || P <= 0) return s;
        Sol cur = s;
        double base = shortfallOf(m, cur);
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * perStr));
        k = std::min(k, n);
        order.resize(n);
        std::iota(order.begin(), order.end(), 0);
        std::shuffle(order.begin(), order.end(), rng.g);
        std::vector<int> row, old, uni;
        for (int q = 0; q < k; ++q) {
            int i = order[q];
            double sc = m.s[i] * std::max(0.05, 1.0 + noise * (2.0 * rng.uniform() - 1.0));
            forb.assign(P, 0);
            if (rng.uniform() < pForbid) {
                ones.clear();
                for (int t = 0; t < P; ++t) if (cur[i][t]) ones.push_back(t);
                if (!ones.empty()) forb[ones[rng.below((int)ones.size())]] = 1;
            }
            bool ok = ww(i, sc, row);
            if (!ok) { forb.assign(P, 0); ok = ww(i, sc, row); }
            if (!ok) continue;
            old = cur[i];
            if (row == old) continue;
            cur[i] = row;
            double v = shortfallOf(m, cur);
            if (v <= base + kEps) { base = std::min(base, v); continue; }
            uni.assign(P, 0);
            for (int t = 0; t < P; ++t) uni[t] = (row[t] | old[t]) ? 1 : 0;
            if (uni != old) {
                cur[i] = uni;
                v = shortfallOf(m, cur);
                if (v <= base + kEps) { base = std::min(base, v); continue; }
            }
            cur[i] = old;
        }
        if (cur != s) return cur;
        return fallbackDistinct(m, s, shortfallOf(m, s), rng);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("items_per_strength", 1.0);
    double nz = params.get("cost_noise", 0.3);
    double pf = params.get("p_forbid", 0.5);
    return std::make_unique<ItemWagnerWhitinReoptimize>(model, ps, nz, pf);
}
