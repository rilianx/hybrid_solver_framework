// COMPONENT: {"name": "single_machine_schrage_resequence", "slot": "neighborhood", "params": {"rules": {"type": "cat", "values": ["schrage", "all"]}, "machines": {"type": "cat", "values": ["critical", "all"]}}}
struct JsCoreS {
    const Model& M;
    int n, m, T;
    std::vector<int> jp, jn;
    std::vector<long long> p, rh, rt;
    Model::Solution cur;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0; long long version = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, q;
    int stamp = 0;
    explicit JsCoreS(const Model& md) : M(md), n(md.n), m(md.m), T(md.total_ops) {
        jp.assign(T, -1); jn.assign(T, -1); p.assign(T, 0); rh.assign(T, 0); rt.assign(T, 0);
        for (int j = 0; j < n; ++j) {
            const auto& R = M.routes[j]; int prev = -1; long long acc = 0;
            for (size_t k = 0; k < R.size(); ++k) {
                int o = M.op_of[j][R[k].first];
                p[o] = R[k].second; jp[o] = prev; if (prev >= 0) jn[prev] = o;
                rh[o] = acc; acc += p[o]; prev = o;
            }
            acc = 0;
            for (size_t k = R.size(); k-- > 0;) { int o = M.op_of[j][R[k].first]; rt[o] = acc; acc += p[o]; }
        }
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0); seen.assign(T, 0);
        r.assign(T, 0); q.assign(T, 0); topo.reserve(T);
    }
    int op(int i, int j) const { return (i >= 0 && i < m && j >= 0 && j < n) ? M.opflat[(size_t)i * n + j] : -1; }
    void ensure(const Model::Solution& s) { if (!valid || s != cur) compute(s); }
    void compute(const Model::Solution& s) {
        cur = s; valid = true; ++version; obj = M.objective(s); feas = false; cmax = 0;
        ++stamp;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        if ((int)s.size() != m) return;
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            const auto& seq = s[i];
            for (int k = 0; k < (int)seq.size(); ++k) {
                int o = op(i, seq[k]);
                if (o < 0 || seen[o] == stamp) return;
                seen[o] = stamp; ++cnt;
                if (k > 0) { int pr = op(i, seq[k - 1]); mp[o] = pr; ms[pr] = o; }
            }
        }
        if (cnt != T) return;
        topo.clear();
        for (int o = 0; o < T; ++o) { indeg[o] = (jp[o] >= 0) + (mp[o] >= 0); if (!indeg[o]) topo.push_back(o); }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = jn[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            int b = ms[o]; if (b >= 0 && --indeg[b] == 0) topo.push_back(b);
        }
        if ((int)topo.size() != T) return;
        for (int o : topo) {
            long long a = 0;
            if (jp[o] >= 0) a = r[jp[o]] + p[jp[o]];
            if (mp[o] >= 0) a = std::max(a, r[mp[o]] + p[mp[o]]);
            r[o] = a; cmax = std::max(cmax, a + p[o]);
        }
        for (int h = T - 1; h >= 0; --h) {
            int o = topo[h]; long long b = 0;
            if (jn[o] >= 0) b = q[jn[o]] + p[jn[o]];
            if (ms[o] >= 0) b = std::max(b, q[ms[o]] + p[ms[o]]);
            q[o] = b;
        }
        feas = true;
    }
    bool critArc(int u, int v) const { return r[u] + p[u] == r[v] && r[v] + p[v] + q[v] == cmax; }
};

class SingleMachineSchrageResequence : public hsf::Neighborhood<Model> {
    const Model& M;
    JsCoreS A;
    bool allRules, allMach;
    Sol work; long long workVer = -1;
    std::vector<long long> rel, tl, pp;
    std::vector<int> idx, res, heap, tmp;
    std::vector<std::vector<int>> found;

    void buildSeq(const Sol& s, int i, int rule, std::vector<int>& outSeq) {
        const auto& seq = s[i];
        int L = (int)seq.size();
        rel.resize(L); tl.resize(L); pp.resize(L); idx.resize(L);
        for (int k = 0; k < L; ++k) {
            int o = A.op(i, seq[k]);
            if (o < 0) { outSeq = seq; return; }
            pp[k] = A.p[o];
            if (A.feas) {
                int a = A.jp[o]; rel[k] = a >= 0 ? A.r[a] + A.p[a] : 0;
                int b = A.jn[o]; tl[k] = b >= 0 ? A.p[b] + A.q[b] : 0;
            } else { rel[k] = A.rh[o]; tl[k] = A.rt[o]; }
            idx[k] = k;
        }
        if (rule == 1) {
            std::sort(idx.begin(), idx.end(), [&](int x, int y) {
                if (rel[x] != rel[y]) return rel[x] < rel[y];
                if (tl[x] != tl[y]) return tl[x] > tl[y];
                return x < y; });
        } else if (rule == 2) {
            std::sort(idx.begin(), idx.end(), [&](int x, int y) {
                if (tl[x] != tl[y]) return tl[x] > tl[y];
                if (rel[x] != rel[y]) return rel[x] < rel[y];
                return x < y; });
        } else {
            std::sort(idx.begin(), idx.end(), [&](int x, int y) {
                if (rel[x] != rel[y]) return rel[x] < rel[y];
                return x < y; });
            auto low = [&](int x, int y) {
                if (tl[x] != tl[y]) return tl[x] < tl[y];
                if (rel[x] != rel[y]) return rel[x] > rel[y];
                return x > y; };
            heap.clear(); res.clear();
            long long t = 0; int ptr = 0;
            while ((int)res.size() < L) {
                if (heap.empty() && ptr < L && rel[idx[ptr]] > t) t = rel[idx[ptr]];
                while (ptr < L && rel[idx[ptr]] <= t) { heap.push_back(idx[ptr++]); std::push_heap(heap.begin(), heap.end(), low); }
                std::pop_heap(heap.begin(), heap.end(), low);
                int x = heap.back(); heap.pop_back();
                res.push_back(x); t += pp[x];
            }
            idx = res;
        }
        outSeq.resize(L);
        for (int k = 0; k < L; ++k) outSeq[k] = seq[idx[k]];
    }
    void addMachine(const Sol& s, int i, std::vector<Move>& out) {
        int nr = allRules ? 3 : 1;
        found.clear();
        for (int rule = 0; rule < nr; ++rule) {
            buildSeq(s, i, rule, tmp);
            if (tmp == s[i]) continue;
            bool dup = false;
            for (auto& f : found) if (f == tmp) { dup = true; break; }
            if (dup) continue;
            found.push_back(tmp);
            out.push_back(Move{i, rule, 0, 0, 0, 0, 0});
        }
    }
public:
    SingleMachineSchrageResequence(const Model& md, bool ar, bool am) : M(md), A(md), allRules(ar), allMach(am) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        int mm = std::min(A.m, (int)s.size());
        std::vector<char> done(mm, 0);
        if (A.feas && !allMach) {
            for (int i = 0; i < mm; ++i) {
                const auto& seq = s[i]; bool c = false;
                for (int k = 0; k + 1 < (int)seq.size() && !c; ++k) {
                    int u = A.op(i, seq[k]), v = A.op(i, seq[k + 1]);
                    if (u >= 0 && v >= 0 && A.critArc(u, v)) c = true;
                }
                if (c) { done[i] = 1; addMachine(s, i, out); }
            }
        }
        if (out.empty())
            for (int i = 0; i < mm; ++i) if (!done[i]) addMachine(s, i, out);
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& mv) override {
        A.ensure(s);
        Sol r = s;
        int i = mv[0];
        if (i >= 0 && i < (int)s.size() && i < A.m) buildSeq(s, i, mv[1], r[i]);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        A.ensure(s);
        int i = mv[0];
        if (i < 0 || i >= (int)s.size() || i >= A.m) return 0.0;
        if (workVer != A.version) { work = s; workVer = A.version; }
        buildSeq(s, i, mv[1], tmp);
        work[i].swap(tmp);
        double v = M.objective(work);
        work[i].swap(tmp);
        return v - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool ar = params.text("rules", "schrage") == "all";
    bool am = params.text("machines", "critical") == "all";
    return std::make_unique<SingleMachineSchrageResequence>(model, ar, am);
}
