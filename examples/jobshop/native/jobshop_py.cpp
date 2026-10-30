// Módulo Python `hsf_jobshop`: el modelo y el catálogo nativos del job shop (ver `native_parts.py`).
#include "jobshop.hpp"

#include <hsf/py.hpp>

namespace py = pybind11;
using jobshop::JobShop;

static py::tuple sol_to_py(const JobShop::Solution& s) {
    py::tuple out(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        py::tuple seq(s[i].size());
        for (size_t k = 0; k < s[i].size(); ++k) seq[k] = py::int_(s[i][k]);
        out[i] = seq;
    }
    return out;
}

static JobShop::Solution sol_from_py(py::handle h) {
    JobShop::Solution s;
    for (auto seq : h) {
        s.emplace_back();
        for (auto j : seq) s.back().push_back(j.cast<int>());
    }
    return s;
}

static const hsf::Catalog<JobShop> CATALOG = jobshop::handwritten();

PYBIND11_MODULE(hsf_jobshop, mod) {
    hsf::bind_model<JobShop>(mod, &CATALOG, sol_to_py, sol_from_py);
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
    py::class_<JobShop::Partial>(mod, "Partial")
        .def_readonly("seqs", &JobShop::Partial::seqs)
        .def_readonly("nxt", &JobShop::Partial::nxt)
        .def_readonly("job_ready", &JobShop::Partial::job_ready)
        .def_readonly("mach_ready", &JobShop::Partial::mach_ready)
        .def_readonly("order", &JobShop::Partial::order)
        .def("__repr__", [](const JobShop::Partial& p) {
            return "Partial(seqs=" + std::string(py::repr(py::cast(p.seqs))) + ", order=" + std::string(py::repr(py::cast(p.order))) + ")";
        });
    py::class_<JobShop::Action>(mod, "Action")
        .def_readonly("job", &JobShop::Action::job)
        .def_readonly("op", &JobShop::Action::op)
        .def_readonly("machine", &JobShop::Action::machine)
        .def_readonly("start", &JobShop::Action::start)
        .def_readonly("end", &JobShop::Action::end)
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
