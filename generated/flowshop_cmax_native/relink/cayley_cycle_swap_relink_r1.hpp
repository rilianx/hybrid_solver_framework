// COMPONENT: {"name": "cayley_cycle_swap_relink", "slot": "relink", "params": {"max_swaps": {"type": "int", "range": [1, 4]}, "multi_prob": {"type": "float", "range": [0.0, 1.0]}}}
class CayleyCycleSwapRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& M;
    int maxSwaps;
    double multiProb;
    std::vector<int> mark, posB, posC, mism;
    std::vector<char> seen;
    int stamp = 0;

    bool isPerm(const Sol& s) {
        if (s.size() != 1) return false;
        const auto& v = s[0];
        if ((int)v.size() != M.n) return false;
        if (++stamp == std::numeric_limits<int>::max()) { std::fill(mark.begin(), mark.end(), 0); stamp = 1; }
        for (int j : v) {
            if (j < 0 || j >= M.n || mark[j] == stamp) return false;
            mark[j] = stamp;
        }
        return true;
    }
    static long long rawDiff(const Sol& a, const Sol& b) {
        long long d = std::llabs((long long)a.size() - (long long)b.size());
        size_t R = std::min(a.size(), b.size());
        for (size_t r = 0; r < R; ++r) {
            const auto& x = a[r]; const auto& y = b[r];
            size_t L = std::min(x.size(), y.size());
            d += std::llabs((long long)x.size() - (long long)y.size());
            for (size_t i = 0; i < L; ++i) if (x[i] != y[i]) ++d;
        }
        return d;
    }
    Sol fbStep(const Sol& cur, const Sol& guide, Rng& rng) {
        if (cur.size() != guide.size()) return guide;
        Sol out = cur;
        for (size_t r = 0; r < cur.size(); ++r) {
            if (cur[r] == guide[r]) continue;
            auto& x = out[r]; const auto& y = guide[r];
            size_t L = std::min(x.size(), y.size());
            mism.clear();
            for (size_t i = 0; i < L; ++i) if (x[i] != y[i]) mism.push_back((int)i);
            if (!mism.empty()) { int i = mism[rng.below((int)mism.size())]; x[i] = y[i]; }
            else if (x.size() > y.size()) x.pop_back();
            else x.push_back(y[x.size()]);
            return out;
        }
        return guide;
    }
    int permDist(const std::vector<int>& a, const std::vector<int>& b) {
        int n = M.n;
        for (int k = 0; k < n; ++k) posB[b[k]] = k;
        std::fill(seen.begin(), seen.end(), 0);
        int cycles = 0;
        for (int i = 0; i < n; ++i) {
            if (seen[i]) continue;
            ++cycles;
            int j = i;
            while (!seen[j]) { seen[j] = 1; j = posB[a[j]]; }
        }
        return n - cycles;
    }

public:
    CayleyCycleSwapRelink(const Model& m, int ms, double mp)
        : M(m), maxSwaps(ms), multiProb(mp), mark(m.n, 0), posB(m.n), posC(m.n), seen(m.n, 0) {}

    int distance(const Sol& a, const Sol& b) override {
        if (a == b) return 0;
        if (isPerm(a) && isPerm(b)) return permDist(a[0], b[0]);
        long long d = (long long)M.n + rawDiff(a, b);
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur == guide) return guide;
        if (!(isPerm(cur) && isPerm(guide))) return fbStep(cur, guide, rng);
        Sol out = cur;
        auto& v = out[0];
        const auto& g = guide[0];
        int n = M.n;
        for (int i = 0; i < n; ++i) posC[v[i]] = i;
        int done = 0;
        while (true) {
            mism.clear();
            for (int i = 0; i < n; ++i) if (v[i] != g[i]) mism.push_back(i);
            if (mism.empty()) break;
            int i = mism[rng.below((int)mism.size())];
            int k = posC[g[i]];
            std::swap(v[i], v[k]);
            posC[v[i]] = i; posC[v[k]] = k;
            ++done;
            if (done >= maxSwaps || rng.uniform() >= multiProb) break;
        }
        return out;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ms = (int)params.get("max_swaps", 1.0);
    if (ms < 1) ms = 1;
    double mp = params.get("multi_prob", 0.3);
    return std::make_unique<CayleyCycleSwapRelink>(model, ms, mp);
}
