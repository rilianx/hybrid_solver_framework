// COMPONENT: {"name": "forced_insert_ejection_repair", "slot": "neighborhood", "params": {"max_add": {"type": "int", "range": [1, 500]}, "refill": {"type": "int", "range": [0, 1]}}}
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

class InsertRepair : public hsf::Neighborhood<Model> {
    BaseState B;
    int maxAdd;
    bool refill;
    std::vector<int> x2, mark, viol;
    std::vector<double> used2;
    int stamp = 0;
public:
    using Sol = Model::Solution;
    InsertRepair(const Model& mod, int ma, bool rf) : B(mod), maxAdd(ma), refill(rf) {
        mark.assign(B.n, 0);
    }

    bool build(const Move& mv, double& dp) {
        const int m = B.m, n = B.n;
        const auto& wt = B.M.wt;
        const auto& p = B.M.profit;
        x2 = B.x; used2 = B.used; dp = 0;
        ++stamp;
        int j = mv[0] - 1;
        if (j >= 0 && j < n && !x2[j]) {
            x2[j] = 1; dp += p[j];
            const double* w = &wt[(size_t)j * m];
            for (int r = 0; r < m; ++r) used2[r] += w[r];
        }
        bool feas = true;
        while (true) {
            viol.clear();
            for (int r = 0; r < m; ++r) if (used2[r] > B.lim[r]) viol.push_back(r);
            if (viol.empty()) break;
            int best = -1;
            double bestScore = std::numeric_limits<double>::infinity();
            for (int k = 0; k < n; ++k) {
                if (!x2[k] || k == j) continue;
                const double* w = &wt[(size_t)k * m];
                double sc = 0;
                for (int r : viol) sc += w[r] * B.invcap[r];
                if (sc <= 0) continue;
                double score = p[k] / sc;
                if (score < bestScore) { bestScore = score; best = k; }
            }
            if (best < 0) { feas = false; break; }
            x2[best] = 0; dp -= p[best]; mark[best] = stamp;
            const double* w = &wt[(size_t)best * m];
            for (int r = 0; r < m; ++r) used2[r] -= w[r];
        }
        if (feas && refill) {
            for (int k : B.order) {
                if (x2[k] || mark[k] == stamp || k == j) continue;
                const double* w = &wt[(size_t)k * m];
                bool ok = true;
                for (int r = 0; r < m; ++r) if (used2[r] + w[r] > B.lim[r]) { ok = false; break; }
                if (!ok) continue;
                x2[k] = 1; dp += p[k];
                for (int r = 0; r < m; ++r) used2[r] += w[r];
            }
        }
        return feas;
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        B.refresh(s);
        int cnt = 0;
        for (int t = 0; t < B.n && cnt < maxAdd; ++t) {
            int j = B.order[t];
            if (!B.x[j]) { out.push_back(mk(j + 1)); ++cnt; }
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
    int ma = (int)params.get("max_add", 60);
    int rf = (int)params.get("refill", 1);
    return std::make_unique<InsertRepair>(model, std::max(1, ma), rf != 0);
}
