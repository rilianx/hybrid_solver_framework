// COMPONENT: {"name": "period_column_copy", "slot": "relink", "params": {"max_cols": {"type": "int", "range": [1, 3]}, "adjacent_prob": {"type": "float", "range": [0.0, 1.0]}}}
class PeriodColumnCopy : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    int maxCols;
    double adjProb;
    std::vector<char> diffCol;
    std::vector<int> cols;
    void computeDiff(const Sol& a, const Sol& b) {
        int T = m.T;
        std::fill(diffCol.begin(), diffCol.end(), 0);
        size_t R = std::min(a.size(), b.size());
        for (size_t i = 0; i < R; ++i) {
            const int* ai = a[i].data();
            const int* bi = b[i].data();
            int L = (int)std::min(std::min(a[i].size(), b[i].size()), (size_t)T);
            for (int t = 0; t < L; ++t) if (ai[t] != bi[t]) diffCol[t] = 1;
        }
    }
    void copyCol(Sol& out, const Sol& guide, int t) {
        for (int i = 0; i < m.n; ++i) out[i][t] = guide[i][t];
    }
public:
    PeriodColumnCopy(const Model& model, int mc, double ap) : m(model), maxCols(mc), adjProb(ap) {
        diffCol.assign(std::max(1, m.T), 0);
        cols.reserve(m.T);
    }
    int distance(const Sol& a, const Sol& b) override {
        computeDiff(a, b);
        int dd = 0;
        for (int t = 0; t < m.T; ++t) dd += diffCol[t];
        return dd;
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        computeDiff(cur, guide);
        cols.clear();
        for (int t = 0; t < m.T; ++t) if (diffCol[t]) cols.push_back(t);
        Sol out = cur;
        int total = (int)cols.size();
        if (total == 0) return out;
        int k = 1 + rng.below(std::max(1, maxCols));
        if (k > total) k = total;
        int last = -1;
        for (int f = 0; f < k; ++f) {
            int t = -1;
            if (last >= 0 && rng.uniform() < adjProb) {
                int cand[2] = {last - 1, last + 1};
                int o = rng.below(2);
                for (int z = 0; z < 2 && t < 0; ++z) {
                    int c = cand[(o + z) & 1];
                    if (c >= 0 && c < m.T && diffCol[c]) t = c;
                }
            }
            if (t < 0) {
                int p = rng.below((int)cols.size());
                t = cols[p];
            }
            // remove t from cols
            for (size_t q = 0; q < cols.size(); ++q)
                if (cols[q] == t) { cols[q] = cols.back(); cols.pop_back(); break; }
            diffCol[t] = 0;
            copyCol(out, guide, t);
            last = t;
        }
        return out;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int mc = (int)params.get("max_cols", 1);
    if (mc < 1) mc = 1;
    double ap = params.get("adjacent_prob", 0.5);
    return std::make_unique<PeriodColumnCopy>(model, mc, ap);
}
