// COMPONENT: {"name": "head_tail_pair_swap", "slot": "neighborhood", "params": {"max_dist": {"type": "int", "range": [1, 500]}}}
class HeadTailSwap : public hsf::Neighborhood<Model> {
public:
    HeadTailSwap(const Model& model, int maxd) : M(model), maxd(maxd) {
        const int m = std::max(1, M.m);
        f.assign(m, 0);
        av.assign(m, 0);
        bv.assign(m, 0);
        Wt.assign((size_t)m * m, 0);
        T = std::max(1, M.m);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int Ls = (int)s[0].size();
        if (Ls != tmplL) buildTemplate(Ls);
        out.insert(out.end(), tmpl.begin(), tmpl.end());
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        std::swap(t[0][mv[0]], t[0][mv[1]]);
        return t;
    }

    double delta(const Sol& s, const Move& mv) override {
        if (s.empty() || M.m == 0) return M.objective(apply(s, mv)) - M.objective(s);
        sync(s);
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i == j) return 0.0;
        const int span = j - i - 1;
        long long nms;
        if (span == 0) {
            rowI = i; upto = i; matEmpty = true; lastJ = j;
            nms = direct(i, j);
        } else if (i == rowI && (j == lastJ + 1 || j == lastJ)) {
            lastJ = j;
            if (span >= T) {
                while (upto < j - 2) { ++upto; append(prow(seq[upto])); }
                prepAB(i, j);
                if (upto == j - 2) {
                    const long long* p = prow(seq[j - 1]);
                    upto = j - 1;
                    if (p && !matEmpty) nms = appendEval(p);
                    else { append(p); nms = evalOnly(); }
                } else {
                    nms = evalOnly();
                }
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
    int maxd;
    int T = 1;
    std::vector<int> seq;
    bool have = false;
    int L = 0;
    double ms0 = 0, pv = 0;
    std::vector<long long> E, Q, f, av, bv, Wt;
    std::vector<const long long*> plist;
    int rowI = -1, upto = -1, lastJ = -1;
    bool matEmpty = true;
    std::vector<Move> tmpl;
    int tmplL = -1;

    void buildTemplate(int Ls) {
        tmpl.clear();
        size_t cnt = 0;
        for (int i = 0; i < Ls; ++i) {
            int hi = std::min(Ls - 1, i + maxd);
            if (hi > i) cnt += (size_t)(hi - i);
        }
        tmpl.reserve(cnt);
        for (int i = 0; i < Ls; ++i)
            for (int j = i + 1; j <= std::min(Ls - 1, i + maxd); ++j)
                tmpl.push_back(Move{i, j, 0, 0, 0, 0, 0});
        tmplL = Ls;
    }

    inline const long long* prow(int J) const {
        return (J >= 0 && J < M.n) ? &M.pt[(size_t)J * M.m] : nullptr;
    }

    static inline void fwdp(long long* x, const long long* p, int m) {
        long long c = x[0] + p[0];
        x[0] = c;
        for (int r = 1; r < m; ++r) { long long a = x[r]; c = (a > c ? a : c) + p[r]; x[r] = c; }
    }

    // Wt[s*m + r] = longest path in the middle block from machine r (first job) to machine s (last job), r <= s
    void append(const long long* p) {
        if (!p) return;
        const int m = M.m;
        long long* W = Wt.data();
        if (matEmpty) {
            for (int s = 0; s < m; ++s) {
                long long* cur = W + (size_t)s * m;
                const long long ps = p[s];
                if (s > 0) {
                    const long long* prev = cur - m;
                    for (int r = 0; r < s; ++r) cur[r] = prev[r] + ps;
                }
                cur[s] = ps;
            }
            matEmpty = false;
            return;
        }
        for (int s = 0; s < m; ++s) {
            long long* cur = W + (size_t)s * m;
            const long long ps = p[s];
            if (s > 0) {
                const long long* prev = cur - m;
                for (int r = 0; r < s; ++r) {
                    long long o = cur[r], v = prev[r];
                    cur[r] = (o > v ? o : v) + ps;
                }
            }
            cur[s] += ps;
        }
    }

    void prepAB(int i, int j) {
        const int m = M.m;
        long long* a = av.data();
        const long long* e = &E[(size_t)i * m];
        for (int r = 0; r < m; ++r) a[r] = e[r];
        const long long* pJ = prow(seq[j]);
        if (pJ) fwdp(a, pJ, m);
        const long long* q = &Q[(size_t)(j + 1) * m];
        const long long* pI = prow(seq[i]);
        long long* b = bv.data();
        if (pI) {
            long long bb = 0;
            for (int r = m - 1; r >= 0; --r) {
                long long qr = q[r];
                bb = (qr > bb ? qr : bb) + pI[r];
                b[r] = bb;
            }
        } else {
            for (int r = 0; r < m; ++r) b[r] = q[r];
        }
    }

    long long evalOnly() const {
        const int m = M.m;
        const long long* a = av.data();
        const long long* b = bv.data();
        long long nms = 0;
        if (matEmpty) {
            for (int r = 0; r < m; ++r) { long long y = a[r] + b[r]; nms = nms > y ? nms : y; }
            return nms;
        }
        const long long* W = Wt.data();
        for (int s = 0; s < m; ++s) {
            const long long* row = W + (size_t)s * m;
            long long best = a[s] + row[s];
            for (int r = 0; r < s; ++r) { long long y = a[r] + row[r]; best = best > y ? best : y; }
            long long y = best + b[s];
            nms = nms > y ? nms : y;
        }
        return nms;
    }

    // appends job p (matrix not empty) and evaluates in the same pass
    long long appendEval(const long long* p) {
        const int m = M.m;
        const long long* a = av.data();
        const long long* b = bv.data();
        long long* W = Wt.data();
        long long nms = 0;
        for (int s = 0; s < m; ++s) {
            long long* cur = W + (size_t)s * m;
            const long long ps = p[s];
            long long d = cur[s] + ps;
            cur[s] = d;
            long long best = a[s] + d;
            if (s > 0) {
                const long long* prev = cur - m;
                for (int r = 0; r < s; ++r) {
                    long long o = cur[r], v = prev[r];
                    long long nv = (o > v ? o : v) + ps;
                    cur[r] = nv;
                    long long y = a[r] + nv;
                    best = best > y ? best : y;
                }
            }
            long long y = best + b[s];
            nms = nms > y ? nms : y;
        }
        return nms;
    }

    long long direct(int i, int j) {
        const int m = M.m;
        const long long** P = plist.data();
        int cp = 0;
        {
            const long long* p = prow(seq[j]);
            if (p) P[cp++] = p;
            for (int k = i + 1; k < j; ++k) { p = prow(seq[k]); if (p) P[cp++] = p; }
            p = prow(seq[i]);
            if (p) P[cp++] = p;
        }
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

    void resetRow() { rowI = -1; upto = -1; lastJ = -1; matEmpty = true; }

    void sync(const Sol& s) {
        const auto& v = s[0];
        if (have && v.size() == seq.size()) {
            if (std::equal(v.begin(), v.end(), seq.begin())) return;
            const int n = (int)v.size();
            int a = (int)(std::mismatch(v.begin(), v.end(), seq.begin()).first - v.begin());
            int b = n - 1;
            while (b > a && v[b] == seq[b]) --b;
            std::copy(v.begin() + a, v.begin() + b + 1, seq.begin() + a);
            resetRow();
            recompute(a, b);
            pv = M.penalty * M.perm_violation(s);
            return;
        }
        seq = v;
        have = true;
        resetRow();
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
    int maxd = (int)params.get("max_dist", 500);
    if (maxd < 1) maxd = 1;
    return std::make_unique<HeadTailSwap>(model, maxd);
}
