// COMPONENT: {"name": "critical_path_adjacent_swap", "slot": "neighborhood", "params": {"block_ends_only": {"type": "int", "range": [0, 1]}}}
class CriticalAdjacentSwap : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    CriticalAdjacentSwap(const JobShop& md, bool ends) : M(md), ends_only(ends) {
        int N = M.n_ops;
        pt.assign(N, 0); jpred.assign(N, -1); jsucc.assign(N, -1); machOf.assign(N, 0);
        mcnt.assign(std::max(M.m, 0), 0);
        for (int j = 0; j < M.n; ++j) {
            int L = (int)M.routes[j].size();
            for (int k = 0; k < L; ++k) {
                int op = M.off[j] + k;
                pt[op] = M.routes[j][k].second;
                machOf[op] = M.routes[j][k].first;
                jpred[op] = k > 0 ? op - 1 : -1;
                jsucc[op] = k + 1 < L ? op + 1 : -1;
                if (machOf[op] >= 0 && machOf[op] < M.m) mcnt[machOf[op]]++;
            }
            if (L > 0) lastOps.push_back(M.off[j + 1] - 1);
        }
        moff.assign(std::max(M.m, 0) + 1, 0);
        for (int mm = 0; mm < M.m; ++mm) moff[mm + 1] = moff[mm] + mcnt[mm];
        MS_ = std::max(1, moff.empty() ? 1 : moff.back());
        mp.assign(N, -1); ms.assign(N, -1); bend.assign(N, 0); nend.assign(N, 0); mpos.assign(N, 0);
        pos.assign(N, 0); T.assign(N, 0); indeg.assign(N, 0); mark.assign(N, 0); chg.assign(N, 0);
        qq.assign(N, 0); fc.assign(N, 0); gc.assign(N, 0); dirty.assign(N + 1, 0);
        ost.assign(std::max(N, 1), 0);
        opIdx.assign((size_t)std::max(M.n, 0) * (size_t)std::max(M.m, 0), -1);
        for (int j = 0; j < M.n; ++j)
            for (int mm = 0; mm < M.m; ++mm)
                if (M.opk[j][mm] >= 0) opIdx[(size_t)j * M.m + mm] = M.off[j] + M.opk[j][mm];
        stk_.reserve(N + 4);
        wpos_.assign(MS_, 0);
        unsigned long long z = 0x9E3779B97F4A7C15ULL;
        for (int k = 0; k < MS_; ++k) {
            z += 0x9E3779B97F4A7C15ULL;
            unsigned long long x = z;
            x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
            x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
            x ^= x >> 31;
            wpos_[k] = x | 1ULL;
        }
        size_t per = (size_t)std::max(N, 1) * 4 + (size_t)MS_ * 24 + 256;
        K_ = 1;
        while (K_ < 256 && (size_t)(K_ * 2) * per <= ((size_t)16 << 20)) K_ *= 2;
        slots_.resize(K_);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        int si = ensure(s);
        Slot& sl = slots_[si];
        bool wasEmpty = out.empty();
        if (wasEmpty && sl.mvOk) { out.insert(out.end(), sl.mv.begin(), sl.mv.end()); return; }
        work(s, si);
        int rel;
        if (clean_) { criticalFast(); rel = 0; }
        else rel = critical(s);
        if (rel == 0) {
            size_t P = path.size();
            for (size_t t = 0; t + 1 < P; ++t) {
                if (path[t].first != path[t + 1].first || path[t + 1].second != path[t].second + 1) continue;
                if (ends_only) {
                    bool first = (t == 0) || path[t - 1].first != path[t].first || path[t].second != path[t - 1].second + 1;
                    bool last = (t + 2 >= P) || path[t + 2].first != path[t + 1].first || path[t + 2].second != path[t + 1].second + 1;
                    if (!first && !last) continue;
                }
                out.push_back(Move{path[t].first, path[t].second, 0, 0, 0, 0});
            }
        }
        if (out.empty())
            for (int mm = 0; mm < (int)s.size(); ++mm)
                for (int i = 0; i + 1 < (int)s[mm].size(); ++i) out.push_back(Move{mm, i, 0, 0, 0, 0});
        if (wasEmpty) { sl.mv.assign(out.begin(), out.end()); sl.mvOk = true; }
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        std::swap(r[mv[0]][mv[1]], r[mv[0]][mv[1] + 1]);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        int si = ensure(s);
        Slot& sl = slots_[si];
        int mm = mv[0], i = mv[1];
        bool inr = mm >= 0 && mm < M.m && i >= 0 && i + 1 < mcnt[mm];
        int idx = 0;
        if (inr) {
            memoReady(sl);
            idx = moff[mm] + i;
            if (sl.dS[idx] == sl.gen) return sl.dV[idx];
        }
        work(s, si);
        double r = clean_ ? deltaClean(s, mv) : M.objective(apply(s, mv)) - cache_obj_;
        if (inr) { sl.dS[idx] = sl.gen; sl.dV[idx] = r; }
        return r;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& mv) override {
        int si = ensure(s);
        Slot& sl = slots_[si];
        int mm = mv[0], i = mv[1];
        bool inr = mm >= 0 && mm < M.m && i >= 0 && i + 1 < mcnt[mm];
        if (!inr) return delta(s, mv);
        memoReady(sl);
        int idx = moff[mm] + i;
        if (sl.dS[idx] == sl.gen) return sl.dV[idx];
        if (sl.eS[idx] == sl.gen) return sl.eV[idx];
        work(s, si);
        if (!clean_) return delta(s, mv);
        const auto& mo = mop_[mm];
        int a = mo[i], b = mo[i + 1];
        if (!tails_ok_) computeTails();
        int C = mk_;
        int L = boundL(a, b);
        double r;
        if (L >= C) r = (double)L - cache_obj_;
        else if (avoidCount(a, b) != 0ULL) r = (double)C - cache_obj_;
        else r = (double)L - cache_obj_;
        sl.eS[idx] = sl.gen; sl.eV[idx] = r;
        return r;
    }

private:
    struct Slot {
        Sol sol;
        unsigned long long h = 0;
        unsigned gen = 0;
        bool valid = false, mvOk = false;
        std::vector<Move> mv;
        std::vector<double> dV, eV;
        std::vector<unsigned> dS, eS;
    };
    const JobShop& M;
    bool ends_only;
    int MS_ = 1, K_ = 1, cur_ = -1, workSlot_ = -1;
    unsigned gen_ = 0, workGen_ = 0;
    std::vector<Slot> slots_;
    std::vector<unsigned long long> wpos_;
    std::vector<int> start, posOf;
    std::vector<std::pair<int, int>> path;
    double cache_obj_ = 0;
    int mk_ = 0;
    bool clean_ = false, tails_ok_ = false;
    std::vector<int> pt, jpred, jsucc, machOf, mp, ms, bend, nend, pos, T, indeg, mpos, lastOps, qq, mcnt, moff, opIdx, stk_;
    std::vector<unsigned long long> fc, gc;
    unsigned long long totC = 0;
    std::vector<std::vector<int>> mop_;
    std::vector<unsigned> mark, chg, ost;
    std::vector<char> dirty;
    unsigned stamp_ = 0, ostamp_ = 0;

    static inline unsigned long long fmix(unsigned long long x) {
        x ^= x >> 33; x *= 0xFF51AFD7ED558CCDULL; x ^= x >> 33; x *= 0xC4CEB9FE1A85EC53ULL; x ^= x >> 33;
        return x;
    }
    unsigned long long hashSol(const Sol& s) const {
        if ((int)s.size() == M.m) {
            bool ok = true;
            for (int mm = 0; mm < M.m; ++mm) if ((int)s[mm].size() != mcnt[mm]) { ok = false; break; }
            if (ok) {
                unsigned long long h0 = 0x243F6A8885A308D3ULL, h1 = 0;
                for (int mm = 0; mm < M.m; ++mm) {
                    const int* x = s[mm].data();
                    const unsigned long long* w = wpos_.data() + moff[mm];
                    int L = mcnt[mm];
                    int i = 0;
                    for (; i + 1 < L; i += 2) {
                        h0 += (unsigned long long)(long long)x[i] * w[i];
                        h1 += (unsigned long long)(long long)x[i + 1] * w[i + 1];
                    }
                    if (i < L) h0 += (unsigned long long)(long long)x[i] * w[i];
                }
                return fmix(h0 + h1 * 0x9E3779B97F4A7C15ULL);
            }
        }
        unsigned long long h = 0x13198A2E03707344ULL ^ (unsigned long long)s.size();
        for (const auto& row : s) {
            h = (h ^ (unsigned long long)row.size()) * 0x100000001B3ULL;
            for (int x : row) h = (h ^ (unsigned long long)(unsigned)x) * 0x100000001B3ULL;
        }
        return fmix(h);
    }
    unsigned nextGen() {
        if (++gen_ == 0) {
            for (auto& sl : slots_) {
                std::fill(sl.dS.begin(), sl.dS.end(), 0u);
                std::fill(sl.eS.begin(), sl.eS.end(), 0u);
                sl.valid = false; sl.mvOk = false; sl.gen = 0;
            }
            gen_ = 1; cur_ = -1; workSlot_ = -1;
        }
        return gen_;
    }
    inline void memoReady(Slot& sl) {
        if ((int)sl.dS.size() != MS_) {
            sl.dS.assign(MS_, 0u); sl.eS.assign(MS_, 0u);
            sl.dV.assign(MS_, 0.0); sl.eV.assign(MS_, 0.0);
        }
    }
    int ensure(const Sol& s) {
        if (cur_ >= 0 && slots_[cur_].sol == s) return cur_;
        unsigned long long h = hashSol(s);
        int idx = (int)(h & (unsigned long long)(K_ - 1));
        Slot& sl = slots_[idx];
        if (sl.valid && sl.h == h && sl.sol == s) { cur_ = idx; return idx; }
        unsigned g = nextGen();
        Slot& s2 = slots_[idx];
        if (s2.sol.size() != s.size()) s2.sol.resize(s.size());
        for (size_t r = 0; r < s.size(); ++r) s2.sol[r].assign(s[r].begin(), s[r].end());
        s2.h = h; s2.valid = true; s2.mvOk = false; s2.gen = g;
        cur_ = idx;
        return idx;
    }
    inline void work(const Sol& s, int si) {
        if (workSlot_ == si && workGen_ == slots_[si].gen) return;
        prepare(s);
        workSlot_ = si; workGen_ = slots_[si].gen;
    }

    void resetStamps() {
        std::fill(mark.begin(), mark.end(), 0);
        std::fill(chg.begin(), chg.end(), 0);
        stamp_ = 1;
    }

    bool reaches(int a, int jb) {
        int lim = bend[jb] - pt[jb], pj = pos[jb];
        if (++stamp_ == 0) resetStamps();
        unsigned st = stamp_;
        stk_.clear();
        mark[a] = st; stk_.push_back(a);
        while (!stk_.empty()) {
            int w = stk_.back(); stk_.pop_back();
            int c1 = jsucc[w], c2 = ms[w];
            if (c1 >= 0) {
                if (c1 == jb) return true;
                if (mark[c1] != st && pos[c1] < pj && bend[c1] <= lim) { mark[c1] = st; stk_.push_back(c1); }
            }
            if (c2 >= 0) {
                if (c2 == jb) return true;
                if (mark[c2] != st && pos[c2] < pj && bend[c2] <= lim) { mark[c2] = st; stk_.push_back(c2); }
            }
        }
        return false;
    }

    inline int boundL(int a, int b) const {
        int jb = jpred[b];
        int ma = mp[a], ja = jpred[a];
        int rb2 = jb >= 0 ? bend[jb] : 0;
        if (ma >= 0 && bend[ma] > rb2) rb2 = bend[ma];
        int eb2 = rb2 + pt[b];
        int ra2 = ja >= 0 ? bend[ja] : 0;
        if (eb2 > ra2) ra2 = eb2;
        int w1 = jsucc[a], w2 = ms[b], w3 = jsucc[b];
        int qa2 = w1 >= 0 ? pt[w1] + qq[w1] : 0;
        if (w2 >= 0 && pt[w2] + qq[w2] > qa2) qa2 = pt[w2] + qq[w2];
        int qb2 = w3 >= 0 ? pt[w3] + qq[w3] : 0;
        if (pt[a] + qa2 > qb2) qb2 = pt[a] + qa2;
        int L = eb2 + qb2;
        int L2 = ra2 + pt[a] + qa2;
        if (L2 > L) L = L2;
        return L;
    }
    inline unsigned long long avoidCount(int a, int b) const {
        int C = mk_;
        unsigned long long thA = (bend[a] + qq[a] == C) ? fc[a] * gc[a] : 0ULL;
        unsigned long long thB = (bend[b] + qq[b] == C) ? fc[b] * gc[b] : 0ULL;
        unsigned long long both = (bend[a] == bend[b] - pt[b] && bend[b] + qq[b] == C) ? fc[a] * gc[b] : 0ULL;
        return totC - thA - thB + both;
    }

    double deltaClean(const Sol& s, const Move& mv) {
        int mm = mv[0], i = mv[1];
        const auto& mo = mop_[mm];
        int a = mo[i], b = mo[i + 1];
        int ta = pos[a];
        int jb = jpred[b];
        if (jb >= 0 && bend[jb] - pt[jb] >= bend[a] && pos[jb] > ta) {
            if (reaches(a, jb)) return M.objective(apply(s, mv)) - cache_obj_;
        }
        if (!tails_ok_) computeTails();
        int C = mk_;
        int L = boundL(a, b);
        if (L >= C) return (double)L - cache_obj_;
        if (avoidCount(a, b) != 0ULL) return (double)C - cache_obj_;
        return fullDelta(a, b);
    }

    double fullDelta(int a, int b) {
        if (++stamp_ == 0) resetStamps();
        unsigned st = stamp_;
        int jb = jpred[b];
        int q = ms[b], ma = mp[a];
        int sb = 0;
        if (jb >= 0) sb = bend[jb];
        if (ma >= 0 && bend[ma] > sb) sb = bend[ma];
        int nb = sb + pt[b];
        nend[b] = nb; chg[b] = st;
        int sa = nb;
        int ja = jpred[a];
        if (ja >= 0 && bend[ja] > sa) sa = bend[ja];
        int na = sa + pt[a];
        nend[a] = na; chg[a] = st;
        int lo = M.n_ops, hi = -1;
        char* dt = dirty.data();
        const int* P = pos.data();
        auto push = [&](int v) {
            if (v >= 0 && v != a && v != b) {
                int p = P[v];
                if (!dt[p]) { dt[p] = 1; if (p < lo) lo = p; if (p > hi) hi = p; }
            }
        };
        if (nb != bend[b]) push(jsucc[b]);
        if (na != bend[a]) push(jsucc[a]);
        push(q);
        const int* Tp = T.data();
        const int* jpp = jpred.data();
        const int* mpp = mp.data();
        const int* ptp = pt.data();
        const int* bp = bend.data();
        int* np = nend.data();
        unsigned* cp = chg.data();
        for (int p = lo; p <= hi; ++p) {
            if (!dt[p]) continue;
            dt[p] = 0;
            int v = Tp[p];
            int sv = 0;
            int jp = jpp[v];
            if (jp >= 0) sv = cp[jp] == st ? np[jp] : bp[jp];
            int m2 = (v == q) ? a : mpp[v];
            if (m2 >= 0) { int e = cp[m2] == st ? np[m2] : bp[m2]; if (e > sv) sv = e; }
            int e = sv + ptp[v];
            if (e != bp[v]) {
                np[v] = e; cp[v] = st;
                push(jsucc[v]);
                push(ms[v]);
            }
        }
        int mx = 0;
        for (int o : lastOps) { int e = cp[o] == st ? np[o] : bp[o]; if (e > mx) mx = e; }
        return (double)mx - cache_obj_;
    }

    void computeTails() {
        int N = M.n_ops;
        const int* Tp = T.data();
        const int* jpp = jpred.data();
        const int* jsp = jsucc.data();
        const int* mpp = mp.data();
        const int* msp = ms.data();
        const int* ptp = pt.data();
        const int* bp = bend.data();
        int* qp = qq.data();
        unsigned long long* fp = fc.data();
        unsigned long long* gp = gc.data();
        for (int t = 0; t < N; ++t) {
            int v = Tp[t];
            int jp = jpp[v], m2 = mpp[v];
            int r = bp[v] - ptp[v];
            unsigned long long f = (r == 0) ? 1ULL : 0ULL;
            if (jp >= 0 && bp[jp] == r) f += fp[jp];
            if (m2 >= 0 && bp[m2] == r) f += fp[m2];
            fp[v] = f;
        }
        int C = mk_;
        unsigned long long tc = 0;
        for (int t = N - 1; t >= 0; --t) {
            int v = Tp[t];
            int w1 = jsp[v], w2 = msp[v];
            int q = 0;
            int q1 = -1, q2 = -1;
            if (w1 >= 0) { q1 = ptp[w1] + qp[w1]; q = q1; }
            if (w2 >= 0) { q2 = ptp[w2] + qp[w2]; if (q2 > q) q = q2; }
            qp[v] = q;
            unsigned long long g = (q == 0) ? 1ULL : 0ULL;
            if (w1 >= 0 && q1 == q) g += gp[w1];
            if (w2 >= 0 && q2 == q) g += gp[w2];
            gp[v] = g;
            if (q == 0 && bp[v] == C) tc += fp[v];
        }
        totC = tc;
        tails_ok_ = true;
    }

    void prepare(const Sol& s) {
        tails_ok_ = false;
        clean_ = false;
        if ((int)s.size() != M.m) { cache_obj_ = M.objective(s); return; }
        if (++ostamp_ == 0) { std::fill(ost.begin(), ost.end(), 0); ostamp_ = 1; }
        unsigned os = ostamp_;
        int N = M.n_ops, Mm = M.m, Nn = M.n;
        mop_.resize(Mm);
        int* mpp = mp.data();
        int* msp = ms.data();
        int* mposp = mpos.data();
        unsigned* osp = ost.data();
        const int* oi = opIdx.data();
        bool ok = true;
        for (int mm = 0; mm < Mm && ok; ++mm) {
            const auto& seq = s[mm];
            int L = (int)seq.size();
            if (L != mcnt[mm]) { ok = false; break; }
            auto& mo = mop_[mm];
            mo.resize(L);
            int prev = -1;
            for (int i = 0; i < L; ++i) {
                int j = seq[i];
                if (j < 0 || j >= Nn) { ok = false; break; }
                int o = oi[(size_t)j * Mm + mm];
                if (o < 0 || osp[o] == os) { ok = false; break; }
                osp[o] = os;
                mo[i] = o;
                mpp[o] = prev;
                if (prev >= 0) msp[prev] = o;
                mposp[o] = i;
                prev = o;
            }
            if (ok && prev >= 0) msp[prev] = -1;
        }
        if (!ok) { cache_obj_ = M.objective(s); return; }
        const int* jpp = jpred.data();
        const int* jsp = jsucc.data();
        const int* ptp = pt.data();
        int* dg = indeg.data();
        int* Tp = T.data();
        int* pp = pos.data();
        int* bp = bend.data();
        int cnt = 0;
        for (int op = 0; op < N; ++op) {
            int d = (jpp[op] >= 0) + (mpp[op] >= 0);
            dg[op] = d;
            if (d == 0) Tp[cnt++] = op;
        }
        int h = 0, C = 0;
        while (h < cnt) {
            int v = Tp[h];
            pp[v] = h;
            ++h;
            int jp = jpp[v], m2 = mpp[v];
            int r = 0;
            if (jp >= 0) r = bp[jp];
            if (m2 >= 0 && bp[m2] > r) r = bp[m2];
            int e = r + ptp[v];
            bp[v] = e;
            if (e > C) C = e;
            int nx = jsp[v];
            if (nx >= 0 && --dg[nx] == 0) Tp[cnt++] = nx;
            int m3 = msp[v];
            if (m3 >= 0 && --dg[m3] == 0) Tp[cnt++] = m3;
        }
        if (cnt != N) { cache_obj_ = M.objective(s); return; }
        mk_ = C;
        cache_obj_ = (double)C;
        clean_ = true;
    }

    void criticalFast() {
        path.clear();
        int cur = -1;
        for (int op : lastOps) if (bend[op] == mk_) { cur = op; break; }
        int guard = M.n_ops + 1;
        while (cur >= 0 && guard-- > 0) {
            int p = mpos[cur];
            path.push_back({machOf[cur], p});
            int st = bend[cur] - pt[cur];
            if (st == 0) break;
            int nx = -1;
            if (p > 0) { int o2 = mp[cur]; if (bend[o2] == st) nx = o2; }
            if (nx < 0 && jpred[cur] >= 0 && bend[cur - 1] == st) nx = cur - 1;
            cur = nx;
        }
        std::reverse(path.begin(), path.end());
    }

    int opid(int j, int mm) const {
        if (j < 0 || j >= M.n || M.opk[j][mm] < 0) return -1;
        return M.off[j] + M.opk[j][mm];
    }
    int endt(int op) const { int j = M.job_of[op]; return start[op] + M.routes[j][op - M.off[j]].second; }
    int critical(const Sol& s) {
        int mk;
        int rel = M.schedule(s, start, mk);
        path.clear();
        posOf.assign(M.n_ops, -1);
        for (int mm = 0; mm < (int)s.size() && mm < M.m; ++mm)
            for (int i = 0; i < (int)s[mm].size(); ++i) { int op = opid(s[mm][i], mm); if (op >= 0) posOf[op] = i; }
        int cur = -1;
        for (int j = 0; j < M.n; ++j)
            if (!M.routes[j].empty()) { int op = M.off[j + 1] - 1; if (endt(op) == mk) { cur = op; break; } }
        int guard = M.n_ops + 1;
        while (cur >= 0 && guard-- > 0) {
            int j = M.job_of[cur], k = cur - M.off[j], mach = M.routes[j][k].first, p = posOf[cur];
            if (p < 0) break;
            path.push_back({mach, p});
            int st = start[cur];
            if (st == 0) break;
            int nx = -1;
            if (p > 0) { int o2 = opid(s[mach][p - 1], mach); if (o2 >= 0 && endt(o2) == st) nx = o2; }
            if (nx < 0 && k > 0 && endt(cur - 1) == st) nx = cur - 1;
            cur = nx;
        }
        std::reverse(path.begin(), path.end());
        return rel;
    }
};

std::unique_ptr<hsf::Neighborhood<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<CriticalAdjacentSwap>(model, params.get("block_ends_only", 0) >= 0.5);
}
