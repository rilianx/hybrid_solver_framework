// COMPONENT: {"name": "critical_path_adjacent_swap", "slot": "neighborhood", "params": {"block_ends_only": {"type": "int", "range": [0, 1]}}}
class CriticalAdjacentSwap : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    CriticalAdjacentSwap(const JobShop& md, bool ends) : M(md), ends_only(ends) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        int rel = critical(s);
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
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        std::swap(r[mv[0]][mv[1]], r[mv[0]][mv[1] + 1]);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        if (!has_ || !(s == cache_)) { cache_ = s; cache_obj_ = M.objective(s); has_ = true; }
        return M.objective(apply(s, mv)) - cache_obj_;
    }

private:
    const JobShop& M;
    bool ends_only;
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
    return std::make_unique<CriticalAdjacentSwap>(model, params.get("block_ends_only", 0) >= 0.5);
}
