// COMPONENT: {"name": "sequential_cheapest_insertion", "slot": "constructor", "params": {"seed_rcl": {"type": "int", "range": [1, 10]}, "mu": {"type": "float", "range": [0.0, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.2]}}}
class SequentialCheapestInsertion : public hsf::Constructor<Model> {
    const Model& m;
    int rcl;
    double mu, noise;
    std::vector<int> nxt, bestEdge, cand;
    std::vector<double> bestCost, bias;
    std::vector<char> routed;

    double insCost(int u, int c) const {
        int v = nxt[u];
        return m.dist(u, c) + m.dist(c, v) - m.dist(u, v);
    }
    void fullScan(int c) {
        int u = 0;
        double bc = std::numeric_limits<double>::infinity();
        int be = 0;
        do {
            double ic = insCost(u, c);
            if (ic < bc) { bc = ic; be = u; }
            u = nxt[u];
        } while (u != 0);
        bestCost[c] = bc;
        bestEdge[c] = be;
    }
public:
    SequentialCheapestInsertion(const Model& model, int r, double mu_, double nz)
        : m(model), rcl(std::max(1, r)), mu(mu_), noise(nz) {}

    Sol build(Rng& rng) override {
        int n = m.n;
        if (n <= 0) return {};
        nxt.assign(n + 1, 0);
        bestEdge.assign(n + 1, 0);
        bestCost.assign(n + 1, 0.0);
        bias.assign(n + 1, 1.0);
        routed.assign(n + 1, 0);
        for (int c = 1; c <= n; ++c) bias[c] = 1.0 + noise * (2.0 * rng.uniform() - 1.0);
        const double cap = m.capacity + 1e-9;
        int remaining = n;
        Sol s;
        std::vector<int> top;
        while (remaining > 0) {
            // semilla: aleatoria entre las rcl más lejanas del depósito
            top.clear();
            for (int c = 1; c <= n; ++c) if (!routed[c]) top.push_back(c);
            int k = std::min<int>(rcl, (int)top.size());
            std::partial_sort(top.begin(), top.begin() + k, top.end(), [&](int a, int b) {
                double da = m.dist(0, a), db = m.dist(0, b);
                return da > db || (da == db && a < b);
            });
            int seed = top[rng.below(k)];
            routed[seed] = 1;
            --remaining;
            nxt[0] = seed;
            nxt[seed] = 0;
            double load = m.demand[seed];
            cand.clear();
            for (int c : top) if (!routed[c] && load + m.demand[c] <= cap) { cand.push_back(c); fullScan(c); }
            while (!cand.empty()) {
                // filtrar por capacidad y elegir el mejor
                int bi = -1;
                double bv = std::numeric_limits<double>::infinity();
                size_t w = 0;
                for (size_t q = 0; q < cand.size(); ++q) {
                    int c = cand[q];
                    if (load + m.demand[c] > cap) continue;
                    cand[w++] = c;
                    double v = (bestCost[c] - mu * 2.0 * m.dist(0, c)) * bias[c];
                    if (bestCost[c] - mu * 2.0 * m.dist(0, c) < 0) v = (bestCost[c] - mu * 2.0 * m.dist(0, c)) / bias[c];
                    if (v < bv) { bv = v; bi = (int)(w - 1); }
                }
                cand.resize(w);
                if (bi < 0) break;
                int x = cand[bi];
                cand[bi] = cand.back();
                cand.pop_back();
                int u = bestEdge[x];
                int v = nxt[u];
                nxt[u] = x;
                nxt[x] = v;
                routed[x] = 1;
                --remaining;
                load += m.demand[x];
                for (int c : cand) {
                    if (load + m.demand[c] > cap) continue;
                    if (bestEdge[c] == u) { fullScan(c); continue; }
                    double a = insCost(u, c);
                    if (a < bestCost[c]) { bestCost[c] = a; bestEdge[c] = u; }
                    double b = insCost(x, c);
                    if (b < bestCost[c]) { bestCost[c] = b; bestEdge[c] = x; }
                }
            }
            std::vector<int> r;
            for (int u = nxt[0]; u != 0; u = nxt[u]) r.push_back(u);
            s.push_back(std::move(r));
        }
        return s;
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<SequentialCheapestInsertion>(model,
        (int)params.get("seed_rcl", 3), params.get("mu", 0.2), params.get("noise", 0.05));
}
