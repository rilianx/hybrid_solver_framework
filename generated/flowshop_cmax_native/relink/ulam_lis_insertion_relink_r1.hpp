// COMPONENT: {"name": "ulam_lis_insertion_relink", "slot": "relink", "params": {"placement": {"type": "cat", "values": ["random", "after_pred", "before_succ"]}, "greedy_prob": {"type": "float", "range": [0.0, 1.0]}}}
class UlamLisInsertionRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& M;
    int placement; // 0 random, 1 after_pred, 2 before_succ
    double greedyProb;
    std::vector<int> mark, posG, q, tailIdx, parent, lisList, cand, mism;
    std::vector<char> inLis;
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
    // computes LIS of q (guide positions of cur); marks inLis, fills lisList (indices in increasing order)
    int computeLis(const std::vector<int>& a, const std::vector<int>& b) {
        int n = M.n;
        for (int k = 0; k < n; ++k) posG[b[k]] = k;
        for (int i = 0; i < n; ++i) q[i] = posG[a[i]];
        int len = 0;
        for (int i = 0; i < n; ++i) {
            int lo = 0, hi = len;
            while (lo < hi) { int mid = (lo + hi) >> 1; if (q[tailIdx[mid]] < q[i]) lo = mid + 1; else hi = mid; }
            parent[i] = lo > 0 ? tailIdx[lo - 1] : -1;
            tailIdx[lo] = i;
            if (lo == len) ++len;
        }
        std::fill(inLis.begin(), inLis.end(), 0);
        lisList.assign(len, 0);
        int k = len > 0 ? tailIdx[len - 1] : -1;
        for (int t = len - 1; t >= 0; --t) { lisList[t] = k; inLis[k] = 1; k = parent[k]; }
        return len;
    }

public:
    UlamLisInsertionRelink(const Model& m, int pl, double gp)
        : M(m), placement(pl), greedyProb(gp), mark(m.n, 0), posG(m.n), q(m.n), tailIdx(m.n + 1),
          parent(m.n), inLis(m.n, 0) {}

    int distance(const Sol& a, const Sol& b) override {
        if (a == b) return 0;
        if (isPerm(a) && isPerm(b)) return M.n - computeLis(a[0], b[0]);
        long long d = (long long)M.n + rawDiff(a, b);
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur == guide) return guide;
        if (!(isPerm(cur) && isPerm(guide))) return fbStep(cur, guide, rng);
        const auto& v = cur[0];
        int n = M.n;
        computeLis(v, guide[0]);
        cand.clear();
        for (int i = 0; i < n; ++i) if (!inLis[i]) cand.push_back(i);
        if (cand.empty()) return guide;
        int ix;
        if (rng.uniform() < greedyProb) {
            int best = -1; int bd = -1; int ties = 0;
            for (int i : cand) {
                int d = std::abs(i - q[i]);
                if (d > bd) { bd = d; best = i; ties = 1; }
                else if (d == bd && rng.below(++ties) == 0) best = i;
            }
            ix = best;
        } else ix = cand[rng.below((int)cand.size())];
        int g = q[ix];
        int predJob = -1, succJob = -1;
        for (int t : lisList) {
            if (q[t] < g) predJob = v[t];
            else { succJob = v[t]; break; }
        }
        int x = v[ix];
        Sol out(1);
        auto& w = out[0];
        w.reserve(n);
        for (int i = 0; i < n; ++i) if (i != ix) w.push_back(v[i]);
        int predIdx = -1, succIdx = (int)w.size();
        for (int i = 0; i < (int)w.size(); ++i) {
            if (w[i] == predJob) predIdx = i;
            if (w[i] == succJob) { succIdx = i; break; }
        }
        int lo = predIdx + 1, hi = succIdx;
        int p;
        if (placement == 1) p = lo;
        else if (placement == 2) p = hi;
        else p = lo + rng.below(hi - lo + 1);
        w.insert(w.begin() + p, x);
        return out;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string pl = params.text("placement", "random");
    int p = pl == "after_pred" ? 1 : (pl == "before_succ" ? 2 : 0);
    double gp = params.get("greedy_prob", 0.2);
    return std::make_unique<UlamLisInsertionRelink>(model, p, gp);
}
