// COMPONENT: {"name": "biased_job_repetition_sampling_best_of_k", "slot": "constructor", "params": {"samples": {"type": "int", "range": [1, 30]}, "beta": {"type": "float", "range": [0.0, 3.0]}}}
class BiasedRepetitionSampler : public hsf::Constructor<Model> {
public:
    BiasedRepetitionSampler(const Model& md, int samples, double beta)
        : md_(md), samples_(samples), beta_(beta) {
        tot_.assign(md_.n, 0);
        for (int j = 0; j < md_.n; ++j) for (auto& o : md_.routes[j]) tot_[j] += o.second;
    }
    Model::Solution build(Rng& rng) override {
        Model::Solution best;
        double bestv = 1e300;
        for (int k = 0; k < samples_; ++k) {
            Model::Solution s = sample(rng);
            double v = md_.objective(s);
            if (v < bestv) { bestv = v; best = std::move(s); }
        }
        return best;
    }
private:
    Model::Solution sample(Rng& rng) {
        int n = md_.n;
        nk_.assign(n, 0);
        rem_ = tot_;
        w_.assign(n, 0.0);
        Model::Solution s(md_.m);
        int left = md_.total_ops;
        while (left > 0) {
            double sum = 0.0;
            for (int j = 0; j < n; ++j) {
                if (nk_[j] >= (int)md_.routes[j].size()) { w_[j] = 0.0; continue; }
                w_[j] = std::pow((double)rem_[j] + 1.0, beta_);
                sum += w_[j];
            }
            double r = rng.uniform() * sum;
            int pick = -1;
            for (int j = 0; j < n; ++j) {
                if (w_[j] <= 0.0) continue;
                pick = j;
                r -= w_[j];
                if (r <= 0.0) break;
            }
            auto& op = md_.routes[pick][nk_[pick]];
            if (op.first < md_.m) s[op.first].push_back(pick);
            rem_[pick] -= op.second;
            ++nk_[pick]; --left;
        }
        return s;
    }
    const Model& md_;
    int samples_;
    double beta_;
    std::vector<long long> tot_, rem_;
    std::vector<int> nk_;
    std::vector<double> w_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int samples = std::max(1, (int)params.get("samples", 8));
    double beta = params.get("beta", 1.0);
    return std::make_unique<BiasedRepetitionSampler>(model, samples, beta);
}
