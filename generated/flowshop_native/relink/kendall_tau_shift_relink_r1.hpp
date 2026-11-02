// COMPONENT: {"name": "kendall_tau_shift_relink", "slot": "relink", "params": {"max_shift": {"type": "int", "range": [1, 64]}}}
class KendallShiftRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& md;
    int maxShift;
    std::vector<int> pg, v, bit, desc;
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
    void mapRel(const std::vector<int>& c, const std::vector<int>& g) {
        for (int i = 0; i < md.n; ++i) pg[g[i]] = i;
        for (int i = 0; i < md.n; ++i) v[i] = pg[c[i]];
    }
    long long inversions() {
        int n = md.n;
        std::fill(bit.begin(), bit.end(), 0);
        long long inv = 0;
        for (int i = n - 1; i >= 0; --i) {
            for (int k = v[i]; k > 0; k -= k & -k) inv += bit[k];       // menores a la derecha
            for (int k = v[i] + 1; k <= n; k += k & -k) bit[k]++;
        }
        return inv;
    }
    long long offset() const { long long n = md.n; return n * (n - 1) / 2; }
public:
    KendallShiftRelink(const Model& m, int ms) : md(m), maxShift(ms) {
        int n = std::max(1, md.n);
        pg.assign(n, 0); v.assign(n, 0); bit.assign(n + 1, 0); mk.assign(n, 0u);
    }
    int distance(const Sol& a, const Sol& b) override {
        long long d;
        if (isPerm(a) && isPerm(b)) { mapRel(a[0], b[0]); d = inversions(); }
        else {
            long long h = genHam(a, b);
            if (h == 0) return 0;
            d = offset() + h;
        }
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (!(isPerm(cur) && isPerm(guide))) return genStep(cur, guide, rng);
        mapRel(cur[0], guide[0]);
        int n = md.n;
        desc.clear();
        for (int i = 0; i + 1 < n; ++i) if (v[i] > v[i + 1]) desc.push_back(i);
        if (desc.empty()) return guide;
        int i = desc[rng.below((int)desc.size())];
        int cap = 1 + rng.below(std::max(1, maxShift));
        Sol s = cur;
        std::vector<int>& r = s[0];
        int steps = 0;
        if (rng.below(2) == 0) {  // mover r[i] hacia la derecha
            int j = i;
            while (j + 1 < n && v[j] > v[j + 1] && steps < cap) {
                std::swap(v[j], v[j + 1]); std::swap(r[j], r[j + 1]); ++j; ++steps;
            }
        } else {                  // mover r[i+1] hacia la izquierda
            int j = i + 1;
            while (j > 0 && v[j - 1] > v[j] && steps < cap) {
                std::swap(v[j], v[j - 1]); std::swap(r[j], r[j - 1]); --j; ++steps;
            }
        }
        return s;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ms = (int)params.get("max_shift", 8);
    ms = std::max(1, std::min(64, ms));
    return std::make_unique<KendallShiftRelink>(model, ms);
}
