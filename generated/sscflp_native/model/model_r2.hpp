#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <utility>
#include <algorithm>
#include <numeric>
#include <cstdlib>
#include <cmath>

namespace gen {

struct Model {
    using Solution = std::vector<int>;

    int n = 0, m = 0;
    std::vector<double> capacity, fixed, demand;
    std::vector<double> cost;  // cost[i*m + j]
    double penalty = 10.0;

    mutable std::vector<double> load_;
    mutable std::vector<char> open_;

    struct Eval { double apertura, transporte, unassigned, excess; };

    static Model parse(const std::string& text) {
        Model md;
        const char* p = text.c_str();
        char* end = nullptr;
        auto next = [&]() -> double {
            double v = std::strtod(p, &end);
            if (end == p) return 0.0;
            p = end;
            return v;
        };
        md.n = (int)next();
        md.m = (int)next();
        md.capacity.resize(md.n);
        md.fixed.resize(md.n);
        for (int i = 0; i < md.n; ++i) { md.capacity[i] = next(); md.fixed[i] = next(); }
        md.demand.resize(md.m);
        for (int j = 0; j < md.m; ++j) md.demand[j] = next();
        md.cost.assign((size_t)md.n * md.m, 0.0);
        for (int i = 0; i < md.n; ++i)
            for (int j = 0; j < md.m; ++j) md.cost[(size_t)i * md.m + j] = next();
        md.load_.assign(md.n, 0.0);
        md.open_.assign(md.n, 0);
        Solution t = md.trivial();
        Eval e = md.eval(t);
        md.penalty = 10.0 * (std::fabs(e.apertura + e.transporte) + 1.0);
        return md;
    }

    // Greedy: clientes por demanda decreciente al centro más barato (costo incremental) con capacidad residual.
    Solution trivial() const {
        std::vector<int> a(m, -1);
        std::vector<int> ord(m);
        std::iota(ord.begin(), ord.end(), 0);
        std::stable_sort(ord.begin(), ord.end(), [&](int x, int y) { return demand[x] > demand[y]; });
        std::vector<double> res(capacity);
        std::vector<char> op(n, 0);
        for (int j : ord) {
            int best = -1; double bc = 0;
            for (int i = 0; i < n; ++i) {
                if (res[i] + 1e-9 < demand[j]) continue;
                double c = cost[(size_t)i * m + j] + (op[i] ? 0.0 : fixed[i]);
                if (best < 0 || c < bc) { best = i; bc = c; }
            }
            if (best >= 0) { a[j] = best; res[best] -= demand[j]; op[best] = 1; }
        }
        return a;
    }

    Solution random(hsf::Rng& rng) const {
        std::vector<int> a(m, -1);
        if (n > 0) for (int j = 0; j < m; ++j) a[j] = rng.below(n);
        return a;
    }

    Eval eval(const Solution& s) const {
        std::fill(load_.begin(), load_.end(), 0.0);
        std::fill(open_.begin(), open_.end(), 0);
        Eval e{0, 0, 0, 0};
        int lim = std::min<int>(m, (int)s.size());
        for (int j = 0; j < lim; ++j) {
            int v = s[j];
            if (v >= 0 && v < n) {
                load_[v] += demand[j];
                e.transporte += cost[(size_t)v * m + j];
                if (!open_[v]) { open_[v] = 1; e.apertura += fixed[v]; }
            } else {
                e.unassigned += 1.0;
            }
        }
        if (lim < m) e.unassigned += (double)(m - lim);
        for (int i = 0; i < n; ++i) {
            double ex = load_[i] - capacity[i];
            if (ex > 1e-9) e.excess += ex;
        }
        return e;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        Eval e = eval(s);
        out.clear();
        out.emplace_back("asignacion", e.unassigned);
        out.emplace_back("capacidad", e.excess);
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        Eval e = eval(s);
        out.clear();
        out.emplace_back("apertura", e.apertura);
        out.emplace_back("transporte", e.transporte);
    }

    double objective(const Solution& s) const {
        Eval e = eval(s);
        return e.apertura + e.transporte + penalty * (e.unassigned + e.excess);
    }

    bool feasible(const Solution& s) const {
        Eval e = eval(s);
        return e.unassigned == 0.0 && e.excess <= 1e-9;
    }
};

}  // namespace gen
