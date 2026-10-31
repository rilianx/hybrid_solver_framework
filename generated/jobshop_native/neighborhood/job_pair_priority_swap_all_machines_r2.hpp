// COMPONENT: {"name": "job_pair_priority_swap_all_machines", "slot": "neighborhood", "params": {"restrict": {"type": "cat", "values": ["critical", "all"]}}}
class JobPairPrioritySwap : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    JobPairPrioritySwap(const JobShop& md, bool crit) : M(md), only_crit(crit) {
        int N = M.n_ops, n = M.n, m = M.m;
        pt_.assign(std::max(N, 1), 0); first_.assign(std::max(N, 1), 0); last_.assign(std::max(N, 1), 0);
        for (int j = 0; j < n; ++j)
            for (int k = 0; k < (int)M.routes[j].size(); ++k) {
                int op = M.off[j] + k;
                pt_[op] = M.routes[j][k].second;
                first_[op] = (k == 0);
                last_[op] = (k + 1 == (int)M.routes[j].size());
            }
        for (int j = 0; j < n; ++j)
            if (!M.routes[j].empty()) lastOps_.push_back(M.off[j + 1] - 1);
        mcnt_.assign(std::max(m, 0), 0);
        opIdx_.assign((size_t)std::max(n, 0) * (size_t)std::max(m, 0), -1);
        for (int j = 0; j < n; ++j)
            for (int mm = 0; mm < m; ++mm)
                if (M.opk[j][mm] >= 0) { mcnt_[mm]++; opIdx_[(size_t)j * m + mm] = M.off[j] + M.opk[j][mm]; }
        share_.assign((size_t)std::max(n, 0) * (size_t)std::max(n, 0), 0);
        for (int a = 0; a < n; ++a)
            for (int b = 0; b < n; ++b) {
                bool sh = false;
                for (int mm = 0; mm < m && !sh; ++mm) sh = M.opk[a][mm] >= 0 && M.opk[b][mm] >= 0;
                share_[(size_t)a * n + b] = sh;
            }
        int NN = std::max(N, 1);
        mp_.assign(NN, -1); ms_.assign(NN, -1); mpos_.assign(NN, -1); oend_.assign(NN, 0); nend_.assign(NN, 0);
        pos_.assign(NN, 0); T_.assign(NN, 0); deg_.assign(NN, 0); q_.assign(NN, 0); ost_.assign(NN, 0);
        sdeg_.assign(NN, 0); send_.assign(NN, 0); sfin_.assign(NN, 0);
        sdone_.assign(std::max(n, 1), 0); jlen_.assign(std::max(n, 1), 0);
        for (int j = 0; j < n; ++j) jlen_[j] = (int)M.routes[j].size();
        rdy_.reserve(2 * NN + 8);
        shm_.assign(std::max(m, 1), 0); slo_.assign(std::max(m, 1), 0); shi_.assign(std::max(m, 1), 0);
        long long nn = (long long)n * n;
        memoOn_ = nn > 0 && nn <= 4000000LL;
        if (memoOn_) { memoS_.assign((size_t)nn, 0); memoV_.assign((size_t)nn, 0.0); }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = M.n;
        bool use_crit = false;
        if (only_crit) {
            if (!has_ || !(s == cache_)) prepare(s);
            int rel;
            if (clean_) { criticalFastJobs(); rel = 0; }
            else rel = critical_jobs(s);
            use_crit = (rel == 0);
            if (use_crit) {
                bool any = false;
                for (int j = 0; j < n; ++j) any |= (bool)isCrit[j];
                use_crit = any;
            }
        }
        const char* sh = share_.data();
        for (int a = 0; a < n; ++a) {
            if (use_crit && !isCrit[a]) continue;
            const char* row = sh + (size_t)a * n;
            for (int b = 0; b < n; ++b) {
                if (b == a) continue;
                if (use_crit) { if (isCrit[b] && b < a) continue; }
                else if (b < a) continue;
                if (row[b]) out.push_back(Move{std::min(a, b), std::max(a, b), 0, 0, 0, 0});
            }
        }
        if (out.empty())
            for (int mm = 0; mm < (int)s.size(); ++mm)
                if (s[mm].size() >= 2) { out.push_back(Move{s[mm][0], s[mm][1], 0, 0, 0, 0}); break; }
        if (out.empty() && n >= 2) out.push_back(Move{0, 1, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        int a = mv[0], b = mv[1];
        for (auto& v : r) {
            int pa = -1, pb = -1;
            for (int i = 0; i < (int)v.size(); ++i) {
                if (v[i] == a && pa < 0) pa = i;
                else if (v[i] == b && pb < 0) pb = i;
            }
            if (pa >= 0 && pb >= 0) std::swap(v[pa], v[pb]);
        }
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        if (!has_ || !(s == cache_)) prepare(s);
        if (!clean_) return M.objective(apply(s, mv)) - cache_obj_;
        int a = mv[0], b = mv[1], n = M.n;
        if (a == b || a < 0 || a >= n || b < 0 || b >= n) return 0.0;
        if (memoOn_) {
            size_t idx = (size_t)std::min(a, b) * n + std::max(a, b);
            if (memoS_[idx] == solStamp_) return memoV_[idx];
            double r = deltaSwap(a, b);
            memoS_[idx] = solStamp_; memoV_[idx] = r;
            return r;
        }
        return deltaSwap(a, b);
    }

private:
    const JobShop& M;
    bool only_crit;
    std::vector<int> start, posOf;
    std::vector<char> isCrit;
    Sol cache_;
    double cache_obj_ = 0;
    bool has_ = false, clean_ = false, memoOn_ = false;
    int mk_ = 0;
    std::vector<int> pt_, lastOps_, mcnt_, opIdx_, mp_, ms_, mpos_, oend_, nend_, pos_, T_, deg_, q_;
    std::vector<int> sdeg_, send_, sdone_, jlen_, rdy_, shm_, slo_, shi_;
    std::vector<char> first_, last_, share_, sfin_;
    std::vector<unsigned> ost_, memoS_;
    std::vector<double> memoV_;
    std::vector<std::vector<int>> mop_;
    unsigned solStamp_ = 0, ostamp_ = 0;

    void prepare(const Sol& s) {
        has_ = true;
        clean_ = false;
        if (++solStamp_ == 0) { std::fill(memoS_.begin(), memoS_.end(), 0); solStamp_ = 1; }
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
                int o = opIdx_[(size_t)j * Mm + mm];
                if (o < 0 || ost_[o] == os) { ok = false; break; }
                ost_[o] = os;
                mo[i] = o;
                mp_[o] = prev;
                if (prev >= 0) ms_[prev] = o;
                mpos_[o] = i;
                prev = o;
            }
        }
        if (!ok) { cache_obj_ = M.objective(s); return; }
        int* dg = deg_.data();
        int* Tp = T_.data();
        int* pp = pos_.data();
        int* bp = oend_.data();
        const int* ptp = pt_.data();
        const int* mpp = mp_.data();
        const int* msp = ms_.data();
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
        mk_ = C;
        cache_obj_ = (double)C;
        clean_ = true;
    }

    inline void relink(const std::vector<int>& mo, int L, int c) {
        for (int i = c - 1; i <= c + 1; ++i) {
            if (i < 0 || i >= L) continue;
            int o = mo[i];
            mp_[o] = i > 0 ? mo[i - 1] : -1;
            ms_[o] = i + 1 < L ? mo[i + 1] : -1;
        }
    }

    double deltaSwap(int a, int b) {
        int Mm = M.m, N = M.n_ops;
        int nsh = 0, kmin = N;
        const int* P = pos_.data();
        for (int mm = 0; mm < Mm; ++mm) {
            int oa = opIdx_[(size_t)a * Mm + mm], ob = opIdx_[(size_t)b * Mm + mm];
            if (oa < 0 || ob < 0) continue;
            int ia = mpos_[oa], ib = mpos_[ob];
            int lo = std::min(ia, ib), hi = std::max(ia, ib);
            auto& mo = mop_[mm];
            int L = (int)mo.size();
            std::swap(mo[lo], mo[hi]);
            shm_[nsh] = mm; slo_[nsh] = lo; shi_[nsh] = hi; ++nsh;
            relink(mo, L, lo); relink(mo, L, hi);
            int c;
            c = P[mo[lo]]; if (c < kmin) kmin = c;
            c = P[mo[hi]]; if (c < kmin) kmin = c;
            if (lo + 1 < L) { c = P[mo[lo + 1]]; if (c < kmin) kmin = c; }
            if (hi + 1 < L) { c = P[mo[hi + 1]]; if (c < kmin) kmin = c; }
        }
        if (nsh == 0) return 0.0;
        const int* Tp = T_.data();
        const int* ptp = pt_.data();
        const int* mpp = mp_.data();
        const int* msp = ms_.data();
        const int* oe = oend_.data();
        const char* fs = first_.data();
        const char* ls = last_.data();
        int* dg = deg_.data();
        int* ne = nend_.data();
        int* qq = q_.data();
        int qt = 0;
        for (int t = kmin; t < N; ++t) {
            int v = Tp[t];
            int d = 0;
            if (!fs[v] && P[v - 1] >= kmin) ++d;
            int p = mpp[v];
            if (p >= 0 && P[p] >= kmin) ++d;
            dg[v] = d;
            if (d == 0) qq[qt++] = v;
        }
        int qh = 0;
        while (qh < qt) {
            int v = qq[qh++];
            int r = 0;
            if (!fs[v]) { int jp = v - 1; r = P[jp] >= kmin ? ne[jp] : oe[jp]; }
            int p = mpp[v];
            if (p >= 0) { int e = P[p] >= kmin ? ne[p] : oe[p]; if (e > r) r = e; }
            ne[v] = r + ptp[v];
            if (!ls[v]) { int x = v + 1; if (P[x] >= kmin && --dg[x] == 0) qq[qt++] = x; }
            int y = msp[v];
            if (y >= 0 && P[y] >= kmin && --dg[y] == 0) qq[qt++] = y;
        }
        double res;
        if (qt == N - kmin) {
            int mk = 0;
            for (int o : lastOps_) { int e = P[o] >= kmin ? ne[o] : oe[o]; if (e > mk) mk = e; }
            res = (double)mk - cache_obj_;
        } else {
            res = exactObj() - cache_obj_;
        }
        for (int i = nsh - 1; i >= 0; --i) {
            auto& mo = mop_[shm_[i]];
            int L = (int)mo.size();
            std::swap(mo[slo_[i]], mo[shi_[i]]);
            relink(mo, L, slo_[i]); relink(mo, L, shi_[i]);
        }
        return res;
    }

    // emula M.schedule exactamente sobre los arcos actuales (mp_/ms_)
    double exactObj() {
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
        double sq = 0.0, od = (double)rel;
        return (double)mk + M.penalty * (sq + od);
    }

    void criticalFastJobs() {
        isCrit.assign(M.n, 0);
        int mk = mk_;
        int cur = -1;
        for (int op : lastOps_) if (oend_[op] == mk) { cur = op; break; }
        int guard = M.n_ops + 1;
        const int* jo = M.job_of.data();
        while (cur >= 0 && guard-- > 0) {
            int p = mpos_[cur];
            if (p < 0) break;
            int st = oend_[cur] - pt_[cur];
            int nx = -1;
            if (st > 0) {
                if (p > 0) { int o2 = mp_[cur]; if (o2 >= 0 && oend_[o2] == st) nx = o2; }
                if (nx < 0 && !first_[cur] && oend_[cur - 1] == st) nx = cur - 1;
            }
            if (nx >= 0 && jo[nx] != jo[cur]) { isCrit[jo[cur]] = 1; isCrit[jo[nx]] = 1; }
            cur = nx;
        }
    }

    int opid(int j, int mm) const {
        if (j < 0 || j >= M.n || M.opk[j][mm] < 0) return -1;
        return M.off[j] + M.opk[j][mm];
    }
    int endt(int op) const { int j = M.job_of[op]; return start[op] + M.routes[j][op - M.off[j]].second; }
    int critical_jobs(const Sol& s) {
        int mk;
        int rel = M.schedule(s, start, mk);
        isCrit.assign(M.n, 0);
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
            int st = start[cur];
            int nx = -1;
            if (st > 0) {
                if (p > 0) { int o2 = opid(s[mach][p - 1], mach); if (o2 >= 0 && endt(o2) == st) nx = o2; }
                if (nx < 0 && k > 0 && endt(cur - 1) == st) nx = cur - 1;
            }
            if (nx >= 0 && M.job_of[nx] != j) { isCrit[j] = 1; isCrit[M.job_of[nx]] = 1; }
            cur = nx;
        }
        return rel;
    }
};

std::unique_ptr<hsf::Neighborhood<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<JobPairPrioritySwap>(model, params.text("restrict", "critical") == "critical");
}
