// El catálogo escrito a mano del CVRP en C++: la partida de referencia y los puntajes del constructor greedy (los
// de `construction.py`). Los vecindarios, perturbaciones y relinks en C++ los escribe el LLM (`llm.native_generator`).
#pragma once

#include "model.hpp"

namespace cvrp {

struct CheapestInsertion : hsf::GreedyScore<CVRP> {
    double score(const CVRP::Partial&, const CVRP::Action& a) override { return a.delta; }
};

struct NearestFromDepot : hsf::GreedyScore<CVRP> {
    const CVRP& v;
    explicit NearestFromDepot(const CVRP& m) : v(m) {}
    double score(const CVRP::Partial&, const CVRP::Action& a) override { return 1000.0 * v.dist(0, a.customer) + a.delta; }
};

inline hsf::Catalog<CVRP> handwritten() {
    hsf::Catalog<CVRP> c;
    // el constructor de referencia de Python (`SingletonRoutes`): una ruta por cliente
    c.constructors["singleton_routes"] = [](const CVRP& m, const hsf::Config&) { return std::make_unique<hsf::TrivialConstructor<CVRP>>(m); };
    c.scores["cheapest_insertion"] = [](const CVRP&, const hsf::Config&) { return std::make_unique<CheapestInsertion>(); };
    c.scores["nearest_from_depot"] = [](const CVRP& m, const hsf::Config&) { return std::make_unique<NearestFromDepot>(m); };
    return c;
}

}  // namespace cvrp
