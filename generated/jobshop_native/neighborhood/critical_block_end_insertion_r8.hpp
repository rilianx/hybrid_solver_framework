// COMPONENT: {"name": "critical_block_end_insertion", "slot": "neighborhood", "params": {"max_shift": {"type": "int", "range": [2, 60]}}}
class CriticalBlockInsertion : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    CriticalBlockInsertion(const JobShop& md, int ms) : M(md), max_shift(ms) {
        int N = M.n_ops;
        pt_.assign(N, 0); first_.assign(N, 0); last_.assign(N, 0); machOf_.assign(N, -1);
        for (int j = 0; j < M.n; ++j)
            for (int k = 0; k < (int)M.routes[j].size(); ++k) {
                int op = M.off[j] + k;
                pt_[op] = M.routes[j][k].second;
                machOf_[op] = M.routes[j][k].first;
                first_[op] = (k == 0);
                last_[op] = (k + 1 == (int)M.routes[j].size());
            }
        for (int j = 0; j < M.n; ++j)
            if (!M.routes[j].empty()) lastOps_.push_back(M.off[j + 1] - 1);
        mcnt_.assign(std::max(M.m, 0), 0);
        for (int j = 0; j < M.n; ++j)
            for (int mm = 0; mm < M.m; ++mm) if (M.opk[j][mm] >= 0) mcnt_[mm]++;
        opIdx_.assign((size_t)std::max(M.n, 0) * (size_t)std::max(M.m, 0), -1);
        for (int j = 0; j < M.n; ++j)
            for (int mm = 0; mm < M.m; ++mm)
                if (M.opk[j][mm] >= 0) opIdx_[(size_t)j * M.m + mm] = M.off[j] + M.opk[j][mm];
        ost_.assign(std::max(N, 1), 0);
        mp_.assign(N, -1); ms_.assign(N, -1); oend_.assign(N, 0); nend_.assign(N, 0); mark_.assign(N, 0);
        deg_.assign(N, 0); tl_.assign(N, 0); seg_.assign(N + 1, 0);
        mpos_.assign(N, -1); pos_.assign(N, 0); T_.assign(N, 0);
        chg_.assign(N, 0); inq_.assign(N, 0); vis_.assign(N, 0);
        bits_.assign((size_t)((2 * N + 2) / 64 + 2), 0ULL);
        stk_.reserve(N); lst_.reserve(N); q_.reserve(N); heap_.reserve(N + 8);
        moff_.assign(std::max(M.m, 0) + 1, 0);
        long long tot = 0;
        for (int mm = 0; mm < M.m; ++mm) { tot += (long long)mcnt_[mm] * mcnt_[mm]; moff_[mm + 1] = (int)std::min<long long>(tot, 2000000000LL); }
        memoOn_ = tot > 0 && tot <= 8000000LL;
        if (memoOn_) { memoS_.assign((size_t)tot, 0); memoV_.assign((size_t)tot, 0.0); }
        sdeg_.assign(std::max(N, 1), 0); send_.assign(std::max(N, 1), 0); sfin_.assign(std::max(N, 1), 0);
        sdone_.assign(std::max(M.n, 1), 0); jlen_.assign(std::max(M.n, 1), 0);
        for (int j = 0; j < M.n; ++j) jlen_[j] = (int)M.routes[j].size();
        rdy_.reserve(2 * N + 8);
        thT_.assign(std::max(N, 1), 0);
        tq_.assign(std::max(N, 1), 0);
        bmx_.assign((size_t)(std::max(N, 1) / 16 + 2), 0);
        rec_.assign(std::max(N, 1), Rec{0, -1, -1, 0});
        cgK_.assign(std::max(N, 1), 0); exK_.assign(std::max(N, 1), 0); nvK_.assign(std::max(N, 1), 0);
        if (memoOn_) { segS_.assign((size_t)tot, 0); segA_.assign((size_t)tot, 0); segB_.assign((size_t)tot, 0); }
        oeT_.assign(std::max(N, 1), 0); preOe_.assign(N + 2, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        sync(s);
        int rel;
        if (clean_) { criticalFast(); rel = 0; }
        else rel = critical(s);
        if (rel == 0) {
            size_t P = path.size(), t = 0;
            while (t < P) {
                size_t u = t;
                while (u + 1 < P && path[u + 1].first == path[t].first && path[u + 1].second == path[u].second + 1) ++u;
                int mach = path[t].first, lo = path[t].second, hi = path[u].second;
                if (hi - lo == 1) out.push_back(Move{mach, lo, hi, 0, 0, 0});
                else if (hi > lo) {
                    for (int p = lo; p <= hi; ++p) {
                        if (p != lo && p - lo <= max_shift) out.push_back(Move{mach, p, lo, 0, 0, 0});
                        if (p != hi && hi - p <= max_shift) out.push_back(Move{mach, p, hi, 0, 0, 0});
                    }
                    for (int p = lo + 1; p < hi; ++p) {
                        if (p - lo <= max_shift) out.push_back(Move{mach, lo, p, 0, 0, 0});
                        if (hi - p <= max_shift) out.push_back(Move{mach, hi, p, 0, 0, 0});
                    }
                }
                t = u + 1;
            }
        }
        if (out.empty())
            for (int mm = 0; mm < (int)s.size(); ++mm) {
                int L = (int)s[mm].size();
                for (int f = 0; f < L; ++f)
                    for (int to = std::max(0, f - max_shift); to <= std::min(L - 1, f + max_shift); ++to)
                        if (to != f && to != f - 1) out.push_back(Move{mm, f, to, 0, 0, 0});
            }
    }
    Sol apply(const Sol& s, const Move& mv) override {
        pend_ = true; pmv_ = mv;
        Sol r = s;
        auto& v = r[mv[0]];
        int f = mv[1], t = mv[2];
        if (f < t) std::rotate(v.begin() + f, v.begin() + f + 1, v.begin() + t + 1);
        else if (f > t) std::rotate(v.begin() + t, v.begin() + f, v.begin() + f + 1);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        if (clean_) {
            int mach = mv[0], f = mv[1], t = mv[2];
            if (memoOn_ && mach >= 0 && mach < M.m) {
                int L = mcnt_[mach];
                if (f >= 0 && f < L && t >= 0 && t < L) {
                    size_t idx = (size_t)moff_[mach] + (size_t)f * L + t;
                    if (memoS_[idx] == solStamp_) return memoV_[idx];
                    double r = deltaRaw(s, mv);
                    memoS_[idx] = solStamp_; memoV_[idx] = r;
                    return r;
                }
            }
        }
        return deltaRaw(s, mv);
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& mv) override {
        sync(s);
        if (!clean_) return delta(s, mv);
        int mach = mv[0], f = mv[1], t = mv[2];
        if (mach < 0 || mach >= M.m) return delta(s, mv);
        const auto& mo = mop_[mach];
        int L = (int)mo.size();
        if (L != (int)s[mach].size() || f < 0 || f >= L || t < 0 || t >= L) return delta(s, mv);
        if (f == t) return 0.0;
        if (memoOn_) {
            size_t idx = (size_t)moff_[mach] + (size_t)f * L + t;
            if (memoS_[idx] == solStamp_) return memoV_[idx];
        }
        if (!tails_ok_) computeTails();
        int lo = std::min(f, t), hi = std::max(f, t);
        double pen = 0.0;
        {
            int u0 = mo[f];
            bool cyc = f < t ? reach(last_[u0] ? -1 : u0 + 1, mo[t]) : reach(mo[t], first_[u0] ? -1 : u0 - 1);
            if (cyc) pen = M.penalty > 0 ? (double)M.penalty : 1e9;
        }
        const int* mop = mo.data();
        const int* ptp = pt_.data();
        const int* oe = oend_.data();
        const int* tl = tl_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        int* sg = seg_.data();
        int ne = lo > 0 ? oe[mop[lo - 1]] : 0;
        for (int i = lo; i <= hi; ++i) {
            int o = (i == t) ? mop[f] : (f < t ? mop[i + 1] : mop[i - 1]);
            int r = fs[o] ? 0 : oe[o - 1];
            if (ne > r) r = ne;
            ne = r + ptp[o];
            sg[i - lo] = ne;
        }
        int qn = (hi + 1 < L) ? ptp[mop[hi + 1]] + tl[mop[hi + 1]] : 0;
        int best = 0;
        for (int i = hi; i >= lo; --i) {
            int o = (i == t) ? mop[f] : (f < t ? mop[i + 1] : mop[i - 1]);
            int q = ls[o] ? 0 : ptp[o + 1] + tl[o + 1];
            if (qn > q) q = qn;
            int v = sg[i - lo] + q;
            if (v > best) best = v;
            qn = ptp[o] + q;
        }
        return (double)best - cache_obj_ + pen;
    }
    Move tabu_key(const Move& mv) override { return Move{mv[0], mv[2], mv[1], 0, 0, 0}; }

private:
    const JobShop& M;
    int max_shift;
    std::vector<int> start, posOf;
    std::vector<std::pair<int, int>> path;
    Sol cache_;
    double cache_obj_ = 0;
    int mk_ = 0, cntC_ = 0;
    bool has_ = false, clean_ = false, tails_ok_ = false;

    std::vector<int> pt_, mp_, ms_, oend_, nend_, mark_, deg_, stk_, lst_, q_, tl_, seg_, lastOps_;
    std::vector<int> machOf_, mpos_, pos_, T_, mcnt_, moff_, opIdx_;
    std::vector<unsigned> chg_, inq_, vis_, memoS_, ost_;
    std::vector<double> memoV_;
    std::vector<unsigned long long> heap_, bits_;
    std::vector<char> first_, last_;
    std::vector<std::vector<int>> mop_;
    bool memoOn_ = false;
    int stamp_ = 0;
    unsigned cst_ = 0, vst_ = 0, solStamp_ = 0, ostamp_ = 0;
    const std::vector<int>* cmo_ = nullptr;
    int cm_ = 0, cf_ = 0, ct_ = 0, clo_ = 0, chi_ = 0, cL_ = 0;
    std::vector<int> sdeg_, send_, sdone_, jlen_, rdy_, thT_;
    std::vector<char> sfin_;
    std::vector<int> tq_, bmx_;
    bool pend_ = false;
    Move pmv_{};
    struct Rec { int th, jp, mp, pt; };
    std::vector<Rec> rec_;
    std::vector<unsigned> cgK_, exK_, segS_;
    std::vector<int> nvK_, segA_, segB_;
    std::vector<int> oeT_, preOe_;

    void bumpSol() {
        if (++solStamp_ == 0) {
            std::fill(memoS_.begin(), memoS_.end(), 0);
            std::fill(segS_.begin(), segS_.end(), 0);
            solStamp_ = 1;
        }
    }

    static void rotRow(std::vector<int>& v, int f, int t) {
        if (f < t) std::rotate(v.begin() + f, v.begin() + f + 1, v.begin() + t + 1);
        else if (f > t) std::rotate(v.begin() + t, v.begin() + f, v.begin() + f + 1);
    }

    void sync(const Sol& s) {
        if (has_ && s == cache_) return;
        if (pend_ && has_ && clean_ && tryIncr(s)) { pend_ = false; return; }
        pend_ = false;
        prepare(s);
    }

    // s == apply(cache_, pmv_)? then update the cached state incrementally
    bool tryIncr(const Sol& s) {
        int mach = pmv_[0], f = pmv_[1], t = pmv_[2];
        if (mach < 0 || mach >= M.m || (int)cache_.size() != M.m || s.size() != cache_.size()) return false;
        auto& row = cache_[mach];
        int L = (int)row.size();
        if (f < 0 || f >= L || t < 0 || t >= L || f == t) return false;
        if (L != (int)mop_[mach].size()) return false;
        rotRow(row, f, t);
        if (!(s == cache_)) return false;
        bumpSol();
        tails_ok_ = false;
        auto& mo = mop_[mach];
        rotRow(mo, f, t);
        int lo = std::min(f, t), hi = std::max(f, t);
        for (int i = lo; i <= hi; ++i) mpos_[mo[i]] = i;
        int a = std::max(0, lo - 1), b = std::min(L - 1, hi + 1);
        for (int i = a; i <= b; ++i) restoreAt(mo, L, i);
        int N = M.n_ops;
        int* P = pos_.data();
        int kmin = N;
        for (int i = lo; i <= b; ++i) { int c = P[mo[i]]; if (c < kmin) kmin = c; }
        int* Tp = T_.data();
        int* dg = deg_.data();
        int* bp = oend_.data();
        int* tq = tq_.data();
        const int* mpp = mp_.data();
        const int* msp = ms_.data();
        const int* ptp = pt_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        int qt = 0;
        for (int k = kmin; k < N; ++k) {
            int v = Tp[k];
            int d = 0;
            if (!fs[v] && P[v - 1] >= kmin) ++d;
            int p = mpp[v];
            if (p >= 0 && P[p] >= kmin) ++d;
            dg[v] = d;
            if (d == 0) tq[qt++] = v;
        }
        int qh = 0;
        while (qh < qt) {
            int v = tq[qh];
            P[v] = kmin + qh;
            ++qh;
            int r = fs[v] ? 0 : bp[v - 1];
            int p = mpp[v];
            if (p >= 0 && bp[p] > r) r = bp[p];
            bp[v] = r + ptp[v];
            if (!ls[v]) { int x = v + 1; if (P[x] >= kmin && --dg[x] == 0) tq[qt++] = x; }
            int y = msp[v];
            if (y >= 0 && P[y] >= kmin && --dg[y] == 0) tq[qt++] = y;
        }
        if (qt != N - kmin) return false;
        for (int i = 0; i < qt; ++i) Tp[kmin + i] = tq[i];
        int C = 0;
        for (int o : lastOps_) if (bp[o] > C) C = bp[o];
        int cc = 0;
        for (int o : lastOps_) if (bp[o] == C) ++cc;
        mk_ = C; cntC_ = cc;
        cache_obj_ = (double)C;
        return true;
    }

    // exact delta via longest path through the moved segment + pruned avoid-path DP; false if not applicable
    bool quickExact(int mach, int f, int t, double& d) {
        const auto& mo = mop_[mach];
        int L = (int)mo.size();
        if (!tails_ok_) computeTails();
        int lo = std::min(f, t), hi = std::max(f, t);
        const int* mop = mo.data();
        const int* ptp = pt_.data();
        const int* oe = oend_.data();
        const int* tl = tl_.data();
        const int* P = pos_.data();
        const int* mof = machOf_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        int* sg = seg_.data();
        int a0 = mop[lo], b0 = mop[hi];
        int endLo = oe[a0], posLo = P[a0], needHi = ptp[b0] + tl[b0], posHi = P[b0];
        int fails = 0;
        int ne = lo > 0 ? oe[mop[lo - 1]] : 0;
        for (int i = lo; i <= hi; ++i) {
            int o = (i == t) ? mop[f] : (f < t ? mop[i + 1] : mop[i - 1]);
            int r = 0;
            if (!fs[o]) {
                int p = o - 1;
                if (mof[p] == mach) return false;
                if (!(P[p] < posLo || oe[p] - ptp[p] < endLo)) {
                    if (++fails > 6 || reach(a0, p)) return false;
                }
                r = oe[p];
            }
            if (ne > r) r = ne;
            ne = r + ptp[o];
            sg[i - lo] = ne;
        }
        int qn = (hi + 1 < L) ? ptp[mop[hi + 1]] + tl[mop[hi + 1]] : 0;
        int best = 0;
        for (int i = hi; i >= lo; --i) {
            int o = (i == t) ? mop[f] : (f < t ? mop[i + 1] : mop[i - 1]);
            int q = 0;
            if (!ls[o]) {
                int x = o + 1;
                if (mof[x] == mach) return false;
                if (!(P[x] > posHi || tl[x] < needHi)) {
                    if (++fails > 6 || reach(x, b0)) return false;
                }
                q = ptp[x] + tl[x];
            }
            if (qn > q) q = qn;
            int v = sg[i - lo] + q;
            if (v > best) best = v;
            qn = ptp[o] + q;
        }
        const int C = mk_;
        if (best >= C) { d = (double)best - cache_obj_; return true; }
        size_t sidx = 0;
        if (memoOn_) {
            sidx = (size_t)moff_[mach] + (size_t)lo * L + hi;
            if (segS_[sidx] == solStamp_) {
                int A = segA_[sidx], b = segB_[sidx];
                if (A > b) { d = (double)(A > best ? A : best) - cache_obj_; return true; }
                if (best >= b) { d = (double)best - cache_obj_; return true; }
            }
        }
        bumpStamp();
        unsigned st = cst_;
        unsigned* cg = cgK_.data();
        unsigned* ex = exK_.data();
        int* nv = nvK_.data();
        const Rec* rc = rec_.data();
        int N = M.n_ops;
        int kmin = N;
        for (int i = lo; i <= hi; ++i) { int pk = P[mop[i]]; ex[pk] = st; if (pk < kmin) kmin = pk; }
        const int* oT = oeT_.data();
        int b2 = best;
        if (preOe_[kmin] > b2) b2 = preOe_[kmin];
        const int* bm = bmx_.data();
        int nb = (N + 15) >> 4;
        bool stop = b2 >= C;
        for (int bk = kmin >> 4; bk < nb && !stop; ++bk) {
            if (bm[bk] <= best) continue;
            int kEnd = std::min(N, (bk + 1) << 4);
            int k0 = std::max(kmin, bk << 4);
            for (int k = k0; k < kEnd; ++k) {
                const Rec& R = rc[k];
                if (R.th <= best || ex[k] == st) continue;
                int r = 0;
                int jp = R.jp;
                if (jp >= 0) { if (jp < kmin) r = oT[jp]; else if (cg[jp] == st) r = nv[jp]; }
                int p = R.mp;
                if (p >= 0) {
                    int e2 = p < kmin ? oT[p] : (cg[p] == st ? nv[p] : 0);
                    if (e2 > r) r = e2;
                }
                int e = r + R.pt;
                nv[k] = e; cg[k] = st;
                if (e > b2) { b2 = e; if (b2 >= C) { stop = true; break; } }
            }
        }
        if (memoOn_) { segS_[sidx] = solStamp_; segA_[sidx] = b2; segB_[sidx] = best; }
        d = (double)b2 - cache_obj_;
        return true;
    }

    // objective(apply(s, mv)) - cache_obj_ for a valid permutation, emulating M.schedule exactly
    double cycObj(const Move& mv) {
        int mach = mv[0], f = mv[1], t = mv[2];
        const auto& mo = mop_[mach];
        int L = (int)mo.size();
        int lo = std::min(f, t), hi = std::max(f, t);
        auto nA = [&](int i) -> int {
            if (i == t) return mo[f];
            return f < t ? mo[i + 1] : mo[i - 1];
        };
        for (int i = lo; i <= hi; ++i) {
            int o = nA(i);
            mp_[o] = i > lo ? nA(i - 1) : (lo > 0 ? mo[lo - 1] : -1);
            ms_[o] = i < hi ? nA(i + 1) : (hi + 1 < L ? mo[hi + 1] : -1);
        }
        if (lo > 0) ms_[mo[lo - 1]] = nA(lo);
        if (hi + 1 < L) mp_[mo[hi + 1]] = nA(hi);

        int N = M.n_ops;
        int* dg = sdeg_.data();
        int* en = send_.data();
        char* fin = sfin_.data();
        int* dn = sdone_.data();
        const int* mpp = mp_.data();
        const int* msp = ms_.data();
        const int* ptp = pt_.data();
        const int* jo = M.job_of.data();
        const int* jl = jlen_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        for (int op = 0; op < N; ++op) { dg[op] = (!fs[op]) + (mpp[op] >= 0); fin[op] = 0; }
        for (int j = 0; j < M.n; ++j) dn[j] = 0;
        rdy_.clear();
        for (int op = 0; op < N; ++op) if (dg[op] == 0) rdy_.push_back(op);
        int nd = 0, rel = 0, jp = 0;
        while (nd < N) {
            if (rdy_.empty()) {
                while (dn[jp] >= jl[jp]) ++jp;
                rdy_.push_back(M.off[jp] + dn[jp]);
                ++rel;
            }
            int op = rdy_.back();
            rdy_.pop_back();
            if (fin[op]) continue;
            int s0 = fs[op] ? 0 : en[op - 1];
            int p = mpp[op];
            if (p >= 0 && fin[p] && en[p] > s0) s0 = en[p];
            en[op] = s0 + ptp[op];
            fin[op] = 1;
            ++dn[jo[op]];
            ++nd;
            if (!ls[op]) { int x = op + 1; if (!fin[x] && --dg[x] == 0) rdy_.push_back(x); }
            int y = msp[op];
            if (y >= 0 && !fin[y] && --dg[y] == 0) rdy_.push_back(y);
        }
        int mk = 0;
        for (int o : lastOps_) if (en[o] > mk) mk = en[o];

        int a = std::max(0, lo - 1), b = std::min(L - 1, hi + 1);
        for (int i = a; i <= b; ++i) {
            int o = mo[i];
            mp_[o] = i > 0 ? mo[i - 1] : -1;
            ms_[o] = i + 1 < L ? mo[i + 1] : -1;
        }
        double sq = 0.0, od = (double)rel;
        double obj = (double)mk + M.penalty * (sq + od);
        return obj - cache_obj_;
    }

    double deltaRaw(const Sol& s, const Move& mv) {
        if (clean_) {
            double d;
            {
                int mach = mv[0], f = mv[1], t = mv[2];
                if (mach >= 0 && mach < M.m) {
                    int L = (int)mop_[mach].size();
                    if (f >= 0 && f < L && t >= 0 && t < L && f != t && quickExact(mach, f, t, d)) return d;
                }
            }
            int r = incr(mv, d);
            if (r == 1) return d;
            if (r == 3) return cycObj(mv);
            if (r == 2 && fast(s, mv, d)) return d;
        }
        return M.objective(apply(s, mv)) - cache_obj_;
    }

    void prepare(const Sol& s) {
        has_ = true;
        tails_ok_ = false;
        clean_ = false;
        bumpSol();
        if (cache_.size() != s.size()) cache_.resize(s.size());
        for (size_t r = 0; r < s.size(); ++r) cache_[r].assign(s[r].begin(), s[r].end());
        if (!((int)s.size() == M.m && M.m > 0)) { cache_obj_ = M.objective(s); return; }
        int N = M.n_ops, Mm = M.m, Nn = M.n;
        std::fill(mp_.begin(), mp_.end(), -1);
        std::fill(ms_.begin(), ms_.end(), -1);
        std::fill(mpos_.begin(), mpos_.end(), -1);
        if (++ostamp_ == 0) { std::fill(ost_.begin(), ost_.end(), 0); ostamp_ = 1; }
        unsigned os = ostamp_;
        mop_.resize(Mm);
        int* mpp = mp_.data();
        int* msp = ms_.data();
        int* mposp = mpos_.data();
        unsigned* osp = ost_.data();
        const int* oi = opIdx_.data();
        bool ok = true;
        for (int mm = 0; mm < Mm && ok; ++mm) {
            const auto& seq = s[mm];
            int L = (int)seq.size();
            if (L != mcnt_[mm]) { ok = false; break; }
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
        }
        if (!ok) { cache_obj_ = M.objective(s); return; }
        int* dg = deg_.data();
        int* Tp = T_.data();
        int* pp = pos_.data();
        int* bp = oend_.data();
        const int* ptp = pt_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        int cnt = 0;
        for (int op = 0; op < N; ++op) {
            int d = (!fs[op]) + (mpp[op] >= 0);
            dg[op] = d;
            if (d == 0) Tp[cnt++] = op;
        }
        int h = 0;
        while (h < cnt) {
            int v = Tp[h];
            pp[v] = h;
            ++h;
            int r = fs[v] ? 0 : bp[v - 1];
            int p = mpp[v];
            if (p >= 0 && bp[p] > r) r = bp[p];
            bp[v] = r + ptp[v];
            if (!ls[v] && --dg[v + 1] == 0) Tp[cnt++] = v + 1;
            int m2 = msp[v];
            if (m2 >= 0 && --dg[m2] == 0) Tp[cnt++] = m2;
        }
        if (cnt != N) { cache_obj_ = M.objective(s); return; }
        int C = 0;
        for (int o : lastOps_) if (bp[o] > C) C = bp[o];
        int cc = 0;
        for (int o : lastOps_) if (bp[o] == C) ++cc;
        mk_ = C; cntC_ = cc;
        cache_obj_ = (double)C;
        clean_ = true;
    }

    void computeTails() {
        int N = M.n_ops;
        const int* Tp = T_.data();
        const int* ptp = pt_.data();
        const int* msp = ms_.data();
        const char* ls = last_.data();
        int* tl = tl_.data();
        const int* P = pos_.data();
        const int* mpp = mp_.data();
        const int* oe = oend_.data();
        const char* fs = first_.data();
        int* bm = bmx_.data();
        Rec* rc = rec_.data();
        for (int t = N - 1; t >= 0; --t) {
            int o = Tp[t];
            int q = 0;
            if (!ls[o]) q = ptp[o + 1] + tl[o + 1];
            int y = msp[o];
            if (y >= 0) { int v = ptp[y] + tl[y]; if (v > q) q = v; }
            tl[o] = q;
            int h = oe[o] + q;
            Rec& R = rc[t];
            R.th = h;
            R.jp = fs[o] ? -1 : P[o - 1];
            int p = mpp[o];
            R.mp = p >= 0 ? P[p] : -1;
            R.pt = ptp[o];
            int bk = t >> 4;
            if (t == N - 1 || (t & 15) == 15) bm[bk] = h;
            else if (h > bm[bk]) bm[bk] = h;
        }
        {
            int* ot = oeT_.data();
            int* po = preOe_.data();
            int mx = 0;
            for (int k = 0; k < N; ++k) { po[k] = mx; int e = oe[Tp[k]]; ot[k] = e; if (e > mx) mx = e; }
            po[N] = mx;
        }
        tails_ok_ = true;
    }

    bool reach(int x, int y) {
        if (x < 0 || y < 0) return false;
        if (x == y) return true;
        const int* P = pos_.data();
        const int* oe = oend_.data();
        const int* tl = tl_.data();
        const int* msp = ms_.data();
        const char* ls = last_.data();
        int lim = oe[y] - pt_[y], py = P[y];
        if (P[x] >= py || oe[x] > lim) return false;
        const bool tk = tails_ok_;
        const int need = tk ? pt_[y] + tl[y] : 0;
        if (tk && tl[x] < need) return false;
        if (++vst_ == 0) { std::fill(vis_.begin(), vis_.end(), 0); vst_ = 1; }
        unsigned st = vst_;
        unsigned* vs = vis_.data();
        stk_.clear();
        vs[x] = st; stk_.push_back(x);
        while (!stk_.empty()) {
            int w = stk_.back(); stk_.pop_back();
            int cs[2] = {ls[w] ? -1 : w + 1, msp[w]};
            for (int c : cs) {
                if (c < 0) continue;
                if (c == y) return true;
                if (vs[c] != st && P[c] < py && oe[c] <= lim && (!tk || tl[c] >= need)) { vs[c] = st; stk_.push_back(c); }
            }
        }
        return false;
    }

    inline int newAt(int i) const {
        const auto& mo = *cmo_;
        if (i == ct_) return mo[cf_];
        return cf_ < ct_ ? mo[i + 1] : mo[i - 1];
    }
    inline int newIdx(int k) const {
        if (k == cf_) return ct_;
        return cf_ < ct_ ? k - 1 : k + 1;
    }
    inline int nmp(int v) const {
        if (machOf_[v] != cm_) return mp_[v];
        int k = mpos_[v];
        if (k < 0) return mp_[v];
        if (k < clo_ || k > chi_) {
            if (k == chi_ + 1) return newAt(chi_);
            return mp_[v];
        }
        int ni = newIdx(k);
        return ni > clo_ ? newAt(ni - 1) : (clo_ > 0 ? (*cmo_)[clo_ - 1] : -1);
    }
    inline int nms(int v) const {
        if (machOf_[v] != cm_) return ms_[v];
        int k = mpos_[v];
        if (k < 0) return ms_[v];
        if (k < clo_ || k > chi_) {
            if (k == clo_ - 1) return newAt(clo_);
            return ms_[v];
        }
        int ni = newIdx(k);
        return ni < chi_ ? newAt(ni + 1) : (chi_ + 1 < cL_ ? (*cmo_)[chi_ + 1] : -1);
    }

    void bumpStamp() {
        if (++cst_ == 0) {
            std::fill(chg_.begin(), chg_.end(), 0);
            std::fill(inq_.begin(), inq_.end(), 0);
            std::fill(cgK_.begin(), cgK_.end(), 0);
            std::fill(exK_.begin(), exK_.end(), 0);
            cst_ = 1;
        }
    }

    // 1: exact delta in d; 0: needs full objective; 2: fall back to fast()
    int incr(const Move& mv, double& d) {
        int mach = mv[0], f = mv[1], t = mv[2];
        if (mach < 0 || mach >= M.m) return 0;
        const auto& mo = mop_[mach];
        int L = (int)mo.size();
        if (f < 0 || f >= L || t < 0 || t >= L) return 0;
        if (f == t) { d = 0.0; return 1; }
        int u = mo[f];
        bool cyc = f < t ? reach(last_[u] ? -1 : u + 1, mo[t]) : reach(mo[t], first_[u] ? -1 : u - 1);
        if (cyc) return 3;
        cmo_ = &mo; cm_ = mach; cf_ = f; ct_ = t; cL_ = L;
        clo_ = std::min(f, t); chi_ = std::max(f, t);
        int ptt = pos_[mo[t]];
        bool orderOk = f < t ? (last_[u] || pos_[u + 1] > ptt) : (first_[u] || pos_[u - 1] < ptt);
        if (orderOk && scanFast(u, f, t, mo, L, ptt, d)) return 1;
        return heapIncr(u, d);
    }

    inline void restoreAt(const std::vector<int>& mo, int L, int i) {
        if (i < 0 || i >= L) return;
        int o = mo[i];
        mp_[o] = i > 0 ? mo[i - 1] : -1;
        ms_[o] = i + 1 < L ? mo[i + 1] : -1;
    }

    bool scanFast(int u, int f, int t, const std::vector<int>& mo, int L, int ptt, double& d) {
        bumpStamp();
        unsigned st = cst_;
        int* mpp = mp_.data();
        int* msp = ms_.data();
        const int* mop = mo.data();
        // patch machine arcs (only O(1) arcs change)
        int s1, s2;  // nodes whose machine predecessor changed (besides u)
        if (f < t) {
            int a = mop[f + 1];
            mpp[a] = f > 0 ? mop[f - 1] : -1;
            if (f > 0) msp[mop[f - 1]] = a;
            msp[mop[t]] = u;
            mpp[u] = mop[t];
            msp[u] = t + 1 < L ? mop[t + 1] : -1;
            if (t + 1 < L) mpp[mop[t + 1]] = u;
            s1 = a; s2 = t + 1 < L ? mop[t + 1] : -1;
        } else {
            msp[mop[f - 1]] = f + 1 < L ? mop[f + 1] : -1;
            if (f + 1 < L) mpp[mop[f + 1]] = mop[f - 1];
            mpp[mop[t]] = u;
            msp[u] = mop[t];
            mpp[u] = t > 0 ? mop[t - 1] : -1;
            if (t > 0) msp[mop[t - 1]] = u;
            s1 = mop[t]; s2 = f + 1 < L ? mop[f + 1] : -1;
        }
        unsigned long long* bt = bits_.data();
        const int* P = pos_.data();
        const int* Tp = T_.data();
        const int* ptp = pt_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        int* ne = nend_.data();
        const int* oe = oend_.data();
        unsigned* cg = chg_.data();
        const int C = mk_;
        int uKey = 2 * ptt + (f < t ? 2 : 0);
        int curKey = -1, minW = std::numeric_limits<int>::max(), maxW = -1, mxNew = 0, dec = 0;
        bool bad = false;
        auto push = [&](int v) {
            if (v < 0) return;
            int k = (v == u) ? uKey : 2 * P[v] + 1;
            if (k <= curKey) { bad = true; return; }
            int w = k >> 6;
            bt[w] |= 1ULL << (k & 63);
            if (w < minW) minW = w;
            if (w > maxW) maxW = w;
        };
        push(u); push(s1); push(s2);
        int w = minW;
        while (w <= maxW && !bad) {
            unsigned long long x = bt[w];
            if (!x) { ++w; continue; }
            int b = __builtin_ctzll(x);
            bt[w] = x & (x - 1);
            int key = (w << 6) | b;
            curKey = key;
            int v = (key & 1) ? Tp[key >> 1] : u;
            int r = 0;
            if (!fs[v]) { int jp = v - 1; r = cg[jp] == st ? ne[jp] : oe[jp]; }
            int p = mpp[v];
            if (p >= 0) { int e = cg[p] == st ? ne[p] : oe[p]; if (e > r) r = e; }
            int e = r + ptp[v];
            int cur = cg[v] == st ? ne[v] : oe[v];
            if (e != cur) {
                ne[v] = e; cg[v] = st;
                if (ls[v]) {
                    if (oe[v] == C && e < C) ++dec;
                    if (e > mxNew) mxNew = e;
                } else push(v + 1);
                push(msp[v]);
            }
        }
        restoreAt(mo, L, f - 1); restoreAt(mo, L, f); restoreAt(mo, L, f + 1);
        restoreAt(mo, L, t - 1); restoreAt(mo, L, t); restoreAt(mo, L, t + 1);
        if (bad) {
            for (int q = minW; q <= maxW; ++q) bt[q] = 0ULL;
            return false;
        }
        int mk;
        if (dec < cntC_) mk = mxNew > C ? mxNew : C;
        else {
            mk = 0;
            for (int o : lastOps_) {
                int e = cg[o] == st ? ne[o] : oe[o];
                if (e > mk) mk = e;
            }
        }
        d = (double)mk - cache_obj_;
        return true;
    }

    int heapIncr(int u, double& d) {
        const auto& mo = *cmo_;
        int f = cf_, t = ct_, L = cL_;
        bumpStamp();
        unsigned st = cst_;
        long long ukey = 2LL * pos_[mo[t]] + (f < t ? 1 : -1);
        heap_.clear();
        auto push = [&](int v) {
            if (v >= 0 && inq_[v] != st) {
                inq_[v] = st;
                long long k = (v == u) ? ukey : 2LL * pos_[v];
                heap_.push_back(((unsigned long long)(k + 1) << 32) | (unsigned)v);
                std::push_heap(heap_.begin(), heap_.end(), std::greater<unsigned long long>());
            }
        };
        for (int i = clo_; i <= chi_; ++i) push(mo[i]);
        if (chi_ + 1 < L) push(mo[chi_ + 1]);
        long long guard = 8LL * M.n_ops + 100;
        while (!heap_.empty()) {
            if (--guard < 0) return 2;
            std::pop_heap(heap_.begin(), heap_.end(), std::greater<unsigned long long>());
            int v = (int)(unsigned)(heap_.back() & 0xffffffffULL);
            heap_.pop_back();
            inq_[v] = 0;
            int r = 0;
            if (!first_[v]) { int jp = v - 1; r = chg_[jp] == st ? nend_[jp] : oend_[jp]; }
            int p = nmp(v);
            if (p >= 0) { int e = chg_[p] == st ? nend_[p] : oend_[p]; if (e > r) r = e; }
            int e = r + pt_[v];
            int cur = chg_[v] == st ? nend_[v] : oend_[v];
            if (e != cur) {
                nend_[v] = e; chg_[v] = st;
                if (!last_[v]) push(v + 1);
                push(nms(v));
            }
        }
        int mk = 0;
        for (int o : lastOps_) {
            int e = chg_[o] == st ? nend_[o] : oend_[o];
            if (e > mk) mk = e;
        }
        d = (double)mk - cache_obj_;
        return 1;
    }

    bool fast(const Sol& s, const Move& mv, double& d) {
        int mach = mv[0], f = mv[1], t = mv[2];
        if (mach < 0 || mach >= M.m) return false;
        const auto& mo = mop_[mach];
        int L = (int)mo.size();
        if (L != (int)s[mach].size()) return false;
        if (f < 0 || f >= L || t < 0 || t >= L) return false;
        if (f == t) { d = 0.0; return true; }
        int lo = std::min(f, t), hi = std::max(f, t);
        auto nA = [&](int i) -> int {
            if (i == t) return mo[f];
            return f < t ? mo[i + 1] : mo[i - 1];
        };
        for (int i = lo; i <= hi; ++i) {
            int o = nA(i);
            mp_[o] = i > lo ? nA(i - 1) : (lo > 0 ? mo[lo - 1] : -1);
            ms_[o] = i < hi ? nA(i + 1) : (hi + 1 < L ? mo[hi + 1] : -1);
        }
        if (lo > 0) ms_[mo[lo - 1]] = nA(lo);
        if (hi + 1 < L) mp_[mo[hi + 1]] = nA(hi);

        int st = ++stamp_;
        stk_.clear(); lst_.clear();
        for (int i = lo; i <= hi; ++i) { int o = mo[i]; mark_[o] = st; stk_.push_back(o); }
        while (!stk_.empty()) {
            int o = stk_.back(); stk_.pop_back();
            lst_.push_back(o);
            if (!last_[o]) { int x = o + 1; if (mark_[x] != st) { mark_[x] = st; stk_.push_back(x); } }
            int y = ms_[o];
            if (y >= 0 && mark_[y] != st) { mark_[y] = st; stk_.push_back(y); }
        }
        q_.clear();
        for (int o : lst_) {
            int dg = 0;
            if (!first_[o] && mark_[o - 1] == st) ++dg;
            int p = mp_[o];
            if (p >= 0 && mark_[p] == st) ++dg;
            deg_[o] = dg;
            if (dg == 0) q_.push_back(o);
        }
        size_t qi = 0;
        while (qi < q_.size()) {
            int o = q_[qi++];
            int r = 0;
            if (!first_[o]) r = (mark_[o - 1] == st) ? nend_[o - 1] : oend_[o - 1];
            int p = mp_[o];
            if (p >= 0) { int e = (mark_[p] == st) ? nend_[p] : oend_[p]; if (e > r) r = e; }
            nend_[o] = r + pt_[o];
            if (!last_[o]) { int x = o + 1; if (--deg_[x] == 0) q_.push_back(x); }
            int y = ms_[o];
            if (y >= 0 && mark_[y] == st && --deg_[y] == 0) q_.push_back(y);
        }
        bool ok = (q_.size() == lst_.size());
        int a = std::max(0, lo - 1), b = std::min(L - 1, hi + 1);
        for (int i = a; i <= b; ++i) {
            int o = mo[i];
            mp_[o] = i > 0 ? mo[i - 1] : -1;
            ms_[o] = i + 1 < L ? mo[i + 1] : -1;
        }
        if (!ok) return false;
        int mk = 0;
        for (int o : lastOps_) {
            int e = (mark_[o] == st) ? nend_[o] : oend_[o];
            if (e > mk) mk = e;
        }
        d = (double)mk - cache_obj_;
        return true;
    }

    void criticalFast() {
        path.clear();
        int mk = (int)cache_obj_;
        int cur = -1;
        for (int op : lastOps_) if (oend_[op] == mk) { cur = op; break; }
        int guard = M.n_ops + 1;
        while (cur >= 0 && guard-- > 0) {
            int p = mpos_[cur];
            if (p < 0) break;
            path.push_back({machOf_[cur], p});
            int st = oend_[cur] - pt_[cur];
            if (st == 0) break;
            int nx = -1;
            if (p > 0) { int o2 = mp_[cur]; if (o2 >= 0 && oend_[o2] == st) nx = o2; }
            if (nx < 0 && !first_[cur] && oend_[cur - 1] == st) nx = cur - 1;
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
    int ms = (int)params.get("max_shift", 60);
    return std::make_unique<CriticalBlockInsertion>(model, std::max(2, ms));
}
