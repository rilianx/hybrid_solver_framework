// COMPONENT: {"name": "clsp_related_items_horizon", "slot": "destruction", "params": {"alpha": {"type": "float", "range": [0.0, 1.0]}, "noise": {"type": "float", "range": [0.0, 1.0]}}}
class RelatedItemsHorizon : public hsf::Destruction<Model> {
public:
    RelatedItemsHorizon(const Model& m, double alpha, double noise)
        : m_(m), alpha_(alpha), noise_(noise) {
        int n = m.n, T = m.T;
        normD_.assign(n, std::vector<double>(T, 0.0));
        for (int i = 0; i < n; ++i) {
            double nn = 0.0;
            for (int t = 0; t < T; ++t) nn += m.d[i][t] * m.d[i][t];
            nn = std::sqrt(nn);
            if (nn > 0) for (int t = 0; t < T; ++t) normD_[i][t] = m.d[i][t] / nn;
        }
        score_.resize(n); order_.resize(n);
    }

    std::vector<int> destroy(const Sol& s, double ratio, Rng& rng) override {
        const int n = m_.n, T = m_.T, N = n * T;
        std::vector<int> out;
        if (N <= 0) return out;
        long long k = std::llround(ratio * N);
        if (k < 1) k = 1;
        if (k > N) k = N;
        int rows = (int)(k / T), rem = (int)(k % T);
        int seed = rng.below(n);
        for (int j = 0; j < n; ++j) {
            if (j == seed) { score_[j] = 1e18; continue; }
            int both = 0, either = 0;
            for (int t = 0; t < T; ++t) {
                bool a = s[seed][t] != 0, b = s[j][t] != 0;
                both += (a && b); either += (a || b);
            }
            double pat = either > 0 ? (double)both / either : 0.0;
            double cs = 0.0;
            for (int t = 0; t < T; ++t) cs += normD_[seed][t] * normD_[j][t];
            score_[j] = alpha_ * pat + (1.0 - alpha_) * cs + noise_ * rng.uniform();
        }
        std::iota(order_.begin(), order_.end(), 0);
        std::sort(order_.begin(), order_.end(), [&](int a, int b) { return score_[a] > score_[b]; });
        out.reserve((size_t)k);
        for (int r = 0; r < rows && r < n; ++r) {
            int i = order_[r];
            for (int t = 0; t < T; ++t) out.push_back(i * T + t);
        }
        if (rem > 0 && rows < n) {
            int i = order_[rows];
            int st = rng.below(T - rem + 1);
            for (int t = st; t < st + rem; ++t) out.push_back(i * T + t);
        }
        if (out.empty()) out.push_back(rng.below(N));
        return out;
    }
private:
    const Model& m_;
    double alpha_, noise_;
    std::vector<std::vector<double>> normD_;
    std::vector<double> score_;
    std::vector<int> order_;
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<RelatedItemsHorizon>(model, params.get("alpha", 0.5), params.get("noise", 0.2));
}
