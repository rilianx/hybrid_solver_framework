// COMPONENT: {"name": "radial_ruin_greedy_blink_recreate", "slot": "perturbation", "params": {"remove_per_strength": {"type": "float", "range": [1.0, 12.0]}, "max_frac": {"type": "float", "range": [0.05, 0.6]}, "blink": {"type": "float", "range": [0.0, 0.2]}, "order": {"type": "cat", "values": ["random", "demand", "far", "near"]}}}

static CVRP::Solution rr_repair(const CVRP& M, const CVRP::Solution& s) {
    std::vector<char> seen(M.n + 1, 0);
    CVRP::Solution out;
    for (auto& r : s) {
        std::vector<int> cur;
        double load = 0.0;
        for (int c : r) {
            if (c < 1 || c > M.n || seen[c]) continue;
            seen[c] = 1;
            if (!cur.empty() && load + M.demand[c] > M.capacity + 1e-9) {
                out.push_back(cur);
                cur.clear();
                load = 0.0;
            }
            cur.push_back(c);
            load += M.demand[c];
        }
        if (!cur.empty()) out.push_back(cur);
    }
    for (int c = 1; c <= M.n; ++c)
        if (!seen[c]) out.push_back({c});
    return out;
}

static CVRP::Solution rr_canon(const CVRP::Solution& s) {
    CVRP::Solution c;
    for (auto& r : s)
        if (!r.empty()) c.push_back(r);
    std::sort(c.begin(), c.end(), [](const std::vector<int>& a, const std::vector<int>& b) { return a.front() < b.front(); });
    return c;
}

static void rr_force_change(const CVRP& M, CVRP::Solution& sol, Rng& rng) {
    std::vector<int> multi;
    for (int k = 0; k < (int)sol.size(); ++k)
        if (sol[k].size() >= 2) multi.push_back(k);
    if (!multi.empty()) {
        int k = multi[rng.below((int)multi.size())];
        if (rng.uniform() < 0.5) {
            std::reverse(sol[k].begin(), sol[k].end());
        } else {
            int cut = 1 + rng.below((int)sol[k].size() - 1);
            std::vector<int> tail(sol[k].begin() + cut, sol[k].end());
            sol[k].resize(cut);
            sol.push_back(tail);
        }
        return;
    }
    int R = (int)sol.size();
    for (int i = 0; i < R; ++i)
        for (int j = i + 1; j < R; ++j)
            if (M.route_load(sol[i]) + M.route_load(sol[j]) <= M.capacity + 1e-9) {
                sol[i].insert(sol[i].end(), sol[j].begin(), sol[j].end());
                sol.erase(sol.begin() + j);
                return;
            }
}

class RadialRuinRecreate : public hsf::Perturbation<CVRP> {
public:
    using Sol = CVRP::Solution;
    RadialRuinRecreate(const CVRP& m, double rps, double mf, double bl, std::string ord)
        : M(m), rps_(rps), mf_(mf), blink_(bl), order_(std::move(ord)) {
        int n = M.n;
        K_ = std::max(0, std::min(n - 1, 200));
        nb_.assign(n + 1, {});
        std::vector<int> others;
        for (int c = 1; c <= n; ++c) {
            others.clear();
            for (int v = 1; v <= n; ++v)
                if (v != c) others.push_back(v);
            std::partial_sort(others.begin(), others.begin() + K_, others.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            nb_[c].assign(others.begin(), others.begin() + K_);
        }
        removed_.assign(n + 1, 0);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol sol = rr_repair(M, s);
        int n = M.n;
        if (n == 0) return sol;
        int kmax = std::max(1, (int)(mf_ * n));
        int k = (int)std::lround(rps_ * std::max(1.0, strength));
        k = std::max(1, std::min(k, std::min(kmax, n)));

        std::fill(removed_.begin(), removed_.end(), 0);
        std::vector<int> rem;
        int seed = 1 + rng.below(n);
        rem.push_back(seed);
        removed_[seed] = 1;
        for (int v : nb_[seed]) {
            if ((int)rem.size() >= k) break;
            rem.push_back(v);
            removed_[v] = 1;
        }
        while ((int)rem.size() < k) {
            int c = 1 + rng.below(n);
            if (!removed_[c]) { removed_[c] = 1; rem.push_back(c); }
        }

        Sol routes;
        std::vector<double> loads;
        for (auto& r : sol) {
            std::vector<int> nr;
            double l = 0.0;
            for (int c : r)
                if (!removed_[c]) { nr.push_back(c); l += M.demand[c]; }
            if (!nr.empty()) { routes.push_back(std::move(nr)); loads.push_back(l); }
        }

        if (order_ == "random") std::shuffle(rem.begin(), rem.end(), rng.g);
        else if (order_ == "demand") std::sort(rem.begin(), rem.end(), [&](int a, int b) { return M.demand[a] > M.demand[b]; });
        else if (order_ == "far") std::sort(rem.begin(), rem.end(), [&](int a, int b) { return M.dist(0, a) > M.dist(0, b); });
        else std::sort(rem.begin(), rem.end(), [&](int a, int b) { return M.dist(0, a) < M.dist(0, b); });

        for (int c : rem) {
            double dc = M.demand[c];
            double best = 2.0 * M.dist(0, c);
            int bk = -1, bp = 0;
            for (int r = 0; r < (int)routes.size(); ++r) {
                if (loads[r] + dc > M.capacity + 1e-9) continue;
                const auto& rt = routes[r];
                int prev = 0;
                int sz = (int)rt.size();
                for (int p = 0; p <= sz; ++p) {
                    int next = p < sz ? rt[p] : 0;
                    if (blink_ > 0.0 && rng.uniform() < blink_) { prev = next; continue; }
                    double d = M.dist(prev, c) + M.dist(c, next) - M.dist(prev, next);
                    if (d < best) { best = d; bk = r; bp = p; }
                    prev = next;
                }
            }
            if (bk < 0) { routes.push_back({c}); loads.push_back(dc); }
            else { routes[bk].insert(routes[bk].begin() + bp, c); loads[bk] += dc; }
        }

        if (rr_canon(routes) == rr_canon(s)) rr_force_change(M, routes, rng);
        return routes;
    }

private:
    const CVRP& M;
    double rps_, mf_, blink_;
    std::string order_;
    int K_ = 0;
    std::vector<std::vector<int>> nb_;
    std::vector<char> removed_;
};

std::unique_ptr<hsf::Perturbation<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<RadialRuinRecreate>(model, params.get("remove_per_strength", 4.0), params.get("max_frac", 0.3),
                                                params.get("blink", 0.02), params.text("order", "random"));
}
