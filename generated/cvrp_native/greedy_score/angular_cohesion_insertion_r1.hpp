// COMPONENT: {"name": "angular_cohesion_insertion", "slot": "greedy_score", "params": {"ang_w": {"type": "float", "range": [0.0, 2.0]}, "open_factor": {"type": "float", "range": [1.0, 3.0]}}}
class AngularCohesionInsertion : public hsf::GreedyScore<CVRP> {
public:
    AngularCohesionInsertion(const CVRP& m, double ang_w, double open_factor)
        : m_(m), w_(ang_w), open_(open_factor) {
        ang_.assign(m.n + 1, 0.0);
        for (int c = 1; c <= m.n; ++c) ang_[c] = std::atan2(m.y[c] - m.y[0], m.x[c] - m.x[0]);
    }
    double score(const CVRP::Partial& p, const CVRP::Action& a) override {
        if (a.new_route) return open_ * a.delta;
        const auto& r = p.routes[a.route];
        if (r.empty()) return a.delta;
        double d = std::fabs(ang_[a.customer] - ang_[r[0]]);
        if (d > M_PI) d = 2.0 * M_PI - d;
        return a.delta + w_ * d * m_.dist(0, a.customer);
    }
private:
    const CVRP& m_;
    double w_, open_;
    std::vector<double> ang_;
};

std::unique_ptr<hsf::GreedyScore<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<AngularCohesionInsertion>(model, params.get("ang_w", 0.5), params.get("open_factor", 1.5));
}
