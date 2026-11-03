// COMPONENT: {"name": "segment_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 500]}}}
typedef int sv4 __attribute__((vector_size(16)));
static inline sv4 ssplat(int x) { sv4 v = {x, x, x, x}; return v; }
static inline sv4 sld(const int* p) { sv4 v; __builtin_memcpy(&v, p, sizeof(sv4)); return v; }
static inline void sst(int* p, sv4 v) { __builtin_memcpy(p, &v, sizeof(sv4)); }
static inline sv4 smax(sv4 a, sv4 b) { sv4 k = a > b; return (a & k) | (b & ~k); }
static inline long long shmax(sv4 a) {
    int b = a[0];
    for (int k = 1; k < 4; ++k) b = b > a[k] ? b : a[k];
    return (long long)b;
}

class SegmentReversal : public hsf::Neighborhood<Model> {
public:
    SegmentReversal(const Model& model, int maxl) : M(model), maxl(maxl) {
        const int m = std::max(1, M.m);
        f.assign(m, 0);
        W.assign((size_t)m * m, 0);
        useMat = (2 * maxl >= M.m);
        MP = ((m + 3) / 4) * 4;
        W32.assign((size_t)(m + 1) * MP, NEG32);
        Wb32.assign((size_t)(m + 1) * MP, NEG32);
        nonneg = true;
        rowsum.assign((size_t)std::max(1, M.n), 0);
        for (int j = 0; j < M.n; ++j) {
            long long sm = 0;
            for (int r = 0; r < M.m; ++r) {
                long long x = M.pt[(size_t)j * M.m + r];
                if (x < 0) nonneg = false;
                sm += x;
            }
            rowsum[j] = sm;
        }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int Ls = (int)s[0].size();
        if (Ls != tmplL) buildTemplate(Ls);
        out.insert(out.end(), tmpl.begin(), tmpl.end());
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        lastData = nullptr;
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        std::reverse(t[0].begin() + i, t[0].begin() + j + 1);
        return t;
    }

    double delta(const Sol& s, const Move& mv) override {
        if (s.empty() || M.m == 0) return M.objective(apply(s, mv)) - M.objective(s);
        {
            const auto& v0 = s[0];
            const int a0 = mv[0], b0 = mv[1];
            if (!(have && v0.data() == lastData && (int)v0.size() == L && a0 >= 0 && a0 < L && b0 >= 0 && b0 < L &&
                  v0[a0] == seq[a0] && v0[b0] == seq[b0]))
                sync(s);
        }
        const int m = M.m;
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i == j) return 0.0;
        long long nms;
        if (useMat) {
            if (i != rowI) { rowI = i; upto = i - 1; midEmpty = true; wDirty = true; }
            if (use32) {
                if (j > upto && j - upto <= 2) {
                    int* Wp = W32.data();
                    if (wDirty) { resetW(Wp); wDirty = false; }
                    while (upto < j - 1) { ++upto; const long long* pp = prow(seq[upto]); if (pp) prepend32(Wp, pp); }
                    const long long* p = prow(seq[j]);
                    upto = j;
                    nms = p ? prependEval32(Wp, p, i, j) : eval32(Wp, i, j);
                } else if (j == upto && !wDirty) {
                    nms = eval32(W32.data(), i, j);
                } else {
                    nms = randomAccess(i, j);
                }
            } else {
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
            }
        } else {
            nms = use32 ? randomAccess(i, j) : direct(i, j);
        }
        return ((double)nms + pv) - (ms0 + pv);
    }

private:
    static constexpr long long NEG = -(1LL << 60);
    static constexpr int NEG32 = -(1 << 30);
    static constexpr long long LIM32 = (1LL << 28);
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

    // 32-bit machinery
    bool nonneg = true, use32 = false, wDirty = true;
    std::vector<long long> rowsum;
    int MP = 4;
    std::vector<int> W32, Wb32, E32, Q32;
    const int* lastData = nullptr;
    // row cache (random access)
    int CW = 1;
    std::vector<long long> rcache;
    std::vector<uint32_t> rstamp, rdone;
    std::vector<int> rhits;
    uint32_t curStamp = 1;

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

    void resetW(int* Wp) const {
        const int m = M.m, mp = MP;
        std::fill(Wp, Wp + (size_t)(m + 1) * mp, NEG32);
        for (int r = 0; r < m; ++r) Wp[(size_t)r * mp + r] = 0;
    }

    void prepend32(int* Wp, const long long* p) const {
        const int m = M.m, mp = MP;
        for (int r = m - 1; r >= 0; --r) {
            int* row = Wp + (size_t)r * mp;
            const int* below = row + mp;
            const sv4 pr = ssplat((int)p[r]);
            for (int k = r & ~3; k < mp; k += 4) sst(row + k, smax(sld(row + k), sld(below + k)) + pr);
        }
    }

    long long prependEval32(int* Wp, const long long* p, int i, int j) const {
        const int m = M.m, mp = MP;
        const int* e = E32.data() + (size_t)i * mp;
        const int* q = Q32.data() + (size_t)(j + 1) * mp;
        sv4 acc = ssplat(0);
        for (int r = m - 1; r >= 0; --r) {
            int* row = Wp + (size_t)r * mp;
            const int* below = row + mp;
            const sv4 pr = ssplat((int)p[r]);
            sv4 best = ssplat(NEG32);
            for (int k = r & ~3; k < mp; k += 4) {
                sv4 nv = smax(sld(row + k), sld(below + k)) + pr;
                sst(row + k, nv);
                best = smax(best, nv + sld(q + k));
            }
            acc = smax(acc, best + ssplat(e[r]));
        }
        return shmax(acc);
    }

    long long eval32(const int* Wp, int i, int j) const {
        const int m = M.m, mp = MP;
        const int* e = E32.data() + (size_t)i * mp;
        const int* q = Q32.data() + (size_t)(j + 1) * mp;
        sv4 acc = ssplat(0);
        for (int r = m - 1; r >= 0; --r) {
            const int* row = Wp + (size_t)r * mp;
            sv4 best = ssplat(NEG32);
            for (int k = r & ~3; k < mp; k += 4) best = smax(best, sld(row + k) + sld(q + k));
            acc = smax(acc, best + ssplat(e[r]));
        }
        return shmax(acc);
    }

    void buildRow(int i) {
        int* Wp = Wb32.data();
        resetW(Wp);
        const long long* p0 = prow(seq[i]);
        if (p0) prepend32(Wp, p0);
        const int hi = std::min(L - 1, i + maxl - 1);
        long long* out = rcache.data() + (size_t)i * CW;
        for (int j = i + 1; j <= hi; ++j) {
            const long long* p = prow(seq[j]);
            out[j - i - 1] = p ? prependEval32(Wp, p, i, j) : eval32(Wp, i, j);
        }
        rdone[i] = curStamp;
    }

    long long randomAccess(int i, int j) {
        if (j > i + maxl - 1 || j - i - 1 >= CW) return direct(i, j);
        if (rstamp[i] != curStamp) { rstamp[i] = curStamp; rhits[i] = 0; }
        else if (rdone[i] == curStamp) return rcache[(size_t)i * CW + (j - i - 1)];
        if (++rhits[i] >= 3) {
            buildRow(i);
            return rcache[(size_t)i * CW + (j - i - 1)];
        }
        return direct(i, j);
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

    void upd32() {
        use32 = false;
        if (nonneg) {
            long long tot = 0;
            for (int k = 0; k < L; ++k) {
                int J = seq[k];
                if (J >= 0 && J < M.n) tot += rowsum[J];
            }
            use32 = (tot <= LIM32);
        }
        if (!use32) return;
        const int m = M.m, mp = MP;
        for (int k = 0; k <= L; ++k) {
            const long long* e = &E[(size_t)k * m];
            const long long* q = &Q[(size_t)k * m];
            int* e3 = &E32[(size_t)k * mp];
            int* q3 = &Q32[(size_t)k * mp];
            for (int r = 0; r < m; ++r) { e3[r] = (int)e[r]; q3[r] = (int)q[r]; }
        }
    }

    void resetState() {
        rowI = -1; upto = -1; midEmpty = true; wDirty = true;
        ++curStamp;
        if (curStamp == 0) {
            std::fill(rstamp.begin(), rstamp.end(), 0u);
            std::fill(rdone.begin(), rdone.end(), 0u);
            curStamp = 1;
        }
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
            resetState();
            recompute(a, b);
            upd32();
            pv = M.penalty * M.perm_violation(s);
            return;
        }
        seq = v;
        have = true;
        const int m = M.m;
        L = (int)seq.size();
        E.resize((size_t)(L + 1) * m);
        Q.resize((size_t)(L + 1) * m);
        plist.resize((size_t)L + 2);
        E32.assign((size_t)(L + 1) * MP, 0);
        Q32.assign((size_t)(L + 1) * MP, 0);
        CW = std::max(1, std::min(maxl - 1, L - 1));
        rcache.assign((size_t)std::max(1, L) * CW, 0);
        rstamp.assign((size_t)std::max(1, L), 0u);
        rdone.assign((size_t)std::max(1, L), 0u);
        rhits.assign((size_t)std::max(1, L), 0);
        resetState();
        for (int r = 0; r < m; ++r) { E[r] = 0; Q[(size_t)L * m + r] = 0; }
        recompute(0, L - 1);
        upd32();
        pv = M.penalty * M.perm_violation(s);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxl = (int)params.get("max_len", 60);
    if (maxl < 2) maxl = 2;
    return std::make_unique<SegmentReversal>(model, maxl);
}
