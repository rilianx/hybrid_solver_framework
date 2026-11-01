// COMPONENT: {"name": "route_cluster_merge_prins_resplit", "slot": "perturbation", "params": {"routes_per_strength": {"type": "float", "range": [0.5, 4.0]}, "order": {"type": "cat", "values": ["angle", "nn", "mixed"]}, "nn_noise": {"type": "float", "range": [0.0, 0.5]}}}

static CVRP::Solution ms_repair(const CVRP& M, const CVRP::Solution& s) {
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

static CVRP::Solution ms_canon(const CVRP::Solution& s) {
    CVRP::Solution c;
    for (auto& r : s)
        if (!r.empty()) c.push_back(r);
    std::sort(c.begin(), c.end(), [](const std::vector<int>& a, const std::vector<int>& b) { return a.front() < b.front(); });
    return c;
}

static void ms_force_change(const CVRP& M, CVRP::Solution& sol, Rng& rng) {
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

class MergeResplit : public hsf::Perturbation<CVRP> {
public:
    using Sol = CVRP::Solution;
    MergeResplit(const CVRP& m, double rps, std::string ord, double noise)
        : M(m), rps_(rps), order_(std::move(ord)), noise_(noise) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol sol = ms_repair(M, s);
        int R = (int)sol.size();
        if (M.n == 0 || R == 0) return sol;
        int q = (int)std::lround(1.0 + rps_ * std::max(1.0, strength));
        q = std::max(std::min(2, R), std::min(q, R));

        // centroids
        std::vector<double> cx(R), cy(R);
        for (int r = 0; r < R; ++r) {
            double sx = 0, sy = 0;
            for (int c : sol[r]) { sx += M.x[c]; sy += M.y[c]; }
            cx[r] = sx / sol[r].size();
            cy[r] = sy / sol[r].size();
        }
        int seed = rng.below(R);
        std::vector<int> idx(R);
        std::iota(idx.begin(), idx.end(), 0);
        auto d2 = [&](int r) { double dx = cx[r] - cx[seed], dy = cy[r] - cy[seed]; return dx * dx + dy * dy; };
        std::partial_sort(idx.begin(), idx.begin() + q, idx.end(), [&](int a, int b) { return d2(a) < d2(b); });
        std::vector<char> sel(R, 0);
        std::vector<int> pool;
        for (int i = 0; i < q; ++i) {
            sel[idx[i]] = 1;
            pool.insert(pool.end(), sol[idx[i]].begin(), sol[idx[i]].end());
        }

        std::string ord = order_;
        if (ord == "mixed") ord = rng.uniform() < 0.5 ? "angle" : "nn";
        int m = (int)pool.size();
        if (ord == "angle") {
            const double TWO_PI = 6.283185307179586;
            double off = rng.uniform() * TWO_PI;
            std::vector<std::pair<double, int>> key;
            key.reserve(m);
            for (int c : pool) {
                double a = std::atan2(M.y[c] - M.y[0], M.x[c] - M.x[0]);
                double k = std::fmod(a - off + 2 * TWO_PI, TWO_PI);
                key.push_back({k, c});
            }
            std::sort(key.begin(), key.end());
            for (int i = 0; i < m; ++i) pool[i] = key[i].second;
            if (rng.uniform() < 0.5) std::reverse(pool.begin(), pool.end());
        } else {
            std::vector<int> rest = pool, tour;
            tour.reserve(m);
            int cur = rest[rng.below(m)];
            rest.erase(std::find(rest.begin(), rest.end(), cur));
            tour.push_back(cur);
            while (!rest.empty()) {
                int b1 = -1, b2 = -1;
                double d1 = std::numeric_limits<double>::infinity(), dd2 = d1;
                for (int i = 0; i < (int)rest.size(); ++i) {
                    double d = M.dist(cur, rest[i]);
                    if (d < d1) { dd2 = d1; b2 = b1; d1 = d; b1 = i; }
                    else if (d < dd2) { dd2 = d; b2 = i; }
                }
                int pick = (b2 >= 0 && rng.uniform() < noise_) ? b2 : b1;
                cur = rest[pick];
                rest[pick] = rest.back();
                rest.pop_back();
                tour.push_back(cur);
            }
            pool = std::move(tour);
        }

        // Prins split
        const double INF = std::numeric_limits<double>::infinity();
        std::vector<double> V(m + 1, INF);
        std::vector<int> pred(m + 1, -1);
        V[0] = 0.0;
        for (int i = 0; i < m; ++i) {
            if (V[i] == INF) continue;
            double load = 0.0, inner = 0.0;
            for (int j = i; j < m; ++j) {
                int c = pool[j];
                load += M.demand[c];
                if (j > i && load > M.capacity + 1e-9) break;
                if (j > i) inner += M.dist(pool[j - 1], c);
                double cost = M.dist(0, pool[i]) + inner + M.dist(c, 0);
                if (V[i] + cost < V[j + 1]) { V[j + 1] = V[i] + cost; pred[j + 1] = i; }
            }
        }
        Sol out;
        out.reserve(R + 2);
        for (int r = 0; r < R; ++r)
            if (!sel[r]) out.push_back(sol[r]);
        int j = m;
        while (j > 0) {
            int i = pred[j];
            out.emplace_back(pool.begin() + i, pool.begin() + j);
            j = i;
        }
        if (ms_canon(out) == ms_canon(s)) ms_force_change(M, out, rng);
        return out;
    }

private:
    const CVRP& M;
    double rps_;
    std::string order_;
    double noise_;
};

std::unique_ptr<hsf::Perturbation<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<MergeResplit>(model, params.get("routes_per_strength", 1.5), params.text("order", "mixed"),
                                          params.get("nn_noise", 0.15));
}
