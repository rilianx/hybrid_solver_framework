// COMPONENT: {"name": "critical_block_end_insertion", "slot": "neighborhood", "params": {"max_shift": {"type": "int", "range": [2, 60]}}}
class CriticalBlockInsertion : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    CriticalBlockInsertion(const JobShop& md, int ms) : M(md), max_shift(ms) {}

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
                    // extremos hacia el interior
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
        if (!has_ || !(s == cache_)) { cache_ = s; cache_obj_ = M.objective(s); has_ = true; }
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
    bool has_ = false;

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
