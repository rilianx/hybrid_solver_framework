// COMPONENT: {"name": "critical_path_adjacent_swap", "slot": "neighborhood", "params": {"block_ends_only": {"type": "int", "range": [0, 1]}}}
class CriticalAdjacentSwap : public hsf::Neighborhood<JobShop> {
public:
    using Sol = JobShop::Solution;
    CriticalAdjacentSwap(const JobShop& md, bool ends) : M(md), ends_only(ends) {
        int N = M.n_ops;
        pt.assign(N, 0); jpred.assign(N, -1);
        for (int j = 0; j < M.n; ++j)
            for (int k = 0; k < (int)M.routes[j].size(); ++k) {
                int op = M.off[j] + k;
                pt[op] = M.routes[j][k].second;
                jpred[op] = k > 0 ? op - 1 : -1;
            }
        mp.assign(N, -1); ms.assign(N, -1); bend.assign(N, 0); nend.assign(N, 0);
        pos.assign(N, 0); T.assign(N, 0); pmax.assign(N + 1, 0); indeg.assign(N, 0); mark.assign(N, 0);
        bstart.assign(N, 0);
    }

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
        if (!has_ || !(s == cache_)) prepare(s);
        if (!clean_) return M.objective(apply(s, mv)) - cache_obj_;
        int mm = mv[0], i = mv[1];
        const auto& row = s[mm];
        int a = M.off[row[i]] + M.opk[row[i]][mm];
        int b = M.off[row[i + 1]] + M.opk[row[i + 1]][mm];
        int ta = pos[a], tb = pos[b];
        if (++stamp_ == 0) { std::fill(mark.begin(), mark.end(), 0); stamp_ = 1; }
        unsigned st = stamp_;
        mark[a] = st;
        for (int t = ta + 1; t <= tb; ++t) {
            int v = T[t];
            int jp = jpred[v], m2 = mp[v];
            if ((jp >= 0 && mark[jp] == st) || (m2 >= 0 && mark[m2] == st)) mark[v] = st;
        }
        { int jb = jpred[b]; if (jb >= 0 && mark[jb] == st) return M.objective(apply(s, mv)) - cache_obj_; }
        int mx = pmax[ta];
        auto E = [&](int u) -> int { return pos[u] < ta ? bend[u] : nend[u]; };
        auto calc = [&](int v, int m2) {
            int sv = 0;
            int jp = jpred[v];
            if (jp >= 0) sv = E(jp);
            if (m2 >= 0) { int e = E(m2); if (e > sv) sv = e; }
            int e = sv + pt[v];
            nend[v] = e;
            if (e > mx) mx = e;
        };
        for (int t = ta + 1; t < tb; ++t) { int v = T[t]; if (mark[v] != st) calc(v, mp[v]); }
        calc(b, mp[a]);
        calc(a, b);
        for (int t = ta + 1; t < tb; ++t) { int v = T[t]; if (mark[v] == st) calc(v, mp[v]); }
        int q = ms[b];
        int N = M.n_ops;
        for (int t = tb + 1; t < N; ++t) { int v = T[t]; calc(v, v == q ? a : mp[v]); }
        return (double)mx - cache_obj_;
    }

private:
    const JobShop& M;
    bool ends_only;
    std::vector<int> start, posOf;
    std::vector<std::pair<int, int>> path;
    Sol cache_;
    double cache_obj_ = 0;
    bool has_ = false, clean_ = false;
    std::vector<int> pt, jpred, mp, ms, bend, nend, pos, T, pmax, indeg, bstart;
    std::vector<unsigned> mark;
    unsigned stamp_ = 0;

    void prepare(const Sol& s) {
        cache_ = s; has_ = true;
        cache_obj_ = M.objective(s);
        int mk;
        int rel = M.schedule(s, bstart, mk);
        int sq = M.sequence_errors(s);
        clean_ = (rel == 0 && sq == 0);
        if (!clean_) return;
        int N = M.n_ops;
        std::fill(mp.begin(), mp.end(), -1);
        std::fill(ms.begin(), ms.end(), -1);
        for (int mm = 0; mm < M.m; ++mm) {
            int prev = -1;
            for (int j : s[mm]) {
                int op = M.off[j] + M.opk[j][mm];
                if (prev >= 0) mp[op] = prev, ms[prev] = op;
                prev = op;
            }
        }
        int cnt = 0;
        for (int op = 0; op < N; ++op) {
            bend[op] = bstart[op] + pt[op];
            indeg[op] = (jpred[op] >= 0) + (mp[op] >= 0);
            if (indeg[op] == 0) T[cnt++] = op;
        }
        int h = 0;
        while (h < cnt) {
            int op = T[h++];
            int j = M.job_of[op];
            int nx = (op + 1 < M.off[j + 1]) ? op + 1 : -1;
            if (nx >= 0 && --indeg[nx] == 0) T[cnt++] = nx;
            int m2 = ms[op];
            if (m2 >= 0 && --indeg[m2] == 0) T[cnt++] = m2;
        }
        if (cnt != N) { clean_ = false; return; }
        pmax[0] = 0;
        for (int t = 0; t < N; ++t) {
            pos[T[t]] = t;
            pmax[t + 1] = std::max(pmax[t], bend[T[t]]);
        }
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
