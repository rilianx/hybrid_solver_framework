// COMPONENT: {"name": "drop_k_greedy_refill", "slot": "neighborhood", "params": {"max_drop": {"type": "int", "range": [1, 500]}, "pair_pool": {"type": "int", "range": [0, 30]}, "refill_order": {"type": "cat", "values": ["ratio", "profit"]}}}
struct BaseState {
    const Model& M;
    int n, m;
    std::vector<double> lim, invcap;
    std::vector<int> order;
    std::vector<int> x;
    std::vector<double> used;
    double obj = 0;
    bool safe = false, valid = false;
    Model::Solution work;
    explicit BaseState(const Model& mod) : M(mod), n(mod.n), m(mod.m) {
        bool integral = true;
        for (double c : M.capacity) if (c != std::floor(c) || std::fabs(c) > 1e15) integral = false;
        for (double w : M.wt) if (w != std::floor(w) || std::fabs(w) > 1e15) integral = false;
        lim.resize(m); invcap.resize(m);
        for (int r = 0; r < m; ++r) {
            double c = M.capacity[r];
            lim[r] = integral ? c : c - 1e-9 * std::max(1.0, std::fabs(c));
            invcap[r] = c > 0 ? 1.0 / c : 1e12;
        }
        std::vector<double> ratio(n);
        for (int j = 0; j < n; ++j) {
            double s = 0;
            for (int r = 0; r < m; ++r) s += M.wt[(size_t)j * m + r] * invcap[r];
            ratio[j] = s > 0 ? M.profit[j] / s : std::numeric_limits<double>::infinity();
        }
        order.resize(n);
        std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return ratio[a] > ratio[b]; });
        work.assign(1, std::vector<int>(n, 0));
    }
    void refresh(const Model::Solution& s) {
        if (valid && s[0] == x) return;
        x = s[0];
        used.assign(m, 0.0);
        for (int j = 0; j < n; ++j) if (x[j]) {
            const double* w = &M.wt[(size_t)j * m];
            for (int r = 0; r < m; ++r) used[r] += w[r];
        }
        safe = true;
        for (int r = 0; r < m; ++r) if (used[r] > lim[r]) { safe = false; break; }
        obj = M.objective(s);
        valid = true;
    }
};

static inline Move mk(int a, int b = 0, int c = 0) { Move v{}; v[0] = a; v[1] = b; v[2] = c; return v; }

class DropRefill : public hsf::Neighborhood<Model> {
    BaseState B;
    int maxDrop, pairPool;
    std::vector<int> fill;
    std::vector<int> ins, x2;
    std::vector<double> used2;
public:
    using Sol = Model::Solution;
    DropRefill(const Model& mod, int md, int pp, bool byProfit) : B(mod), maxDrop(md), pairPool(pp) {
        if (byProfit) {
            fill.resize(B.n);
            std::iota(fill.begin(), fill.end(), 0);
            std::stable_sort(fill.begin(), fill.end(), [&](int a, int b) { return mod.profit[a] > mod.profit[b]; });
        } else fill = B.order;
    }

    bool build(const Move& mv, double& dp) {
        const int m = B.m, n = B.n;
        const auto& wt = B.M.wt;
        x2 = B.x; used2 = B.used; dp = 0;
        int cnt = mv[0], a = mv[1], b = mv[2];
        auto drop = [&](int j) {
            if (j < 0 || j >= n || !x2[j]) return;
            x2[j] = 0; dp -= B.M.profit[j];
            const double* w = &wt[(size_t)j * m];
            for (int r = 0; r < m; ++r) used2[r] -= w[r];
        };
        if (cnt >= 1) drop(a);
        if (cnt >= 2) drop(b);
        for (int r = 0; r < m; ++r) if (used2[r] > B.lim[r]) return false;
        for (int j : fill) {
            if (x2[j]) continue;
            if (cnt >= 1 && j == a) continue;
            if (cnt >= 2 && j == b) continue;
            const double* w = &wt[(size_t)j * m];
            bool ok = true;
            for (int r = 0; r < m; ++r) if (used2[r] + w[r] > B.lim[r]) { ok = false; break; }
            if (!ok) continue;
            x2[j] = 1; dp += B.M.profit[j];
            for (int r = 0; r < m; ++r) used2[r] += w[r];
        }
        return true;
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        B.refresh(s);
        ins.clear();
        for (int t = B.n - 1; t >= 0; --t) { int j = B.order[t]; if (B.x[j]) ins.push_back(j); }
        int ns = B.safe ? std::min<int>(maxDrop, (int)ins.size()) : (int)ins.size();
        for (int a = 0; a < ns; ++a) out.push_back(mk(1, ins[a]));
        if (B.safe) {
            int np = std::min<int>(pairPool, (int)ins.size());
            for (int a = 0; a < np; ++a)
                for (int b = a + 1; b < np; ++b) out.push_back(mk(2, ins[a], ins[b]));
        }
        out.push_back(mk(0));
    }

    Sol apply(const Sol& s, const Move& mv) override {
        B.refresh(s);
        double dp;
        build(mv, dp);
        Sol r(1);
        r[0] = x2;
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        B.refresh(s);
        double dp;
        bool ok = build(mv, dp);
        if (B.safe && ok) return -dp;
        B.work[0] = x2;
        return B.M.objective(B.work) - B.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int md = (int)params.get("max_drop", 40);
    int pp = (int)params.get("pair_pool", 8);
    bool byProfit = params.text("refill_order", "ratio") == "profit";
    return std::make_unique<DropRefill>(model, std::max(1, md), std::max(0, pp), byProfit);
}
