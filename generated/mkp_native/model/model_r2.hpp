#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <utility>
#include <cmath>
#include <algorithm>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<double> profit;      // profit[j]
    std::vector<double> wcol;        // wcol[j*m + i] = weight[i][j]
    std::vector<double> capacity;    // capacity[i]
    double total_profit = 0.0;
    double penalty = 10.0;
    double big = 0.0;                // extra de violación para que infactible > cualquier factible
    mutable std::vector<double> load;

    static Model parse(const std::string& text) {
        Model M;
        std::istringstream in(text);
        in >> M.n >> M.m;
        M.profit.assign(M.n, 0.0);
        for (int j = 0; j < M.n; ++j) in >> M.profit[j];
        M.wcol.assign((size_t)M.n * M.m, 0.0);
        for (int i = 0; i < M.m; ++i)
            for (int j = 0; j < M.n; ++j) {
                double w = 0; in >> w;
                M.wcol[(size_t)j * M.m + i] = w;
            }
        M.capacity.assign(M.m, 0.0);
        for (int i = 0; i < M.m; ++i) in >> M.capacity[i];
        M.total_profit = 0.0;
        for (int j = 0; j < M.n; ++j) M.total_profit += std::fabs(M.profit[j]);
        M.load.assign(M.m, 0.0);
        // cota del |costo| de cualquier solución (p.ej. la trivial de referencia)
        M.penalty = 10.0 * (M.total_profit + 1.0);
        M.big = (M.total_profit + 1.0) / M.penalty;
        return M;
    }

    Solution trivial() const { return Solution{std::vector<int>(n, 0)}; }

    Solution random(hsf::Rng& rng) const {
        Solution s{std::vector<int>(n, 0)};
        for (int j = 0; j < n; ++j) s[0][j] = rng.below(2);
        return s;
    }

    // devuelve beneficio total y exceso total (suma de excesos sobre recursos)
    inline void eval(const Solution& s, double& prof, double& excess) const {
        prof = 0.0; excess = 0.0;
        if (s.empty()) return;
        const std::vector<int>& x = s[0];
        int len = std::min<int>(n, (int)x.size());
        std::fill(load.begin(), load.end(), 0.0);
        for (int j = 0; j < len; ++j) {
            if (x[j]) {
                prof += profit[j];
                const double* w = &wcol[(size_t)j * m];
                for (int i = 0; i < m; ++i) load[i] += w[i];
            }
        }
        for (int i = 0; i < m; ++i) {
            double e = load[i] - capacity[i];
            if (e > 1e-9) excess += e;
        }
    }

    inline double cap_violation(double excess) const {
        return excess > 0.0 ? excess + big : 0.0;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double p, e; eval(s, p, e);
        out.emplace_back("capacidad", cap_violation(e));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double p, e; eval(s, p, e);
        out.emplace_back("beneficio", -p);
    }

    double objective(const Solution& s) const {
        double p, e; eval(s, p, e);
        return -p + penalty * cap_violation(e);
    }

    bool feasible(const Solution& s) const {
        double p, e; eval(s, p, e);
        return e <= 0.0;
    }
};

} // namespace gen
