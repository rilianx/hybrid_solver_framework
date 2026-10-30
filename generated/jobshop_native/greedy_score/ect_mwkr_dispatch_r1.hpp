// COMPONENT: {"name": "ect_mwkr_dispatch", "slot": "greedy_score", "params": {"w_end": {"type": "float", "range": [0.0, 1.0]}, "mwkr": {"type": "float", "range": [0.0, 2.0]}}}
class EctMwkrDispatch : public hsf::GreedyScore<JobShop> {
public:
    EctMwkrDispatch(const JobShop& md, double w_end, double mwkr) : M(md), w_end_(w_end), mwkr_(mwkr) {
        tail_.assign(M.n_ops + 1, 0);
        for (int j = 0; j < M.n; ++j) {
            int acc = 0;
            for (int k = (int)M.routes[j].size() - 1; k >= 0; --k) {
                acc += M.routes[j][k].second;
                tail_[M.off[j] + k] = acc;
            }
        }
    }
    double score(const JobShop::Partial&, const JobShop::Action& a) override {
        double rem_after = tail_[M.off[a.job] + a.op] - (a.end - a.start);
        return (1.0 - w_end_) * a.start + w_end_ * a.end - mwkr_ * rem_after;
    }
private:
    const JobShop& M;
    double w_end_, mwkr_;
    std::vector<int> tail_;
};

std::unique_ptr<hsf::GreedyScore<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<EctMwkrDispatch>(model, params.get("w_end", 0.5), params.get("mwkr", 0.3));
}
