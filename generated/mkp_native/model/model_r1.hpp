#pragma once
#include <hsf/core.hpp>
#include <string>
#include <vector>
#include <sstream>
#include <cmath>
#include <utility>
#include <algorithm>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<double> profit;      // n
    std::vector<double> wt;          // n*m, wt[j*m+i] = weight[i][j]
    std::vector<double> cap;         // m
    double penalty = 10.0;
    mutable std::vector<double> load;

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        in >> md.n >> md.m;
        md.profit.assign(md.n, 0.0);
        for (int j = 0; j < md.n; ++j) in >> md.profit[j];
        md.wt.assign((size_t)md.n * md.m, 0.0);
        for (int i = 0; i < md.m; ++i)
            for (int j = 0; j < md.n; ++j) {
                double w = 0; in >> w;
                md.wt[(size_t)j * md.m + i] = w;
            }
        md.cap.assign(md.m, 0.0);
        for (int i = 0; i < md.m; ++i) in >> md.cap[i];
        md.load.assign(md.m, 0.0);
        double tc = md.profit_of(md.trivial());
        md.penalty = 10.0 * (std::fabs(-tc) + 1.0);
        return md;
    }

    Solution trivial() const { return Solution{std::vector<int>(n, 0)}; }

    Solution random(hsf::Rng& rng) const {
        std::vector<int> x(n, 0);
        for (int j = 0; j < n; ++j) x[j] = rng.below(2);
        return Solution{x};
    }

    // Recorre los ítems elegidos aplanando la solución en orden.
    template <class F>
    void for_chosen(const Solution& s, F&& f) const {
        int j = 0;
        for (const auto& row : s) {
            for (int v : row) {
                if (j >= n) return;
                if (v != 0) f(j);
                ++j;
            }
        }
    }

    double profit_of(const Solution& s) const {
        double p = 0.0;
        for_chosen(s, [&](int j) { p += profit[j]; });
        return p;
    }

    double excess(const Solution& s) const {
        std::fill(load.begin(), load.end(), 0.0);
        for_chosen(s, [&](int j) {
            const double* w = wt.data() + (size_t)j * m;
            for (int i = 0; i < m; ++i) load[i] += w[i];
        });
        double ex = 0.0;
        for (int i = 0; i < m; ++i) {
            double tol = 1e-9 * std::max(1.0, std::fabs(cap[i]));
            if (load[i] > cap[i] + tol) ex += load[i] - cap[i];
        }
        return ex;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("capacidad", excess(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("beneficio", -profit_of(s));
    }

    double objective(const Solution& s) const {
        double p = 0.0;
        std::fill(load.begin(), load.end(), 0.0);
        for_chosen(s, [&](int j) {
            p += profit[j];
            const double* w = wt.data() + (size_t)j * m;
            for (int i = 0; i < m; ++i) load[i] += w[i];
        });
        double ex = 0.0;
        for (int i = 0; i < m; ++i) {
            double tol = 1e-9 * std::max(1.0, std::fabs(cap[i]));
            if (load[i] > cap[i] + tol) ex += load[i] - cap[i];
        }
        return -p + penalty * ex;
    }

    bool feasible(const Solution& s) const { return excess(s) == 0.0; }
};

}  // namespace gen
