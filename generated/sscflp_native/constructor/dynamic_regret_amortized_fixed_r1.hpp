// COMPONENT: {"name": "dynamic_regret_amortized_fixed", "slot": "constructor", "params": {"rcl": {"type": "int", "range": [1, 6]}, "fixed_weight": {"type": "float", "range": [0.0, 2.0]}, "tries": {"type": "int", "range": [1, 8]}, "polish": {"type": "cat", "values": ["none", "reassign", "close"]}}}
class DynamicRegretAmortized : public hsf::Constructor<Model> {
public:
    DynamicRegretAmortized(const Model& model, int rcl, double fw, int tries, const std::string& polish)
        : M(model), n(model.n), m(model.m), rcl_(std::max(1, rcl)), fw_(fw),
          tries_(std::max(1, tries)), polish_(polish) {}

    Model::Solution build(Rng& rng) override {
        const double INF = std::numeric_limits<double>::infinity();
        double bestCost = INF;
        Model::Solution best;
        std::vector<int> asg;
        for (int t = 0; t < tries_; ++t) {
            if (greedy(rng, asg)) {
                cnt.assign(n, 0);
                for (int j = 0; j < m; ++j) cnt[asg[j]]++;
                if (polish_ != "none") reassign_pass(asg);
                if (polish_ == "close") { close_pass(asg); reassign_pass(asg); }
                double cst = total_cost(asg);
                if (cst < bestCost) {
                    Model::Solution s = to_sol(asg);
                    if (M.feasible(s)) { bestCost = cst; best = std::move(s); }
                }
            }
            if (rcl_ == 1) break;
        }
        if (bestCost < INF) return best;
        return M.trivial();
    }

private:
    const Model& M;
    int n, m, rcl_;
    double fw_;
    int tries_;
    std::string polish_;
    std::vector<double> rem, e1, e2;
    std::vector<char> open;
    std::vector<int> b1, b2, un, pos, cnt;

    inline double C(int i, int j) const { return M.cost[(size_t)i * m + j]; }
    inline bool fits(int i, int j) const { return rem[i] + Model::EPS >= M.demand[j]; }
    inline double eff(int i, int j) const {
        double v = C(i, j);
        if (!open[i]) v += fw_ * M.fixed[i] * M.demand[j] / std::max(M.capacity[i], 1e-12);
        return v;
    }
    void recompute(int j) {
        const double INF = std::numeric_limits<double>::infinity();
        e1[j] = e2[j] = INF; b1[j] = b2[j] = -1;
        for (int i = 0; i < n; ++i) {
            if (!fits(i, j)) continue;
            double v = eff(i, j);
            if (v < e1[j]) { e2[j] = e1[j]; b2[j] = b1[j]; e1[j] = v; b1[j] = i; }
            else if (v < e2[j]) { e2[j] = v; b2[j] = i; }
        }
    }
    void update(int i) {
        for (int j : un) {
            if (b1[j] == i || b2[j] == i) { recompute(j); continue; }
            if (!fits(i, j)) continue;
            double v = eff(i, j);
            if (v < e1[j]) { e2[j] = e1[j]; b2[j] = b1[j]; e1[j] = v; b1[j] = i; }
            else if (v < e2[j]) { e2[j] = v; b2[j] = i; }
        }
    }
    inline double regret(int j) const { return b2[j] < 0 ? 1e300 : e2[j] - e1[j]; }
    inline bool better(int a, int b) const {
        double ra = regret(a), rb = regret(b);
        if (ra != rb) return ra > rb;
        if (M.demand[a] != M.demand[b]) return M.demand[a] > M.demand[b];
        return a < b;
    }
    bool greedy(Rng& rng, std::vector<int>& asg) {
        rem.assign(M.capacity.begin(), M.capacity.end());
        open.assign(n, 0);
        asg.assign(m, -1);
        un.resize(m); pos.resize(m);
        for (int j = 0; j < m; ++j) { un[j] = j; pos[j] = j; }
        b1.assign(m, -1); b2.assign(m, -1); e1.assign(m, 0.0); e2.assign(m, 0.0);
        for (int j = 0; j < m; ++j) recompute(j);
        std::vector<int> top;
        top.reserve(rcl_ + 1);
        while (!un.empty()) {
            top.clear();
            for (int j : un) {
                if (b1[j] < 0) return false;
                if ((int)top.size() < rcl_ || better(j, top.back())) {
                    if ((int)top.size() == rcl_) top.pop_back();
                    top.push_back(j);
                    for (int k = (int)top.size() - 1; k > 0 && better(top[k], top[k - 1]); --k)
                        std::swap(top[k], top[k - 1]);
                }
            }
            int j = top[top.size() == 1 ? 0 : rng.below((int)top.size())];
            int i = b1[j];
            rem[i] -= M.demand[j];
            open[i] = 1;
            asg[j] = i;
            int p = pos[j], last = un.back();
            un[p] = last; pos[last] = p; un.pop_back();
            update(i);
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
        std::vector<int> ord;
        for (int i = 0; i < n; ++i) if (cnt[i] > 0) ord.push_back(i);
        std::sort(ord.begin(), ord.end(), [&](int a, int b) {
            if (M.fixed[a] != M.fixed[b]) return M.fixed[a] > M.fixed[b];
            return a < b; });
        std::vector<double> tmp;
        std::vector<int> tgt;
        for (int i : ord) {
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
    int rcl = (int)params.get("rcl", 2);
    double fw = params.get("fixed_weight", 1.0);
    int tries = (int)params.get("tries", 3);
    std::string polish = params.text("polish", "close");
    return std::make_unique<DynamicRegretAmortized>(model, rcl, fw, tries, polish);
}
