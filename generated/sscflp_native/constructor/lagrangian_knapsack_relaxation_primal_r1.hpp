// COMPONENT: {"name": "lagrangian_knapsack_relaxation_primal", "slot": "constructor", "params": {"iters": {"type": "int", "range": [5, 200]}, "lam0": {"type": "float", "range": [0.1, 2.0]}, "noise": {"type": "float", "range": [0.0, 0.3]}, "primal_every": {"type": "int", "range": [1, 10]}, "slack": {"type": "float", "range": [1.0, 1.5]}}}
class LagrangianPrimal : public hsf::Constructor<Model> {
public:
    LagrangianPrimal(const Model& model, int iters, double lam0, double noise, int pe, double slack)
        : M(model), n(model.n), m(model.m), iters_(std::max(1, iters)), lam0_(lam0), noise_(noise),
          pe_(std::max(1, pe)), slack_(slack) {
        totalD = 0.0;
        for (int j = 0; j < m; ++j) totalD += M.demand[j];
    }

    Model::Solution build(Rng& rng) override {
        const double INF = std::numeric_limits<double>::infinity();
        std::vector<double> u(m), g(m);
        for (int j = 0; j < m; ++j) {
            double b = INF;
            for (int i = 0; i < n; ++i) {
                double v = C(i, j) + M.fixed[i] * M.demand[j] / std::max(M.capacity[i], 1e-12);
                if (v < b) b = v;
            }
            if (b == INF) b = 0.0;
            u[j] = b * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
        }
        val.assign(n, 0.0);
        std::vector<std::pair<double, int>> items;
        items.reserve(m);
        double bestUB = INF, bestLB = -INF, lam = lam0_;
        int stall = 0;
        std::vector<int> asg, bestAsg;
        for (int it = 0; it < iters_; ++it) {
            double L = 0.0;
            for (int j = 0; j < m; ++j) L += u[j];
            std::fill(g.begin(), g.end(), 1.0);
            for (int i = 0; i < n; ++i) {
                items.clear();
                for (int j = 0; j < m; ++j) {
                    double r = C(i, j) - u[j];
                    if (r < 0) items.push_back({r / std::max(M.demand[j], 1e-12), j});
                }
                std::sort(items.begin(), items.end());
                double capLeft = M.capacity[i], v = M.fixed[i];
                size_t mark = sel.size();
                (void)mark;
                tmpSel.clear();
                for (auto& pr : items) {
                    int j = pr.second;
                    double d = M.demand[j];
                    if (d <= capLeft + Model::EPS) {
                        capLeft -= d; v += C(i, j) - u[j]; tmpSel.push_back(j);
                    }
                }
                val[i] = v;
                if (v < 0) {
                    L += v;
                    for (int j : tmpSel) g[j] -= 1.0;
                }
            }
            if (L > bestLB + 1e-9) { bestLB = L; stall = 0; }
            else if (++stall >= 5) { lam *= 0.5; stall = 0; }

            if (it % pe_ == 0 || it == iters_ - 1) {
                if (primal(asg)) {
                    double cst = total_cost(asg);
                    if (cst < bestUB) { bestUB = cst; bestAsg = asg; }
                }
            }
            double norm = 0.0;
            for (int j = 0; j < m; ++j) norm += g[j] * g[j];
            if (norm < 1e-12) break;
            double ub = (bestUB < INF) ? bestUB : std::fabs(L) * 1.1 + 1.0;
            double gap = ub - L;
            if (gap <= 1e-9) gap = 0.01 * std::fabs(ub) + 1e-6;
            double step = lam * gap / norm;
            for (int j = 0; j < m; ++j) u[j] += step * g[j];
        }
        if (bestUB < INF) {
            Model::Solution s = to_sol(bestAsg);
            if (M.feasible(s)) return s;
        }
        return M.trivial();
    }

private:
    const Model& M;
    int n, m, iters_;
    double lam0_, noise_;
    int pe_;
    double slack_, totalD;
    std::vector<double> val, rem, key;
    std::vector<int> cnt, ord, sel, tmpSel, ford;

    inline double C(int i, int j) const { return M.cost[(size_t)i * m + j]; }

    bool primal(std::vector<int>& asg) {
        std::vector<char> op(n, 0);
        double cap = 0.0;
        for (int i = 0; i < n; ++i) if (val[i] < 0) { op[i] = 1; cap += M.capacity[i]; }
        double target = slack_ * totalD;
        if (cap < target) {
            ford.resize(n);
            std::iota(ford.begin(), ford.end(), 0);
            std::sort(ford.begin(), ford.end(), [&](int a, int b) {
                if (val[a] != val[b]) return val[a] < val[b];
                return a < b; });
            for (int i : ford) {
                if (cap >= target) break;
                if (op[i]) continue;
                op[i] = 1; cap += M.capacity[i];
            }
        }
        if (!allocate(op, asg)) return false;
        reassign_pass(asg);
        close_pass(asg);
        reassign_pass(asg);
        return true;
    }
    bool allocate(std::vector<char>& op, std::vector<int>& asg) {
        const double INF = std::numeric_limits<double>::infinity();
        rem.assign(M.capacity.begin(), M.capacity.end());
        cnt.assign(n, 0);
        asg.assign(m, -1);
        key.assign(m, 0.0);
        for (int j = 0; j < m; ++j) {
            double a = INF, b = INF;
            for (int i = 0; i < n; ++i) {
                if (!op[i] || M.capacity[i] + Model::EPS < M.demand[j]) continue;
                double v = C(i, j);
                if (v < a) { b = a; a = v; } else if (v < b) b = v;
            }
            key[j] = (a == INF) ? 2e300 : (b == INF ? 1e300 : b - a);
        }
        ord.resize(m);
        std::iota(ord.begin(), ord.end(), 0);
        std::sort(ord.begin(), ord.end(), [&](int x, int y) {
            if (key[x] != key[y]) return key[x] > key[y];
            if (M.demand[x] != M.demand[y]) return M.demand[x] > M.demand[y];
            return x < y; });
        for (int j : ord) {
            double d = M.demand[j], bv = INF;
            int bi = -1;
            for (int i = 0; i < n; ++i) {
                if (!op[i] || rem[i] + Model::EPS < d) continue;
                double v = C(i, j);
                if (v < bv) { bv = v; bi = i; }
            }
            if (bi < 0) {
                for (int i = 0; i < n; ++i) {
                    if (op[i] || rem[i] + Model::EPS < d) continue;
                    double v = C(i, j) + M.fixed[i];
                    if (v < bv) { bv = v; bi = i; }
                }
                if (bi < 0) return false;
                op[bi] = 1;
            }
            asg[j] = bi; rem[bi] -= d; cnt[bi]++;
        }
        return true;
    }
    void reassign_pass(std::vector<int>& asg) {
        for (int j = 0; j < m; ++j) {
            int i0 = asg[j];
            double d = M.demand[j], bv = C(i0, j);
            int bi = i0;
            for (int i = 0; i < n; ++i) {
                if (i == i0 || cnt[i] == 0 || rem[i] + Model::EPS < d) continue;
                double v = C(i, j);
                if (v < bv - 1e-12) { bv = v; bi = i; }
            }
            if (bi != i0) { rem[i0] += d; rem[bi] -= d; cnt[i0]--; cnt[bi]++; asg[j] = bi; }
        }
    }
    void close_pass(std::vector<int>& asg) {
        std::vector<std::vector<int>> lst(n);
        for (int j = 0; j < m; ++j) lst[asg[j]].push_back(j);
        std::vector<int> fo;
        for (int i = 0; i < n; ++i) if (cnt[i] > 0) fo.push_back(i);
        std::sort(fo.begin(), fo.end(), [&](int a, int b) {
            if (M.fixed[a] != M.fixed[b]) return M.fixed[a] > M.fixed[b];
            return a < b; });
        std::vector<double> tmp;
        std::vector<int> tgt;
        for (int i : fo) {
            if (cnt[i] == 0) continue;
            tmp = rem;
            tgt.clear();
            double delta = -M.fixed[i];
            bool ok = true;
            std::vector<int>& L = lst[i];
            std::sort(L.begin(), L.end(), [&](int a, int b) {
                if (M.demand[a] != M.demand[b]) return M.demand[a] > M.demand[b];
                return a < b; });
            for (int j : L) {
                double d = M.demand[j], bv = std::numeric_limits<double>::infinity();
                int bk = -1;
                for (int k = 0; k < n; ++k) {
                    if (k == i || cnt[k] == 0 || tmp[k] + Model::EPS < d) continue;
                    double v = C(k, j);
                    if (v < bv) { bv = v; bk = k; }
                }
                if (bk < 0) { ok = false; break; }
                tmp[bk] -= d;
                delta += bv - C(i, j);
                tgt.push_back(bk);
            }
            if (ok && delta < -1e-9) {
                rem = tmp;
                rem[i] = M.capacity[i];
                for (size_t q = 0; q < L.size(); ++q) {
                    int j = L[q], k = tgt[q];
                    asg[j] = k; cnt[k]++; lst[k].push_back(j);
                }
                cnt[i] = 0;
                L.clear();
            }
        }
    }
    double total_cost(const std::vector<int>& asg) const {
        double s = 0.0;
        std::vector<char> o(n, 0);
        for (int j = 0; j < m; ++j) { s += C(asg[j], j); o[asg[j]] = 1; }
        for (int i = 0; i < n; ++i) if (o[i]) s += M.fixed[i];
        return s;
    }
    Model::Solution to_sol(const std::vector<int>& asg) const {
        Model::Solution s(n);
        for (int j = 0; j < m; ++j) s[asg[j]].push_back(j);
        return s;
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int iters = (int)params.get("iters", 40);
    double lam0 = params.get("lam0", 1.0);
    double noise = params.get("noise", 0.05);
    int pe = (int)params.get("primal_every", 3);
    double slack = params.get("slack", 1.05);
    return std::make_unique<LagrangianPrimal>(model, iters, lam0, noise, pe, slack);
}
