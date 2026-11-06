// COMPONENT: {"name": "grasp_slack_adaptive_rcl", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 0.5]}, "rcl_max": {"type": "int", "range": [1, 12]}, "slack_pow": {"type": "float", "range": [0.5, 2.0]}}}
class Codec {
public:
    explicit Codec(const Model& md) : M(md), base(md.trivial()) {
        const int n = M.n;
        std::vector<char> T(n, 0);
        for (int j = 0; j < n; ++j) T[j] = M.chosen(base, j) ? 1 : 0;
        if (base.empty()) return;
        const std::vector<int>& r0 = base[0];
        if ((int)r0.size() == n) {
            bool ok = true;
            for (int j = 0; j < n && ok; ++j)
                if (!((r0[j] == 0 && !T[j]) || (r0[j] == 1 && T[j]))) ok = false;
            if (ok) { mode = 1; return; }
        }
        std::vector<char> seen(n, 0);
        bool ok = true;
        for (int v : r0) { if (v < 0 || v >= n || seen[v]) { ok = false; break; } seen[v] = 1; }
        for (int j = 0; j < n && ok; ++j) if (seen[j] != T[j]) ok = false;
        if (!ok) return;
        mode = 2;
        if (base.size() >= 2) {
            std::vector<char> s2(n, 0);
            bool c = true;
            for (int v : base[1]) { if (v < 0 || v >= n || s2[v] || T[v]) { c = false; break; } s2[v] = 1; }
            for (int j = 0; j < n && c; ++j) if (!T[j] && !s2[j]) c = false;
            comp = c;
        }
    }
    Model::Solution finalize(const std::vector<char>& x) const {
        if (mode == 0) return base;
        Model::Solution s = base;
        const int n = M.n;
        if (mode == 1) {
            s[0].assign(n, 0);
            for (int j = 0; j < n; ++j) if (x[j]) s[0][j] = 1;
        } else {
            s[0].clear();
            for (int j = 0; j < n; ++j) if (x[j]) s[0].push_back(j);
            if (comp) { s[1].clear(); for (int j = 0; j < n; ++j) if (!x[j]) s[1].push_back(j); }
        }
        for (int j = 0; j < n; ++j) if (M.chosen(s, j) != (x[j] != 0)) return base;
        if (!M.feasible(s)) return base;
        return s;
    }
private:
    const Model& M;
    Model::Solution base;
    int mode = 0;
    bool comp = false;
};

class GraspSlackRcl : public hsf::Constructor<Model> {
public:
    GraspSlackRcl(const Model& md, double a, int rm, double sp)
        : M(md), codec(md), n(md.n), m(md.m), alpha(a), rcl_max(std::max(1, rm)), slack_pow(sp) {
        lim.resize(m);
        for (int i = 0; i < m; ++i) lim[i] = M.capacity[i] + 1e-9 * std::max(1.0, std::fabs(M.capacity[i]));
    }
    Model::Solution build(Rng& rng) override {
        const double* w = M.wcol.data();
        load.assign(m, 0.0);
        x.assign(n, 0);
        cand.resize(n);
        std::iota(cand.begin(), cand.end(), 0);
        inv.resize(m);
        while (!cand.empty()) {
            for (size_t k = 0; k < cand.size();) {
                if (!fits(cand[k], w)) { cand[k] = cand.back(); cand.pop_back(); }
                else ++k;
            }
            if (cand.empty()) break;
            for (int i = 0; i < m; ++i) {
                double s = std::max(M.capacity[i] - load[i], 1e-9);
                inv[i] = (slack_pow == 1.0) ? 1.0 / s : 1.0 / std::pow(s, slack_pow);
            }
            sc.clear();
            double best = -std::numeric_limits<double>::infinity();
            double worst = std::numeric_limits<double>::infinity();
            for (size_t k = 0; k < cand.size(); ++k) {
                const double* wj = w + (size_t)cand[k] * m;
                double d = 0.0;
                for (int i = 0; i < m; ++i) d += wj[i] * inv[i];
                double s = d > 0.0 ? M.profit[cand[k]] / d : std::numeric_limits<double>::infinity();
                sc.push_back({s, (int)k});
                best = std::max(best, s);
                worst = std::min(worst, s);
            }
            rcl.clear();
            if (std::isinf(best)) {
                for (auto& p : sc) if (std::isinf(p.first)) rcl.push_back(p);
            } else {
                double thr = best - alpha * (best - worst);
                for (auto& p : sc) if (p.first >= thr) rcl.push_back(p);
            }
            if ((int)rcl.size() > rcl_max) {
                std::nth_element(rcl.begin(), rcl.begin() + rcl_max, rcl.end(),
                                 [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
                                     if (a.first != b.first) return a.first > b.first;
                                     return a.second < b.second;
                                 });
                rcl.resize(rcl_max);
            }
            int k = rcl[rng.below((int)rcl.size())].second;
            int j = cand[k];
            x[j] = 1;
            const double* wj = w + (size_t)j * m;
            for (int i = 0; i < m; ++i) load[i] += wj[i];
            cand[k] = cand.back();
            cand.pop_back();
        }
        return codec.finalize(x);
    }
private:
    bool fits(int j, const double* w) const {
        const double* wj = w + (size_t)j * m;
        for (int i = 0; i < m; ++i) if (load[i] + wj[i] > lim[i]) return false;
        return true;
    }
    const Model& M;
    Codec codec;
    int n, m;
    double alpha;
    int rcl_max;
    double slack_pow;
    std::vector<double> lim, load, inv;
    std::vector<char> x;
    std::vector<int> cand;
    std::vector<std::pair<double, int>> sc, rcl;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = params.get("alpha", 0.15);
    int rcl_max = (int)params.get("rcl_max", 4);
    double sp = params.get("slack_pow", 1.0);
    return std::make_unique<GraspSlackRcl>(model, alpha, rcl_max, sp);
}
