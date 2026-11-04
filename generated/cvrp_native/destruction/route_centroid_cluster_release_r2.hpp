// COMPONENT: {"name": "route_centroid_cluster_release", "slot": "destruction", "params": {"noise": {"type": "float", "range": [0.0, 1.0]}, "partial": {"type": "cat", "values": ["segment", "skip"]}, "degree": {"type": "int", "range": [3, 12]}}}
class RouteClusterDestruction : public hsf::Destruction<Model> {
    const Model& m;
    double noise;
    bool segment;
    int L;
    std::vector<char> seen, inS;
    std::vector<int> pred, succ;
    std::vector<std::vector<int>> routes;
    std::vector<double> cx, cy;
    std::vector<std::pair<double, int>> order, rest, cand;
    std::vector<int> S;
public:
    RouteClusterDestruction(const Model& mod, double nz, bool seg, int deg)
        : m(mod), noise(nz), segment(seg), L(std::max(1, deg)) {}

    std::vector<int> destroy(const Model::Solution& s, double ratio, Rng& rng) override {
        std::vector<int> out;
        int n = m.n;
        if (n < 1) return out;
        double B = std::max(1.0, ratio * (double)n * (double)(n + 1));
        int k = (int)std::ceil(B / (double)(L + 4));
        k = std::max(1, std::min(n, k));

        seen.assign(n + 1, 0);
        inS.assign(n + 1, 0);
        pred.assign(n + 1, -1);
        succ.assign(n + 1, -1);
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
            int sz = (int)rr.size();
            for (int i = 0; i < sz; ++i) {
                pred[rr[i]] = i > 0 ? rr[i - 1] : 0;
                succ[rr[i]] = i + 1 < sz ? rr[i + 1] : 0;
            }
            cx.push_back(sx / sz);
            cy.push_back(sy / sz);
            routes.push_back(std::move(rr));
        }

        S.clear();
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
                    for (int c : rr) { inS[c] = 1; S.push_back(c); }
                    sel += sz;
                } else if (segment || pr.second == r0) {
                    int need = k - sel;
                    int st = rng.below(sz - need + 1);
                    for (int i = st; i < st + need; ++i) { inS[rr[i]] = 1; S.push_back(rr[i]); }
                    sel += need;
                    break;
                }
            }
        }
        if (sel < k) {
            rest.clear();
            for (int c = 1; c <= n; ++c)
                if (!inS[c]) rest.emplace_back(std::hypot(m.xs[c] - ox, m.ys[c] - oy), c);
            int need = std::min((int)rest.size(), k - sel);
            if (need > 0) {
                std::nth_element(rest.begin(), rest.begin() + (need - 1), rest.end());
                for (int i = 0; i < need; ++i) { inS[rest[i].second] = 1; S.push_back(rest[i].second); }
                sel += need;
            }
        }
        if (S.empty()) { int c = 1 + rng.below(n); inS[c] = 1; S.push_back(c); }

        auto add = [&](int i, int j) {
            if (i < 0 || j < 0 || i == j) return;
            out.push_back(i * n + (j < i ? j : j - 1));
        };
        out.reserve(S.size() * (size_t)(L + 5));
        for (int i : S) {
            add(0, i); add(i, 0);
            if (pred[i] >= 0) add(pred[i], i);
            if (succ[i] >= 0) add(i, succ[i]);
            // puente que cierra el hueco de cada segmento liberado
            if (pred[i] >= 0 && (pred[i] == 0 || !inS[pred[i]])) {
                int e = i;
                while (succ[e] > 0 && inS[succ[e]]) e = succ[e];
                int a = pred[i], b = succ[e];
                if (b >= 0 && a != b) add(a, b);
            }
        }
        int sn = (int)S.size();
        if (sn > 1) {
            int take = std::min(L, sn - 1);
            for (int i : S) {
                cand.clear();
                for (int j : S)
                    if (j != i) cand.emplace_back(std::hypot(m.xs[j] - m.xs[i], m.ys[j] - m.ys[i]), j);
                if (take < (int)cand.size())
                    std::nth_element(cand.begin(), cand.begin() + (take - 1), cand.end());
                for (int t = 0; t < take; ++t) add(i, cand[t].second);
            }
        }
        std::sort(out.begin(), out.end());
        out.erase(std::unique(out.begin(), out.end()), out.end());
        return out;
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = params.get("noise", 0.3);
    bool seg = params.text("partial", "segment") == "segment";
    int deg = (int)params.get("degree", 6);
    return std::make_unique<RouteClusterDestruction>(model, noise, seg, deg);
}
