// COMPONENT: {"name": "segment_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
class SegmentReversal : public hsf::Neighborhood<Model> {
public:
    SegmentReversal(const Model& model, int maxl) : M(model), maxl(maxl) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        for (int i = 0; i < L; ++i)
            for (int j = i + 1; j <= std::min(L - 1, i + maxl - 1); ++j)
                out.push_back(Move{i, j, 0, 0, 0, 0, 0});
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        std::reverse(t[0].begin() + i, t[0].begin() + j + 1);
        return t;
    }

    double delta(const Sol& s, const Move& mv) override {
        if (s.empty() || M.m == 0) return M.objective(apply(s, mv)) - M.objective(s);
        sync(s);
        const int m = M.m;
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i == j) return 0.0;
        for (int r = 0; r < m; ++r) f[r] = E[(size_t)i * m + r];
        for (int k = j; k >= i; --k) push(seq[k]);
        long long nms = 0;
        for (int r = 0; r < m; ++r) nms = std::max(nms, f[r] + Q[(size_t)(j + 1) * m + r]);
        return ((double)nms + pv) - (ms0 + pv);
    }

private:
    const Model& M;
    int maxl;
    std::vector<int> seq;
    bool have = false;
    double ms0 = 0, pv = 0;
    std::vector<long long> E, Q, f;

    inline void push(int J) {
        if (J < 0 || J >= M.n) return;
        const int m = M.m;
        const long long* p = &M.pt[(size_t)J * m];
        long long c = f[0] + p[0];
        f[0] = c;
        for (int r = 1; r < m; ++r) { c = std::max(f[r], c) + p[r]; f[r] = c; }
    }

    void sync(const Sol& s) {
        if (have && s[0] == seq) return;
        seq = s[0];
        have = true;
        const int m = M.m;
        int L = (int)seq.size();
        f.assign(m, 0);
        E.assign((size_t)(L + 1) * m, 0);
        Q.assign((size_t)(L + 1) * m, 0);
        for (int k = 0; k < L; ++k) {
            long long* prev = &E[(size_t)k * m];
            long long* cur = &E[(size_t)(k + 1) * m];
            int J = seq[k];
            if (J < 0 || J >= M.n) { for (int r = 0; r < m; ++r) cur[r] = prev[r]; continue; }
            const long long* p = &M.pt[(size_t)J * m];
            long long c = prev[0] + p[0];
            cur[0] = c;
            for (int r = 1; r < m; ++r) { c = std::max(prev[r], c) + p[r]; cur[r] = c; }
        }
        for (int k = L - 1; k >= 0; --k) {
            long long* nxt = &Q[(size_t)(k + 1) * m];
            long long* cur = &Q[(size_t)k * m];
            int J = seq[k];
            if (J < 0 || J >= M.n) { for (int r = 0; r < m; ++r) cur[r] = nxt[r]; continue; }
            const long long* p = &M.pt[(size_t)J * m];
            long long b = 0;
            for (int r = m - 1; r >= 0; --r) { b = std::max(nxt[r], b) + p[r]; cur[r] = b; }
        }
        ms0 = M.makespan(s);
        pv = M.penalty * M.perm_violation(s);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxl = (int)params.get("max_len", 60);
    if (maxl < 2) maxl = 2;
    return std::make_unique<SegmentReversal>(model, maxl);
}
