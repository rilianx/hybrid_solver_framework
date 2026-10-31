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
        jst_.assign(std::max(M.n, 0), 0);
        mp_.assign(N, -1); ms_.assign(N, -1); oend_.assign(N, 0); nend_.assign(N, 0); mark_.assign(N, 0);
        deg_.assign(N, 0); tl_.assign(N, 0); seg_.assign(N + 1, 0);
        mpos_.assign(N, -1); pos_.assign(N, 0); T_.assign(N, 0);
        chg_.assign(N, 0); inq_.assign(N, 0); vis_.assign(N, 0);
        stk_.reserve(N); lst_.reserve(N); q_.reserve(N); heap_.reserve(N + 8);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (!has_ || !(s == cache_)) prepare(s);
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
        Sol r = s;
        auto& v = r[mv[0]];
        int x = v[mv[1]];
        v.erase(v.begin() + mv[1]);
        v.insert(v.begin() + mv[2], x);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        if (!has_ || !(s == cache_)) prepare(s);
        if (clean_) {
            double d;
            int r = incr(mv, d);
            if (r == 1) return d;
            if (r == 2 && fast(s, mv, d)) return d;
        }
        return M.objective(apply(s, mv)) - cache_obj_;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& mv) override {
        if (!has_ || !(s == cache_)) prepare(s);
        if (!clean_) return delta(s, mv);
        int mach = mv[0], f = mv[1], t = mv[2];
        if (mach < 0 || mach >= M.m) return delta(s, mv);
        const auto& mo = mop_[mach];
        int L = (int)mo.size();
        if (L != (int)s[mach].size() || f < 0 || f >= L || t < 0 || t >= L) return delta(s, mv);
        if (f == t) return 0.0;
        if (!tails_ok_) computeTails();
        int lo = std::min(f, t), hi = std::max(f, t);
        auto newAt = [&](int i) -> int {
            if (i == t) return mo[f];
            return f < t ? mo[i + 1] : mo[i - 1];
        };
        int ne = lo > 0 ? oend_[mo[lo - 1]] : 0;
        for (int i = lo; i <= hi; ++i) {
            int o = newAt(i);
            int r = first_[o] ? 0 : oend_[o - 1];
            if (ne > r) r = ne;
            ne = r + pt_[o];
            seg_[i - lo] = ne;
        }
        int qn = (hi + 1 < L) ? pt_[mo[hi + 1]] + tl_[mo[hi + 1]] : 0;
        int best = 0;
        for (int i = hi; i >= lo; --i) {
            int o = newAt(i);
            int q = last_[o] ? 0 : pt_[o + 1] + tl_[o + 1];
            if (qn > q) q = qn;
            int v = seg_[i - lo] + q;
            if (v > best) best = v;
            qn = pt_[o] + q;
        }
        return (double)best - cache_obj_;
    }
    Move tabu_key(const Move& mv) override { return Move{mv[0], mv[2], mv[1], 0, 0, 0}; }

private:
    const JobShop& M;
    int max_shift;
    std::vector<int> start, posOf;
    std::vector<std::pair<int, int>> path;
    Sol cache_;
    double cache_obj_ = 0;
    bool has_ = false, clean_ = false, tails_ok_ = false;

    std::vector<int> pt_, mp_, ms_, oend_, nend_, mark_, deg_, stk_, lst_, q_, tl_, seg_, lastOps_;
    std::vector<int> machOf_, mpos_, pos_, T_, mcnt_;
    std::vector<unsigned> chg_, inq_, vis_, jst_;
    std::vector<unsigned long long> heap_;
    std::vector<char> first_, last_;
    std::vector<std::vector<int>> mop_;
    int stamp_ = 0;
    unsigned cst_ = 0, vst_ = 0, jstamp_ = 0;
    // current move context
    const std::vector<int>* cmo_ = nullptr;
    int cm_ = 0, cf_ = 0, ct_ = 0, clo_ = 0, chi_ = 0, cL_ = 0;

    void prepare(const Sol& s) {
        has_ = true;
        tails_ok_ = false;
        clean_ = false;
        if (cache_.size() != s.size()) cache_.resize(s.size());
        for (size_t r = 0; r < s.size(); ++r) cache_[r].assign(s[r].begin(), s[r].end());
        bool ok = ((int)s.size() == M.m) && M.m > 0;
        if (ok) {
            for (int mm = 0; mm < M.m && ok; ++mm) {
                const auto& seq = s[mm];
                if ((int)seq.size() != mcnt_[mm]) { ok = false; break; }
                if (++jstamp_ == 0) { std::fill(jst_.begin(), jst_.end(), 0); jstamp_ = 1; }
                unsigned js = jstamp_;
                for (int j : seq) {
                    if (j < 0 || j >= M.n || M.opk[j][mm] < 0 || jst_[j] == js) { ok = false; break; }
                    jst_[j] = js;
                }
            }
        }
        if (!ok) { cache_obj_ = M.objective(s); return; }
        int N = M.n_ops;
        std::fill(mp_.begin(), mp_.end(), -1);
        std::fill(ms_.begin(), ms_.end(), -1);
        std::fill(mpos_.begin(), mpos_.end(), -1);
        mop_.resize(M.m);
        for (int mm = 0; mm < M.m; ++mm) {
            const auto& seq = s[mm];
            int L = (int)seq.size();
            auto& mo = mop_[mm];
            mo.resize(L);
            for (int i = 0; i < L; ++i) mo[i] = M.off[seq[i]] + M.opk[seq[i]][mm];
            for (int i = 0; i < L; ++i) {
                int o = mo[i];
                mp_[o] = i > 0 ? mo[i - 1] : -1;
                ms_[o] = i + 1 < L ? mo[i + 1] : -1;
                mpos_[o] = i;
            }
        }
        int cnt = 0;
        for (int op = 0; op < N; ++op) {
            deg_[op] = (!first_[op]) + (mp_[op] >= 0);
            if (deg_[op] == 0) T_[cnt++] = op;
        }
        int h = 0;
        while (h < cnt) {
            int op = T_[h++];
            if (!last_[op] && --deg_[op + 1] == 0) T_[cnt++] = op + 1;
            int m2 = ms_[op];
            if (m2 >= 0 && --deg_[m2] == 0) T_[cnt++] = m2;
        }
        if (cnt != N) { cache_obj_ = M.objective(s); return; }
        for (int t = 0; t < N; ++t) {
            int v = T_[t];
            pos_[v] = t;
            int r = first_[v] ? 0 : oend_[v - 1];
            int p = mp_[v];
            if (p >= 0 && oend_[p] > r) r = oend_[p];
            oend_[v] = r + pt_[v];
        }
        int C = 0;
        for (int o : lastOps_) if (oend_[o] > C) C = oend_[o];
        cache_obj_ = (double)C;
        clean_ = true;
    }

    void computeTails() {
        int N = M.n_ops;
        for (int t = N - 1; t >= 0; --t) {
            int o = T_[t];
            int q = 0;
            if (!last_[o]) q = pt_[o + 1] + tl_[o + 1];
            int y = ms_[o];
            if (y >= 0) { int v = pt_[y] + tl_[y]; if (v > q) q = v; }
            tl_[o] = q;
        }
        tails_ok_ = true;
    }

    // old-graph reachability x ~> y
    bool reach(int x, int y) {
        if (x < 0 || y < 0) return false;
        if (x == y) return true;
        int lim = oend_[y] - pt_[y], py = pos_[y];
        if (pos_[x] >= py || oend_[x] > lim) return false;
        if (++vst_ == 0) { std::fill(vis_.begin(), vis_.end(), 0); vst_ = 1; }
        unsigned st = vst_;
        stk_.clear();
        vis_[x] = st; stk_.push_back(x);
        while (!stk_.empty()) {
            int w = stk_.back(); stk_.pop_back();
            int cs[2] = {last_[w] ? -1 : w + 1, ms_[w]};
            for (int c : cs) {
                if (c < 0) continue;
                if (c == y) return true;
                if (vis_[c] != st && pos_[c] < py && oend_[c] <= lim) { vis_[c] = st; stk_.push_back(c); }
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
        if (cyc) return 0;
        cmo_ = &mo; cm_ = mach; cf_ = f; ct_ = t; cL_ = L;
        clo_ = std::min(f, t); chi_ = std::max(f, t);
        if (++cst_ == 0) {
            std::fill(chg_.begin(), chg_.end(), 0);
            std::fill(inq_.begin(), inq_.end(), 0);
            cst_ = 1;
        }
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
