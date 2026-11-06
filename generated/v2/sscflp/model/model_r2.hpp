#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <utility>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<double> capacity, fixed, demand;
    std::vector<double> cost;  // cost[i*m + j]
    std::vector<int> order_demand;  // clientes por demanda decreciente
    double penalty = 1.0;
    mutable std::vector<double> load;

    double c(int i, int j) const { return cost[(size_t)i * m + j]; }

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        in >> md.n >> md.m;
        md.capacity.assign(md.n, 0.0);
        md.fixed.assign(md.n, 0.0);
        for (int i = 0; i < md.n; ++i) in >> md.capacity[i] >> md.fixed[i];
        md.demand.assign(md.m, 0.0);
        for (int j = 0; j < md.m; ++j) in >> md.demand[j];
        md.cost.assign((size_t)md.n * md.m, 0.0);
        for (int i = 0; i < md.n; ++i)
            for (int j = 0; j < md.m; ++j) in >> md.cost[(size_t)i * md.m + j];
        md.load.assign(md.n, 0.0);
        md.order_demand.resize(md.m);
        std::iota(md.order_demand.begin(), md.order_demand.end(), 0);
        std::stable_sort(md.order_demand.begin(), md.order_demand.end(),
                         [&](int a, int b) { return md.demand[a] > md.demand[b]; });
        md.penalty = 1.0;
        Solution t = md.trivial();
        std::vector<std::pair<std::string, double>> terms;
        md.cost_terms(t, terms);
        double tc = 0.0;
        for (const auto& kv : terms) tc += kv.second;
        md.penalty = 10.0 * (std::fabs(tc) + 1.0);
        return md;
    }

    // Voraz: clientes por demanda decreciente; cada uno al centro con menor costo incremental
    // (asignación + fijo si está cerrado) que tenga capacidad residual; si ninguno, al más barato.
    Solution trivial() const {
        Solution s(1, std::vector<int>(m, -1));
        if (n == 0) return s;
        std::vector<double> rem(capacity);
        std::vector<char> open(n, 0);
        for (int j : order_demand) {
            int best = -1; double bv = 0;
            for (int i = 0; i < n; ++i) {
                if (rem[i] + 1e-9 < demand[j]) continue;
                double v = c(i, j) + (open[i] ? 0.0 : fixed[i]);
                if (best < 0 || v < bv) { best = i; bv = v; }
            }
            if (best < 0) {
                for (int i = 0; i < n; ++i) {
                    double v = c(i, j) + (open[i] ? 0.0 : fixed[i]);
                    if (best < 0 || v < bv) { best = i; bv = v; }
                }
            }
            s[0][j] = best;
            rem[best] -= demand[j];
            open[best] = 1;
        }
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        Solution s(1, std::vector<int>(m, -1));
        if (n == 0) return s;
        for (int j = 0; j < m; ++j) s[0][j] = rng.below(n);
        return s;
    }

    // calcula cargas, apertura, transporte, sin atender, exceso
    void eval(const Solution& s, double& open_c, double& trans_c, double& unassigned, double& excess) const {
        std::fill(load.begin(), load.end(), 0.0);
        open_c = trans_c = unassigned = excess = 0.0;
        const std::vector<int>* a = s.empty() ? nullptr : &s[0];
        for (int j = 0; j < m; ++j) {
            int i = (a && j < (int)a->size()) ? (*a)[j] : -1;
            if (i < 0 || i >= n) { unassigned += 1.0; continue; }
            load[i] += demand[j];
            trans_c += c(i, j);
        }
        for (int i = 0; i < n; ++i) {
            if (load[i] > 0.0 || false) open_c += fixed[i];
            double ex = load[i] - capacity[i];
            if (ex > 1e-9) excess += ex;
        }
    }

    double total_cost(const Solution& s) const {
        double o, t, u, e;
        eval_open_by_count(s, o, t, u, e);
        return o + t;
    }

    // versión que marca abierto por número de clientes (demanda 0 también abre)
    void eval_open_by_count(const Solution& s, double& open_c, double& trans_c, double& unassigned,
                            double& excess) const {
        std::fill(load.begin(), load.end(), 0.0);
        open_c = trans_c = unassigned = excess = 0.0;
        const std::vector<int>* a = s.empty() ? nullptr : &s[0];
        // usamos load negativo-sentinela vía conteo separado: codificamos abierto con bit en un segundo paso
        for (int j = 0; j < m; ++j) {
            int i = (a && j < (int)a->size()) ? (*a)[j] : -1;
            if (i < 0 || i >= n) { unassigned += 1.0; continue; }
            trans_c += c(i, j);
        }
        // apertura: centros con al menos un cliente
        for (int j = 0; j < m; ++j) {
            int i = (a && j < (int)a->size()) ? (*a)[j] : -1;
            if (i < 0 || i >= n) continue;
            if (load[i] == 0.0 && !(load[i] < 0.0)) {
                // marcamos con -inf temporal para saber que ya está abierto
            }
        }
        // implementación simple y correcta: carga y bandera
        std::fill(load.begin(), load.end(), -1.0);  // -1 = cerrado
        for (int j = 0; j < m; ++j) {
            int i = (a && j < (int)a->size()) ? (*a)[j] : -1;
            if (i < 0 || i >= n) continue;
            if (load[i] < 0.0) { load[i] = 0.0; open_c += fixed[i]; }
            load[i] += demand[j];
        }
        for (int i = 0; i < n; ++i) {
            if (load[i] < 0.0) continue;
            double ex = load[i] - capacity[i];
            if (ex > 1e-9) excess += ex;
        }
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double o, t, u, e;
        eval_open_by_count(s, o, t, u, e);
        out.clear();
        out.emplace_back("asignacion", u);
        out.emplace_back("capacidad", e);
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double o, t, u, e;
        eval_open_by_count(s, o, t, u, e);
        out.clear();
        out.emplace_back("apertura", o);
        out.emplace_back("transporte", t);
    }

    double objective(const Solution& s) const {
        double o, t, u, e;
        eval_open_by_count(s, o, t, u, e);
        return o + t + penalty * (u + e);
    }

    bool feasible(const Solution& s) const {
        double o, t, u, e;
        eval_open_by_count(s, o, t, u, e);
        return u == 0.0 && e == 0.0;
    }
};

}  // namespace gen
