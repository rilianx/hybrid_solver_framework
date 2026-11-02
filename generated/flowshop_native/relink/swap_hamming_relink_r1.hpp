// COMPONENT: {"name": "swap_hamming_relink", "slot": "relink", "params": {"pair_bias": {"type": "float", "range": [0.0, 1.0]}}}
class SwapHammingRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& md;
    double pairBias;
    std::vector<int> pos, mism, cand;
    std::vector<uint32_t> pst;
    uint32_t stamp = 0;

    static long long rowHam(const std::vector<int>& a, const std::vector<int>& b) {
        size_t k = std::min(a.size(), b.size());
        long long d = 0;
        for (size_t i = 0; i < k; ++i) d += (a[i] != b[i]);
        return d + (long long)(std::max(a.size(), b.size()) - k);
    }
    static long long genHam(const Sol& a, const Sol& b) {
        size_t k = std::min(a.size(), b.size());
        long long d = 0;
        for (size_t r = 0; r < k; ++r) d += rowHam(a[r], b[r]);
        const Sol& L = a.size() > b.size() ? a : b;
        for (size_t r = k; r < L.size(); ++r) d += (long long)L[r].size() + 1;
        return d;
    }
    void rowStep(std::vector<int>& a, const std::vector<int>& b, Rng& rng) {
        if (a.size() != b.size()) {
            if (a.size() > b.size()) a.pop_back(); else a.push_back(b[a.size()]);
            return;
        }
        mism.clear();
        for (size_t i = 0; i < a.size(); ++i) if (a[i] != b[i]) mism.push_back((int)i);
        if (mism.empty()) return;
        if (++stamp == 0) { std::fill(pst.begin(), pst.end(), 0u); stamp = 1; }
        for (int i : mism) { int x = a[i]; if (x >= 0 && x < md.n) { pos[x] = i; pst[x] = stamp; } }
        auto findK = [&](int i) -> int {
            int y = b[i];
            if (y >= 0 && y < md.n && pst[y] == stamp && a[pos[y]] == y) return pos[y];
            return -1;
        };
        int i = -1;
        if (pairBias > 0 && rng.uniform() < pairBias) {
            cand.clear();
            for (int t : mism) { int k = findK(t); if (k >= 0 && a[t] == b[k]) cand.push_back(t); }
            if (!cand.empty()) i = cand[rng.below((int)cand.size())];
        }
        if (i < 0) i = mism[rng.below((int)mism.size())];
        int k = findK(i);
        if (k >= 0 && k != i) std::swap(a[i], a[k]);
        else a[i] = b[i];
    }
public:
    SwapHammingRelink(const Model& m, double pb) : md(m), pairBias(pb) {
        pos.assign(std::max(1, md.n), 0); pst.assign(std::max(1, md.n), 0u);
    }
    int distance(const Sol& a, const Sol& b) override {
        long long d = genHam(a, b);
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        Sol s = cur;
        if (s.size() > guide.size()) { s.pop_back(); return s; }
        if (s.size() < guide.size()) { s.emplace_back(); return s; }
        std::vector<int> rows;
        for (size_t r = 0; r < s.size(); ++r) if (s[r] != guide[r]) rows.push_back((int)r);
        if (rows.empty()) return s;
        int r = rows[rng.below((int)rows.size())];
        rowStep(s[r], guide[r], rng);
        return s;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double pb = params.get("pair_bias", 0.5);
    pb = std::min(1.0, std::max(0.0, pb));
    return std::make_unique<SwapHammingRelink>(model, pb);
}
