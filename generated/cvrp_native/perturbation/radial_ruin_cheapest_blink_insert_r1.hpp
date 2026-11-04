// COMPONENT: {"name": "radial_ruin_cheapest_blink_insert", "slot": "perturbation", "params": {"ruin_base": {"type": "int", "range": [2, 30]}, "ruin_per_strength": {"type": "float", "range": [0.5, 6.0]}, "blink": {"type": "float", "range": [0.0, 0.15]}, "far_first_prob": {"type": "float", "range": [0.0, 1.0]}}}
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

class RadialRuin : public hsf::Perturbation<Model> {
    const Model& m; double base, per, blink, farFirst;
    std::vector<char> rem; std::vector<std::pair<double,int>> cand; std::vector<double> load; std::vector<int> removed;
public:
    RadialRuin(const Model& mm, double b, double p, double bl, double ff) : m(mm), base(b), per(p), blink(bl), farFirst(ff) {
        rem.assign(m.n + 1, 0);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = m.n;
        if (n <= 0) return s;
        int k = (int)std::lround(base + per * std::max(0.0, strength - 1.0));
        k = std::max(1, std::min(n, k));
        int seed = 1 + rng.below(n);
        cand.clear();
        for (int c = 1; c <= n; ++c) cand.push_back({m.dist(seed, c), c});
        std::nth_element(cand.begin(), cand.begin() + (k - 1), cand.end());
        removed.clear();
        for (int i = 0; i < k; ++i) { rem[cand[i].second] = 1; removed.push_back(cand[i].second); }
        Sol out; out.reserve(s.size() + k);
        for (const auto& r : s) {
            std::vector<int> nr; nr.reserve(r.size());
            for (int c : r) if (c >= 1 && c <= n && !rem[c]) nr.push_back(c);
            if (!nr.empty()) out.push_back(std::move(nr));
        }
        for (int c : removed) rem[c] = 0;
        std::shuffle(removed.begin(), removed.end(), rng.g);
        if (rng.uniform() < farFirst)
            std::stable_sort(removed.begin(), removed.end(), [&](int a, int b) { return m.dist(0, a) > m.dist(0, b); });
        load.assign(out.size(), 0.0);
        for (size_t r = 0; r < out.size(); ++r) for (int c : out[r]) load[r] += m.demand[c];
        for (int c : removed) {
            double d = m.demand[c];
            double best = 2.0 * m.dist(0, c); int bestR = -1, bestP = 0;
            for (size_t r = 0; r < out.size(); ++r) {
                if (load[r] + d > m.capacity + 1e-9) continue;
                const auto& rt = out[r];
                int prev = 0; size_t L = rt.size();
                for (size_t p = 0; p <= L; ++p) {
                    int next = p < L ? rt[p] : 0;
                    if (blink > 0 && rng.uniform() < blink) { prev = next; continue; }
                    double delta = m.dist(prev, c) + m.dist(c, next) - m.dist(prev, next);
                    if (delta < best) { best = delta; bestR = (int)r; bestP = (int)p; }
                    prev = next;
                }
            }
            if (bestR < 0) { out.push_back({c}); load.push_back(d); }
            else { out[bestR].insert(out[bestR].begin() + bestP, c); load[bestR] += d; }
        }
        ensureDistinct(out, s, m);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<RadialRuin>(model, params.get("ruin_base", 8), params.get("ruin_per_strength", 2.0),
                                        params.get("blink", 0.02), params.get("far_first_prob", 0.3));
}
