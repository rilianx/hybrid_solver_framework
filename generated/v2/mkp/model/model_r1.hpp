#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <utility>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <limits>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<double> profit;     // n
    std::vector<double> wt;         // transpuesta: wt[j*m + i]
    std::vector<double> capacity;   // m
    double penalty = 1.0;
    mutable std::vector<double> used;

    static constexpr double EPS = 1e-9;

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
        md.capacity.assign(md.m, 0.0);
        for (int i = 0; i < md.m; ++i) in >> md.capacity[i];
        md.used.assign(md.m, 0.0);
        Solution t = md.trivial();
        double c = md.total_profit(t);
        md.penalty = 10.0 * (std::fabs(-c) + 1.0);
        return md;
    }

    double total_profit(const Solution& s) const {
        double p = 0.0;
        if (s.empty()) return 0.0;
        const auto& x = s[0];
        int lim = std::min<int>(n, (int)x.size());
        for (int j = 0; j < lim; ++j) if (x[j]) p += profit[j];
        return p;
    }

    double excess(const Solution& s) const {
        std::fill(used.begin(), used.end(), 0.0);
        if (!s.empty()) {
            const auto& x = s[0];
            int lim = std::min<int>(n, (int)x.size());
            for (int j = 0; j < lim; ++j) if (x[j]) {
                const double* w = &wt[(size_t)j * m];
                for (int i = 0; i < m; ++i) used[i] += w[i];
            }
        }
        double ex = 0.0;
        for (int i = 0; i < m; ++i) {
            double d = used[i] - capacity[i];
            if (d > EPS * std::max(1.0, std::fabs(capacity[i]))) ex += d;
        }
        return ex;
    }

    Solution trivial() const {
        const double INF = std::numeric_limits<double>::infinity();
        std::vector<double> ratio(n);
        for (int j = 0; j < n; ++j) {
            double sum = 0.0;
            for (int i = 0; i < m; ++i) {
                double w = wt[(size_t)j * m + i];
                if (capacity[i] > 0) sum += w / capacity[i];
                else if (w > 0) sum += INF;
            }
            if (sum == 0.0) ratio[j] = INF;
            else if (std::isinf(sum)) ratio[j] = 0.0;
            else ratio[j] = profit[j] / sum;
        }
        std::vector<int> ord(n);
        std::iota(ord.begin(), ord.end(), 0);
        std::stable_sort(ord.begin(), ord.end(), [&](int a, int b) {
            return ratio[a] > ratio[b];
        });
        std::vector<double> rem(capacity);
        Solution s(1, std::vector<int>(n, 0));
        for (int j : ord) {
            const double* w = &wt[(size_t)j * m];
            bool fits = true;
            for (int i = 0; i < m; ++i)
                if (w[i] > rem[i] + EPS * std::max(1.0, std::fabs(capacity[i]))) { fits = false; break; }
            if (fits) {
                for (int i = 0; i < m; ++i) rem[i] -= w[i];
                s[0][j] = 1;
            }
        }
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        Solution s(1, std::vector<int>(n, 0));
        for (int j = 0; j < n; ++j) s[0][j] = rng.below(2);
        return s;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("capacidad", excess(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("beneficio", -total_profit(s));
    }

    double objective(const Solution& s) const {
        return -total_profit(s) + penalty * excess(s);
    }

    bool feasible(const Solution& s) const {
        return excess(s) == 0.0;
    }
};

} // namespace gen
