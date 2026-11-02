// COMPONENT: {"name": "kendall_inversion_bubble_relink", "slot": "relink", "params": {"max_jump": {"type": "int", "range": [1, 16]}, "direction": {"type": "cat", "values": ["both", "left", "right"]}}}
class KendallInversionBubbleRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& M;
    int maxJump;
    int direction; // 0 both, 1 left, 2 right
    std::vector<int> mark, posG, q, bit, cand, mism;
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
    void mapQ(const std::vector<int>& a, const std::vector<int>& b) {
        int n = M.n;
        for (int k = 0; k < n; ++k) posG[b[k]] = k;
        for (int i = 0; i < n; ++i) q[i] = posG[a[i]];
    }
    long long inversions() {
        int n = M.n;
        std::fill(bit.begin(), bit.end(), 0);
        long long inv = 0;
        for (int i = n - 1; i >= 0; --i) {
            for (int k = q[i]; k > 0; k -= k & -k) inv += bit[k];   // count smaller to the right
            for (int k = q[i] + 1; k <= n; k += k & -k) ++bit[k];
        }
        return inv;
    }
    long long offset() const { return (long long)M.n * (M.n - 1) / 2 + 1; }

public:
    KendallInversionBubbleRelink(const Model& m, int mj, int dir)
        : M(m), maxJump(mj), direction(dir), mark(m.n, 0), posG(m.n), q(m.n), bit(m.n + 1, 0) {}

    int distance(const Sol& a, const Sol& b) override {
        if (a == b) return 0;
        long long d;
        if (isPerm(a) && isPerm(b)) { mapQ(a[0], b[0]); d = inversions(); }
        else d = offset() + rawDiff(a, b);
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur == guide) return guide;
        if (!(isPerm(cur) && isPerm(guide))) return fbStep(cur, guide, rng);
        int n = M.n;
        mapQ(cur[0], guide[0]);
        cand.clear();
        for (int i = 0; i + 1 < n; ++i) if (q[i] > q[i + 1]) cand.push_back(i);
        if (cand.empty()) return guide;
        int i = cand[rng.below((int)cand.size())];
        int L = 1 + rng.below(maxJump);
        bool left = direction == 1 || (direction == 0 && rng.uniform() < 0.5);
        Sol out = cur;
        auto& v = out[0];
        if (left) {
            int j = i + 1;
            int x = v[j], qx = q[j], steps = 0;
            while (j > 0 && steps < L && q[j - 1] > qx) {
                v[j] = v[j - 1]; q[j] = q[j - 1]; --j; ++steps;
            }
            v[j] = x; q[j] = qx;
        } else {
            int j = i;
            int x = v[j], qx = q[j], steps = 0;
            while (j + 1 < n && steps < L && q[j + 1] < qx) {
                v[j] = v[j + 1]; q[j] = q[j + 1]; ++j; ++steps;
            }
            v[j] = x; q[j] = qx;
        }
        return out;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int mj = (int)params.get("max_jump", 4.0);
    if (mj < 1) mj = 1;
    std::string d = params.text("direction", "both");
    int dir = d == "left" ? 1 : (d == "right" ? 2 : 0);
    return std::make_unique<KendallInversionBubbleRelink>(model, mj, dir);
}
