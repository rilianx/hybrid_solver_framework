// COMPONENT: {"name": "geo_ball_arc_release", "slot": "destruction", "params": {"noise": {"type": "float", "range": [0.0, 0.6]}}}
static int budgetNodesGB(int n, double ratio) {
    double total = (double)n * (double)(n + 1);
    double target = std::max(1.0, ratio * total);
    int m = (int)std::ceil((1.0 + std::sqrt(1.0 + 4.0 * target)) / 2.0);
    return std::max(2, std::min(n + 1, m));
}
static void emitArcsGB(int n, const std::vector<int>& nodes, std::vector<int>& out) {
    out.clear();
    out.reserve(nodes.size() * (nodes.size() - 1));
    for (int i : nodes)
        for (int j : nodes)
            if (i != j) out.push_back(i * n + (j < i ? j : j - 1));
    std::sort(out.begin(), out.end());
}

class GeoBallDestruction : public hsf::Destruction<Model> {
    const Model& m;
    double noise;
    std::vector<std::pair<double, int>> buf;
    std::vector<int> nodes;
public:
    GeoBallDestruction(const Model& mod, double nz) : m(mod), noise(nz) {}
    std::vector<int> destroy(const Model::Solution& s, double ratio, Rng& rng) override {
        (void)s;
        std::vector<int> out;
        int n = m.n;
        if (n < 1) return out;
        int k = budgetNodesGB(n, ratio) - 1;  // clientes a liberar
        int seed = 1 + rng.below(n);
        buf.clear();
        buf.reserve(n);
        for (int c = 1; c <= n; ++c) {
            double d = (c == seed) ? -1.0 : m.dist(seed, c) * (1.0 + noise * rng.uniform());
            buf.emplace_back(d, c);
        }
        if (k < n) std::nth_element(buf.begin(), buf.begin() + (k - 1), buf.end());
        nodes.clear();
        nodes.push_back(0);
        for (int i = 0; i < k; ++i) nodes.push_back(buf[i].second);
        emitArcsGB(n, nodes, out);
        return out;
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.2);
    return std::make_unique<GeoBallDestruction>(model, noise);
}
