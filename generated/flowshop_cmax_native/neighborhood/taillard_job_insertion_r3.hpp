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
        if (i < j) std::rotate(v.begin() + i, v.begin() + i + 1, v.begin() + j + 1);
        else if (j < i) std::rotate(v.begin() + j, v.begin() + i, v.begin() + i + 1);
        return t;
    }

    double delta(const Sol& s, const Move& mv) override {
        if (s.empty() || M.m == 0) return M.objective(apply(s, mv)) - M.objective(s);
        sync(s);
        int i = mv[0], j = mv[1];
        if (i == remI && j >= rowLo && j <= rowHi) return rowv[j];
        if (i >= 0 && i < L && (i == lastI || j == firstJ(i))) {
            lastI = i;
            build(i);
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
            pv = M.penalty * M.perm_violation(s);
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
        for (int r = 0; r < m; ++r) { Eo[r] = 0; Qo[(size_t)L * m + r] = 0; }
        recompute(0, L - 1);
        pv = M.penalty * M.perm_violation(s);
    }

    double direct(int i, int j) {
        const int m = M.m;
        long long* c = cur.data();
        int J = seq[i];
        const long long* tail;
        if (j < i) {
            std::copy(Eo.begin() + (size_t)j * m, Eo.begin() + (size_t)(j + 1) * m, cur.begin());
            fwd(c, J);
            for (int k = j; k < i; ++k) fwd(c, seq[k]);
            tail = &Qo[(size_t)(i + 1) * m];
        } else {
            std::copy(Eo.begin() + (size_t)i * m, Eo.begin() + (size_t)(i + 1) * m, cur.begin());
            for (int k = i + 1; k <= j; ++k) fwd(c, seq[k]);
            fwd(c, J);
            tail = &Qo[(size_t)(j + 1) * m];
        }
        long long nms = 0;
        for (int r = 0; r < m; ++r) nms = std::max(nms, c[r] + tail[r]);
        return ((double)nms + pv) - (ms0 + pv);
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
