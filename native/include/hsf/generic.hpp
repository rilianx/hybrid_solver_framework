// Un MODELO en C++ escrito por el LLM (`llm.native_model_generator`) y sus bindings, iguales para cualquier problema.
//
// El contrato (lo que ve el LLM; el modelo va en `namespace gen` y se llama `Model`):
//
//   struct Model {
//       using Solution = std::vector<std::vector<int>>;   // la solución con la forma de la respuesta del problema
//       double penalty;                                   // peso de una unidad de violación en `objective`
//       static Model parse(const std::string& text);      // la instancia en su formato de entrada
//       Solution trivial() const;                         // la solución trivial (la de la descripción)
//       Solution random(hsf::Rng& rng) const;             // una solución al azar bien formada
//       // magnitud de cada familia de restricciones (0 = se cumple) y cada término del costo, con sus nombres
//       void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const;
//       void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const;
//       double objective(const Solution& s) const;        // Σ costo + penalty · Σ violaciones
//       bool feasible(const Solution& s) const;           // todas las violaciones en 0
//   };
//
// `penalty` = 10 · (|costo de la solución trivial| + 1), como `core.model_parts.PartsModel`. Los esqueletos y los
// componentes solo usan `objective`, `feasible` y lo que el modelo exponga.
#pragma once

#include "model.hpp"

#include <hsf/py.hpp>

namespace hsf::generic {
namespace py = pybind11;

inline py::tuple sol_to_py(const std::vector<std::vector<int>>& s) {
    py::tuple out(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        py::tuple row(s[i].size());
        for (size_t k = 0; k < s[i].size(); ++k) row[k] = py::int_(s[i][k]);
        out[i] = row;
    }
    return out;
}

inline std::vector<std::vector<int>> sol_from_py(py::handle h) {
    std::vector<std::vector<int>> s;
    for (auto row : h) {
        s.emplace_back();
        for (auto v : row) s.back().push_back(v.cast<int>());
    }
    return s;
}

template <class M>
py::dict as_dict(const std::vector<std::pair<std::string, double>>& v) {
    py::dict d;
    for (auto& [k, x] : v) d[py::str(k)] = d.contains(k) ? d[py::str(k)].cast<double>() + x : x;
    return d;
}

template <class M>
void bind_problem(py::module_& mod) {
    using Model = std::shared_ptr<M>;
    mod.def("parse", [](const std::string& text) { return std::make_shared<M>(M::parse(text)); });
    mod.def("trivial_solution", [](Model m) { return sol_to_py(m->trivial()); });
    mod.def("random_solution", [](Model m, uint64_t seed) {
        hsf::Rng rng(seed);
        return sol_to_py(m->random(rng));
    });
    mod.def("violations", [](Model m, py::handle s) {
        std::vector<std::pair<std::string, double>> v;
        m->violations(sol_from_py(s), v);
        return as_dict<M>(v);
    });
    mod.def("cost_terms", [](Model m, py::handle s) {
        std::vector<std::pair<std::string, double>> v;
        m->cost_terms(sol_from_py(s), v);
        return as_dict<M>(v);
    });
    mod.def("penalty", [](Model m) { return m->penalty; });
}

}  // namespace hsf::generic
