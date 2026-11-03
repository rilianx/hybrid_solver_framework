// COMPONENT: {"name": "lcs_insertion_relink", "slot": "relink", "params": {"random_gap_prob": {"type": "float", "range": [0.0, 1.0]}}}
class LcsInsertionRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& md;
    double gapProb;
    std::vector<int> pg, v, tailIdx, tailVal, par, outS;
    std::vector<char> inS;
    std::vector<uint32_t> mk;
    uint32_t stamp = 0;

    bool isPerm(const Sol& s) {
        if (s.size() != 1 || (int)s[0].size() != md.n) return false;
        if (++stamp == 0) { std::fill(mk.begin(), mk.end(), 0u); stamp = 1; }
        for (int x : s[0]) {
            if (x < 0 || x >= md.n || mk[x] == stamp) return false;
            mk[x] = stamp;
        }
        return true;
    }
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
    static Sol genStep(const Sol& cur, const Sol& g, Rng& rng) {
        Sol s = cur;
        if (s.size() > g.size()) { s.pop_back(); return s; }
        if (s.size() < g.size()) { s.emplace_back(); return s; }
        std::vector<int> rows;
        for (size_t r = 0; r < s.size(); ++r) if (s[r] != g[r]) rows.push_back((int)r);
        if (rows.empty()) return s;
        int r = rows[rng.below((int)rows.size())];
        std::vector<int>& a = s[r]; const std::vector<int>& b = g[r];
        if (a.size() != b.size()) {
            if (a.size() > b.size()) a.pop_back(); else a.push_back(b[a.size()]);
            return s;
        }
        std::vector<int> mism;
        for (size_t i = 0; i < a.size(); ++i) if (a[i] != b[i]) mism.push_back((int)i);
        int i = mism[rng.below((int)mism.size())];
        for (int k : mism) if (a[k] == b[i]) { std::swap(a[i], a[k]); return s; }
        a[i] = b[i];
        return s;
    }
    // LCS de dos permutaciones vía LIS; marca inS; devuelve su longitud
    int lcs(const std::vector<int>& c, const std::vector<int>& g) {
        int n = md.n;
        for (int i = 0; i < n; ++i) pg[g[i]] = i;
        int L = 0;
        for (int i = 0; i < n; ++i) {
            int x = pg[c[i]];
            v[i] = x;
            int lo = (int)(std::lower_bound(tailVal.begin(), tailVal.begin() + L, x) - tailVal.begin());
            par[i] = lo > 0 ? tailIdx[lo - 1] : -1;
            tailIdx[lo] = i; tailVal[lo] = x;
            if (lo == L) ++L;
        }
        std::fill(inS.begin(), inS.end(), 0);
        if (L > 0) for (int i = tailIdx[L - 1]; i >= 0; i = par[i]) inS[c[i]] = 1;
        return L;
    }
public:
    LcsInsertionRelink(const Model& m, double gp) : md(m), gapProb(gp) {
        int n = std::max(1, md.n);
        pg.assign(n, 0); v.assign(n, 0); tailIdx.assign(n, 0); tailVal.assign(n, 0);
        par.assign(n, -1); inS.assign(n, 0); mk.assign(n, 0u);
    }
    int distance(const Sol& a, const Sol& b) override {
        if (isPerm(a) && isPerm(b)) return md.n - lcs(a[0], b[0]);
        long long h = genHam(a, b);
        if (h == 0) return 0;
        return (int)std::min<long long>((long long)md.n + h, std::numeric_limits<int>::max());
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (!(isPerm(cur) && isPerm(guide))) return genStep(cur, guide, rng);
        const std::vector<int>& c = cur[0];
        const std::vector<int>& g = guide[0];
        int L = lcs(c, g);
        int n = md.n;
        if (L == n) return guide;
        outS.clear();
        for (int i = 0; i < n; ++i) if (!inS[c[i]]) outS.push_back(i);
        int p = outS[rng.below((int)outS.size())];
        int x = c[p];
        int pred = -1, succ = -1;
        for (int k = pg[x] - 1; k >= 0; --k) if (inS[g[k]]) { pred = g[k]; break; }
        for (int k = pg[x] + 1; k < n; ++k) if (inS[g[k]]) { succ = g[k]; break; }
        Sol s = cur;
        std::vector<int>& r = s[0];
        r.erase(r.begin() + p);
        int lo = 0, hi = (int)r.size();
        if (pred >= 0 || succ >= 0) {
            for (int i = 0; i < (int)r.size(); ++i) {
                if (r[i] == pred) lo = i + 1;
                if (r[i] == succ) hi = i;
            }
        }
        int at = lo;
        if (hi > lo && rng.uniform() < gapProb) at = lo + rng.below(hi - lo + 1);
        r.insert(r.begin() + at, x);
        return s;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double gp = params.get("random_gap_prob", 0.5);
    gp = std::min(1.0, std::max(0.0, gp));
    return std::make_unique<LcsInsertionRelink>(model, gp);
}
