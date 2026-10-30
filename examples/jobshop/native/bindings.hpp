// Bindings del modelo del job shop (sin catálogo): conversión de soluciones, la vista heurística como las
// piezas (`trivial_solution`, `violations`, `cost_terms`, ...) y la vista constructiva. Los usan el módulo del
// catálogo a mano (`jobshop_py.cpp`) y los módulos con componentes generados por el LLM (`native/generated.py`).
#pragma once

#include "model.hpp"

#include <hsf/py.hpp>

namespace jobshop_py {
namespace py = pybind11;
using jobshop::JobShop;

inline py::tuple sol_to_py(const JobShop::Solution& s) {
    py::tuple out(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        py::tuple seq(s[i].size());
        for (size_t k = 0; k < s[i].size(); ++k) seq[k] = py::int_(s[i][k]);
        out[i] = seq;
    }
    return out;
}

inline JobShop::Solution sol_from_py(py::handle h) {
    JobShop::Solution s;
    for (auto seq : h) {
        s.emplace_back();
        for (auto j : seq) s.back().push_back(j.cast<int>());
    }
    return s;
}

inline void bind_problem(py::module_& mod) {
    using Model = std::shared_ptr<JobShop>;
    mod.def("parse", [](const std::string& text) { return std::make_shared<JobShop>(JobShop::parse(text)); });

    // la vista heurística, como las piezas
    mod.def("trivial_solution", [](Model m) { return sol_to_py(m->trivial()); });
    mod.def("random_solution", [](Model m, uint64_t seed) {
        hsf::Rng rng(seed);
        return sol_to_py(m->random(rng));
    });
    mod.def("violations", [](Model m, py::handle s) {
        double sq, od, mk;
        m->evaluate(sol_from_py(s), sq, od, mk);
        py::dict d;
        d["secuencia"] = sq;
        d["orden"] = od;
        return d;
    });
    mod.def("cost_terms", [](Model m, py::handle s) {
        double sq, od, mk;
        m->evaluate(sol_from_py(s), sq, od, mk);
        py::dict d;
        d["makespan"] = mk;
        return d;
    });

    // la vista constructiva
    py::class_<JobShop::Partial>(mod, "Partial", py::module_local())
        .def_readonly("seqs", &JobShop::Partial::seqs)
        .def_readonly("nxt", &JobShop::Partial::nxt)
        .def_readonly("job_ready", &JobShop::Partial::job_ready)
        .def_readonly("mach_ready", &JobShop::Partial::mach_ready)
        .def_readonly("order", &JobShop::Partial::order)
        .def(py::pickle(  // el validador compara la parcial antes y después de puntuar (no debe cambiar)
            [](const JobShop::Partial& p) { return py::make_tuple(p.seqs, p.nxt, p.job_ready, p.mach_ready, p.order); },
            [](py::tuple t) {
                return JobShop::Partial{t[0].cast<std::vector<std::vector<int>>>(), t[1].cast<std::vector<int>>(),
                                        t[2].cast<std::vector<int>>(), t[3].cast<std::vector<int>>(), t[4].cast<std::vector<int>>()};
            }))
        .def("__repr__", [](const JobShop::Partial& p) {
            return "Partial(seqs=" + std::string(py::repr(py::cast(p.seqs))) + ", order=" + std::string(py::repr(py::cast(p.order))) + ")";
        });
    py::class_<JobShop::Action>(mod, "Action", py::module_local())
        .def_readonly("job", &JobShop::Action::job)
        .def_readonly("op", &JobShop::Action::op)
        .def_readonly("machine", &JobShop::Action::machine)
        .def_readonly("start", &JobShop::Action::start)
        .def_readonly("end", &JobShop::Action::end)
        .def(py::pickle([](const JobShop::Action& a) { return py::make_tuple(a.job, a.op, a.machine, a.start, a.end); },
                        [](py::tuple t) {
                            return JobShop::Action{t[0].cast<int>(), t[1].cast<int>(), t[2].cast<int>(), t[3].cast<int>(),
                                                   t[4].cast<int>()};
                        }))
        .def("__repr__", [](const JobShop::Action& a) {
            return "Dispatch(job=" + std::to_string(a.job) + ", op=" + std::to_string(a.op) + ", machine=" +
                   std::to_string(a.machine) + ", start=" + std::to_string(a.start) + ", end=" + std::to_string(a.end) + ")";
        });
    mod.def("empty_partial", [](Model m) { return m->empty(); });
    mod.def("candidates", [](Model m, const JobShop::Partial& p) {
        std::vector<JobShop::Action> out;
        m->candidates(p, out);
        return out;
    });
    mod.def("apply_action", [](Model m, const JobShop::Partial& p, const JobShop::Action& a) { return m->apply(p, a); });
    mod.def("is_complete", [](Model m, const JobShop::Partial& p) { return m->is_complete(p); });
    mod.def("to_solution", [](Model m, const JobShop::Partial& p) { return sol_to_py(m->to_solution(p)); });
    mod.def("complete_partial", [](Model m, const JobShop::Partial& p, uint64_t seed) {
        hsf::Rng rng(seed);
        return sol_to_py(m->complete(p, rng));
    });
}

}  // namespace jobshop_py
