// COMPONENT: {"name": "schrage_block_resequencing", "slot": "neighborhood", "params": {"extend": {"type": "int", "range": [0, 3]}, "rules": {"type": "cat", "values": ["schrage", "all"]}}}
struct JsState {
    const Model& M;
    int N = 0, MM = 0, T = 0;
    std::vector<int> jp, js, jobOf, pos, mp, ms, indeg, topo;
    std::vector<long long> p, r, q, sh, stl;
    std::vector<char> cr;
    Model::Solution cur;
    bool valid = false, feas = false;
    long long cmax = 0;
    double obj = 0;
    explicit JsState(const Model& m) : M(m) {
        N = m.n; MM = m.m; T = m.total_ops;
        jp.assign(T, -1); js.assign(T, -1); jobOf.assign(T, 0);
        pos.assign(T, 0); mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0);
        topo.reserve(T);
        p.assign(T, 0); r.assign(T, 0); q.assign(T, 0); sh.assign(T, 0); stl.assign(T, 0); cr.assign(T, 0);
        for (int j = 0; j < N; ++j) {
            const auto& rt = m.routes[j];
            int prev = -1; long long acc = 0;
            for (size_t k = 0; k < rt.size(); ++k) {
                int o = m.op_of[j][rt[k].first];
                jobOf[o] = j; p[o] = m.op_proc[o]; jp[o] = prev;
                if (prev >= 0) js[prev] = o;
                sh[o] = acc; acc += p[o]; prev = o;
            }
            long long t = 0;
            for (int k = (int)rt.size() - 1; k >= 0; --k) {
                int o = m.op_of[j][rt[k].first]; t += p[o]; stl[o] = t;
            }
        }
    }
    int opAt(const Model::Solution& s, int i, int k) const { return M.opflat[(size_t)i * N + s[i][k]]; }
    void ensure(const Model::Solution& s) {
        if (valid && s == cur) return;
        cur = s; valid = true; compute(s); obj = M.objective(s);
    }
    void compute(const Model::Solution& s) {
        std::fill(mp.begin(), mp.end(), -1);
        std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < MM && i < (int)s.size(); ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int o = opAt(s, i, k);
                pos[o] = k; mp[o] = prev;
                if (prev >= 0) ms[prev] = o;
                prev = o;
            }
        }
        topo.clear();
        for (int o = 0; o < T; ++o) {
            indeg[o] = (jp[o] >= 0) + (mp[o] >= 0);
            if (!indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = js[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            a = ms[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
        }
        feas = (int)topo.size() == T;
        if (!feas) {
            r = sh; q = stl; std::fill(cr.begin(), cr.end(), 0); cmax = 0; return;
        }
        cmax = 0;
        for (int o : topo) {
            long long st = 0;
            if (jp[o] >= 0) st = r[jp[o]] + p[jp[o]];
            if (mp[o] >= 0) st = std::max(st, r[mp[o]] + p[mp[o]]);
            r[o] = st; cmax = std::max(cmax, st + p[o]);
        }
        for (int h = T - 1; h >= 0; --h) {
            int o = topo[h];
            long long b = 0;
            if (js[o] >= 0) b = q[js[o]];
            if (ms[o] >= 0) b = std::max(b, q[ms[o]]);
            q[o] = p[o] + b;
            cr[o] = (r[o] + q[o] == cmax);
        }
    }
};

static Move mk4(int a, int b, int c, int d) { Move m{}; m[0] = a; m[1] = b; m[2] = c; m[3] = d; return m; }

class SchrageBlockResequencing : public hsf::Neighborhood<Model> {
    const Model& M;
    JsState A;
    Sol work;
    int E;
    int nRules;
    std::vector<int> ops, idx, ord;
    std::vector<long long> rd, tl, pr;
    std::vector<char> done;
    std::vector<std::vector<int>> seenOrd;

    // assumes A ensured for s; fills ord with the new op order; returns false if move invalid
    bool reseq(const Sol& s, int i, int a, int L, int rule) {
        if (i < 0 || i >= (int)s.size() || a < 0 || L < 2 || a + L > (int)s[i].size()) return false;
        ops.resize(L); rd.resize(L); tl.resize(L); pr.resize(L);
        for (int t = 0; t < L; ++t) {
            int o = A.opAt(s, i, a + t);
            ops[t] = o;
            int jpo = A.jp[o], jso = A.js[o];
            rd[t] = jpo >= 0 ? A.r[jpo] + A.p[jpo] : 0;
            tl[t] = jso >= 0 ? A.q[jso] : 0;
            pr[t] = A.p[o];
        }
        long long t0 = 0;
        if (a > 0 && A.feas) { int po = A.opAt(s, i, a - 1); t0 = A.r[po] + A.p[po]; }
        idx.clear();
        if (rule == 0) {
            done.assign(L, 0);
            long long t = t0;
            int cnt = 0;
            while (cnt < L) {
                int best = -1;
                for (int x = 0; x < L; ++x) {
                    if (done[x] || rd[x] > t) continue;
                    if (best < 0 || tl[x] > tl[best] || (tl[x] == tl[best] && rd[x] < rd[best])) best = x;
                }
                if (best < 0) {
                    long long mn = std::numeric_limits<long long>::max();
                    for (int x = 0; x < L; ++x) if (!done[x]) mn = std::min(mn, rd[x]);
                    t = mn;
                    continue;
                }
                done[best] = 1; idx.push_back(best); ++cnt;
                t = std::max(t, rd[best]) + pr[best];
            }
        } else {
            idx.resize(L);
            for (int x = 0; x < L; ++x) idx[x] = x;
            if (rule == 1) {
                std::stable_sort(idx.begin(), idx.end(), [&](int x, int y) {
                    if (rd[x] != rd[y]) return rd[x] < rd[y];
                    return tl[x] > tl[y];
                });
            } else {
                std::stable_sort(idx.begin(), idx.end(), [&](int x, int y) {
                    if (tl[x] != tl[y]) return tl[x] > tl[y];
                    return rd[x] < rd[y];
                });
            }
        }
        ord.resize(L);
        for (int x = 0; x < L; ++x) ord[x] = ops[idx[x]];
        return true;
    }
    void writeOrd(Sol& t, int i, int a) const {
        for (int x = 0; x < (int)ord.size(); ++x) t[i][a + x] = A.jobOf[ord[x]];
    }
public:
    SchrageBlockResequencing(const Model& m, int e, int nr) : M(m), A(m), E(e), nRules(nr) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (A.feas) {
            for (int i = 0; i < (int)s.size(); ++i) {
                int len = (int)s[i].size();
                for (int k = 0; k < len; ++k) {
                    int o = A.opAt(s, i, k);
                    if (!A.cr[o]) continue;
                    int bs = k;
                    while (k + 1 < len) {
                        int nx = A.opAt(s, i, k + 1);
                        if (!A.cr[nx] || A.r[o] + A.p[o] != A.r[nx]) break;
                        ++k; o = nx;
                    }
                    int be = k;
                    for (int a = std::max(0, bs - E); a <= bs; ++a) {
                        for (int b = be; b <= std::min(len - 1, be + E); ++b) {
                            int L = b - a + 1;
                            if (L < 2) continue;
                            seenOrd.clear();
                            for (int rule = 0; rule < nRules; ++rule) {
                                if (!reseq(s, i, a, L, rule)) continue;
                                if (ord == ops) continue;
                                bool dup = false;
                                for (const auto& v : seenOrd) if (v == ord) { dup = true; break; }
                                if (dup) continue;
                                seenOrd.push_back(ord);
                                out.push_back(mk4(i, a, L, rule));
                            }
                        }
                    }
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < (int)s.size(); ++i) {
                int len = (int)s[i].size();
                if (len < 2) continue;
                for (int rule = 0; rule < nRules; ++rule) out.push_back(mk4(i, 0, len, rule));
            }
        }
        if (out.empty()) out.push_back(mk4(0, 0, 1, 0));
    }
    Sol apply(const Sol& s, const Move& m) override {
        A.ensure(s);
        Sol t = s;
        if (reseq(s, m[0], m[1], m[2], m[3])) writeOrd(t, m[0], m[1]);
        return t;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        work = s;
        if (reseq(s, m[0], m[1], m[2], m[3])) writeOrd(work, m[0], m[1]);
        return M.objective(work) - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int e = (int)params.get("extend", 1);
    if (e < 0) e = 0;
    int nr = params.text("rules", "all") == "all" ? 3 : 1;
    return std::unique_ptr<hsf::Neighborhood<Model>>(new SchrageBlockResequencing(model, e, nr));
}
