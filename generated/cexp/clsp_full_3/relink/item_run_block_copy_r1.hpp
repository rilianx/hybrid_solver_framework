// COMPONENT: {"name": "item_run_block_copy", "slot": "relink", "params": {"short_bias": {"type": "float", "range": [0.0, 1.0]}, "max_runs": {"type": "int", "range": [1, 3]}}}
class ItemRunBlockCopy : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    double shortBias;
    int maxRuns;
    struct Run { int i, a, b; };
    std::vector<Run> runs;
public:
    ItemRunBlockCopy(const Model& model, double sb, int mr) : m(model), shortBias(sb), maxRuns(mr) {
        runs.reserve((size_t)m.n * (m.T / 2 + 1));
    }
    int distance(const Sol& a, const Sol& b) override {
        int dd = 0;
        size_t R = std::min(a.size(), b.size());
        for (size_t i = 0; i < R; ++i) {
            const int* ai = a[i].data();
            const int* bi = b[i].data();
            size_t L = std::min(a[i].size(), b[i].size());
            bool prev = false;
            for (size_t t = 0; t < L; ++t) {
                bool df = ai[t] != bi[t];
                if (df && !prev) ++dd;
                prev = df;
            }
        }
        return dd;
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        runs.clear();
        int T = m.T;
        for (int i = 0; i < m.n; ++i) {
            const int* ci = cur[i].data();
            const int* gi = guide[i].data();
            int t = 0;
            while (t < T) {
                if (ci[t] != gi[t]) {
                    int s = t;
                    while (t < T && ci[t] != gi[t]) ++t;
                    runs.push_back({i, s, t});
                } else ++t;
            }
        }
        Sol out = cur;
        int total = (int)runs.size();
        if (total == 0) return out;
        int k = 1 + rng.below(std::max(1, maxRuns));
        if (k > total) k = total;
        for (int f = 0; f < k; ++f) {
            int sz = (int)runs.size();
            int p = rng.below(sz);
            if (sz > 1 && rng.uniform() < shortBias) {
                int q = rng.below(sz);
                if (runs[q].b - runs[q].a < runs[p].b - runs[p].a) p = q;
            }
            Run r = runs[p];
            runs[p] = runs.back();
            runs.pop_back();
            std::vector<int>& oi = out[r.i];
            const std::vector<int>& gi = guide[r.i];
            for (int t = r.a; t < r.b; ++t) oi[t] = gi[t];
        }
        return out;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sb = params.get("short_bias", 0.3);
    int mr = (int)params.get("max_runs", 1);
    if (mr < 1) mr = 1;
    return std::make_unique<ItemRunBlockCopy>(model, sb, mr);
}
