// COMPONENT: {"name": "segment_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
class SegmentReversal : public hsf::Neighborhood<Model> {
public:
    SegmentReversal(const Model& model, int maxl) : M(model), maxl(maxl) {
        const int m = std::max(1, M.m);
        f.assign(m, 0);
        W.assign((size_t)m * m, 0);
        useMat = (2 * maxl >= M.m);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int Ls = (int)s[0].size();
        if (Ls != tmplL) buildTemplate(Ls);
        out.insert(out.end(), tmpl.begin(), tmpl.end());
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
            const bool big = 2 * (j - i + 1) >= m;
            if (j > upto && j - upto <= 2) {
                while (upto < j - 1) { ++upto; prepend(prow(seq[upto])); }
                const long long* p = prow(seq[j]);
                upto = j;
                if (big && p && !midEmpty) nms = prependEval(p, i, j);
                else {
                    prepend(p);
                    nms = big ? viaMatrix(i, j) : direct(i, j);
                }
            } else if (j == upto && big) {
                nms = viaMatrix(i, j);
            } else {
                nms = direct(i, j);
            }
        } else {
            nms = direct(i, j);
        }
        return ((double)nms + pv) - (ms0 + pv);
    }

private:
    static constexpr long long NEG = -(1LL << 60);
    const Model& M;
    int maxl;
    bool useMat = false;
    std::vector<int> seq;
    bool have = false;
    int L = 0;
    double ms0 = 0, pv = 0;
    std::vector<long long> E, Q, f, W;
    std::vector<const long long*> plist;
    int rowI = -1, upto = -1;
    bool midEmpty = true;
    std::vector<Move> tmpl;
    int tmplL = -1;

    void buildTemplate(int Ls) {
        tmpl.clear();
        size_t cnt = 0;
        for (int i = 0; i < Ls; ++i) {
            int hi = std::min(Ls - 1, i + maxl - 1);
            if (hi > i) cnt += (size_t)(hi - i);
        }
        tmpl.reserve(cnt);
        for (int i = 0; i < Ls; ++i)
            for (int j = i + 1; j <= std::min(Ls - 1, i + maxl - 1); ++j)
                tmpl.push_back(Move{i, j, 0, 0, 0, 0, 0});
        tmplL = Ls;
    }

    inline const long long* prow(int J) const {
        return (J >= 0 && J < M.n) ? &M.pt[(size_t)J * M.m] : nullptr;
    }

    // antepone el job (p) al bloque (invertido) representado por W
    void prepend(const long long* p) {
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
            row[r] += pr;
            const long long* below = row + m;
            for (int t = r + 1; t < m; ++t) {
                long long a = below[t], b = row[t];
                row[t] = (a > b ? a : b) + pr;
            }
        }
    }

    // antepone (matriz no vacía, p válido) y evalúa en la misma pasada
    long long prependEval(const long long* p, int i, int j) {
        const int m = M.m;
        long long* Wd = W.data();
        const long long* e = &E[(size_t)i * m];
        const long long* q = &Q[(size_t)(j + 1) * m];
        long long nms = 0;
        for (int r = m - 1; r >= 0; --r) {
            long long* row = Wd + (size_t)r * m;
            const long long pr = p[r];
            long long d = row[r] + pr;
            row[r] = d;
            long long best = d + q[r];
            const long long* below = row + m;
            for (int t = r + 1; t < m; ++t) {
                long long a = below[t], b = row[t];
                long long nv = (a > b ? a : b) + pr;
                row[t] = nv;
                long long y = nv + q[t];
                best = best > y ? best : y;
            }
            long long y = e[r] + best;
            nms = nms > y ? nms : y;
        }
        return nms;
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

    static inline void fwdp(long long* x, const long long* p, int m) {
        long long c = x[0] + p[0];
        x[0] = c;
        for (int r = 1; r < m; ++r) { long long a = x[r]; c = (a > c ? a : c) + p[r]; x[r] = c; }
    }

    long long direct(int i, int j) {
        const int m = M.m;
        const long long** P = plist.data();
        int cp = 0;
        for (int k = j; k >= i; --k) { const long long* p = prow(seq[k]); if (p) P[cp++] = p; }
        long long* x = f.data();
        const long long* e = &E[(size_t)i * m];
        for (int r = 0; r < m; ++r) x[r] = e[r];
        int t = 0;
        for (; t + 4 <= cp; t += 4) {
            const long long* p1 = P[t];
            const long long* p2 = P[t + 1];
            const long long* p3 = P[t + 2];
            const long long* p4 = P[t + 3];
            long long c1 = NEG, c2 = NEG, c3 = NEG, c4 = NEG;
            for (int r = 0; r < m; ++r) {
                long long xr = x[r];
                c1 = (xr > c1 ? xr : c1) + p1[r];
                c2 = (c1 > c2 ? c1 : c2) + p2[r];
                c3 = (c2 > c3 ? c2 : c3) + p3[r];
                c4 = (c3 > c4 ? c3 : c4) + p4[r];
                x[r] = c4;
            }
        }
        for (; t < cp; ++t) fwdp(x, P[t], m);
        const long long* q = &Q[(size_t)(j + 1) * m];
        long long nms = 0;
        for (int r = 0; r < m; ++r) { long long y = x[r] + q[r]; nms = nms > y ? nms : y; }
        return nms;
    }

    void recompute(int a, int b) {
        const int m = M.m;
        for (int k = a; k < L; ++k) {
            const long long* prev = &E[(size_t)k * m];
            long long* cur = &E[(size_t)(k + 1) * m];
            const long long* p = prow(seq[k]);
            if (!p) { for (int r = 0; r < m; ++r) cur[r] = prev[r]; continue; }
            long long c = prev[0] + p[0];
            cur[0] = c;
            for (int r = 1; r < m; ++r) { long long x = prev[r]; c = (x > c ? x : c) + p[r]; cur[r] = c; }
        }
        for (int k = b; k >= 0; --k) {
            const long long* nxt = &Q[(size_t)(k + 1) * m];
            long long* cur = &Q[(size_t)k * m];
            const long long* p = prow(seq[k]);
            if (!p) { for (int r = 0; r < m; ++r) cur[r] = nxt[r]; continue; }
            long long bb = 0;
            for (int r = m - 1; r >= 0; --r) { long long x = nxt[r]; bb = (x > bb ? x : bb) + p[r]; cur[r] = bb; }
        }
        ms0 = (double)E[(size_t)L * m + m - 1];
    }

    void sync(const Sol& s) {
        const auto& v = s[0];
        if (have && v.size() == seq.size()) {
            if (std::equal(v.begin(), v.end(), seq.begin())) return;
            const int n = (int)v.size();
            int a = (int)(std::mismatch(v.begin(), v.end(), seq.begin()).first - v.begin());
            int b = n - 1;
            while (b > a && v[b] == seq[b]) --b;
            std::copy(v.begin() + a, v.begin() + b + 1, seq.begin() + a);
            rowI = -1; upto = -1; midEmpty = true;
            recompute(a, b);
            pv = M.penalty * M.perm_violation(s);
            return;
        }
        seq = v;
        have = true;
        rowI = -1; upto = -1; midEmpty = true;
        const int m = M.m;
        L = (int)seq.size();
        E.resize((size_t)(L + 1) * m);
        Q.resize((size_t)(L + 1) * m);
        plist.resize((size_t)L + 2);
        for (int r = 0; r < m; ++r) { E[r] = 0; Q[(size_t)L * m + r] = 0; }
        recompute(0, L - 1);
        pv = M.penalty * M.perm_violation(s);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxl = (int)params.get("max_len", 60);
    if (maxl < 2) maxl = 2;
    return std::make_unique<SegmentReversal>(model, maxl);
}
