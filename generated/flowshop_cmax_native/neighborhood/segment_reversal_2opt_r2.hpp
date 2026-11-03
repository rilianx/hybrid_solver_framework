// COMPONENT: {"name": "segment_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
class SegmentReversal : public hsf::Neighborhood<Model> {
public:
    SegmentReversal(const Model& model, int maxl) : M(model), maxl(maxl) {
        const int m = std::max(1, M.m);
        f.assign(m, 0);
        W.assign((size_t)m * m, 0);
        useMat = (maxl >= M.m);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        size_t cnt = 0;
        for (int i = 0; i < L; ++i) {
            int hi = std::min(L - 1, i + maxl - 1);
            if (hi > i) cnt += (size_t)(hi - i);
        }
        out.reserve(out.size() + cnt);
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
        long long nms;
        if (useMat) {
            if (i != rowI) { rowI = i; upto = i - 1; midEmpty = true; }
            if (j > upto && j - upto <= 2) {
                for (int k = upto + 1; k <= j; ++k) prepend(seq[k]);
                upto = j;
            }
            if (j == upto && 2 * (j - i + 1) >= m) nms = viaMatrix(i, j);
            else nms = direct(i, j);
        } else {
            nms = direct(i, j);
        }
        return ((double)nms + pv) - (ms0 + pv);
    }

private:
    const Model& M;
    int maxl;
    bool useMat = false;
    std::vector<int> seq;
    bool have = false;
    double ms0 = 0, pv = 0;
    std::vector<long long> E, Q, f, W;
    int rowI = -1, upto = -1;
    bool midEmpty = true;

    inline const long long* prow(int J) const {
        return (J >= 0 && J < M.n) ? &M.pt[(size_t)J * M.m] : nullptr;
    }

    // antepone el job J al bloque (invertido) representado por W
    void prepend(int J) {
        const long long* p = prow(J);
        if (!p) return;
        const int m = M.m;
        long long* Wd = W.data();
        if (midEmpty) {
            for (int r = 0; r < m; ++r) {
                long long* row = Wd + (size_t)r * m;
                long long acc = 0;
                for (int t = r; t < m; ++t) { acc += p[t]; row[t] = acc; }
            }
            midEmpty = false;
            return;
        }
        for (int r = m - 1; r >= 0; --r) {
            long long* row = Wd + (size_t)r * m;
            const long long pr = p[r];
            row[r] = row[r] + pr;
            if (r + 1 < m) {
                const long long* below = row + m;
                for (int t = r + 1; t < m; ++t) {
                    long long a = below[t], b = row[t];
                    row[t] = (a > b ? a : b) + pr;
                }
            }
        }
    }

    long long viaMatrix(int i, int j) const {
        const int m = M.m;
        const long long* e = &E[(size_t)i * m];
        const long long* q = &Q[(size_t)(j + 1) * m];
        long long nms = 0;
        if (midEmpty) {
            for (int r = 0; r < m; ++r) { long long y = e[r] + q[r]; nms = nms > y ? nms : y; }
            return nms;
        }
        const long long* Wd = W.data();
        for (int r = 0; r < m; ++r) {
            const long long* row = Wd + (size_t)r * m;
            long long best = row[r] + q[r];
            for (int t = r + 1; t < m; ++t) { long long y = row[t] + q[t]; best = best > y ? best : y; }
            long long y = e[r] + best;
            nms = nms > y ? nms : y;
        }
        return nms;
    }

    long long direct(int i, int j) {
        const int m = M.m;
        long long* x = f.data();
        const long long* e = &E[(size_t)i * m];
        for (int r = 0; r < m; ++r) x[r] = e[r];
        for (int k = j; k >= i; --k) {
            const long long* p = prow(seq[k]);
            if (!p) continue;
            long long c = x[0] + p[0];
            x[0] = c;
            for (int r = 1; r < m; ++r) { long long a = x[r]; c = (a > c ? a : c) + p[r]; x[r] = c; }
        }
        const long long* q = &Q[(size_t)(j + 1) * m];
        long long nms = 0;
        for (int r = 0; r < m; ++r) { long long y = x[r] + q[r]; nms = nms > y ? nms : y; }
        return nms;
    }

    void sync(const Sol& s) {
        const auto& v = s[0];
        if (have && v.size() == seq.size() && std::equal(v.begin(), v.end(), seq.begin())) return;
        seq = v;
        have = true;
        rowI = -1; upto = -1; midEmpty = true;
        const int m = M.m;
        int L = (int)seq.size();
        E.resize((size_t)(L + 1) * m);
        Q.resize((size_t)(L + 1) * m);
        for (int r = 0; r < m; ++r) { E[r] = 0; Q[(size_t)L * m + r] = 0; }
        for (int k = 0; k < L; ++k) {
            long long* prev = &E[(size_t)k * m];
            long long* cur = &E[(size_t)(k + 1) * m];
            const long long* p = prow(seq[k]);
            if (!p) { for (int r = 0; r < m; ++r) cur[r] = prev[r]; continue; }
            long long c = prev[0] + p[0];
            cur[0] = c;
            for (int r = 1; r < m; ++r) { long long a = prev[r]; c = (a > c ? a : c) + p[r]; cur[r] = c; }
        }
        for (int k = L - 1; k >= 0; --k) {
            long long* nxt = &Q[(size_t)(k + 1) * m];
            long long* cur = &Q[(size_t)k * m];
            const long long* p = prow(seq[k]);
            if (!p) { for (int r = 0; r < m; ++r) cur[r] = nxt[r]; continue; }
            long long b = 0;
            for (int r = m - 1; r >= 0; --r) { long long a = nxt[r]; b = (a > b ? a : b) + p[r]; cur[r] = b; }
        }
        ms0 = (double)E[(size_t)L * m + m - 1];
        pv = M.penalty * M.perm_violation(s);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxl = (int)params.get("max_len", 60);
    if (maxl < 2) maxl = 2;
    return std::make_unique<SegmentReversal>(model, maxl);
}
