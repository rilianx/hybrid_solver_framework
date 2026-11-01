// COMPONENT: {"name": "neighbor_guided_random_move_walk", "slot": "perturbation", "params": {"moves_per_strength": {"type": "float", "range": [1.0, 8.0]}, "neighbor_k": {"type": "int", "range": [3, 30]}, "p_relocate": {"type": "float", "range": [0.0, 1.0]}, "p_swap": {"type": "float", "range": [0.0, 1.0]}, "p_cross": {"type": "float", "range": [0.0, 1.0]}}}

static CVRP::Solution mw_repair(const CVRP& M, const CVRP::Solution& s) {
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

static CVRP::Solution mw_canon(const CVRP::Solution& s) {
    CVRP::Solution c;
    for (auto& r : s)
        if (!r.empty()) c.push_back(r);
    std::sort(c.begin(), c.end(), [](const std::vector<int>& a, const std::vector<int>& b) { return a.front() < b.front(); });
    return c;
}

static void mw_force_change(const CVRP& M, CVRP::Solution& sol, Rng& rng) {
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

class RandomMoveWalk : public hsf::Perturbation<CVRP> {
public:
    using Sol = CVRP::Solution;
    RandomMoveWalk(const CVRP& m, double mps, int k, double pr, double ps, double pc) : M(m), mps_(mps) {
        double tot = pr + ps + pc + 0.25;
        pr_ = pr / tot; ps_ = ps / tot; pc_ = pc / tot;
        int n = M.n;
        K_ = std::max(0, std::min(n - 1, std::max(1, k)));
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
        rid_.assign(n + 1, -1);
        pos_.assign(n + 1, -1);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol sol = mw_repair(M, s);
        int n = M.n;
        if (n < 2 || K_ == 0) {
            if (mw_canon(sol) == mw_canon(s)) mw_force_change(M, sol, rng);
            return sol;
        }
        int moves = std::max(1, (int)std::lround(mps_ * std::max(1.0, strength)));
        int done = 0, attempts = 0, max_att = 30 * moves + 50;
        std::vector<double> loads;
        while (done < moves && attempts++ < max_att) {
            // locate
            loads.assign(sol.size(), 0.0);
            for (int r = 0; r < (int)sol.size(); ++r)
                for (int p = 0; p < (int)sol[r].size(); ++p) {
                    int c = sol[r][p];
                    rid_[c] = r; pos_[c] = p;
                    loads[r] += M.demand[c];
                }
            int c = 1 + rng.below(n);
            int v = nb_[c][rng.below(K_)];
            int ra = rid_[c], pa = pos_[c], rb = rid_[v], pb = pos_[v];
            double dc = M.demand[c], dv = M.demand[v];
            double u = rng.uniform();
            bool ok = false;
            if (u < pr_) {  // relocate c next to v
                if (ra != rb && loads[rb] + dc > M.capacity + 1e-9) continue;
                sol[ra].erase(sol[ra].begin() + pa);
                auto& b = sol[rb];
                int iv = (int)(std::find(b.begin(), b.end(), v) - b.begin());
                int ins = rng.uniform() < 0.5 ? iv + 1 : iv;
                b.insert(b.begin() + ins, c);
                if (sol[ra].empty()) sol.erase(sol.begin() + ra);
                ok = true;
            } else if (u < pr_ + ps_) {  // swap c and v
                if (ra == rb) continue;
                if (loads[ra] - dc + dv > M.capacity + 1e-9 || loads[rb] - dv + dc > M.capacity + 1e-9) continue;
                std::swap(sol[ra][pa], sol[rb][pb]);
                ok = true;
            } else if (u < pr_ + ps_ + pc_) {  // 2-opt*: tails after c and after v exchanged
                if (ra == rb) continue;
                auto& a = sol[ra];
                auto& b = sol[rb];
                double preA = 0.0, preB = 0.0;
                for (int i = 0; i <= pa; ++i) preA += M.demand[a[i]];
                for (int i = 0; i <= pb; ++i) preB += M.demand[b[i]];
                double tailA = loads[ra] - preA, tailB = loads[rb] - preB;
                if (preA + tailB > M.capacity + 1e-9 || preB + tailA > M.capacity + 1e-9) continue;
                std::vector<int> na(a.begin(), a.begin() + pa + 1), nb(b.begin(), b.begin() + pb + 1);
                na.insert(na.end(), b.begin() + pb + 1, b.end());
                nb.insert(nb.end(), a.begin() + pa + 1, a.end());
                if ((int)na.size() == (int)a.size() && na == a) continue;
                a = std::move(na);
                b = std::move(nb);
                ok = true;
            } else {  // intra-route segment reversal between c and v
                if (ra != rb) continue;
                int lo = std::min(pa, pb), hi = std::max(pa, pb);
                std::reverse(sol[ra].begin() + lo, sol[ra].begin() + hi + 1);
                ok = true;
            }
            if (ok) ++done;
        }
        Sol out;
        for (auto& r : sol)
            if (!r.empty()) out.push_back(std::move(r));
        if (mw_canon(out) == mw_canon(s)) mw_force_change(M, out, rng);
        return out;
    }

private:
    const CVRP& M;
    double mps_, pr_, ps_, pc_;
    int K_ = 0;
    std::vector<std::vector<int>> nb_;
    std::vector<int> rid_, pos_;
};

std::unique_ptr<hsf::Perturbation<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<RandomMoveWalk>(model, params.get("moves_per_strength", 3.0), (int)params.get("neighbor_k", 10),
                                            params.get("p_relocate", 0.35), params.get("p_swap", 0.25),
                                            params.get("p_cross", 0.25));
}
