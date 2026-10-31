// Bindings genéricos (pybind11) de un modelo C++ y su catálogo: lo que necesita el validador de Python
// para probar los componentes nativos con las mismas capas que los de Python, y `solve` para correr una
// configuración entera en C++.
//
// Del lado de Python, una solución es la misma que en las piezas (p.ej. una tupla de tuplas); `to_py` y
// `from_py` (del pack) la convierten. Un movimiento es una tupla de 6 enteros.
#pragma once

#include <hsf/core.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace hsf {
namespace py = pybind11;

inline Config config_from(const py::dict& d) {
    Config c;
    for (auto [k, v] : d) {
        std::string key = py::str(k);
        if (py::isinstance<py::str>(v)) c.str[key] = v.cast<std::string>();
        else if (v.is_none()) continue;
        else c.num[key] = v.cast<double>();
    }
    return c;
}

inline py::tuple move_to_py(const Move& m) { return py::make_tuple(m[0], m[1], m[2], m[3], m[4], m[5]); }

inline Move move_from(const py::handle& h) {
    Move m{0, 0, 0, 0, 0, 0};
    size_t i = 0;
    for (auto x : h) {
        if (i >= m.size()) throw std::invalid_argument("un movimiento tiene a lo sumo 6 enteros");
        m[i++] = x.cast<int>();
    }
    return m;
}

template <class M>
struct NbhHandle {
    std::shared_ptr<M> model;
    std::unique_ptr<Neighborhood<M>> impl;
};
template <class M>
struct PertHandle {
    std::shared_ptr<M> model;
    std::unique_ptr<Perturbation<M>> impl;
};
template <class M>
struct ScoreHandle {
    std::shared_ptr<M> model;
    std::unique_ptr<GreedyScore<M>> impl;
};
template <class M>
struct CtorHandle {
    std::shared_ptr<M> model;
    std::unique_ptr<Constructor<M>> impl;
};

// `catalog` debe vivir lo que vive el módulo (una variable estática del pack).
template <class M, class ToPy, class FromPy>
void bind_model(py::module_& mod, const Catalog<M>* catalog, ToPy to_py, FromPy from_py) {
    using Move = hsf::Move;
    using Model = std::shared_ptr<M>;
    py::class_<M, std::shared_ptr<M>>(mod, "Model", py::module_local())
        .def("objective", [=](const M& m, py::handle s) { return m.objective(from_py(s)); })
        .def("feasible", [=](const M& m, py::handle s) { return m.feasible(from_py(s)); });

    py::class_<NbhHandle<M>>(mod, "Neighborhood", py::module_local())
        .def("moves", [=](NbhHandle<M>& h, py::handle s) {
            std::vector<Move> out;
            h.impl->moves(from_py(s), out);
            py::list l;
            for (auto& m : out) l.append(move_to_py(m));
            return l;
        })
        .def("apply", [=](NbhHandle<M>& h, py::handle s, py::handle m) { return to_py(h.impl->apply(from_py(s), move_from(m))); })
        .def("delta", [=](NbhHandle<M>& h, py::handle s, py::handle m) { return h.impl->delta(from_py(s), move_from(m)); })
        .def("has_estimate", [](NbhHandle<M>& h) { return h.impl->has_estimate(); })
        .def("estimate", [=](NbhHandle<M>& h, py::handle s, py::handle m) { return h.impl->estimate(from_py(s), move_from(m)); });
    py::class_<PertHandle<M>>(mod, "Perturbation", py::module_local())
        .def("perturb", [=](PertHandle<M>& h, py::handle s, double strength, uint64_t seed) {
            Rng rng(seed);
            return to_py(h.impl->perturb(from_py(s), strength, rng));
        });
    py::class_<CtorHandle<M>>(mod, "Constructor", py::module_local())
        .def("build", [=](CtorHandle<M>& h, uint64_t seed) {
            Rng rng(seed);
            return to_py(h.impl->build(rng));
        });

    py::class_<ScoreHandle<M>>(mod, "GreedyScore", py::module_local())
        .def("score", [](ScoreHandle<M>& h, const typename M::Partial& p, const typename M::Action& a) {
            return h.impl->score(p, a);
        });
    mod.def("make_score", [catalog](Model m, const std::string& name, py::dict params) {
        auto it = catalog->scores.find(name);
        if (it == catalog->scores.end()) throw std::invalid_argument("puntaje desconocido: " + name);
        return ScoreHandle<M>{m, it->second(*m, config_from(params))};
    });
    mod.def("names", [catalog]() {
        py::dict d;
        auto keys = [](const auto& m) { py::list l; for (auto& [k, _] : m) l.append(k); return l; };
        d["constructor"] = keys(catalog->constructors);
        d["greedy_score"] = keys(catalog->scores);
        d["neighborhood"] = keys(catalog->neighborhoods);
        d["perturbation"] = keys(catalog->perturbations);
        return d;
    });
    mod.def("make_neighborhood", [catalog](Model m, const std::string& name, py::dict params) {
        Config c = config_from(params);
        Config scoped;
        for (auto& [k, v] : c.num) scoped.num[name + "." + k] = v;
        for (auto& [k, v] : c.str) scoped.str[name + "." + k] = v;
        return NbhHandle<M>{m, catalog->neighborhood(name, *m, scoped)};
    });
    mod.def("make_perturbation", [catalog](Model m, const std::string& name, py::dict params) {
        Config c = config_from(params), scoped;
        for (auto& [k, v] : c.num) scoped.num[name + "." + k] = v;
        for (auto& [k, v] : c.str) scoped.str[name + "." + k] = v;
        return PertHandle<M>{m, catalog->perturbation(name, *m, scoped)};
    });
    mod.def("make_constructor", [catalog](Model m, const std::string& name, py::dict params) {
        Config c = config_from(params), scoped;
        for (auto& [k, v] : c.num) scoped.num[name + "." + k] = v;
        for (auto& [k, v] : c.str) scoped.str[name + "." + k] = v;
        return CtorHandle<M>{m, catalog->constructor(name, *m, scoped)};
    });
    // corre la configuración entera en C++ (sin el GIL): (mejor solución, objetivo, iteraciones, segundos)
    // la operación que el esqueleto repite, medida en C++ (desde Python la conversión de la solución en cada
    // llamada taparía la diferencia): delta de cada movimiento de cada solución (una vez por movimiento, para no
    // medir una caché por movimiento), perturbaciones o construcciones greedy completas, por segundo
    mod.def("bench", [catalog, from_py](Model m, const std::string& slot, const std::string& name, py::dict params,
                                         py::list sols_py, double seconds) {
        std::vector<typename M::Solution> sols;
        for (auto s : sols_py) sols.push_back(from_py(s));
        Config c = config_from(params), scoped;
        for (auto& [k, v] : c.num) scoped.num[name + "." + k] = v;
        for (auto& [k, v] : c.str) scoped.str[name + "." + k] = v;
        Clock clock;
        long n = 0;
        Rng rng(0), fresh(12345);
        // soluciones nuevas en cada pasada (fuera del tiempo medido): repetir las mismas mediría una caché por solución
        double paused = 0;
        auto busy = [&] { return clock.elapsed() - paused; };
        auto refresh = [&] {
            Clock t;
            for (auto& s : sols) s = m->random(fresh);
            paused += t.elapsed();
        };
        if (slot == "neighborhood") {
            auto nbh = catalog->neighborhood(name, *m, scoped);
            std::vector<Move> mv;
            volatile double sink = 0;
            for (; busy() < seconds; refresh())
                for (auto& s : sols) {
                    mv.clear();
                    nbh->moves(s, mv);
                    for (auto& x : mv) sink = sink + nbh->delta(s, x), ++n;
                    if (busy() >= seconds) break;
                }
        } else if (slot == "neighborhood_ts") {
            // un paso de TS: todos los candidatos con `estimate` (o `delta` si no la hay) y `delta` exacto de los 5
            // mejores; cuenta candidatos revisados por segundo
            auto nbh = catalog->neighborhood(name, *m, scoped);
            std::vector<Move> mv;
            std::vector<std::pair<double, size_t>> order;
            volatile double sink = 0;
            bool est = nbh->has_estimate();
            for (; busy() < seconds; refresh())
                for (auto& s : sols) {
                    mv.clear();
                    nbh->moves(s, mv);
                    order.clear();
                    for (size_t i = 0; i < mv.size(); ++i)
                        order.push_back({est ? nbh->estimate(s, mv[i]) : nbh->delta(s, mv[i]), i});
                    if (est) {
                        size_t k = std::min<size_t>(5, order.size());
                        std::partial_sort(order.begin(), order.begin() + k, order.end());
                        for (size_t i = 0; i < k; ++i) sink = sink + nbh->delta(s, mv[order[i].second]);
                    }
                    n += (long)mv.size();
                    if (busy() >= seconds) break;
                }
        } else if (slot == "neighborhood_walk") {
            // una trayectoria, como la recorren los esqueletos: desde cada solución, 50 pasos en que se revisan los
            // candidatos como en TS y se aplica uno de los 5 mejores (al azar, con la misma semilla); la solución
            // siguiente es la que devolvió `apply`. Cuenta pasos por segundo
            auto nbh = catalog->neighborhood(name, *m, scoped);
            std::vector<Move> mv;
            std::vector<std::pair<double, size_t>> order;
            bool est = nbh->has_estimate();
            for (; busy() < seconds; refresh())
                for (auto& s0 : sols) {
                    auto s = s0;
                    for (int step = 0; step < 50; ++step) {
                        mv.clear();
                        nbh->moves(s, mv);
                        if (mv.empty()) break;
                        order.clear();
                        for (size_t i = 0; i < mv.size(); ++i)
                            order.push_back({est ? nbh->estimate(s, mv[i]) : nbh->delta(s, mv[i]), i});
                        size_t k = std::min<size_t>(5, order.size());
                        std::partial_sort(order.begin(), order.begin() + k, order.end());
                        if (est)
                            for (size_t i = 0; i < k; ++i) order[i].first = nbh->delta(s, mv[order[i].second]);
                        s = nbh->apply(s, mv[order[rng.below((int)k)].second]);
                        ++n;
                    }
                    if (busy() >= seconds) break;
                }
        } else if (slot == "perturbation") {
            auto pert = catalog->perturbation(name, *m, scoped);
            for (; busy() < seconds; refresh())
                for (auto& s : sols) { pert->perturb(s, 1.0, rng); ++n; }
        } else if (slot == "greedy_score" || slot == "constructor") {
            auto ctor = catalog->constructor(slot == "greedy_score" ? "greedy_" + name : name, *m, scoped);
            while (busy() < seconds) { ctor->build(rng); ++n; }
        } else {
            throw std::invalid_argument("bench: slot sin medición: " + slot);
        }
        return n / std::max(busy(), 1e-9);
    });
    // cuánto cuesta cada método de un vecindario (microsegundos por llamada) y cuántos movimientos da por solución
    mod.def("profile_neighborhood", [catalog, from_py](Model m, const std::string& name, py::dict params, py::list sols_py,
                                                        double seconds) {
        std::vector<typename M::Solution> sols;
        for (auto s : sols_py) sols.push_back(from_py(s));
        Config c = config_from(params), scoped;
        for (auto& [k, v] : c.num) scoped.num[name + "." + k] = v;
        for (auto& [k, v] : c.str) scoped.str[name + "." + k] = v;
        auto nbh = catalog->neighborhood(name, *m, scoped);
        bool est = nbh->has_estimate();
        double t_moves = 0, t_delta = 0, t_est = 0, t_apply = 0;
        long n_sol = 0, n_moves = 0, n_apply = 0;
        std::vector<Move> mv;
        volatile double sink = 0;
        Clock total;
        Rng fresh(12345);
        double paused = 0;
        for (; total.elapsed() - paused < seconds; ) {
            for (auto& s : sols) {
                // en una solución nueva (la primera llamada de cada método paga lo que el componente prepare por solución)
                mv.clear();
                Clock a;
                nbh->moves(s, mv);
                t_moves += a.elapsed();
                Clock b;
                for (auto& x : mv) sink = sink + nbh->delta(s, x);
                t_delta += b.elapsed();
                if (est) {
                    Clock e;
                    for (auto& x : mv) sink = sink + nbh->estimate(s, x);
                    t_est += e.elapsed();
                }
                Clock d;
                for (size_t i = 0; i < mv.size() && i < 5; ++i) { auto r = nbh->apply(s, mv[i]); sink = sink + r.size(); ++n_apply; }
                t_apply += d.elapsed();
                ++n_sol;
                n_moves += (long)mv.size();
                if (total.elapsed() - paused >= seconds) break;
            }
            Clock t;  // soluciones nuevas en cada pasada, como en `bench`
            for (auto& s : sols) s = m->random(fresh);
            paused += t.elapsed();
        }
        py::dict out;
        out["moves_per_solution"] = n_sol ? (double)n_moves / n_sol : 0.0;
        out["moves_us_per_solution"] = n_sol ? 1e6 * t_moves / n_sol : 0.0;
        out["delta_us"] = n_moves ? 1e6 * t_delta / n_moves : 0.0;
        if (est) out["estimate_us"] = n_moves ? 1e6 * t_est / n_moves : 0.0;
        out["apply_us"] = n_apply ? 1e6 * t_apply / n_apply : 0.0;
        return out;
    });
    // el objetivo completo por segundo, como referencia del costo de una evaluación
    mod.def("bench_objective", [from_py](Model m, py::list sols_py, double seconds) {
        std::vector<typename M::Solution> sols;
        for (auto s : sols_py) sols.push_back(from_py(s));
        Clock clock;
        long n = 0;
        volatile double sink = 0;
        while (clock.elapsed() < seconds)
            for (auto& s : sols) sink = sink + m->objective(s), ++n;
        return n / std::max(clock.elapsed(), 1e-9);
    });
    mod.def("solve", [catalog, to_py](Model m, py::dict config, std::vector<std::string> shake, uint64_t seed, double budget) {
        Config c = config_from(config);
        Result<M> r = [&] {
            py::gil_scoped_release nogil;
            return solve(*catalog, *m, c, shake, seed, budget);
        }();
        return py::make_tuple(to_py(r.best), r.objective, r.iterations, r.elapsed);
    });
}

}  // namespace hsf
