// COMPONENT: {"name": "clsp_bottleneck_weighted_sampling", "slot": "destruction", "params": {"greed": {"type": "float", "range": [0.5, 4.0]}, "neighbor_weight": {"type": "float", "range": [0.0, 1.0]}, "idle_weight": {"type": "float", "range": [0.02, 0.5]}}}
class BottleneckWeightedSampling : public hsf::Destruction<Model> {
public:
    BottleneckWeightedSampling(const Model& m, double greed, double nw, double idle)
        : m_(m), greed_(greed), nw_(nw), idle_(idle) {
        util_.resize(m.T); keys_.resize((size_t)m.n * m.T);
    }

    std::vector<int> destroy(const Sol& s, double ratio, Rng& rng) override {
        const int n = m_.n, T = m_.T, N = n * T;
        std::vector<int> out;
        if (N <= 0) return out;
        long long k = std::llround(ratio * N);
        if (k < 1) k = 1;
        if (k > N) k = N;
        bool ok = m_.wellFormed(s);
        if (ok) {
            double unmet = 0.0, hold = 0.0;
            m_.solveFlow(s, unmet, hold);
            for (int t = 0; t < T; ++t) {
                double c = m_.cap[t];
                if (c <= 1e-12) { util_[t] = 1.0; continue; }
                double resid = m_.E[m_.srcEdge[t]].cap;
                double u = 1.0 - resid / c;
                util_[t] = std::min(1.0, std::max(0.0, u));
            }
        } else {
            std::fill(util_.begin(), util_.end(), 0.5);
        }
        for (int i = 0; i < n; ++i) {
            const bool wf = ok;
            for (int t = 0; t < T; ++t) {
                double base = 0.05 + util_[t];
                double nb = 0.0; int cnt = 0;
                if (t > 0) { nb += util_[t - 1]; ++cnt; }
                if (t + 1 < T) { nb += util_[t + 1]; ++cnt; }
                if (cnt) base += nw_ * nb / cnt;
                double f;
                bool y = wf && s[i][t];
                if (y) f = 1.0;
                else {
                    bool adj = wf && ((t > 0 && s[i][t - 1]) || (t + 1 < T && s[i][t + 1]));
                    f = adj ? 0.6 : idle_ + (m_.d[i][t] > 0 ? 0.1 : 0.0);
                }
                double w = std::pow(base * f, greed_);
                if (w < 1e-12) w = 1e-12;
                double u = rng.uniform();
                if (u < 1e-300) u = 1e-300;
                keys_[i * T + t] = {std::log(u) / w, i * T + t};
            }
        }
        std::nth_element(keys_.begin(), keys_.begin() + (k - 1), keys_.end(),
                         [](const std::pair<double,int>& a, const std::pair<double,int>& b) { return a.first > b.first; });
        out.reserve((size_t)k);
        for (long long j = 0; j < k; ++j) out.push_back(keys_[j].second);
        if (out.empty()) out.push_back(rng.below(N));
        return out;
    }
private:
    const Model& m_;
    double greed_, nw_, idle_;
    std::vector<double> util_;
    std::vector<std::pair<double,int>> keys_;
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<BottleneckWeightedSampling>(model, params.get("greed", 1.5),
                                                        params.get("neighbor_weight", 0.5),
                                                        params.get("idle_weight", 0.15));
}
