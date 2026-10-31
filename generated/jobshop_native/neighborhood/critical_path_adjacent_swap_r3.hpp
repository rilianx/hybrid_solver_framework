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
        mp.assign(N, -1); ms.assign(N, -1); bend.assign(N, 0); nend.assign(N, 0); mpos.assign(N, 0);
        pos.assign(N, 0); T.assign(N, 0); indeg.assign(N, 0); mark.assign(N, 0); chg.assign(N, 0); inq.assign(N, 0);
        qq.assign(N, 0); fc.assign(N, 0); gc.assign(N, 0);
        jst.assign(std::max(M.n, 0), 0);
        heap.reserve(N + 4);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (!has_ || !(s == cache_)) prepare(s);
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
        const auto& mo = mop_[mm];
        int a = mo[i], b = mo[i + 1];
        int ta = pos[a];
        int jb = jpred[b];
        if (jb >= 0 && bend[jb] - pt[jb] >= bend[a] && pos[jb] > ta) {
            if (++stamp_ == 0) resetStamps();
            unsigned st = stamp_;
            mark[a] = st;
            int pj = pos[jb];
            for (int t = ta + 1; t <= pj; ++t) {
                int v = T[t];
                int jp = jpred[v], m2 = mp[v];
                if ((jp >= 0 && mark[jp] == st) || (m2 >= 0 && mark[m2] == st)) mark[v] = st;
            }
            if (mark[jb] == st) return M.objective(apply(s, mv)) - cache_obj_;
        }
        int C = mk_;
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
        if (L >= C) return (double)L - cache_obj_;
        unsigned long long thA = (bend[a] + qq[a] == C) ? fc[a] * gc[a] : 0ULL;
        unsigned long long thB = (bend[b] + qq[b] == C) ? fc[b] * gc[b] : 0ULL;
        unsigned long long both = (bend[a] == bend[b] - pt[b] && bend[b] + qq[b] == C) ? fc[a] * gc[b] : 0ULL;
        unsigned long long avoid = totC - thA - thB + both;
        if (avoid != 0ULL) return (double)C - cache_obj_;
        return fullDelta(a, b);
    }

private:
    const JobShop& M;
    bool ends_only;
    std::vector<int> start, posOf;
    std::vector<std::pair<int, int>> path;
    Sol cache_;
    double cache_obj_ = 0;
    int mk_ = 0;
    bool has_ = false, clean_ = false;
    std::vector<int> pt, jpred, jsucc, machOf, mp, ms, bend, nend, pos, T, indeg, mpos, lastOps, heap, qq, mcnt;
    std::vector<unsigned long long> fc, gc;
    unsigned long long totC = 0;
    std::vector<std::vector<int>> mop_;
    std::vector<unsigned> mark, chg, inq, jst;
    unsigned stamp_ = 0, jstamp_ = 0;

    void resetStamps() {
        std::fill(mark.begin(), mark.end(), 0);
        std::fill(chg.begin(), chg.end(), 0);
        std::fill(inq.begin(), inq.end(), 0);
        stamp_ = 1;
    }

    double fullDelta(int a, int b) {
        if (++stamp_ == 0) resetStamps();
        unsigned st = stamp_;
        int jb = jpred[b];
        int q = ms[b], ma = mp[a];
        auto E = [&](int u) -> int { return chg[u] == st ? nend[u] : bend[u]; };
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
        heap.clear();
        auto push = [&](int v) {
            if (v >= 0 && inq[v] != st) {
                inq[v] = st;
                heap.push_back(pos[v]);
                std::push_heap(heap.begin(), heap.end(), std::greater<int>());
            }
        };
        if (nb != bend[b]) push(jsucc[b]);
        if (na != bend[a]) push(jsucc[a]);
        push(q);
        while (!heap.empty()) {
            std::pop_heap(heap.begin(), heap.end(), std::greater<int>());
            int p = heap.back(); heap.pop_back();
            int v = T[p];
            if (v == a || v == b) continue;
            int sv = 0;
            int jp = jpred[v];
            if (jp >= 0) sv = E(jp);
            int m2 = (v == q) ? a : mp[v];
            if (m2 >= 0) { int e = E(m2); if (e > sv) sv = e; }
            int e = sv + pt[v];
            if (e != bend[v]) {
                nend[v] = e; chg[v] = st;
                push(jsucc[v]);
                push(ms[v]);
            }
        }
        int mx = 0;
        for (int o : lastOps) { int e = E(o); if (e > mx) mx = e; }
        return (double)mx - cache_obj_;
    }

    void prepare(const Sol& s) {
        has_ = true;
        if (cache_.size() != s.size()) cache_.resize(s.size());
        for (size_t r = 0; r < s.size(); ++r) cache_[r].assign(s[r].begin(), s[r].end());
        clean_ = false;
        bool ok = ((int)s.size() == M.m);
        if (ok) {
            for (int mm = 0; mm < M.m && ok; ++mm) {
                const auto& seq = s[mm];
                if ((int)seq.size() != mcnt[mm]) { ok = false; break; }
                if (++jstamp_ == 0) { std::fill(jst.begin(), jst.end(), 0); jstamp_ = 1; }
                unsigned js = jstamp_;
                for (int j : seq) {
                    if (j < 0 || j >= M.n || M.opk[j][mm] < 0 || jst[j] == js) { ok = false; break; }
                    jst[j] = js;
                }
            }
        }
        if (!ok) { cache_obj_ = M.objective(s); return; }
        int N = M.n_ops;
        mop_.resize(M.m);
        for (int mm = 0; mm < M.m; ++mm) {
            const auto& seq = s[mm];
            int L = (int)seq.size();
            auto& mo = mop_[mm];
            mo.resize(L);
            for (int i = 0; i < L; ++i) { int j = seq[i]; mo[i] = M.off[j] + M.opk[j][mm]; }
            for (int i = 0; i < L; ++i) {
                int o = mo[i];
                mp[o] = i > 0 ? mo[i - 1] : -1;
                ms[o] = i + 1 < L ? mo[i + 1] : -1;
                mpos[o] = i;
            }
        }
        int cnt = 0;
        for (int op = 0; op < N; ++op) {
            indeg[op] = (jpred[op] >= 0) + (mp[op] >= 0);
            if (indeg[op] == 0) T[cnt++] = op;
        }
        int h = 0;
        while (h < cnt) {
            int op = T[h++];
            int nx = jsucc[op];
            if (nx >= 0 && --indeg[nx] == 0) T[cnt++] = nx;
            int m2 = ms[op];
            if (m2 >= 0 && --indeg[m2] == 0) T[cnt++] = m2;
        }
        if (cnt != N) { cache_obj_ = M.objective(s); return; }
        int C = 0;
        for (int t = 0; t < N; ++t) {
            int v = T[t];
            pos[v] = t;
            int jp = jpred[v], m2 = mp[v];
            int r = 0;
            if (jp >= 0) r = bend[jp];
            if (m2 >= 0 && bend[m2] > r) r = bend[m2];
            bend[v] = r + pt[v];
            if (bend[v] > C) C = bend[v];
            unsigned long long f = (r == 0) ? 1ULL : 0ULL;
            if (jp >= 0 && bend[jp] == r) f += fc[jp];
            if (m2 >= 0 && bend[m2] == r) f += fc[m2];
            fc[v] = f;
        }
        totC = 0;
        for (int t = N - 1; t >= 0; --t) {
            int v = T[t];
            int w1 = jsucc[v], w2 = ms[v];
            int q = 0;
            if (w1 >= 0) q = pt[w1] + qq[w1];
            if (w2 >= 0 && pt[w2] + qq[w2] > q) q = pt[w2] + qq[w2];
            qq[v] = q;
            unsigned long long g = (q == 0) ? 1ULL : 0ULL;
            if (w1 >= 0 && pt[w1] + qq[w1] == q) g += gc[w1];
            if (w2 >= 0 && pt[w2] + qq[w2] == q) g += gc[w2];
            gc[v] = g;
        }
        for (int v = 0; v < N; ++v) if (qq[v] == 0 && bend[v] == C) totC += fc[v];
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
