// COMPONENT: {"name": "demand_weighted_insertion_ratio", "slot": "greedy_score", "params": {"alpha": {"type": "float", "range": [0.0, 1.5]}, "open_factor": {"type": "float", "range": [1.0, 3.0]}}}
class DemandWeightedInsertionRatio : public hsf::GreedyScore<CVRP> {
public:
    DemandWeightedInsertionRatio(const CVRP& m, double alpha, double open_factor)
        : m_(m), open_(open_factor) {
        double tot = 0.0;
        for (int c = 1; c <= m.n; ++c) tot += m.demand[c];
        double mean = m.n > 0 ? tot / m.n : 1.0;
        if (mean <= 0) mean = 1.0;
        w_.assign(m.n + 1, 1.0);
        for (int c = 1; c <= m.n; ++c) {
            double rel = (m.demand[c] + 0.05 * mean) / mean;  // demanda relativa, nunca 0
            w_[c] = 1.0 / std::pow(rel, alpha);
        }
    }
    double score(const CVRP::Partial&, const CVRP::Action& a) override {
        double d = a.new_route ? a.delta * open_ : a.delta;
        return d * w_[a.customer];
    }
private:
    const CVRP& m_;
    double open_;
    std::vector<double> w_;
};

std::unique_ptr<hsf::GreedyScore<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<DemandWeightedInsertionRatio>(model, params.get("alpha", 0.5), params.get("open_factor", 1.5));
}
