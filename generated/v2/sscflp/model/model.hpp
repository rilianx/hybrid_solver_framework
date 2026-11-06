#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <numeric>
#include <utility>
#include <cmath>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<double> capacity, fixed, demand;
    std::vector<std::vector<double>> cost;
    std::vector<int> cust_order;  // demanda decreciente, empates menor índice
    std::vector<int> fac_order;   // capacidad decreciente, empates menor índice
    double penalty = 1.0;

    mutable std::vector<double> load_;
    mutable std::vector<char> used_;

    static constexpr double EPS = 1e-9;

    static Model parse(const std::string& text) {
        Model M;
        std::istringstream in(text);
        in >> M.n >> M.m;
        M.capacity.assign(M.n, 0.0);
        M.fixed.assign(M.n, 0.0);
        for (int i = 0; i < M.n; ++i) in >> M.capacity[i] >> M.fixed[i];
        M.demand.assign(M.m, 0.0);
        for (int j = 0; j < M.m; ++j) in >> M.demand[j];
        M.cost.assign(M.n, std::vector<double>(M.m, 0.0));
        for (int i = 0; i < M.n; ++i)
            for (int j = 0; j < M.m; ++j) in >> M.cost[i][j];

        M.cust_order.resize(M.m);
        std::iota(M.cust_order.begin(), M.cust_order.end(), 0);
        std::stable_sort(M.cust_order.begin(), M.cust_order.end(),
                         [&](int a, int b) { return M.demand[a] > M.demand[b]; });
        M.fac_order.resize(M.n);
        std::iota(M.fac_order.begin(), M.fac_order.end(), 0);
        std::stable_sort(M.fac_order.begin(), M.fac_order.end(),
                         [&](int a, int b) { return M.capacity[a] > M.capacity[b]; });

        M.load_.assign(M.n, 0.0);
        M.used_.assign(M.n, 0);

        Solution t = M.trivial();
        double c = M.total_cost(t);
        M.penalty = 10.0 * (std::fabs(c) + 1.0);
        return M;
    }

    Solution trivial() const {
        Solution s(1, std::vector<int>(m, -1));
        std::vector<double> freec(capacity);
        bool ok = true;
        for (int j : cust_order) {
            int best = -1;
            double bc = 0.0;
            for (int i = 0; i < n; ++i) {
                if (freec[i] + EPS >= demand[j]) {
                    if (best < 0 || cost[i][j] < bc) { best = i; bc = cost[i][j]; }
                }
            }
            if (best < 0) { ok = false; break; }
            s[0][j] = best;
            freec[best] -= demand[j];
        }
        if (ok) return s;
        // first fit decreasing
        std::fill(s[0].begin(), s[0].end(), -1);
        freec = capacity;
        for (int j : cust_order) {
            for (int i : fac_order) {
                if (freec[i] + EPS >= demand[j]) {
                    s[0][j] = i;
                    freec[i] -= demand[j];
                    break;
                }
            }
        }
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        Solution s(1, std::vector<int>(m, -1));
        if (n > 0)
            for (int j = 0; j < m; ++j) s[0][j] = rng.below(n);
        return s;
    }

    inline int fac_of(const Solution& s, int j) const {
        if (s.empty() || j >= (int)s[0].size()) return -1;
        int i = s[0][j];
        if (i < 0 || i >= n) return -1;
        return i;
    }

    // calcula apertura, transporte, asignacion, capacidad
    void evaluate(const Solution& s, double& ap, double& tr, double& as, double& cap) const {
        std::fill(load_.begin(), load_.end(), 0.0);
        std::fill(used_.begin(), used_.end(), 0);
        ap = tr = as = cap = 0.0;
        for (int j = 0; j < m; ++j) {
            int i = fac_of(s, j);
            if (i < 0) { as += 1.0; continue; }
            tr += cost[i][j];
            load_[i] += demand[j];
            used_[i] = 1;
        }
        for (int i = 0; i < n; ++i) {
            if (used_[i]) ap += fixed[i];
            double ex = load_[i] - capacity[i];
            if (ex > EPS) cap += ex;
        }
    }

    double total_cost(const Solution& s) const {
        double ap, tr, as, cap;
        evaluate(s, ap, tr, as, cap);
        return ap + tr;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double ap, tr, as, cap;
        evaluate(s, ap, tr, as, cap);
        out.clear();
        out.emplace_back("asignacion", as);
        out.emplace_back("capacidad", cap);
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double ap, tr, as, cap;
        evaluate(s, ap, tr, as, cap);
        out.clear();
        out.emplace_back("apertura", ap);
        out.emplace_back("transporte", tr);
    }

    double objective(const Solution& s) const {
        double ap, tr, as, cap;
        evaluate(s, ap, tr, as, cap);
        return ap + tr + penalty * (as + cap);
    }

    bool feasible(const Solution& s) const {
        double ap, tr, as, cap;
        evaluate(s, ap, tr, as, cap);
        return as == 0.0 && cap == 0.0;
    }
};

}  // namespace gen
