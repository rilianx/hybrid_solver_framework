#pragma once
#include <hsf/core.hpp>
#include <string>
#include <vector>
#include <utility>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <numeric>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0;  // centros
    int m = 0;  // clientes
    std::vector<double> capacity, fixed, demand;
    std::vector<double> cost;  // cost[i*m + j]
    std::vector<int> cheapest; // centro más barato por cliente
    double penalty = 10.0;

    mutable std::vector<double> load;
    mutable std::vector<char> used;

    static constexpr double EPS = 1e-9;

    double c(int i, int j) const { return cost[(size_t)i * m + j]; }

    static Model parse(const std::string& text) {
        Model M;
        const char* p = text.c_str();
        auto next = [&]() -> double {
            char* end;
            double v = std::strtod(p, &end);
            p = end;
            return v;
        };
        M.n = (int)next();
        M.m = (int)next();
        M.capacity.resize(M.n);
        M.fixed.resize(M.n);
        for (int i = 0; i < M.n; ++i) {
            M.capacity[i] = next();
            M.fixed[i] = next();
        }
        M.demand.resize(M.m);
        for (int j = 0; j < M.m; ++j) M.demand[j] = next();
        M.cost.assign((size_t)M.n * M.m, 0.0);
        for (int i = 0; i < M.n; ++i)
            for (int j = 0; j < M.m; ++j) M.cost[(size_t)i * M.m + j] = next();
        M.cheapest.assign(M.m, M.n > 0 ? 0 : -1);
        for (int j = 0; j < M.m; ++j) {
            int best = -1;
            double bc = 0;
            for (int i = 0; i < M.n; ++i) {
                double v = M.c(i, j);
                if (best < 0 || v < bc) { best = i; bc = v; }
            }
            M.cheapest[j] = best;
        }
        M.load.assign(M.n, 0.0);
        M.used.assign(M.n, 0);
        double tc = 0.0, tv = 0.0;
        M.eval(M.trivial(), tc, tv);
        double ta, tt, un, ex;
        M.compute(M.trivial(), ta, tt, un, ex);
        M.penalty = 10.0 * (std::fabs(ta + tt) + 1.0);
        return M;
    }

    bool dfs_fit(int k, const std::vector<int>& ord, const std::vector<double>& suf,
                 std::vector<double>& rem, std::vector<int>& a, long long& budget) const {
        if (k == m) return true;
        if (--budget < 0) return false;
        double tot = 0.0;
        for (int i = 0; i < n; ++i) tot += rem[i];
        if (tot + EPS < suf[k]) return false;
        int j = ord[k];
        std::vector<int> fac(n);
        std::iota(fac.begin(), fac.end(), 0);
        std::sort(fac.begin(), fac.end(), [&](int x, int y) { return c(x, j) < c(y, j); });
        std::vector<double> tried;
        for (int i : fac) {
            if (rem[i] + EPS < demand[j]) continue;
            bool dup = false;
            for (double r : tried) if (std::fabs(r - rem[i]) <= EPS) { dup = true; break; }
            if (dup) continue;
            tried.push_back(rem[i]);
            rem[i] -= demand[j];
            a[j] = i;
            if (dfs_fit(k + 1, ord, suf, rem, a, budget)) return true;
            rem[i] += demand[j];
            a[j] = -1;
            if (budget < 0) return false;
        }
        return false;
    }

    Solution trivial() const {
        Solution s(1, std::vector<int>(m, -1));
        if (n == 0) return s;
        std::vector<int> ord(m);
        std::iota(ord.begin(), ord.end(), 0);
        std::stable_sort(ord.begin(), ord.end(), [&](int x, int y) { return demand[x] > demand[y]; });
        // 1) greedy: más barato que cabe
        std::vector<double> rem(capacity);
        bool ok = true;
        for (int j : ord) {
            int best = -1;
            for (int i = 0; i < n; ++i)
                if (rem[i] + EPS >= demand[j] && (best < 0 || c(i, j) < c(best, j))) best = i;
            if (best < 0) { ok = false; break; }
            rem[best] -= demand[j];
            s[0][j] = best;
        }
        if (ok) return s;
        // 2) búsqueda exacta de factibilidad (con tope)
        std::vector<double> suf(m + 1, 0.0);
        for (int k = m - 1; k >= 0; --k) suf[k] = suf[k + 1] + demand[ord[k]];
        rem = capacity;
        std::vector<int> a(m, -1);
        long long budget = 5000000;
        if (dfs_fit(0, ord, suf, rem, a, budget)) {
            s[0] = a;
            return s;
        }
        // 3) respaldo: centro con más capacidad restante
        rem = capacity;
        for (int j : ord) {
            int best = 0;
            for (int i = 1; i < n; ++i) if (rem[i] > rem[best]) best = i;
            rem[best] -= demand[j];
            s[0][j] = best;
        }
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        Solution s(1, std::vector<int>(m, -1));
        if (n > 0)
            for (int j = 0; j < m; ++j) s[0][j] = rng.below(n);
        return s;
    }

    // apertura, transporte, clientes sin atender, exceso de capacidad
    void compute(const Solution& s, double& apertura, double& transporte,
                 double& unassigned, double& excess) const {
        apertura = 0.0; transporte = 0.0; unassigned = 0.0; excess = 0.0;
        const std::vector<int>* row = s.empty() ? nullptr : &s[0];
        int sz = row ? (int)row->size() : 0;
        for (int j = 0; j < m; ++j) {
            int f = (j < sz) ? (*row)[j] : -1;
            if (f < 0 || f >= n) { unassigned += 1.0; continue; }
            transporte += c(f, j);
            load[f] += demand[j];
            used[f] = 1;
        }
        for (int i = 0; i < n; ++i) {
            if (used[i]) {
                apertura += fixed[i];
                double e = load[i] - capacity[i];
                if (e > EPS) excess += e;
            }
            load[i] = 0.0;
            used[i] = 0;
        }
    }

    void eval(const Solution& s, double& costv, double& viol) const {
        double a, t, u, e;
        compute(s, a, t, u, e);
        costv = a + t;
        viol = u + e;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double a, t, u, e;
        compute(s, a, t, u, e);
        out.clear();
        out.emplace_back("asignacion", u);
        out.emplace_back("capacidad", e);
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double a, t, u, e;
        compute(s, a, t, u, e);
        out.clear();
        out.emplace_back("apertura", a);
        out.emplace_back("transporte", t);
    }

    double objective(const Solution& s) const {
        double a, t, u, e;
        compute(s, a, t, u, e);
        return a + t + penalty * (u + e);
    }

    bool feasible(const Solution& s) const {
        double a, t, u, e;
        compute(s, a, t, u, e);
        return u <= 0.0 && e <= EPS;
    }
};

}  // namespace gen
