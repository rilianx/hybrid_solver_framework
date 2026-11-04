// COMPONENT: {"name": "giant_tour_double_bridge_split", "slot": "perturbation", "params": {"bridges_base": {"type": "int", "range": [1, 4]}, "bridges_per_strength": {"type": "float", "range": [0.0, 2.0]}, "reverse_route_prob": {"type": "float", "range": [0.0, 1.0]}, "extra_reversal_prob": {"type": "float", "range": [0.0, 1.0]}}}
using Sol = Model::Solution;

static void ensureDistinct(Sol& out, const Sol& s, const Model& m) {
    if (out != s) return;
    for (auto& r : out) if (r.size() >= 2) { int c = r.back(); r.pop_back(); out.push_back({c}); return; }
    for (size_t i = 0; i < out.size(); ++i)
        for (size_t j = i + 1; j < out.size(); ++j)
            if (m.demand[out[i][0]] + m.demand[out[j][0]] <= m.capacity + 1e-9) {
                out[i].push_back(out[j][0]); out.erase(out.begin() + j); return;
            }
    if (out.size() >= 2) std::swap(out[0], out[1]);
}

class GiantSplit : public hsf::Perturbation<Model> {
    const Model& m; double base, per, revP, extraP;
    std::vector<double> cx, cy, dp; std::vector<int> pred, seq, tmp;
public:
    GiantSplit(const Model& mm, double b, double p, double r, double e)
        : m(mm), base(b), per(p), revP(r), extraP(e) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol rt; rt.reserve(s.size());
        for (const auto& r : s) if (!r.empty()) rt.push_back(r);
        int R = (int)rt.size();
        if (R == 0) return s;
        cx.assign(R, 0); cy.assign(R, 0);
        for (int r = 0; r < R; ++r) {
            for (int c : rt[r]) { cx[r] += m.xs[c]; cy[r] += m.ys[c]; }
            cx[r] /= rt[r].size(); cy[r] /= rt[r].size();
        }
        int nb = (int)std::lround(base + per * std::max(0.0, strength - 1.0));
        nb = std::max(1, nb);
        // Giant tour GLOBAL: todas las rutas en orden polar, con inicio rotado al azar
        std::vector<std::pair<double,int>> sel;
        sel.reserve(R);
        for (int r = 0; r < R; ++r)
            sel.push_back({std::atan2(cy[r] - m.ys[0], cx[r] - m.xs[0]), r});
        std::sort(sel.begin(), sel.end());
        std::rotate(sel.begin(), sel.begin() + rng.below(R), sel.end());
        seq.clear();
        for (auto& pr : sel) {
            const auto& r = rt[pr.second];
            if (rng.uniform() < revP) seq.insert(seq.end(), r.rbegin(), r.rend());
            else seq.insert(seq.end(), r.begin(), r.end());
        }
        int L = (int)seq.size();
        if (L >= 8) {
            for (int b = 0; b < nb; ++b) {
                int p1 = 1 + rng.below(L - 3);
                int p2 = p1 + 1 + rng.below(L - p1 - 2);
                int p3 = p2 + 1 + rng.below(L - p2 - 1);
                tmp.clear();
                tmp.insert(tmp.end(), seq.begin(), seq.begin() + p1);
                tmp.insert(tmp.end(), seq.begin() + p2, seq.begin() + p3);
                tmp.insert(tmp.end(), seq.begin() + p1, seq.begin() + p2);
                tmp.insert(tmp.end(), seq.begin() + p3, seq.end());
                seq.swap(tmp);
            }
        } else if (L >= 2) {
            int i = rng.below(L), j = rng.below(L - 1); if (j >= i) ++j;
            std::swap(seq[i], seq[j]);
        }
        if (L >= 3 && rng.uniform() < extraP) {
            int i = rng.below(L), j = rng.below(L - 1); if (j >= i) ++j;
            if (i > j) std::swap(i, j);
            std::reverse(seq.begin() + i, seq.begin() + j + 1);
        }
        // Split de Prins (óptimo para el orden dado)
        const double INF = std::numeric_limits<double>::infinity();
        dp.assign(L + 1, INF); pred.assign(L + 1, -1); dp[0] = 0.0;
        for (int i = 0; i < L; ++i) {
            if (dp[i] == INF) continue;
            double load = 0.0, cost = 0.0;
            for (int j = i; j < L; ++j) {
                int c = seq[j]; load += m.demand[c];
                if (j > i && load > m.capacity + 1e-9) break;
                cost += (j == i) ? m.dist(0, c) : m.dist(seq[j - 1], c);
                double tot = dp[i] + cost + m.dist(c, 0);
                if (tot < dp[j + 1]) { dp[j + 1] = tot; pred[j + 1] = i; }
            }
        }
        Sol out; out.reserve(R + 2);
        int j = L;
        while (j > 0) {
            int i = pred[j];
            out.emplace_back(seq.begin() + i, seq.begin() + j);
            j = i;
        }
        ensureDistinct(out, s, m);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<GiantSplit>(model, params.get("bridges_base", 1), params.get("bridges_per_strength", 0.5),
        params.get("reverse_route_prob", 0.5), params.get("extra_reversal_prob", 0.3));
}
