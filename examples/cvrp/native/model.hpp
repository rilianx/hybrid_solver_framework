// El MODELO del CVRP en C++ (representación por rutas): la vista heurística y constructiva de `model_parts.py`.
// Mismas familias, mismo costo y misma penalización que `PartsModel(model_parts, inst)`, así que el validador de
// Python lo prueba con los mismos casos. Es lo que ve el LLM cuando genera componentes en C++
// (`llm.native_generator`): solo el modelo, sin componentes.
#pragma once

#include <hsf/core.hpp>

#include <sstream>

namespace cvrp {

using hsf::Move;
using hsf::Rng;

struct CVRP {
    // rutas: cada una, los clientes (1..n) en orden de visita, sin el depósito (0); la cantidad de rutas es libre.
    // El orden de las rutas no importa (Python compara la forma canónica: sin rutas vacías, ordenadas por su primer
    // cliente).
    using Solution = std::vector<std::vector<int>>;

    // vista constructiva: rutas abiertas con su carga y clientes pendientes
    struct Partial {
        std::vector<std::vector<int>> routes;
        std::vector<double> loads;
        std::vector<char> pending;  // pending[c] = 1 si el cliente c falta (pending[0] = 0)
        int n_pending = 0;
    };
    // insertar `customer` en la ruta `route` antes de la posición `pos` (0 = primero); con `new_route`, abrir una
    // ruta nueva con él (`route` = cantidad de rutas, `pos` = 0). `delta` = aumento de distancia.
    struct Action {
        int customer, route, pos;
        double delta;
        bool new_route;
    };

    int n = 0;                       // clientes 1..n; el nodo 0 es el depósito
    double capacity = 0.0;
    bool rounded = false;            // distancias redondeadas al entero más cercano (instancias X de Uchoa)
    std::vector<double> x, y, demand;  // por nodo 0..n (demand[0] = 0)
    std::vector<double> D;           // D[i * (n + 1) + j] = distancia euclidiana de i a j
    double penalty = 0.0;            // peso de cada unidad de violación en el objetivo

    mutable std::vector<int> seen_;  // memoria de trabajo de `evaluate` (un modelo por hilo)

    double dist(int i, int j) const { return D[(size_t)i * (n + 1) + j]; }

    static CVRP parse(const std::string& text) {
        std::istringstream in(text);
        std::string head;
        std::getline(in, head);
        std::istringstream hs(head);
        CVRP v;
        std::string flag;
        hs >> v.n >> v.capacity >> flag;
        v.rounded = flag == "round";
        v.x.resize(v.n + 1), v.y.resize(v.n + 1), v.demand.resize(v.n + 1);
        for (int i = 0; i <= v.n; ++i)
            if (!(in >> v.x[i] >> v.y[i] >> v.demand[i])) throw std::invalid_argument("faltan filas de nodos");
        v.init();
        return v;
    }

    void init() {
        D.assign((size_t)(n + 1) * (n + 1), 0.0);
        for (int i = 0; i <= n; ++i)
            for (int j = 0; j <= n; ++j) {
                double d = std::hypot(x[i] - x[j], y[i] - y[j]);
                D[(size_t)i * (n + 1) + j] = rounded ? std::floor(d + 0.5) : d;
            }
        seen_.assign(n + 1, 0);
        double triv = 0.0;
        for (int c = 1; c <= n; ++c) triv += 2 * dist(0, c);
        penalty = 10.0 * (triv + 1.0);
    }

    double route_length(const std::vector<int>& r) const {
        double t = 0.0;
        int prev = 0;
        for (int c : r) {
            if (c < 1 || c > n) continue;
            t += dist(prev, c);
            prev = c;
        }
        return t + dist(prev, 0);
    }
    double route_load(const std::vector<int>& r) const {
        double l = 0.0;
        for (int c : r) if (c >= 1 && c <= n) l += demand[c];
        return l;
    }

    Solution trivial() const {
        Solution s;
        for (int c = 1; c <= n; ++c) s.push_back({c});
        return s;
    }

    Solution random(Rng& rng) const {
        std::vector<int> cs(n);
        for (int c = 1; c <= n; ++c) cs[c - 1] = c;
        std::shuffle(cs.begin(), cs.end(), rng.g);
        Solution s;
        std::vector<int> cur;
        double load = 0.0;
        for (int c : cs) {
            if (!cur.empty() && (load + demand[c] > capacity || rng.uniform() < 0.25)) {
                s.push_back(cur);
                cur.clear(), load = 0.0;
            }
            cur.push_back(c);
            load += demand[c];
        }
        s.push_back(cur);
        return s;
    }

    // {visita, capacidad} y distancia, como `violations` y `cost_terms` de las piezas
    void evaluate(const Solution& s, double& visita, double& capacidad, double& distancia) const {
        std::fill(seen_.begin(), seen_.end(), 0);
        int bad = 0;
        visita = capacidad = distancia = 0.0;
        for (auto& r : s) {
            for (int c : r) {
                if (c >= 1 && c <= n) ++seen_[c];
                else ++bad;
            }
            capacidad += std::max(0.0, route_load(r) - capacity);
            distancia += route_length(r);
        }
        for (int c = 1; c <= n; ++c) visita += std::abs(seen_[c] - 1);
        visita += bad;
    }

    double objective(const Solution& s) const {
        double v, c, d;
        evaluate(s, v, c, d);
        return d + penalty * (v + c);
    }
    bool feasible(const Solution& s) const {
        double v, c, d;
        evaluate(s, v, c, d);
        return v == 0 && c <= 1e-9;
    }

    // ---------------------------------------------------------------- vista constructiva (inserción)
    Partial empty() const {
        Partial p;
        p.pending.assign(n + 1, 1);
        p.pending[0] = 0;
        p.n_pending = n;
        return p;
    }
    // para cada cliente pendiente (en orden), cada posición de cada ruta donde cabe su demanda, y abrir una ruta nueva
    void candidates(const Partial& p, std::vector<Action>& out) const {
        for (int c = 1; c <= n; ++c) {
            if (!p.pending[c]) continue;
            for (int k = 0; k < (int)p.routes.size(); ++k) {
                if (p.loads[k] + demand[c] > capacity + 1e-9) continue;
                auto& r = p.routes[k];
                for (int pos = 0; pos <= (int)r.size(); ++pos) {
                    int a = pos == 0 ? 0 : r[pos - 1], b = pos == (int)r.size() ? 0 : r[pos];
                    out.push_back({c, k, pos, dist(a, c) + dist(c, b) - dist(a, b), false});
                }
            }
            out.push_back({c, (int)p.routes.size(), 0, 2 * dist(0, c), true});
        }
    }
    Partial apply(const Partial& p, const Action& a) const {
        Partial q = p;
        if (a.new_route) {
            q.routes.push_back({a.customer});
            q.loads.push_back(demand[a.customer]);
        } else {
            q.routes[a.route].insert(q.routes[a.route].begin() + a.pos, a.customer);
            q.loads[a.route] += demand[a.customer];
        }
        q.pending[a.customer] = 0;
        --q.n_pending;
        return q;
    }
    bool is_complete(const Partial& p) const { return p.n_pending == 0; }
    Solution to_solution(const Partial& p) const { return p.routes; }
    Solution complete(const Partial& p, Rng&) const {
        Solution s = p.routes;
        for (int c = 1; c <= n; ++c) if (p.pending[c]) s.push_back({c});
        return s;
    }
};

}  // namespace cvrp
