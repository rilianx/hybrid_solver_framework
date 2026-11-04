// COMPONENT: {"name": "randomized_clarke_wright_savings", "slot": "constructor", "params": {"lambda": {"type": "float", "range": [0.6, 1.8]}, "noise": {"type": "float", "range": [0.0, 0.3]}, "neighbors": {"type": "int", "range": [10, 120]}}}
class RandomizedClarkeWright : public hsf::Constructor<Model> {
    const Model& m;
    double lambda, noise;
    int K;
    std::vector<std::vector<int>> nb;
    struct P { double s; int i, j; };
    std::vector<P> ps;

    void buildNeighbors() {
        int n = m.n;
        int k = std::min(K, n - 1);
        nb.assign(n + 1, {});
        std::vector<int> cand;
        cand.reserve(n);
        for (int i = 1; i <= n; ++i) {
            cand.clear();
            for (int j = 1; j <= n; ++j) if (j != i) cand.push_back(j);
            if (k > 0) {
                std::partial_sort(cand.begin(), cand.begin() + k, cand.end(),
                    [&](int a, int b) {
                        double da = m.dist(i, a), db = m.dist(i, b);
                        return da < db || (da == db && a < b);
                    });
                nb[i].assign(cand.begin(), cand.begin() + k);
            }
        }
    }
public:
    RandomizedClarkeWright(const Model& model, double l, double nz, int k)
        : m(model), lambda(l), noise(nz), K(std::max(1, k)) {}

    Sol build(Rng& rng) override {
        int n = m.n;
        if (n <= 0) return {};
        if (nb.empty()) buildNeighbors();
        ps.clear();
        for (int i = 1; i <= n; ++i) {
            double di = m.dist(0, i);
            for (int j : nb[i]) {
                double s = di + m.dist(0, j) - lambda * m.dist(i, j);
                if (noise > 0.0) s *= 1.0 + noise * (2.0 * rng.uniform() - 1.0);
                if (s > 0.0) ps.push_back({s, i, j});
            }
        }
        std::sort(ps.begin(), ps.end(), [](const P& a, const P& b) {
            if (a.s != b.s) return a.s > b.s;
            if (a.i != b.i) return a.i < b.i;
            return a.j < b.j;
        });
        std::vector<std::vector<int>> r(n + 1);
        std::vector<int> rid(n + 1);
        std::vector<double> load(n + 1, 0.0);
        for (int c = 1; c <= n; ++c) { r[c] = {c}; rid[c] = c; load[c] = m.demand[c]; }
        const double cap = m.capacity + 1e-9;
        for (const P& p : ps) {
            int a = rid[p.i], b = rid[p.j];
            if (a == b) continue;
            if (load[a] + load[b] > cap) continue;
            auto& A = r[a];
            auto& B = r[b];
            if (A.front() != p.i && A.back() != p.i) continue;
            if (B.front() != p.j && B.back() != p.j) continue;
            if (A.back() != p.i) std::reverse(A.begin(), A.end());
            if (B.front() != p.j) std::reverse(B.begin(), B.end());
            if (A.size() >= B.size()) {
                for (int c : B) { rid[c] = a; A.push_back(c); }
                B.clear();
                load[a] += load[b];
            } else {
                for (int c : A) rid[c] = b;
                B.insert(B.begin(), A.begin(), A.end());
                A.clear();
                load[b] += load[a];
            }
        }
        Sol s;
        for (int c = 1; c <= n; ++c) if (!r[c].empty()) s.push_back(std::move(r[c]));
        return s;
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<RandomizedClarkeWright>(model,
        params.get("lambda", 1.0), params.get("noise", 0.1), (int)params.get("neighbors", 40));
}
