// COMPONENT: {"name": "critical_block_end_insertion", "slot": "neighborhood", "params": {"max_shift": {"type": "int", "range": [2, 60]}}}
class CriticalBlockInsertion : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    CriticalBlockInsertion(const JobShop& md, int ms) : M(md), max_shift(ms) {
        int N = M.n_ops;
        pt_.assign(N, 0); first_.assign(N, 0); last_.assign(N, 0);
        for (int j = 0; j < M.n; ++j)
            for (int k = 0; k < (int)M.routes[j].size(); ++k) {
                int op = M.off[j] + k;
                pt_[op] = M.routes[j][k].second;
                first_[op] = (k == 0);
                last_[op] = (k + 1 == (int)M.routes[j].size());
            }
        mp_.assign(N, -1); ms_.assign(N, -1); oend_.assign(N, 0); nend_.assign(N, 0); mark_.assign(N, 0);
        deg_.assign(N, 0);
        stk_.reserve(N); lst_.reserve(N); q_.reserve(N);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        int rel = critical(s);
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
            if (fast(s, mv, d)) return d;
        }
        return M.objective(apply(s, mv)) - cache_obj_;
    }
    Move tabu_key(const Move& mv) override { return Move{mv[0], mv[2], mv[1], 0, 0, 0}; }

private:
    const JobShop& M;
    int max_shift;
    std::vector<int> start, posOf;
    std::vector<std::pair<int, int>> path;
    Sol cache_;
    double cache_obj_ = 0;
    bool has_ = false, clean_ = false;

    std::vector<int> pt_, mp_, ms_, oend_, nend_, mark_, deg_, stk_, lst_, q_;
    std::vector<char> first_, last_;
    std::vector<std::vector<int>> mop_;
    int stamp_ = 0;

    void prepare(const Sol& s) {
        cache_ = s;
        has_ = true;
        double sq, od, mk;
        M.evaluate(s, sq, od, mk);
        cache_obj_ = mk + M.penalty * (sq + od);
        clean_ = (sq == 0 && od == 0 && (int)s.size() >= M.m);
        if (!clean_) return;
        const std::vector<int>& st = M.start_;
        for (int op = 0; op < M.n_ops; ++op) oend_[op] = st[op] + pt_[op];
        mop_.resize(M.m);
        for (int mm = 0; mm < M.m; ++mm) {
            const auto& seq = s[mm];
            int L = (int)seq.size();
            auto& mo = mop_[mm];
            mo.resize(L);
            for (int i = 0; i < L; ++i) mo[i] = M.off[seq[i]] + M.opk[seq[i]][mm];
            for (int i = 0; i < L; ++i) {
                mp_[mo[i]] = i > 0 ? mo[i - 1] : -1;
                ms_[mo[i]] = i + 1 < L ? mo[i + 1] : -1;
            }
        }
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
        auto newAt = [&](int i) -> int {
            if (i == t) return mo[f];
            return f < t ? mo[i + 1] : mo[i - 1];
        };
        // aplicar cambios de arcos de máquina
        for (int i = lo; i <= hi; ++i) {
            int o = newAt(i);
            mp_[o] = i > lo ? newAt(i - 1) : (lo > 0 ? mo[lo - 1] : -1);
            ms_[o] = i < hi ? newAt(i + 1) : (hi + 1 < L ? mo[hi + 1] : -1);
        }
        if (lo > 0) ms_[mo[lo - 1]] = newAt(lo);
        if (hi + 1 < L) mp_[mo[hi + 1]] = newAt(hi);

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
        // restaurar arcos
        int a = std::max(0, lo - 1), b = std::min(L - 1, hi + 1);
        for (int i = a; i <= b; ++i) {
            int o = mo[i];
            mp_[o] = i > 0 ? mo[i - 1] : -1;
            ms_[o] = i + 1 < L ? mo[i + 1] : -1;
        }
        if (!ok) return false;
        int mk = 0;
        for (int j = 0; j < M.n; ++j) {
            if (M.routes[j].empty()) continue;
            int o = M.off[j + 1] - 1;
            int e = (mark_[o] == st) ? nend_[o] : oend_[o];
            if (e > mk) mk = e;
        }
        d = (double)mk - cache_obj_;
        return true;
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
