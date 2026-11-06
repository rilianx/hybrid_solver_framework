// COMPONENT: {"name": "unit_fill_cost_locate_then_allocate", "slot": "constructor", "params": {"slack": {"type": "float", "range": [1.0, 1.6]}, "noise": {"type": "float", "range": [0.0, 0.6]}, "tries": {"type": "int", "range": [1, 8]}}}
class LocateThenAllocate : public hsf::Constructor<Model> {
public:
    LocateThenAllocate(const Model& model, double slack, double noise, int tries)
        : M(model), n(model.n), m(model.m), slack_(slack), noise_(noise), tries_(std::max(1, tries)) {
        score.assign(n, 1e300);
        totalD = 0.0;
        for (int j = 0; j < m; ++j) totalD += M.demand[j];
        std::vector<int> items(m);
        for (int i = 0; i < n; ++i) {
            std::iota(items.begin(), items.end(), 0);
            std::sort(items.begin(), items.end(), [&](int a, int b) {
                double ra = C(i, a) / std::max(M.demand[a], 1e-12);
                double rb = C(i, b) / std::max(M.demand[b], 1e-12);
                if (ra != rb) return ra < rb;
                return a < b; });
            double capLeft = M.capacity[i], fc = 0.0, filled = 0.0;
            for (int j : items) {
                if (M.demand[j] <= capLeft + Model::EPS) {
                    capLeft -= M.demand[j]; fc += C(i, j); filled += M.demand[j];
                }
            }
            if (filled > 1e-12) score[i] = (M.fixed[i] + fc) / filled;
        }
    }

    Model::Solution build(Rng& rng) override {
        const double INF = std::numeric_limits<double>::infinity();
        double bestCost = INF;
        Model::Solution best;
        std::vector<int> asg, ford(n);
        std::vector<double> pert(n);
        std::vector<char> op;
        for (int t = 0; t < tries_; ++t) {
            for (int i = 0; i < n; ++i)
                pert[i] = score[i] * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
            std::iota(ford.begin(), ford.end(), 0);
            std::sort(ford.begin(), ford.end(), [&](int a, int b) {
                if (pert[a] != pert[b]) return pert[a] < pert[b];
                return a < b; });
            op.assign(n, 0);
            double cap = 0.0, target = slack_ * totalD;
            for (int i : ford) {
                if (cap >= target) break;
                op[i] = 1; cap += M.capacity[i];
            }
            if (!allocate(op, asg)) continue;
            reassign_pass(asg);
            close_pass(asg);
            reassign_pass(asg);
            double cst = total_cost(asg);
            if (cst < bestCost) {
                Model::Solution s = to_sol(asg);
                if (M.feasible(s)) { bestCost = cst; best = std::move(s); }
            }
        }
        if (bestCost < INF) return best;
        return M.trivial();
    }

private:
    const Model& M;
    int n, m;
    double slack_, noise_;
    int tries_;
    double totalD;
    std::vector<double> score, rem, key;
    std::vector<int> cnt, ord;

    inline double C(int i, int j) const { return M.cost[(size_t)i * m + j]; }

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
    double slack = params.get("slack", 1.15);
    double noise = params.get("noise", 0.2);
    int tries = (int)params.get("tries", 3);
    return std::make_unique<LocateThenAllocate>(model, slack, noise, tries);
}
