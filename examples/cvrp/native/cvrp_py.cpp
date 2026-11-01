// Módulo Python `hsf_cvrp`: el modelo y el catálogo escrito a mano del CVRP (ver `native_parts.py`).
#include "bindings.hpp"
#include "handwritten.hpp"

static const hsf::Catalog<cvrp::CVRP> CATALOG = cvrp::handwritten();

PYBIND11_MODULE(hsf_cvrp, mod) {
    hsf::bind_model<cvrp::CVRP>(mod, &CATALOG, cvrp_py::sol_to_py, cvrp_py::sol_from_py);
    cvrp_py::bind_problem(mod);
}
