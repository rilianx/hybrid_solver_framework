// COMPONENT: {"name": "route_centroid_cluster_release", "slot": "destruction", "params": {"noise": {"type": "float", "range": [0.0, 1.0]}, "partial": {"type": "cat", "values": ["segment", "skip"]}}}
static int budgetNodesRC(int n, double ratio) {
    double total = (double)n * (double)(n + 1);
    double target = std::max(1.0, ratio * total);
    int m = (int)std::ceil((1.0 + std::sqrt(1.0 + 4.0 * target)) / 2.0);
    return std::max(2, std::min(n + 1, m));
}
static void emitArcsRC(int n, const std::vector<int>& nodes, std::vector<int>& out) {
    out.clear();
    out.reserve(nodes.size() * (nodes.size() - 1));
    for (int i : nodes)
        for (int j : nodes)
            if (i != j) out.push_back(i * n + (j < i ? j : j - 1));
    std::sort(out.begin(), out.end());
}

class RouteClusterDestruction : public hsf::Destruction<Model> {
    const Model& m;
    double noise;
    bool segment;
    std::vector<char> seen, mark;
    std::vector<std::vector<int>> routes;
    std::vector<double> cx, cy;
    std::vector<std::pair<double, int>> order, rest;
    std::vector<int> nodes;
public:
    RouteClusterDestruction(const Model& mod, double nz, bool seg) : m(mod), noise(nz), segment(seg) {}
    std::vector<int> destroy(const Model::Solution& s, double ratio, Rng& rng) override {
        std::vector<int> out;
        int n = m.n;
        if (n < 1) return out;
        int k = budgetNodesRC(n, ratio) - 1;
        seen.assign(n + 1, 0);
        mark.assign(n + 1, 0);
        routes.clear(); cx.clear(); cy.clear();
        for (const auto& r : s) {
            std::vector<int> rr;
            double sx = 0, sy = 0;
            for (int c : r) {
                if (c < 1 || c > n || seen[c]) continue;
                seen[c] = 1;
                rr.push_back(c);
                sx += m.xs[c]; sy += m.ys[c];
            }
            if (rr.empty()) continue;
            cx.push_back(sx / rr.size());
            cy.push_back(sy / rr.size());
            routes.push_back(std::move(rr));
        }
        nodes.clear();
        nodes.push_back(0);
        int sel = 0;
        double ox = m.xs[0], oy = m.ys[0];
        if (!routes.empty()) {
            int R = (int)routes.size();
            int r0 = rng.below(R);
            ox = cx[r0]; oy = cy[r0];
            order.clear();
            for (int r = 0; r < R; ++r) {
                double d = (r == r0) ? -1.0
                    : std::hypot(cx[r] - ox, cy[r] - oy) * (1.0 + noise * rng.uniform());
                order.emplace_back(d, r);
            }
            std::sort(order.begin(), order.end());
            for (auto& pr : order) {
                if (sel >= k) break;
                const auto& rr = routes[pr.second];
                int sz = (int)rr.size();
                if (sel + sz <= k) {
                    for (int c : rr) { mark[c] = 1; nodes.push_back(c); }
                    sel += sz;
                } else if (segment || pr.second == r0) {
                    int need = k - sel;
                    int st = rng.below(sz - need + 1);
                    for (int i = st; i < st + need; ++i) { mark[rr[i]] = 1; nodes.push_back(rr[i]); }
                    sel += need;
                    break;
                }
            }
        }
        if (sel < k) {  // completar con los clientes más cercanos al centro del cúmulo
            rest.clear();
            for (int c = 1; c <= n; ++c)
                if (!mark[c]) rest.emplace_back(std::hypot(m.xs[c] - ox, m.ys[c] - oy), c);
            int need = std::min((int)rest.size(), k - sel);
            if (need > 0) {
                std::nth_element(rest.begin(), rest.begin() + (need - 1), rest.end());
                for (int i = 0; i < need; ++i) { mark[rest[i].second] = 1; nodes.push_back(rest[i].second); }
                sel += need;
            }
        }
        if (nodes.size() < 2) nodes.push_back(1 + rng.below(n));
        emitArcsRC(n, nodes, out);
        return out;
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.3);
    bool seg = params.text("partial", "segment") == "segment";
    return std::make_unique<RouteClusterDestruction>(model, noise, seg);
}
