// COMPONENT: {"name": "route_cluster_merge_prins_resplit", "slot": "perturbation", "params": {"routes_per_strength": {"type": "float", "range": [0.5, 4.0]}, "orient": {"type": "cat", "values": ["nn", "random", "mixed"]}, "cut_penalty": {"type": "float", "range": [0.2, 3.0]}, "split_noise": {"type": "float", "range": [0.0, 0.5]}}}

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
    MergeResplit(const CVRP& m, double rps, std::string ori, double pen, double noise)
        : M(m), rps_(rps), orient_(std::move(ori)), pen_(pen), noise_(noise) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol sol = ms_repair(M, s);
        int R = (int)sol.size();
        if (M.n == 0 || R == 0) return sol;
        int w = (int)std::lround(2.0 + rps_ * std::max(1.0, strength));
        w = std::max(std::min(2, R), std::min(w, R));

        // routes ordered by centroid angle around the depot
        const double TWO_PI = 6.283185307179586;
        std::vector<std::pair<double, int>> ang(R);
        for (int r = 0; r < R; ++r) {
            double sx = 0, sy = 0;
            for (int c : sol[r]) { sx += M.x[c]; sy += M.y[c]; }
            sx /= sol[r].size();
            sy /= sol[r].size();
            ang[r] = {std::atan2(sy - M.y[0], sx - M.x[0]), r};
        }
        std::sort(ang.begin(), ang.end());
        int start = rng.below(R);
        bool ccw = rng.uniform() < 0.5;
        std::vector<int> win;
        win.reserve(w);
        for (int k = 0; k < w; ++k) {
            int p = ccw ? (start + k) % R : ((start - k) % R + R) % R;
            win.push_back(ang[p].second);
        }
        (void)TWO_PI;

        // giant tour: concatenation preserving internal order, with orientation
        std::string ori = orient_;
        std::vector<char> sel(R, 0);
        std::vector<int> pool;
        std::vector<char> oldCut;
        pool.reserve(M.n);
        std::vector<int> cutPos;
        cutPos.push_back(0);
        for (int k = 0; k < w; ++k) {
            int r = win[k];
            sel[r] = 1;
            const auto& rt = sol[r];
            bool rev;
            std::string o = ori;
            if (o == "mixed") o = rng.uniform() < 0.5 ? "nn" : "random";
            if (o == "random" || pool.empty()) {
                rev = rng.uniform() < 0.5;
            } else {
                int tail = pool.back();
                rev = M.dist(tail, rt.back()) < M.dist(tail, rt.front());
            }
            if (rev) pool.insert(pool.end(), rt.rbegin(), rt.rend());
            else pool.insert(pool.end(), rt.begin(), rt.end());
            cutPos.push_back((int)pool.size());
        }
        int m = (int)pool.size();
        oldCut.assign(m + 1, 0);
        for (int p : cutPos) oldCut[p] = 1;

        // penalty scale: average edge length of the giant tour
        double L = M.dist(0, pool[0]) + M.dist(pool[m - 1], 0);
        for (int i = 1; i < m; ++i) L += M.dist(pool[i - 1], pool[i]);
        double edge = L / (m + 1);
        double lambda = pen_ * edge;
        std::vector<double> jit(m, 0.0);
        for (int i = 0; i < m; ++i) jit[i] = noise_ * edge * rng.uniform();

        // Prins split penalizing reuse of the current cuts
        const double INF = std::numeric_limits<double>::infinity();
        std::vector<double> V(m + 1, INF);
        std::vector<int> pred(m + 1, -1);
        V[0] = 0.0;
        for (int i = 0; i < m; ++i) {
            if (V[i] == INF) continue;
            double base = V[i] + jit[i] + ((i > 0 && oldCut[i]) ? lambda : 0.0);
            double load = 0.0, inner = 0.0;
            for (int j = i; j < m; ++j) {
                int c = pool[j];
                load += M.demand[c];
                if (j > i && load > M.capacity + 1e-9) break;
                if (j > i) inner += M.dist(pool[j - 1], c);
                double cost = base + M.dist(0, pool[i]) + inner + M.dist(c, 0);
                if (cost < V[j + 1]) { V[j + 1] = cost; pred[j + 1] = i; }
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
    std::string orient_;
    double pen_;
    double noise_;
};

std::unique_ptr<hsf::Perturbation<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<MergeResplit>(model, params.get("routes_per_strength", 1.5), params.text("orient", "mixed"),
                                          params.get("cut_penalty", 1.0), params.get("split_noise", 0.15));
}
