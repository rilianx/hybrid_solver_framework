// Módulo Python `hsf_jobshop`: el modelo y el catálogo escrito a mano del job shop (ver `native_parts.py`).
#include "bindings.hpp"
#include "handwritten.hpp"

static const hsf::Catalog<jobshop::JobShop> CATALOG = jobshop::handwritten();

PYBIND11_MODULE(hsf_jobshop, mod) {
    hsf::bind_model<jobshop::JobShop>(mod, &CATALOG, jobshop_py::sol_to_py, jobshop_py::sol_from_py);
    jobshop_py::bind_problem(mod);
}
