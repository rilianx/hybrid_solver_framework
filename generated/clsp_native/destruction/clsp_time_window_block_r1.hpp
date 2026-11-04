// COMPONENT: {"name": "clsp_time_window_block", "slot": "destruction", "params": {"partial_pick": {"type": "cat", "values": ["random", "setup_first"]}, "dense_start_prob": {"type": "float", "range": [0.0, 1.0]}}}
class TimeWindowBlock : public hsf::Destruction<Model> {
public:
    TimeWindowBlock(const Model& m, std::string pick, double dense)
        : m_(m), setupFirst_(pick == "setup_first"), dense_(dense) {}

    std::vector<int> destroy(const Sol& s, double ratio, Rng& rng) override {
        const int n = m_.n, T = m_.T, N = n * T;
        std::vector<int> out;
        if (N <= 0) return out;
        long long k = std::llround(ratio * N);
        if (k < 1) k = 1;
        if (k > N) k = N;
        int full = (int)(k / n), rem = (int)(k % n);
        int L = full + (rem > 0 ? 1 : 0);
        if (L > T) L = T;
        int maxStart = T - L;
        int start = 0;
        if (rng.uniform() < dense_) {
            // ventana con más setups (zona congestionada), desempate aleatorio
            std::vector<int> cnt(T, 0);
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t) if (s[i][t]) cnt[t]++;
            int best = -1; int cur = 0;
            for (int t = 0; t < L; ++t) cur += cnt[t];
            std::vector<int> cands;
            for (int st = 0; st <= maxStart; ++st) {
                if (st > 0) cur += cnt[st + L - 1] - cnt[st - 1];
                if (cur > best) { best = cur; cands.clear(); cands.push_back(st); }
                else if (cur == best) cands.push_back(st);
            }
            start = cands[rng.below((int)cands.size())];
        } else {
            start = rng.below(maxStart + 1);
        }
        out.reserve((size_t)k);
        bool partialFirst = rem > 0 && rng.uniform() < 0.5;
        int fullStart = partialFirst ? start + 1 : start;
        int partialT = partialFirst ? start : start + full;
        for (int t = fullStart; t < fullStart + full && t < T; ++t)
            for (int i = 0; i < n; ++i) out.push_back(i * T + t);
        if (rem > 0 && partialT >= 0 && partialT < T) {
            perm_.resize(n);
            std::iota(perm_.begin(), perm_.end(), 0);
            std::shuffle(perm_.begin(), perm_.end(), rng.g);
            if (setupFirst_)
                std::stable_partition(perm_.begin(), perm_.end(),
                                      [&](int i) { return s[i][partialT] != 0; });
            for (int j = 0; j < rem; ++j) out.push_back(perm_[j] * T + partialT);
        }
        if (out.empty()) out.push_back(rng.below(N));
        return out;
    }
private:
    const Model& m_;
    bool setupFirst_;
    double dense_;
    std::vector<int> perm_;
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<TimeWindowBlock>(model, params.text("partial_pick", "random"),
                                             params.get("dense_start_prob", 0.3));
}
