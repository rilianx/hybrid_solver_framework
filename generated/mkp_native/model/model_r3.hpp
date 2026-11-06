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
    mutable std::vector<unsigned> mark;
    mutable unsigned stamp = 0;

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
        md.mark.assign(md.n, 0u);
        double tc = md.profit_of(md.trivial());
        md.penalty = 10.0 * (std::fabs(-tc) + 1.0);
        return md;
    }

    Solution trivial() const { return Solution(1); }

    Solution random(hsf::Rng& rng) const {
        Solution x(1);
        for (int j = 0; j < n; ++j)
            if (rng.below(2)) x[0].push_back(j);
        return x;
    }

    // Recorre los ítems elegidos (índices en s[0]), sin repetir ni salirse de rango.
    template <class F>
    void for_chosen(const Solution& s, F&& f) const {
        if (s.empty()) return;
        if (++stamp == 0) {
            std::fill(mark.begin(), mark.end(), 0u);
            stamp = 1;
        }
        for (int j : s[0]) {
            if (j < 0 || j >= n) continue;
            if (mark[j] == stamp) continue;
            mark[j] = stamp;
            f(j);
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
