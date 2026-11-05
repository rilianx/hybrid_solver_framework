// COMPONENT: {"name": "giffler_thompson_grasp_active", "slot": "constructor", "params": {"rule": {"type": "cat", "values": ["mwkr", "spt", "mopr", "random"]}, "alpha": {"type": "float", "range": [0.0, 1.0]}}}
class GifflerThompsonGrasp : public hsf::Constructor<Model> {
public:
    GifflerThompsonGrasp(const Model& md, std::string rule, double alpha)
        : md_(md), rule_(std::move(rule)), alpha_(alpha) {
        maxm_ = md_.m;
        for (auto& r : md_.routes) for (auto& o : r) maxm_ = std::max(maxm_, o.first + 1);
        tot_.assign(md_.n, 0);
        for (int j = 0; j < md_.n; ++j) for (auto& o : md_.routes[j]) tot_[j] += o.second;
    }
    Model::Solution build(Rng& rng) override {
        int n = md_.n;
        nk_.assign(n, 0); jr_.assign(n, 0); mr_.assign(maxm_, 0);
        rem_ = tot_;
        Model::Solution s(md_.m);
        int left = md_.total_ops;
        while (left > 0) {
            long long cstar = LLONG_MAX; int mstar = -1, jstar = -1;
            for (int j = 0; j < n; ++j) {
                if (nk_[j] >= (int)md_.routes[j].size()) continue;
                auto& op = md_.routes[j][nk_[j]];
                long long est = std::max(jr_[j], mr_[op.first]);
                long long ect = est + op.second;
                if (ect < cstar) { cstar = ect; mstar = op.first; jstar = j; }
            }
            cand_.clear(); score_.clear();
            double lo = 1e300, hi = -1e300;
            for (int j = 0; j < n; ++j) {
                int L = (int)md_.routes[j].size();
                if (nk_[j] >= L) continue;
                auto& op = md_.routes[j][nk_[j]];
                if (op.first != mstar) continue;
                long long est = std::max(jr_[j], mr_[op.first]);
                if (!(est < cstar || j == jstar)) continue;
                double sc;
                if (rule_ == "spt") sc = op.second;
                else if (rule_ == "mopr") sc = -(double)(L - nk_[j]);
                else if (rule_ == "random") sc = rng.uniform();
                else sc = -(double)rem_[j];
                cand_.push_back(j); score_.push_back(sc);
                lo = std::min(lo, sc); hi = std::max(hi, sc);
            }
            double thr = lo + alpha_ * (hi - lo) + 1e-12;
            pool_.clear();
            for (size_t t = 0; t < cand_.size(); ++t) if (score_[t] <= thr) pool_.push_back(cand_[t]);
            int j = pool_.size() == 1 ? pool_[0] : pool_[rng.below((int)pool_.size())];
            auto& op = md_.routes[j][nk_[j]];
            long long est = std::max(jr_[j], mr_[op.first]);
            long long e = est + op.second;
            jr_[j] = e; mr_[op.first] = e;
            rem_[j] -= op.second;
            if (op.first < md_.m) s[op.first].push_back(j);
            ++nk_[j]; --left;
        }
        return s;
    }
private:
    const Model& md_;
    std::string rule_;
    double alpha_;
    int maxm_;
    std::vector<long long> tot_, rem_, jr_, mr_;
    std::vector<int> nk_, cand_, pool_;
    std::vector<double> score_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = std::min(1.0, std::max(0.0, params.get("alpha", 0.2)));
    return std::make_unique<GifflerThompsonGrasp>(model, params.text("rule", "mwkr"), alpha);
}
