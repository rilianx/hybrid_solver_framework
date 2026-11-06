// COMPONENT: {"name": "swap_1_1_ratio_candidates", "slot": "neighborhood", "params": {"max_in": {"type": "int", "range": [5, 300]}, "max_out": {"type": "int", "range": [5, 300]}}}
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

class SwapExchange : public hsf::Neighborhood<Model> {
    BaseState B;
    int maxIn, maxOut;
    std::vector<int> ins, outs;
public:
    using Sol = Model::Solution;
    SwapExchange(const Model& mod, int a, int b) : B(mod), maxIn(a), maxOut(b) {}

    bool fitsShift(int rem, int add) const {
        const int m = B.m;
        const double* wr = rem >= 0 ? &B.M.wt[(size_t)rem * m] : nullptr;
        const double* wa = add >= 0 ? &B.M.wt[(size_t)add * m] : nullptr;
        for (int r = 0; r < m; ++r) {
            double v = B.used[r];
            if (wr) v -= wr[r];
            if (wa) v += wa[r];
            if (v > B.lim[r]) return false;
        }
        return true;
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        B.refresh(s);
        const int n = B.n;
        ins.clear(); outs.clear();
        for (int t = n - 1; t >= 0; --t) { int j = B.order[t]; if (B.x[j]) ins.push_back(j); }
        for (int t = 0; t < n; ++t) { int j = B.order[t]; if (!B.x[j]) outs.push_back(j); }
        if (!B.safe) for (int i : ins) out.push_back(mk(2, i));
        for (int j : outs) if (fitsShift(-1, j)) out.push_back(mk(1, j));
        int ni = std::min<int>(maxIn, (int)ins.size()), no = std::min<int>(maxOut, (int)outs.size());
        for (int a = 0; a < ni; ++a)
            for (int b = 0; b < no; ++b)
                if (!B.safe || fitsShift(ins[a], outs[b])) out.push_back(mk(0, ins[a], outs[b]));
        if (out.empty()) {
            for (int a = 0; a < ni; ++a)
                for (int b = 0; b < no; ++b) out.push_back(mk(0, ins[a], outs[b]));
            if (out.empty()) {
                for (int i : ins) out.push_back(mk(2, i));
                for (int j : outs) out.push_back(mk(1, j));
            }
        }
    }

    void applyTo(std::vector<int>& x, const Move& mv) const {
        if (mv[0] == 0) { x[mv[1]] = 0; x[mv[2]] = 1; }
        else if (mv[0] == 1) x[mv[1]] = 1;
        else x[mv[1]] = 0;
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        applyTo(r[0], mv);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        B.refresh(s);
        double dp;
        int rem = -1, add = -1;
        if (mv[0] == 0) { rem = mv[1]; add = mv[2]; }
        else if (mv[0] == 1) add = mv[1];
        else rem = mv[1];
        dp = (add >= 0 ? B.M.profit[add] : 0.0) - (rem >= 0 ? B.M.profit[rem] : 0.0);
        if (B.safe && fitsShift(rem, add)) return -dp;
        B.work[0] = B.x;
        applyTo(B.work[0], mv);
        return B.M.objective(B.work) - B.obj;
    }

    Move tabu_key(const Move& mv) override {
        if (mv[0] == 0) return mk(0, mv[2], mv[1]);
        if (mv[0] == 1) return mk(2, mv[1]);
        return mk(1, mv[1]);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int a = (int)params.get("max_in", 40);
    int b = (int)params.get("max_out", 60);
    return std::make_unique<SwapExchange>(model, std::max(1, a), std::max(1, b));
}
