// COMPONENT: {"name": "randomized_parallel_savings", "slot": "constructor", "params": {"lambda": {"type": "float", "range": [0.6, 1.8]}, "noise": {"type": "float", "range": [0.0, 0.3]}, "neighbors": {"type": "int", "range": [10, 120]}}}
class RandomizedParallelSavings : public hsf::Constructor<Model> {
public:
    RandomizedParallelSavings(const Model& m, double lambda, double noise, int k)
        : m_(m), lambda_(lambda), noise_(noise), k_(std::max(1, k)) {}

    Sol build(Rng& rng) override {
        const int n = m_.n;
        Sol out;
        if (n <= 0) return out;
        if (!ready_) prepare();

        const size_t P = pi_.size();
        keys_.resize(P);
        for (size_t p = 0; p < P; ++p) {
            int i = pi_[p], j = pj_[p];
            double s = d0_[i] + d0_[j] - lambda_ * pd_[p];
            if (noise_ > 0.0) s *= 1.0 + noise_ * (rng.uniform() - 0.5);
            keys_[p] = {s, (int)p};
        }
        std::sort(keys_.begin(), keys_.end(), [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
            if (a.first != b.first) return a.first > b.first;
            return a.second < b.second;
        });

        parent_.resize(n + 1);
        load_.resize(n + 1);
        nb0_.assign(n + 1, 0);
        nb1_.assign(n + 1, 0);
        for (int c = 0; c <= n; ++c) { parent_[c] = c; load_[c] = m_.demand[c]; }
        const double cap = m_.capacity + 1e-9;

        for (size_t q = 0; q < P; ++q) {
            if (keys_[q].first <= 0.0) break;
            int p = keys_[q].second;
            int i = pi_[p], j = pj_[p];
            if (nb0_[i] != 0 && nb1_[i] != 0) continue;  // i interior
            if (nb0_[j] != 0 && nb1_[j] != 0) continue;  // j interior
            int ri = find(i), rj = find(j);
            if (ri == rj) continue;
            if (load_[ri] + load_[rj] > cap) continue;
            if (nb0_[i] == 0) nb0_[i] = j; else nb1_[i] = j;
            if (nb0_[j] == 0) nb0_[j] = i; else nb1_[j] = i;
            parent_[rj] = ri;
            load_[ri] += load_[rj];
        }

        vis_.assign(n + 1, 0);
        for (int c = 1; c <= n; ++c) {
            if (vis_[c]) continue;
            if (nb0_[c] != 0 && nb1_[c] != 0) continue;
            std::vector<int> route;
            int prev = 0, cur = c;
            while (cur != 0 && !vis_[cur]) {
                route.push_back(cur);
                vis_[cur] = 1;
                int nxt = (nb0_[cur] == prev) ? nb1_[cur] : nb0_[cur];
                prev = cur;
                cur = nxt;
            }
            out.push_back(std::move(route));
        }
        for (int c = 1; c <= n; ++c)  // safety net (should not trigger)
            if (!vis_[c]) out.push_back({c});
        return out;
    }

private:
    int find(int x) {
        while (parent_[x] != x) { parent_[x] = parent_[parent_[x]]; x = parent_[x]; }
        return x;
    }

    void prepare() {
        const int n = m_.n;
        d0_.assign(n + 1, 0.0);
        for (int c = 1; c <= n; ++c) d0_[c] = m_.dist(0, c);
        std::vector<long long> keys;
        std::vector<std::pair<double, int>> cand;
        cand.reserve(n);
        for (int i = 1; i <= n; ++i) {
            cand.clear();
            for (int j = 1; j <= n; ++j) if (j != i) cand.push_back({m_.dist(i, j), j});
            int K = std::min<int>(k_, (int)cand.size());
            if (K < (int)cand.size())
                std::nth_element(cand.begin(), cand.begin() + K, cand.end());
            for (int t = 0; t < K; ++t) {
                int j = cand[t].second;
                int a = std::min(i, j), b = std::max(i, j);
                keys.push_back((long long)a * (n + 1) + b);
            }
        }
        std::sort(keys.begin(), keys.end());
        keys.erase(std::unique(keys.begin(), keys.end()), keys.end());
        pi_.reserve(keys.size()); pj_.reserve(keys.size()); pd_.reserve(keys.size());
        for (long long key : keys) {
            int a = (int)(key / (n + 1)), b = (int)(key % (n + 1));
            pi_.push_back(a); pj_.push_back(b); pd_.push_back(m_.dist(a, b));
        }
        ready_ = true;
    }

    const Model& m_;
    double lambda_, noise_;
    int k_;
    bool ready_ = false;
    std::vector<double> d0_, pd_;
    std::vector<int> pi_, pj_;
    std::vector<std::pair<double, int>> keys_;
    std::vector<int> parent_, nb0_, nb1_;
    std::vector<double> load_;
    std::vector<char> vis_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<RandomizedParallelSavings>(
        model, params.get("lambda", 1.0), params.get("noise", 0.1), (int)params.get("neighbors", 40));
}
