#pragma once
#include <hsf/core.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<double> profit;    // n
    std::vector<double> wcol;      // n*m, item-major: wcol[j*m+i]
    std::vector<double> capacity;  // m
    std::vector<double> tol;       // m, tolerancia por recurso
    double penalty = 1.0;

    mutable std::vector<double> load_;

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        in >> md.n >> md.m;
        md.profit.assign(md.n, 0.0);
        for (int j = 0; j < md.n; ++j) in >> md.profit[j];
        md.wcol.assign((size_t)md.n * md.m, 0.0);
        for (int i = 0; i < md.m; ++i)
            for (int j = 0; j < md.n; ++j) {
                double w = 0;
                in >> w;
                md.wcol[(size_t)j * md.m + i] = w;
            }
        md.capacity.assign(md.m, 0.0);
        for (int i = 0; i < md.m; ++i) in >> md.capacity[i];
        md.tol.resize(md.m);
        for (int i = 0; i < md.m; ++i) md.tol[i] = 1e-9 * std::max(1.0, std::fabs(md.capacity[i]));
        md.load_.assign(md.m, 0.0);
        Solution t = md.trivial();
        double c = md.cost(t);
        md.penalty = 10.0 * (std::fabs(c) + 1.0);
        return md;
    }

    inline bool chosen(const Solution& s, int j) const {
        return !s.empty() && j < (int)s[0].size() && s[0][j] != 0;
    }

    double cost(const Solution& s) const {
        double p = 0;
        if (s.empty()) return 0.0;
        int lim = std::min(n, (int)s[0].size());
        for (int j = 0; j < lim; ++j)
            if (s[0][j]) p += profit[j];
        return -p;
    }

    double violation(const Solution& s) const {
        if (s.empty() || m == 0) return 0.0;
        std::fill(load_.begin(), load_.end(), 0.0);
        int lim = std::min(n, (int)s[0].size());
        for (int j = 0; j < lim; ++j) {
            if (!s[0][j]) continue;
            const double* w = &wcol[(size_t)j * m];
            for (int i = 0; i < m; ++i) load_[i] += w[i];
        }
        double v = 0;
        for (int i = 0; i < m; ++i) {
            double ex = load_[i] - capacity[i];
            if (ex > tol[i]) v += ex;
        }
        return v;
    }

    Solution trivial() const {
        std::vector<double> ratio(n);
        const double INF = std::numeric_limits<double>::infinity();
        for (int j = 0; j < n; ++j) {
            double sum = 0;
            bool inf_term = false;
            for (int i = 0; i < m; ++i) {
                double w = wcol[(size_t)j * m + i];
                if (capacity[i] != 0) sum += w / capacity[i];
                else if (w > 0) inf_term = true;
            }
            if (inf_term) ratio[j] = 0.0;
            else if (sum == 0) ratio[j] = INF;
            else ratio[j] = profit[j] / sum;
        }
        std::vector<int> order(n);
        std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return ratio[a] > ratio[b]; });
        std::vector<double> rem(capacity);
        Solution s(1, std::vector<int>(n, 0));
        for (int j : order) {
            const double* w = &wcol[(size_t)j * m];
            bool fits = true;
            for (int i = 0; i < m; ++i)
                if (w[i] > rem[i] + tol[i]) { fits = false; break; }
            if (!fits) continue;
            for (int i = 0; i < m; ++i) rem[i] -= w[i];
            s[0][j] = 1;
        }
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        std::vector<int> order(n);
        std::iota(order.begin(), order.end(), 0);
        for (int k = n - 1; k > 0; --k) std::swap(order[k], order[rng.below(k + 1)]);
        std::vector<double> rem(capacity);
        Solution s(1, std::vector<int>(n, 0));
        for (int j : order) {
            if (rng.uniform() < 0.3) continue;
            const double* w = &wcol[(size_t)j * m];
            bool fits = true;
            for (int i = 0; i < m; ++i)
                if (w[i] > rem[i] + tol[i]) { fits = false; break; }
            if (!fits) continue;
            for (int i = 0; i < m; ++i) rem[i] -= w[i];
            s[0][j] = 1;
        }
        return s;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("capacidad", violation(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("beneficio", cost(s));
    }

    double objective(const Solution& s) const {
        return cost(s) + penalty * violation(s);
    }

    bool feasible(const Solution& s) const {
        return violation(s) <= 0.0;
    }
};

}  // namespace gen
