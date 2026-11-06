// COMPONENT: {"name": "neh_flowtime_insertion_pruned", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 0.4]}, "order": {"type": "cat", "values": ["asc", "desc"]}}}
class NEHFlowtime : public hsf::Constructor<Model> {
public:
    NEHFlowtime(const Model& md, double noise, bool asc) : M(md), noise_(std::max(0.0, noise)), asc_(asc) {}

    Model::Solution build(Rng& rng) override {
        const int n = M.n, m = M.m;
        Model::Solution out(1);
        if (n <= 0) return out;
        std::vector<double> key(n);
        for (int j = 0; j < n; ++j) {
            double s = 0;
            for (int i = 0; i < m; ++i) s += (double)M.pj[(size_t)j * m + i];
            key[j] = s * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
        }
        std::vector<int> ord(n);
        std::iota(ord.begin(), ord.end(), 0);
        std::stable_sort(ord.begin(), ord.end(), [&](int a, int b) {
            return asc_ ? key[a] < key[b] : key[a] > key[b];
        });
        if (m <= 0) { out[0] = ord; return out; }
        std::vector<int> seq;
        seq.reserve(n);
        std::vector<long long> H((size_t)(n + 1) * m, 0);
        std::vector<long long> FP(n + 1, 0);
        std::vector<long long> T(m);
        for (int t = 0; t < n; ++t) {
            int job = ord[t];
            int k = (int)seq.size();
            // heads for prefixes
            for (int pos = 1; pos <= k; ++pos) {
                const long long* p = &M.pj[(size_t)seq[pos - 1] * m];
                const long long* hp = &H[(size_t)(pos - 1) * m];
                long long* hc = &H[(size_t)pos * m];
                hc[0] = hp[0] + p[0];
                for (int i = 1; i < m; ++i) hc[i] = std::max(hc[i - 1], hp[i]) + p[i];
                FP[pos] = FP[pos - 1] + hc[m - 1];
            }
            const long long* pjb = &M.pj[(size_t)job * m];
            long long best = std::numeric_limits<long long>::max();
            int bestPos = k;
            for (int pos = 0; pos <= k; ++pos) {
                const long long* hp = &H[(size_t)pos * m];
                long long F = FP[pos];
                T[0] = hp[0] + pjb[0];
                for (int i = 1; i < m; ++i) T[i] = std::max(T[i - 1], hp[i]) + pjb[i];
                F += T[m - 1];
                if (F >= best) continue;
                bool pruned = false;
                for (int q = pos; q < k; ++q) {
                    const long long* p = &M.pj[(size_t)seq[q] * m];
                    T[0] += p[0];
                    for (int i = 1; i < m; ++i) T[i] = std::max(T[i - 1], T[i]) + p[i];
                    F += T[m - 1];
                    if (F >= best) { pruned = true; break; }
                }
                if (!pruned && F < best) { best = F; bestPos = pos; }
            }
            seq.insert(seq.begin() + bestPos, job);
        }
        out[0] = std::move(seq);
        return out;
    }

private:
    const Model& M;
    double noise_;
    bool asc_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double nz = params.get("noise", 0.1);
    std::string o = params.text("order", "asc");
    return std::make_unique<NEHFlowtime>(model, nz, o != "desc");
}
