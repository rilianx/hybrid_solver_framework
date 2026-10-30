// COMPONENT: {"name": "bottleneck_weighted_work", "slot": "greedy_score", "params": {"gamma": {"type": "float", "range": [0.0, 4.0]}, "beta": {"type": "float", "range": [0.0, 2.0]}, "idle_w": {"type": "float", "range": [0.0, 2.0]}}}
class BottleneckWeightedWork : public hsf::GreedyScore<JobShop> {
public:
    BottleneckWeightedWork(const JobShop& md, double gamma, double beta, double idle_w)
        : M(md), beta_(beta), idle_w_(idle_w) {
        std::vector<double> load(M.m, 0.0);
        for (int j = 0; j < M.n; ++j)
            for (auto& [mm, pt] : M.routes[j]) load[mm] += pt;
        double mx = 1e-9;
        for (double l : load) mx = std::max(mx, l);
        std::vector<double> w(M.m);
        for (int mm = 0; mm < M.m; ++mm) w[mm] = std::pow(load[mm] / mx, gamma);
        bwork_.assign(M.n_ops + 1, 0.0);
        for (int j = 0; j < M.n; ++j) {
            double acc = 0.0;
            for (int k = (int)M.routes[j].size() - 1; k >= 0; --k) {
                acc += M.routes[j][k].second * w[M.routes[j][k].first];
                bwork_[M.off[j] + k] = acc;
            }
        }
    }
    double score(const JobShop::Partial& p, const JobShop::Action& a) override {
        double idle = a.start - p.mach_ready[a.machine];
        return a.start + idle_w_ * idle - beta_ * bwork_[M.off[a.job] + a.op];
    }
private:
    const JobShop& M;
    double beta_, idle_w_;
    std::vector<double> bwork_;
};

std::unique_ptr<hsf::GreedyScore<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<BottleneckWeightedWork>(model, params.get("gamma", 2.0), params.get("beta", 0.5),
                                                    params.get("idle_w", 0.5));
}
