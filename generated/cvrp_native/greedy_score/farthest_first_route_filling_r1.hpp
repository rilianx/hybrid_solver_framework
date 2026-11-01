// COMPONENT: {"name": "farthest_first_route_filling", "slot": "greedy_score", "params": {"beta": {"type": "float", "range": [0.0, 1.0]}}}
class FarthestFirstRouteFilling : public hsf::GreedyScore<CVRP> {
public:
    FarthestFirstRouteFilling(const CVRP& m, double beta) : m_(m), beta_(beta) {
        double maxPair = 0.0;
        dmax0_ = 0.0;
        for (int c = 1; c <= m.n; ++c) dmax0_ = std::max(dmax0_, m.dist(0, c));
        for (int i = 0; i <= m.n; ++i)
            for (int j = i + 1; j <= m.n; ++j) maxPair = std::max(maxPair, m.dist(i, j));
        // toda inserción vale <= 2*maxPair; abrir ruta siempre queda por encima
        open_ = 2.0 * maxPair + 1.0;
    }
    double score(const CVRP::Partial&, const CVRP::Action& a) override {
        double d0 = m_.dist(0, a.customer);
        if (a.new_route) return open_ + (dmax0_ - d0);  // semilla: el más lejano
        return a.delta - beta_ * d0;
    }
private:
    const CVRP& m_;
    double beta_, dmax0_ = 0.0, open_ = 1.0;
};

std::unique_ptr<hsf::GreedyScore<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<FarthestFirstRouteFilling>(model, params.get("beta", 0.3));
}
