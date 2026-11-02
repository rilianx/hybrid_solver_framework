// COMPONENT: {"name": "taillard_job_insertion", "slot": "neighborhood", "params": {"max_dist": {"type": "int", "range": [2, 500]}}}
class TaillardInsertion : public hsf::Neighborhood<Model> {
public:
    TaillardInsertion(const Model& model, int maxd) : M(model), maxd(maxd) {
        zp.assign((size_t)std::max(1, M.m), 0);
        cur.assign((size_t)std::max(1, M.m), 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int Ls = (int)s[0].size();
        if (Ls != tmplL) buildTemplate(Ls);
        out.insert(out.end(), tmpl.begin(), tmpl.end());
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        auto& v = t[0];
        int i = mv[0], j = mv[1];
        lastData = nullptr;
        if (i < j) std::rotate(v.begin() + i, v.begin() + i + 1, v.begin() + j + 1);
        else if (j < i) std::rotate(v.begin() + j, v.begin() + i, v.begin() + i + 1);
        return t;
    }

    double delta(const Sol& s, const Move& mv) override {
        {
            const int i0 = mv[0], j0 = mv[1];
            if (i0 == remI && j0 >= rowLo && j0 <= rowHi && !s.empty()) {
                const auto& v0 = s[0];
                if (v0.data() == lastData && (int)v0.size() == L && v0[i0] == seq[i0] && v0[j0] == seq[j0])
                    return rowv[j0];
            }
        }
        if (s.empty() || M.m == 0) return M.objective(apply(s, mv)) - M.objective(s);
        sync(s);
        int i = mv[0], j = mv[1];
        if (i == remI && j >= rowLo && j <= rowHi) return rowv[j];
        if (i >= 0 && i < L && (i == lastI || j == firstJ(i))) {
            lastI = i;
            if (valid) buildFast(i); else build(i);
            if (j >= rowLo && j <= rowHi) return rowv[j];
            return direct(i, j);
        }
        lastI = i;
        return direct(i, j);
    }

    Move tabu_key(const Move& mv) override { return Move{mv[1], mv[0], 0, 0, 0, 0, 0}; }

private:
    const Model& M;
    int maxd;
    std::vector<int> seq;
    bool have = false;
    double ms0 = 0, pv = 0;
    int remI = -1, lastI = -1, L = 0, rowLo = 0, rowHi = -1;
    std::vector<long long> Eo, Qo, cur, zp;
    std::vector<long long> Ps;
    std::vector<const long long*> plist;
    bool valid = false;
    const int* lastData = nullptr;
    static constexpr long long NEG = -(1LL << 60);
    std::vector<double> rowv;
    std::vector<Move> tmpl;
    int tmplL = -1;

    void buildTemplate(int Ls) {
        tmpl.clear();
        size_t cnt = 0;
        for (int i = 0; i < Ls; ++i) {
            int lo = std::max(0, i - maxd), hi = std::min(Ls - 1, i + maxd);
            long long c = (long long)(hi - lo + 1) - 1;
            if (i - 1 >= lo) --c;
            if (c > 0) cnt += (size_t)c;
        }
        tmpl.reserve(cnt);
        for (int i = 0; i < Ls; ++i) {
            int lo = std::max(0, i - maxd), hi = std::min(Ls - 1, i + maxd);
            for (int j = lo; j <= hi; ++j) {
                if (j == i || j == i - 1) continue;
                tmpl.push_back(Move{i, j, 0, 0, 0, 0, 0});
            }
        }
        tmplL = Ls;
    }

    inline int firstJ(int i) const {
        int lo = std::max(0, i - maxd), hi = std::min(L - 1, i + maxd);
        int f = lo;
        while (f <= hi && (f == i || f == i - 1)) ++f;
        return f;
    }

    inline const long long* prow(int K) const {
        return (K >= 0 && K < M.n) ? &M.pt[(size_t)K * M.m] : nullptr;
    }

    inline void fwd(long long* c_, int J) const {
        if (J < 0 || J >= M.n) return;
        const int m = M.m;
        const long long* p = &M.pt[(size_t)J * m];
        long long c = c_[0] + p[0];
        c_[0] = c;
        for (int r = 1; r < m; ++r) { c = std::max(c_[r], c) + p[r]; c_[r] = c; }
    }
    inline void bwd(long long* c_, int J) const {
        if (J < 0 || J >= M.n) return;
        const int m = M.m;
        const long long* p = &M.pt[(size_t)J * m];
        long long b = 0;
        for (int r = m - 1; r >= 0; --r) { b = std::max(c_[r], b) + p[r]; c_[r] = b; }
    }

    void recompute(int a, int b) {
        const int m = M.m;
        for (int k = a; k <= b; ++k) {
            const long long* p = prow(seq[k]);
            long long* d = &Ps[(size_t)k * m];
            if (p) { for (int r = 0; r < m; ++r) d[r] = p[r]; }
            else { for (int r = 0; r < m; ++r) d[r] = 0; }
        }
        for (int k = a; k < L; ++k) {
            const long long* prev = &Eo[(size_t)k * m];
            long long* nx = &Eo[(size_t)(k + 1) * m];
            const long long* p = prow(seq[k]);
            if (!p) { for (int r = 0; r < m; ++r) nx[r] = prev[r]; continue; }
            long long c = prev[0] + p[0];
            nx[0] = c;
            for (int r = 1; r < m; ++r) { long long x = prev[r]; c = (x > c ? x : c) + p[r]; nx[r] = c; }
        }
        for (int k = b; k >= 0; --k) {
            const long long* nxt = &Qo[(size_t)(k + 1) * m];
            long long* cq = &Qo[(size_t)k * m];
            const long long* p = prow(seq[k]);
            if (!p) { for (int r = 0; r < m; ++r) cq[r] = nxt[r]; continue; }
            long long bb = 0;
            for (int r = m - 1; r >= 0; --r) { long long x = nxt[r]; bb = (x > bb ? x : bb) + p[r]; cq[r] = bb; }
        }
        ms0 = (double)Eo[(size_t)L * m + m - 1];
    }

    void sync(const Sol& s) {
        const auto& v = s[0];
        lastData = v.data();
        if (have && v.size() == seq.size()) {
            if (std::equal(v.begin(), v.end(), seq.begin())) return;
            const int n = (int)v.size();
            int a = (int)(std::mismatch(v.begin(), v.end(), seq.begin()).first - v.begin());
            int b = n - 1;
            while (b > a && v[b] == seq[b]) --b;
            std::copy(v.begin() + a, v.begin() + b + 1, seq.begin() + a);
            remI = -1;
            lastI = -1;
            recompute(a, b);
            {
                double viol = M.perm_violation(s);
                pv = M.penalty * viol;
                valid = (viol == 0.0);
            }
            return;
        }
        seq = v;
        have = true;
        remI = -1;
        lastI = -1;
        L = (int)seq.size();
        const int m = M.m;
        cur.resize(m);
        Eo.resize((size_t)(L + 1) * m);
        Qo.resize((size_t)(L + 1) * m);
        Ps.resize((size_t)std::max(1, L) * m);
        plist.resize((size_t)L + 2);
        for (int r = 0; r < m; ++r) { Eo[r] = 0; Qo[(size_t)L * m + r] = 0; }
        recompute(0, L - 1);
        {
            double viol = M.perm_violation(s);
            pv = M.penalty * viol;
            valid = (viol == 0.0);
        }
    }

    static inline void fwdp(long long* x, const long long* p, int m) {
        long long c = x[0] + p[0];
        x[0] = c;
        for (int r = 1; r < m; ++r) { long long a = x[r]; c = (a > c ? a : c) + p[r]; x[r] = c; }
    }

    double direct(int i, int j) {
        const int m = M.m;
        const long long** P = plist.data();
        int cp = 0;
        const long long* pJ = prow(seq[i]);
        const long long* x0;
        const long long* tail;
        if (j < i) {
            if (pJ) P[cp++] = pJ;
            for (int k = j; k < i; ++k) { const long long* p = prow(seq[k]); if (p) P[cp++] = p; }
            x0 = &Eo[(size_t)j * m];
            tail = &Qo[(size_t)(i + 1) * m];
        } else {
            for (int k = i + 1; k <= j; ++k) { const long long* p = prow(seq[k]); if (p) P[cp++] = p; }
            if (pJ) P[cp++] = pJ;
            x0 = &Eo[(size_t)i * m];
            tail = &Qo[(size_t)(j + 1) * m];
        }
        long long* x = cur.data();
        for (int r = 0; r < m; ++r) x[r] = x0[r];
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
        long long nms = 0;
        for (int r = 0; r < m; ++r) { long long y = x[r] + tail[r]; nms = nms > y ? nms : y; }
        return ((double)nms + pv) - (ms0 + pv);
    }

    // como build(i), solo con todos los jobs válidos; evalúa dos posiciones por pasada
    void buildFast(int i) {
        const int m = M.m;
        rowv.resize(L);
        const int lo = std::max(0, i - maxd), hi = std::min(L - 1, i + maxd);
        const double base = ms0 + pv;
        const long long* P = Ps.data();
        const long long* pJ = P + (size_t)i * m;
        long long* c = cur.data();
        double* rv = rowv.data();
        const long long* Ed = Eo.data();
        const long long* Qd = Qo.data();
        for (int r = 0; r < m; ++r) c[r] = Ed[(size_t)i * m + r];
        {
            const long long* q = Qd + (size_t)(i + 1) * m;
            long long x = c[0] + pJ[0];
            long long nms = x + q[0];
            if (nms < 0) nms = 0;
            for (int r = 1; r < m; ++r) {
                long long cr = c[r];
                x = (cr > x ? cr : x) + pJ[r];
                long long y = x + q[r];
                nms = nms > y ? nms : y;
            }
            rv[i] = ((double)nms + pv) - base;
        }
        int j = i + 1;
        for (; j + 1 <= hi; j += 2) {
            const long long* p1 = P + (size_t)j * m;
            const long long* p2 = p1 + m;
            const long long* q1 = Qd + (size_t)(j + 1) * m;
            const long long* q2 = q1 + m;
            long long a1 = c[0] + p1[0];
            long long x1 = a1 + pJ[0];
            long long n1 = x1 + q1[0];
            if (n1 < 0) n1 = 0;
            long long a2 = a1 + p2[0];
            long long x2 = a2 + pJ[0];
            long long n2 = x2 + q2[0];
            if (n2 < 0) n2 = 0;
            c[0] = a2;
            for (int r = 1; r < m; ++r) {
                const long long cr = c[r];
                const long long pj = pJ[r];
                a1 = (cr > a1 ? cr : a1) + p1[r];
                x1 = (a1 > x1 ? a1 : x1) + pj;
                long long y1 = x1 + q1[r];
                n1 = n1 > y1 ? n1 : y1;
                a2 = (a1 > a2 ? a1 : a2) + p2[r];
                x2 = (a2 > x2 ? a2 : x2) + pj;
                long long y2 = x2 + q2[r];
                n2 = n2 > y2 ? n2 : y2;
                c[r] = a2;
            }
            rv[j] = ((double)n1 + pv) - base;
            rv[j + 1] = ((double)n2 + pv) - base;
        }
        if (j <= hi) {
            const long long* ps = P + (size_t)j * m;
            const long long* q = Qd + (size_t)(j + 1) * m;
            long long a = c[0] + ps[0];
            c[0] = a;
            long long x = a + pJ[0];
            long long nms = x + q[0];
            if (nms < 0) nms = 0;
            for (int r = 1; r < m; ++r) {
                long long cr = c[r];
                a = (cr > a ? cr : a) + ps[r];
                c[r] = a;
                x = (a > x ? a : x) + pJ[r];
                long long y = x + q[r];
                nms = nms > y ? nms : y;
            }
            rv[j] = ((double)nms + pv) - base;
        }
        if (lo < i) {
            for (int r = 0; r < m; ++r) c[r] = Qd[(size_t)(i + 1) * m + r];
            int k = i - 1;
            for (; k - 1 >= lo; k -= 2) {
                const long long* p1 = P + (size_t)k * m;
                const long long* p2 = p1 - m;
                const long long* e1 = Ed + (size_t)k * m;
                const long long* e2 = e1 - m;
                const int R = m - 1;
                long long cr0 = c[R];
                long long b1 = (cr0 > 0 ? cr0 : 0) + p1[R];
                long long x1 = b1 + pJ[R];
                long long n1 = e1[R] + x1;
                if (n1 < 0) n1 = 0;
                long long b2 = (b1 > 0 ? b1 : 0) + p2[R];
                long long x2 = b2 + pJ[R];
                long long n2 = e2[R] + x2;
                if (n2 < 0) n2 = 0;
                c[R] = b2;
                for (int r = m - 2; r >= 0; --r) {
                    const long long cr = c[r];
                    const long long pj = pJ[r];
                    b1 = (cr > b1 ? cr : b1) + p1[r];
                    x1 = (b1 > x1 ? b1 : x1) + pj;
                    long long y1 = e1[r] + x1;
                    n1 = n1 > y1 ? n1 : y1;
                    b2 = (b1 > b2 ? b1 : b2) + p2[r];
                    x2 = (b2 > x2 ? b2 : x2) + pj;
                    long long y2 = e2[r] + x2;
                    n2 = n2 > y2 ? n2 : y2;
                    c[r] = b2;
                }
                rv[k] = ((double)n1 + pv) - base;
                rv[k - 1] = ((double)n2 + pv) - base;
            }
            if (k >= lo) {
                const long long* ps = P + (size_t)k * m;
                const long long* e = Ed + (size_t)k * m;
                const int R = m - 1;
                long long cr0 = c[R];
                long long b = (cr0 > 0 ? cr0 : 0) + ps[R];
                c[R] = b;
                long long x = b + pJ[R];
                long long nms = e[R] + x;
                if (nms < 0) nms = 0;
                for (int r = m - 2; r >= 0; --r) {
                    long long cr = c[r];
                    b = (cr > b ? cr : b) + ps[r];
                    c[r] = b;
                    x = (b > x ? b : x) + pJ[r];
                    long long y = e[r] + x;
                    nms = nms > y ? nms : y;
                }
                rv[k] = ((double)nms + pv) - base;
            }
        }
        rowLo = lo;
        rowHi = hi;
        remI = i;
    }

    void build(int i) {
        const int m = M.m;
        rowv.resize(L);
        const int lo = std::max(0, i - maxd), hi = std::min(L - 1, i + maxd);
        const double base = ms0 + pv;
        const long long* pJ = prow(seq[i]);
        long long* c = cur.data();
        double* rv = rowv.data();
        const long long* Ed = Eo.data();
        const long long* Qd = Qo.data();
        // j >= i
        for (int r = 0; r < m; ++r) c[r] = Ed[(size_t)i * m + r];
        for (int j = i; j <= hi; ++j) {
            const long long* q = Qd + (size_t)(j + 1) * m;
            const long long* ps = (j > i) ? prow(seq[j]) : nullptr;
            long long nms = 0;
            if (ps && pJ) {
                long long a = c[0] + ps[0];
                c[0] = a;
                long long x = a + pJ[0];
                nms = x + q[0];
                if (nms < 0) nms = 0;
                for (int r = 1; r < m; ++r) {
                    long long cr = c[r];
                    a = (cr > a ? cr : a) + ps[r];
                    c[r] = a;
                    x = (a > x ? a : x) + pJ[r];
                    long long y = x + q[r];
                    nms = nms > y ? nms : y;
                }
            } else {
                if (ps) fwd(c, seq[j]);
                if (pJ) {
                    long long x = c[0] + pJ[0];
                    nms = std::max(nms, x + q[0]);
                    for (int r = 1; r < m; ++r) {
                        long long cr = c[r];
                        x = (cr > x ? cr : x) + pJ[r];
                        long long y = x + q[r];
                        nms = nms > y ? nms : y;
                    }
                } else {
                    for (int r = 0; r < m; ++r) nms = std::max(nms, c[r] + q[r]);
                }
            }
            rv[j] = ((double)nms + pv) - base;
        }
        // j < i
        if (lo < i) {
            for (int r = 0; r < m; ++r) c[r] = Qd[(size_t)(i + 1) * m + r];
            for (int j = i - 1; j >= lo; --j) {
                const long long* e = Ed + (size_t)j * m;
                const long long* ps = prow(seq[j]);
                long long nms = 0;
                if (ps && pJ) {
                    long long b;
                    {
                        const int r = m - 1;
                        long long cr = c[r];
                        b = (cr > 0 ? cr : 0) + ps[r];
                        c[r] = b;
                    }
                    long long x = b + pJ[m - 1];
                    nms = e[m - 1] + x;
                    if (nms < 0) nms = 0;
                    for (int r = m - 2; r >= 0; --r) {
                        long long cr = c[r];
                        b = (cr > b ? cr : b) + ps[r];
                        c[r] = b;
                        x = (b > x ? b : x) + pJ[r];
                        long long y = e[r] + x;
                        nms = nms > y ? nms : y;
                    }
                } else {
                    if (ps) bwd(c, seq[j]);
                    if (pJ) {
                        long long x = c[m - 1] + pJ[m - 1];
                        nms = std::max(nms, e[m - 1] + x);
                        for (int r = m - 2; r >= 0; --r) {
                            long long cr = c[r];
                            x = (cr > x ? cr : x) + pJ[r];
                            long long y = e[r] + x;
                            nms = nms > y ? nms : y;
                        }
                    } else {
                        for (int r = 0; r < m; ++r) nms = std::max(nms, e[r] + c[r]);
                    }
                }
                rv[j] = ((double)nms + pv) - base;
            }
        }
        rowLo = lo;
        rowHi = hi;
        remI = i;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxd = (int)params.get("max_dist", 500);
    if (maxd < 1) maxd = 1;
    return std::make_unique<TaillardInsertion>(model, maxd);
}
