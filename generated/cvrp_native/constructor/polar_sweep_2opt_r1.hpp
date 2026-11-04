// COMPONENT: {"name": "polar_sweep_2opt", "slot": "constructor", "params": {"tries": {"type": "int", "range": [1, 8]}, "opt_passes": {"type": "int", "range": [0, 20]}}}
class PolarSweep2Opt : public hsf::Constructor<Model> {
    const Model& m;
    int tries, passes;
    std::vector<double> ang;
    std::vector<int> order, t;

    void orderRoute(std::vector<int>& r) {
        int L = (int)r.size();
        if (L <= 1) return;
        // vecino más cercano desde el depósito
        int prev = 0;
        for (int k = 0; k < L; ++k) {
            int best = k;
            double bd = m.dist(prev, r[k]);
            for (int q = k + 1; q < L; ++q) {
                double d = m.dist(prev, r[q]);
                if (d < bd) { bd = d; best = q; }
            }
            std::swap(r[k], r[best]);
            prev = r[k];
        }
        if (L < 3 || passes <= 0) return;
        t.assign(L + 2, 0);
        for (int k = 0; k < L; ++k) t[k + 1] = r[k];
        for (int ps = 0; ps < passes; ++ps) {
            bool imp = false;
            for (int i = 0; i < L - 1; ++i) {
                for (int j = i + 2; j <= L; ++j) {
                    double delta = m.dist(t[i], t[j]) + m.dist(t[i + 1], t[j + 1])
                                 - m.dist(t[i], t[i + 1]) - m.dist(t[j], t[j + 1]);
                    if (delta < -1e-10) {
                        std::reverse(t.begin() + i + 1, t.begin() + j + 1);
                        imp = true;
                    }
                }
            }
            if (!imp) break;
        }
        for (int k = 0; k < L; ++k) r[k] = t[k + 1];
    }
public:
    PolarSweep2Opt(const Model& model, int tr, int p) : m(model), tries(std::max(1, tr)), passes(std::max(0, p)) {}

    Sol build(Rng& rng) override {
        int n = m.n;
        if (n <= 0) return {};
        if ((int)ang.size() != n + 1) {
            ang.assign(n + 1, 0.0);
            for (int c = 1; c <= n; ++c) ang[c] = std::atan2(m.ys[c] - m.ys[0], m.xs[c] - m.xs[0]);
        }
        const double TWO_PI = 2.0 * std::acos(-1.0);
        const double cap = m.capacity + 1e-9;
        Sol best;
        double bestCost = std::numeric_limits<double>::infinity();
        std::vector<double> key(n + 1);
        for (int tr = 0; tr < tries; ++tr) {
            double off = rng.uniform() * TWO_PI;
            bool rev = rng.uniform() < 0.5;
            for (int c = 1; c <= n; ++c) {
                double a = std::fmod(ang[c] - off + 2.0 * TWO_PI, TWO_PI);
                key[c] = rev ? -a : a;
            }
            order.resize(n);
            for (int i = 0; i < n; ++i) order[i] = i + 1;
            std::sort(order.begin(), order.end(), [&](int a, int b) {
                if (key[a] != key[b]) return key[a] < key[b];
                return a < b;
            });
            Sol s;
            std::vector<int> cur;
            double load = 0.0;
            for (int c : order) {
                if (!cur.empty() && load + m.demand[c] > cap) {
                    s.push_back(cur);
                    cur.clear();
                    load = 0.0;
                }
                cur.push_back(c);
                load += m.demand[c];
            }
            if (!cur.empty()) s.push_back(cur);
            for (auto& r : s) orderRoute(r);
            double c = m.distanceOf(s);
            if (c < bestCost) { bestCost = c; best = std::move(s); }
        }
        return best;
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<PolarSweep2Opt>(model, (int)params.get("tries", 3), (int)params.get("opt_passes", 5));
}
