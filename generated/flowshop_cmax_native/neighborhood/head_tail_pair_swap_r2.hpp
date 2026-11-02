// COMPONENT: {"name": "head_tail_pair_swap", "slot": "neighborhood", "params": {"max_dist": {"type": "int", "range": [1, 500]}}}
class HeadTailSwap : public hsf::Neighborhood<Model> {
public:
    HeadTailSwap(const Model& model, int maxd) : M(model), maxd(maxd) {
        const int m = std::max(1, M.m);
        f.assign(m, 0);
        av.assign(m, 0);
        cv.assign(m, 0);
        Mat.assign((size_t)m * m, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        size_t cnt = 0;
        for (int i = 0; i < L; ++i) {
            int hi = std::min(L - 1, i + maxd);
            if (hi > i) cnt += (size_t)(hi - i);
        }
        out.reserve(out.size() + cnt);
        for (int i = 0; i < L; ++i)
            for (int j = i + 1; j <= std::min(L - 1, i + maxd); ++j)
                out.push_back(Move{i, j, 0, 0, 0, 0, 0});
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        std::swap(t[0][mv[0]], t[0][mv[1]]);
        return t;
    }

    double delta(const Sol& s, const Move& mv) override {
        if (s.empty() || M.m == 0) return M.objective(apply(s, mv)) - M.objective(s);
        sync(s);
        const int m = M.m;
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i == j) return 0.0;
        const int span = j - i - 1;
        bool useRow = false;
        if (i == rowI && j - 1 >= Mupto && j - 1 <= Mupto + 1) {
            if (j - 1 == Mupto + 1) { append(seq[j - 1]); Mupto = j - 1; }
            useRow = true;
        } else if (span == 0) {
            rowI = i; Mupto = i; midEmpty = true; useRow = true;
        }
        long long nms;
        if (useRow && (midEmpty || 2 * span >= m)) nms = viaMatrix(i, j);
        else nms = direct(i, j);
        return ((double)nms + pv) - (ms0 + pv);
    }

private:
    static constexpr long long NEG = -(1LL << 60);
    const Model& M;
    int maxd;
    std::vector<int> seq;
    bool have = false;
    double ms0 = 0, pv = 0;
    std::vector<long long> E, Q, f, av, cv, Mat;
    int rowI = -1, Mupto = -1;
    bool midEmpty = true;

    inline const long long* prow(int J) const {
        return (J >= 0 && J < M.n) ? &M.pt[(size_t)J * M.m] : nullptr;
    }

    static inline void fwdp(long long* x, const long long* p, int m) {
        long long c = x[0] + p[0];
        x[0] = c;
        for (int r = 1; r < m; ++r) { long long a = x[r]; c = (a > c ? a : c) + p[r]; x[r] = c; }
    }

    void append(int J) {
        const long long* p = prow(J);
        if (!p) return;
        const int m = M.m;
        long long* W = Mat.data();
        if (midEmpty) {
            for (int r = 0; r < m; ++r) {
                long long* row = W + (size_t)r * m;
                long long acc = 0;
                for (int s = r; s < m; ++s) { acc += p[s]; row[s] = acc; }
            }
            midEmpty = false;
        } else {
            for (int r = 0; r < m; ++r) {
                long long* row = W + (size_t)r * m;
                long long v = row[r] + p[r];
                row[r] = v;
                for (int s = r + 1; s < m; ++s) {
                    long long o = row[s];
                    v = (o > v ? o : v) + p[s];
                    row[s] = v;
                }
            }
        }
    }

    long long viaMatrix(int i, int j) {
        const int m = M.m;
        long long* a = av.data();
        const long long* e = &E[(size_t)i * m];
        for (int r = 0; r < m; ++r) a[r] = e[r];
        const long long* pJ = prow(seq[j]);
        if (pJ) fwdp(a, pJ, m);
        const long long* c;
        if (midEmpty) {
            c = a;
        } else {
            long long* cc = cv.data();
            for (int s = 0; s < m; ++s) cc[s] = NEG;
            const long long* W = Mat.data();
            for (int r = 0; r < m; ++r) {
                const long long ar = a[r];
                const long long* row = W + (size_t)r * m;
                for (int s = r; s < m; ++s) {
                    long long y = ar + row[s];
                    cc[s] = cc[s] > y ? cc[s] : y;
                }
            }
            c = cc;
        }
        const long long* q = &Q[(size_t)(j + 1) * m];
        const long long* pI = prow(seq[i]);
        long long nms = 0;
        if (pI) {
            long long b = 0;
            for (int r = m - 1; r >= 0; --r) {
                long long qr = q[r];
                b = (qr > b ? qr : b) + pI[r];
                long long y = c[r] + b;
                nms = nms > y ? nms : y;
            }
        } else {
            for (int r = 0; r < m; ++r) { long long y = c[r] + q[r]; nms = nms > y ? nms : y; }
        }
        return nms;
    }

    long long direct(int i, int j) {
        const int m = M.m;
        long long* x = f.data();
        const long long* e = &E[(size_t)i * m];
        for (int r = 0; r < m; ++r) x[r] = e[r];
        const long long* p = prow(seq[j]);
        if (p) fwdp(x, p, m);
        for (int k = i + 1; k < j; ++k) { p = prow(seq[k]); if (p) fwdp(x, p, m); }
        p = prow(seq[i]);
        if (p) fwdp(x, p, m);
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
        rowI = -1; Mupto = -1; midEmpty = true;
        const int m = M.m;
        int L = (int)seq.size();
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
        ms0 = (double)E[(size_t)L * m + m - 1];
        pv = M.penalty * M.perm_violation(s);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxd = (int)params.get("max_dist", 500);
    if (maxd < 1) maxd = 1;
    return std::make_unique<HeadTailSwap>(model, maxd);
}
