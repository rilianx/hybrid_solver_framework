// COMPONENT: {"name": "route_dissolve_reinsert", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_len": {"type": "int", "range": [1, 50]}}}
class RouteDissolveReinsert : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K, maxLen;
    std::vector<int> nb, rof, pof;
    const double* Dm = nullptr;
    size_t n1 = 1;
    // memoria de trabajo
    std::vector<std::vector<int>> wk;
    std::vector<std::vector<double>> wE;
    std::vector<double> wload, wCost;
    std::vector<char> wValid;
    std::vector<int> slotOf, touched, stamp, order, extra, cands;
    int curStamp = 0;
    // caché por solución
    std::vector<int> flat, cOff;
    std::vector<double> cLoad, cCost, dCache, flatE;
    std::vector<char> dHas, cValid;
    // buffers para la caché que deja apply
    std::vector<int> flatB, cOffB;
    std::vector<double> cLoadB, cCostB, flatEB;
    std::vector<char> cValidB;
    int nC = 0;
    bool haveCache = false;
    int simR = -1;
    double d00 = 0.0;
    double slack = 2.0;
    inline void scanRoute(int idx, int SZ, int c, double dc, const double* rowc, double d0,
                          double thr, double& best, int& bi, int& bp) const {
        int sl = slotOf[idx];
        const int* Rp; int L; const double* E; bool ok; double ld;
        if (sl >= 0) {
            Rp = wk[sl].data(); L = (int)wk[sl].size(); ok = wValid[sl];
            E = wE[sl].data(); ld = wload[sl];
        } else if (idx < SZ) {
            int o = cOff[idx];
            Rp = flat.data() + o; L = cOff[idx + 1] - o; ok = cValid[idx];
            E = flatE.data() + o + idx; ld = cLoad[idx];
        } else {
            Rp = nullptr; L = 0; ok = true; E = &d00; ld = 0.0;
        }
        double pinc = pen(ld + dc) - pen(ld);
        if (pinc - slack > thr + 1e-9 * (std::fabs(pinc) + std::fabs(thr) + 1.0)) return;
        if (ok) {
            double prev = d0;
            if (rowc) {
                for (int k = 0; k < L; ++k) {
                    double cur = rowc[Rp[k]];
                    double cst = prev + cur - E[k] + pinc;
                    if (cst < best) { best = cst; bi = idx; bp = k; }
                    prev = cur;
                }
            } else {
                for (int k = 0; k < L; ++k) {
                    double cur = M.rawDist(c, Rp[k]);
                    double cst = prev + cur - E[k] + pinc;
                    if (cst < best) { best = cst; bi = idx; bp = k; }
                    prev = cur;
                }
            }
            double cst = prev + d0 - E[L] + pinc;
            if (cst < best) { best = cst; bi = idx; bp = L; }
        } else {
            for (int k = 0; k <= L; ++k) {
                int a = 0, b = 0;
                if (k > 0) { a = Rp[k - 1]; if (!valid(a)) continue; }
                if (k < L) { b = Rp[k]; if (!valid(b)) continue; }
                double cst = dst(a, c) + dst(c, b) - dst(a, b) + pinc;
                if (cst < best) { best = cst; bi = idx; bp = k; }
            }
        }
    }
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    inline double pen(double ld) const { return ld > M.capacity + 1e-9 ? M.penalty * (ld - M.capacity) : 0.0; }
    double loadOf(const std::vector<int>& R) const {
        double ld = 0.0;
        for (int c : R) if (valid(c)) ld += M.demand[c];
        return ld;
    }
    double routeCost(const std::vector<int>& R) const {
        double d = 0.0, ld = 0.0; int prev = 0; bool any = false;
        for (int c : R) {
            if (!valid(c)) continue;
            d += dst(prev, c); ld += M.demand[c]; prev = c; any = true;
        }
        if (any) d += dst(prev, 0);
        return d + pen(ld);
    }
    void buildEdges(const int* R, int L, double* E) const {
        int prev = 0;
        for (int k = 0; k < L; ++k) { E[k] = dst(prev, R[k]); prev = R[k]; }
        E[L] = dst(prev, 0);
    }
    inline double edgeCost(const double* E, int L, double ld) const {
        if (L == 0) return 0.0 + pen(ld);
        double d = 0.0;
        for (int k = 0; k <= L; ++k) d += E[k];
        return d + pen(ld);
    }
    bool sameSol(const S& s) const {
        if (!haveCache || (int)s.size() != nC) return false;
        for (int r = 0; r < nC; ++r) {
            if (cOff[r + 1] - cOff[r] != (int)s[r].size()) return false;
        }
        for (int r = 0; r < nC; ++r) {
            const auto& R = s[r];
            if (!R.empty() && !std::equal(R.begin(), R.end(), flat.begin() + cOff[r])) return false;
        }
        return true;
    }
    void prepare(const S& s) {
        if (sameSol(s)) return;
        std::fill(rof.begin(), rof.end(), -1);
        int SZ = (int)s.size();
        const double* dem = M.demand.data();
        const int n = M.n;
        cOff.resize(SZ + 1);
        cLoad.resize(SZ);
        cCost.resize(SZ);
        cValid.resize(SZ);
        dCache.resize(SZ);
        dHas.assign(SZ, 0);
        flat.clear();
        flatE.clear();
        for (int r = 0; r < SZ; ++r) {
            const auto& R = s[r];
            int L = (int)R.size();
            cOff[r] = (int)flat.size();
            flat.insert(flat.end(), R.begin(), R.end());
            double ld = 0.0; bool ok = true;
            for (int p = 0; p < L; ++p) {
                int c = R[p];
                if (c >= 1 && c <= n) {
                    ld += dem[c];
                    if (rof[c] < 0) { rof[c] = r; pof[c] = p; }
                } else ok = false;
            }
            cLoad[r] = ld;
            cValid[r] = ok;
            size_t eo = flatE.size();
            flatE.resize(eo + L + 1, 0.0);
            if (ok) {
                buildEdges(R.data(), L, flatE.data() + eo);
                cCost[r] = edgeCost(flatE.data() + eo, L, ld);
            } else {
                cCost[r] = routeCost(R);
            }
        }
        cOff[SZ] = (int)flat.size();
        nC = SZ;
        haveCache = true;
        simR = -1;
    }
    int openSlot(int idx) {
        if (slotOf[idx] >= 0) return slotOf[idx];
        int sl = (int)touched.size();
        touched.push_back(idx);
        if ((int)wk.size() <= sl) {
            wk.emplace_back(); wE.emplace_back();
            wload.push_back(0.0); wCost.push_back(0.0); wValid.push_back(1);
        }
        if (idx < nC) {
            int o = cOff[idx], L = cOff[idx + 1] - o;
            wk[sl].assign(flat.begin() + o, flat.begin() + o + L);
            wload[sl] = cLoad[idx];
            wValid[sl] = cValid[idx];
            if (cValid[idx]) wE[sl].assign(flatE.begin() + (o + idx), flatE.begin() + (o + idx + L + 1));
        } else {
            wk[sl].clear(); wload[sl] = 0.0; wValid[sl] = 1;
            wE[sl].assign(1, d00);
        }
        slotOf[idx] = sl;
        return sl;
    }
    double simulate(const S& s, int r) {
        (void)s;
        int SZ = nC;
        for (int idx : touched) slotOf[idx] = -1;
        touched.clear();
        if ((int)slotOf.size() < SZ + 1) slotOf.resize(SZ + 1, -1);
        if ((int)stamp.size() < SZ + 1) stamp.assign(SZ + 1, 0);
        order.clear(); extra.clear();
        {
            int o = cOff[r], e = cOff[r + 1];
            for (int i = o; i < e; ++i) { int c = flat[i]; if (valid(c)) order.push_back(c); else extra.push_back(c); }
        }
        const double* dem = M.demand.data();
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            if (dem[a] != dem[b]) return dem[a] > dem[b];
            return a < b;
        });
        const int* RO = rof.data();
        for (int c : order) {
            double dc = dem[c];
            ++curStamp;
            cands.clear();
            const int* nc = nb.data() + (size_t)c * K;
            for (int t = 0; t < K; ++t) {
                int ro = RO[nc[t]];
                if (ro < 0 || ro == r) continue;
                if (stamp[ro] != curStamp) { stamp[ro] = curStamp; cands.push_back(ro); }
            }
            const double* rowc = Dm ? Dm + (size_t)c * n1 : nullptr;
            double d0 = rowc ? rowc[0] : M.rawDist(c, 0);
            const double INF = std::numeric_limits<double>::infinity();
            double bSZ = INF; int biS = SZ, pSZ = 0;
            scanRoute(SZ, SZ, c, dc, rowc, d0, INF, bSZ, biS, pSZ);
            double best = INF;
            int bi = SZ, bp = 0;
            for (int idx : cands) {
                double thr = std::min(best, bSZ);
                scanRoute(idx, SZ, c, dc, rowc, d0, thr, best, bi, bp);
            }
            if (bSZ < best) { best = bSZ; bi = SZ; bp = pSZ; }
            int sl = openSlot(bi);
            auto& W = wk[sl];
            if (wValid[sl]) {
                auto& E = wE[sl];
                int Lw = (int)W.size();
                int a = bp > 0 ? W[bp - 1] : 0;
                int b = bp < Lw ? W[bp] : 0;
                E[bp] = dst(a, c);
                E.insert(E.begin() + bp + 1, dst(c, b));
            }
            W.insert(W.begin() + bp, c);
            wload[sl] += dc;
        }
        if (!extra.empty()) {
            int sl = openSlot(SZ);
            wk[sl].insert(wk[sl].end(), extra.begin(), extra.end());
            wValid[sl] = 0;
        }
        double d = -cCost[r];
        for (int i = 0; i < (int)touched.size(); ++i) {
            int idx = touched[i];
            const auto& W = wk[i];
            double cst;
            if (wValid[i]) cst = edgeCost(wE[i].data(), (int)W.size(), loadOf(W));
            else cst = routeCost(W);
            wCost[i] = cst;
            d += cst;
            if (idx < SZ) d -= cCost[idx];
        }
        simR = r;
        return d;
    }
public:
    RouteDissolveReinsert(const Model& m, int k, int ml) : M(m), maxLen(std::max(1, ml)) {
        int n = M.n;
        n1 = (size_t)n + 1;
        Dm = M.useMatrix ? M.D.data() : nullptr;
        d00 = dst(0, 0);
        if (M.rounded) slack = 2.0;
        else {
            double mnx = 0, mxx = 0, mny = 0, mxy = 0;
            for (int i = 0; i <= n; ++i) {
                if (i == 0 || M.xs[i] < mnx) mnx = M.xs[i];
                if (i == 0 || M.xs[i] > mxx) mxx = M.xs[i];
                if (i == 0 || M.ys[i] < mny) mny = M.ys[i];
                if (i == 0 || M.ys[i] > mxy) mxy = M.ys[i];
            }
            double span = std::hypot(mxx - mnx, mxy - mny);
            slack = 1e-7 * (1.0 + 3.0 * span);
        }
        K = std::max(0, std::min(k, n - 1));
        nb.assign((size_t)(n + 1) * std::max(K, 1), 0);
        std::vector<int> cand;
        for (int c = 1; c <= n && K > 0; ++c) {
            cand.clear();
            for (int v = 1; v <= n; ++v) if (v != c) cand.push_back(v);
            std::partial_sort(cand.begin(), cand.begin() + K, cand.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            for (int t = 0; t < K; ++t) nb[(size_t)c * K + t] = cand[t];
        }
        rof.assign(n + 1, -1); pof.assign(n + 1, -1);
    }
    void moves(const S& s, std::vector<hsf::Move>& out) override {
        int SZ = (int)s.size();
        if (SZ >= 2) {
            for (int r = 0; r < SZ; ++r) {
                int len = (int)s[r].size();
                if (len >= 1 && len <= maxLen) out.push_back({r, s[r][0], 0, 0, 0, 0, 0});
            }
        }
        if (out.empty() && SZ >= 1) {
            int best = 0;
            for (int r = 1; r < SZ; ++r)
                if (!s[r].empty() && (s[best].empty() || s[r].size() < s[best].size())) best = r;
            out.push_back({best, s[best].empty() ? 0 : s[best][0], 0, 0, 0, 0, 0});
        }
        if (out.empty()) out.push_back({-1, 0, 0, 0, 0, 0, 0});
    }
    S apply(const S& s, const hsf::Move& m) override {
        int r = m[0];
        if (r < 0 || r >= (int)s.size()) return s;
        prepare(s);
        if (simR != r) {
            double v = simulate(s, r);
            dCache[r] = v; dHas[r] = 1;
        }
        int SZ = (int)s.size();
        S t;
        t.reserve(SZ + 1);
        flatB.clear(); flatEB.clear(); cOffB.clear();
        cLoadB.clear(); cCostB.clear(); cValidB.clear();
        for (int idx = 0; idx < SZ; ++idx) {
            if (idx == r) continue;
            int sl = slotOf[idx];
            if (sl >= 0) {
                const auto& W = wk[sl];
                t.push_back(W);
                cOffB.push_back((int)flatB.size());
                flatB.insert(flatB.end(), W.begin(), W.end());
                if (wValid[sl]) flatEB.insert(flatEB.end(), wE[sl].begin(), wE[sl].end());
                else flatEB.resize(flatEB.size() + W.size() + 1, 0.0);
                cLoadB.push_back(loadOf(W));
                cCostB.push_back(wCost[sl]);
                cValidB.push_back(wValid[sl]);
            } else {
                t.push_back(s[idx]);
                int o = cOff[idx], L = cOff[idx + 1] - o;
                cOffB.push_back((int)flatB.size());
                flatB.insert(flatB.end(), flat.begin() + o, flat.begin() + o + L);
                flatEB.insert(flatEB.end(), flatE.begin() + (o + idx), flatE.begin() + (o + idx + L + 1));
                cLoadB.push_back(cLoad[idx]);
                cCostB.push_back(cCost[idx]);
                cValidB.push_back(cValid[idx]);
            }
        }
        int sl = slotOf[SZ];
        if (sl >= 0 && !wk[sl].empty()) {
            const auto& W = wk[sl];
            t.push_back(W);
            cOffB.push_back((int)flatB.size());
            flatB.insert(flatB.end(), W.begin(), W.end());
            if (wValid[sl]) flatEB.insert(flatEB.end(), wE[sl].begin(), wE[sl].end());
            else flatEB.resize(flatEB.size() + W.size() + 1, 0.0);
            cLoadB.push_back(loadOf(W));
            cCostB.push_back(wCost[sl]);
            cValidB.push_back(wValid[sl]);
        }
        int SZn = (int)t.size();
        cOffB.push_back((int)flatB.size());
        // rof/pof de la nueva solución
        std::fill(rof.begin(), rof.end(), -1);
        const int n = M.n;
        for (int rr = 0; rr < SZn; ++rr) {
            int o = cOffB[rr], e = cOffB[rr + 1];
            for (int i = o; i < e; ++i) {
                int c = flatB[i];
                if (c >= 1 && c <= n && rof[c] < 0) { rof[c] = rr; pof[c] = i - o; }
            }
        }
        flat.swap(flatB); flatE.swap(flatEB); cOff.swap(cOffB);
        cLoad.swap(cLoadB); cCost.swap(cCostB); cValid.swap(cValidB);
        nC = SZn;
        dCache.resize(SZn);
        dHas.assign(SZn, 0);
        haveCache = true;
        simR = -1;
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        int r = m[0];
        if (r < 0 || r >= (int)s.size()) return 0.0;
        prepare(s);
        if (dHas[r]) return dCache[r];
        double v = simulate(s, r);
        dCache[r] = v; dHas[r] = 1;
        return v;
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-6, m[1], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 10);
    int ml = (int)params.get("max_len", 15);
    return std::make_unique<RouteDissolveReinsert>(model, k, ml);
}
