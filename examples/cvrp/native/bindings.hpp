// Bindings del modelo del CVRP (sin catálogo): conversión de soluciones (a la forma canónica de Python), la vista
// heurística como las piezas (`trivial_solution`, `violations`, `cost_terms`, ...) y la vista constructiva. Los usan
// el módulo del catálogo a mano (`cvrp_py.cpp`) y los módulos con componentes generados por el LLM.
#pragma once

#include "model.hpp"

#include <hsf/py.hpp>

namespace cvrp_py {
namespace py = pybind11;
using cvrp::CVRP;

// la forma canónica de `model_parts.canonical`: sin rutas vacías, ordenadas por su primer cliente
inline py::tuple sol_to_py(const CVRP::Solution& s) {
    std::vector<const std::vector<int>*> rs;
    for (auto& r : s) if (!r.empty()) rs.push_back(&r);
    std::stable_sort(rs.begin(), rs.end(), [](auto a, auto b) { return (*a)[0] < (*b)[0]; });
    py::tuple out(rs.size());
    for (size_t i = 0; i < rs.size(); ++i) {
        py::tuple t(rs[i]->size());
        for (size_t k = 0; k < rs[i]->size(); ++k) t[k] = py::int_((*rs[i])[k]);
        out[i] = t;
    }
    return out;
}

inline CVRP::Solution sol_from_py(py::handle h) {
    CVRP::Solution s;
    for (auto r : h) {
        s.emplace_back();
        for (auto c : r) s.back().push_back(c.cast<int>());
    }
    return s;
}

inline void bind_problem(py::module_& mod) {
    using Model = std::shared_ptr<CVRP>;
    mod.def("parse", [](const std::string& text) { return std::make_shared<CVRP>(CVRP::parse(text)); });

    mod.def("trivial_solution", [](Model m) { return sol_to_py(m->trivial()); });
    mod.def("random_solution", [](Model m, uint64_t seed) {
        hsf::Rng rng(seed);
        return sol_to_py(m->random(rng));
    });
    mod.def("violations", [](Model m, py::handle s) {
        double v, c, d;
        m->evaluate(sol_from_py(s), v, c, d);
        py::dict out;
        out["visita"] = v;
        out["capacidad"] = c;
        return out;
    });
    mod.def("cost_terms", [](Model m, py::handle s) {
        double v, c, d;
        m->evaluate(sol_from_py(s), v, c, d);
        py::dict out;
        out["distancia"] = d;
        return out;
    });

    py::class_<CVRP::Partial>(mod, "Partial", py::module_local())
        .def_readonly("routes", &CVRP::Partial::routes)
        .def_readonly("loads", &CVRP::Partial::loads)
        .def_property_readonly("pending", [](const CVRP::Partial& p) {
            std::vector<int> out;
            for (int c = 0; c < (int)p.pending.size(); ++c) if (p.pending[c]) out.push_back(c);
            return out;
        })
        .def(py::pickle(  // el validador compara la parcial antes y después de puntuar (no debe cambiar)
            [](const CVRP::Partial& p) {
                return py::make_tuple(p.routes, p.loads, std::vector<int>(p.pending.begin(), p.pending.end()), p.n_pending);
            },
            [](py::tuple t) {
                auto pend = t[2].cast<std::vector<int>>();
                return CVRP::Partial{t[0].cast<std::vector<std::vector<int>>>(), t[1].cast<std::vector<double>>(),
                                     std::vector<char>(pend.begin(), pend.end()), t[3].cast<int>()};
            }))
        .def("__repr__", [](const CVRP::Partial& p) {
            return "Partial(routes=" + std::string(py::repr(py::cast(p.routes))) + ", pending=" + std::to_string(p.n_pending) + ")";
        });
    py::class_<CVRP::Action>(mod, "Action", py::module_local())
        .def_readonly("customer", &CVRP::Action::customer)
        .def_readonly("route", &CVRP::Action::route)
        .def_readonly("pos", &CVRP::Action::pos)
        .def_readonly("delta", &CVRP::Action::delta)
        .def_readonly("new_route", &CVRP::Action::new_route)
        .def(py::pickle([](const CVRP::Action& a) { return py::make_tuple(a.customer, a.route, a.pos, a.delta, a.new_route); },
                        [](py::tuple t) {
                            return CVRP::Action{t[0].cast<int>(), t[1].cast<int>(), t[2].cast<int>(), t[3].cast<double>(),
                                                t[4].cast<bool>()};
                        }))
        .def("__repr__", [](const CVRP::Action& a) {
            return "InsertAction(customer=" + std::to_string(a.customer) + ", route=" + std::to_string(a.route) + ", pos=" +
                   std::to_string(a.pos) + ", delta=" + std::string(py::repr(py::float_(a.delta))) + ", new_route=" + (a.new_route ? "True" : "False") + ")";
        });
    mod.def("empty_partial", [](Model m) { return m->empty(); });
    mod.def("candidates", [](Model m, const CVRP::Partial& p) {
        std::vector<CVRP::Action> out;
        m->candidates(p, out);
        return out;
    });
    mod.def("apply_action", [](Model m, const CVRP::Partial& p, const CVRP::Action& a) { return m->apply(p, a); });
    mod.def("is_complete", [](Model m, const CVRP::Partial& p) { return m->is_complete(p); });
    mod.def("to_solution", [](Model m, const CVRP::Partial& p) { return sol_to_py(m->to_solution(p)); });
    mod.def("complete_partial", [](Model m, const CVRP::Partial& p, uint64_t seed) {
        hsf::Rng rng(seed);
        return sol_to_py(m->complete(p, rng));
    });
}

}  // namespace cvrp_py
