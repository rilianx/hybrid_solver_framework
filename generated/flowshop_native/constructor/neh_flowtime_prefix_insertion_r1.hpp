// COMPONENT: {"name": "neh_flowtime_prefix_insertion", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 0.5]}, "max_pos": {"type": "int", "range": [10, 300]}, "order": {"type": "cat", "values": ["sum_asc", "sum_desc", "random"]}}}
class NehFlow : public hsf::Constructor<Model> {
public:
    NehFlow(const Model& md, double noise, int maxpos, std::string order)
        : md_(md), noise_(noise), maxpos_(std::max(2, maxpos)), order_(std::move(order)) {}
    Model::Solution build(Rng& rng) override {
        const int n = md_.n, m = md_.m;
        if (n <= 0) return Model::Solution{std::vector<int>()};
        if (m <= 0) return md_.trivial();
        std::vector<std::pair<double, int>> key(n);
        for (int j = 0; j < n; ++j) {
            double s = 0;
            for (int i = 0; i < m; ++i) s += (double)md_.pj[(size_t)j * m + i];
            double f = 1.0 + noise_ * (2.0 * rng.uniform() - 1.0);
            if (order_ == "random") key[j] = {rng.uniform(), j};
            else if (order_ == "sum_desc") key[j] = {-s * f, j};
            else key[j] = {s * f, j};
        }
        std::sort(key.begin(), key.end());
        std::vector<int> seq;
        seq.reserve(n);
        P_.assign((size_t)(n + 1) * m, 0);
        F_.assign(n + 1, 0);
        std::vector<long long> Cw(m);
        std::vector<int> cand;
        for (int t = 0; t < n; ++t) {
            int j = key[t].second;
            int k = (int)seq.size();
            cand.clear();
            if (k + 1 <= maxpos_) { for (int q = 0; q <= k; ++q) cand.push_back(q); }
            else {
                int off = rng.below(std::max(1, k / (maxpos_ - 1)));
                for (int c = 0; c < maxpos_; ++c) {
                    int q = (int)((long long)c * k / (maxpos_ - 1)) + off;
                    if (q > k) q = k;
                    if (cand.empty() || cand.back() != q) cand.push_back(q);
                }
                if (cand.back() != k) cand.push_back(k);
            }
            long long best = std::numeric_limits<long long>::max();
            int bestq = k;
            for (int q : cand) {
                const long long* pr = &P_[(size_t)q * m];
                for (int i = 0; i < m; ++i) Cw[i] = pr[i];
                long long sum = F_[q];
                add(Cw, j, m);
                sum += Cw[m - 1];
                bool cut = sum >= best;
                for (int x = q; x < k && !cut; ++x) {
                    add(Cw, seq[x], m);
                    sum += Cw[m - 1];
                    if (sum >= best) cut = true;
                }
                if (!cut && sum < best) { best = sum; bestq = q; }
            }
            seq.insert(seq.begin() + bestq, j);
            for (int x = bestq; x <= k; ++x) {
                long long* dst = &P_[(size_t)(x + 1) * m];
                const long long* src = &P_[(size_t)x * m];
                const long long* p = &md_.pj[(size_t)seq[x] * m];
                long long prev = 0;
                for (int i = 0; i < m; ++i) { dst[i] = std::max(src[i], prev) + p[i]; prev = dst[i]; }
                F_[x + 1] = F_[x] + dst[m - 1];
            }
        }
        return Model::Solution{seq};
    }
private:
    void add(std::vector<long long>& C, int j, int m) const {
        const long long* p = &md_.pj[(size_t)j * m];
        long long prev = 0;
        for (int i = 0; i < m; ++i) { C[i] = std::max(C[i], prev) + p[i]; prev = C[i]; }
    }
    const Model& md_;
    double noise_;
    int maxpos_;
    std::string order_;
    std::vector<long long> P_, F_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double nz = params.get("noise", 0.1);
    int mp = (int)params.get("max_pos", 80);
    std::string ord = params.text("order", "sum_asc");
    return std::make_unique<NehFlow>(model, nz, mp, ord);
}
