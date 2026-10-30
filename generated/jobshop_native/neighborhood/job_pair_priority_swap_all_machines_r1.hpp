// COMPONENT: {"name": "job_pair_priority_swap_all_machines", "slot": "neighborhood", "params": {"restrict": {"type": "cat", "values": ["critical", "all"]}}}
class JobPairPrioritySwap : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    JobPairPrioritySwap(const JobShop& md, bool crit) : M(md), only_crit(crit) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = M.n;
        bool use_crit = false;
        if (only_crit) {
            int rel = critical_jobs(s);
            use_crit = (rel == 0);
            if (use_crit) {
                bool any = false;
                for (int j = 0; j < n; ++j) any |= (bool)isCrit[j];
                use_crit = any;
            }
        }
        for (int a = 0; a < n; ++a) {
            if (use_crit && !isCrit[a]) continue;
            for (int b = 0; b < n; ++b) {
                if (b == a) continue;
                if (use_crit) { if (isCrit[b] && b < a) continue; }
                else if (b < a) continue;
                bool share = false;
                for (int mm = 0; mm < M.m && !share; ++mm) share = M.opk[a][mm] >= 0 && M.opk[b][mm] >= 0;
                if (share) out.push_back(Move{std::min(a, b), std::max(a, b), 0, 0, 0, 0});
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
        if (!has_ || !(s == cache_)) { cache_ = s; cache_obj_ = M.objective(s); has_ = true; }
        return M.objective(apply(s, mv)) - cache_obj_;
    }

private:
    const JobShop& M;
    bool only_crit;
    std::vector<int> start, posOf;
    std::vector<char> isCrit;
    Sol cache_;
    double cache_obj_ = 0;
    bool has_ = false;

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
            // un trabajo es "crítico" si alguna operación suya está en un arco de máquina del camino
            if (nx >= 0 && M.job_of[nx] != j) { isCrit[j] = 1; isCrit[M.job_of[nx]] = 1; }
            cur = nx;
        }
        return rel;
    }
};

std::unique_ptr<hsf::Neighborhood<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<JobPairPrioritySwap>(model, params.text("restrict", "critical") == "critical");
}
