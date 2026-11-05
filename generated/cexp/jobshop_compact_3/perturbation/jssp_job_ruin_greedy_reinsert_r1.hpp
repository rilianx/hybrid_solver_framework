// COMPONENT: {"name": "jssp_job_ruin_greedy_reinsert", "slot": "perturbation", "params": {"jobs_frac": {"type": "float", "range": [0.02, 0.3]}, "noise": {"type": "float", "range": [0.0, 3.0]}, "overflow_weight": {"type": "float", "range": [0.0, 3.0]}, "select": {"type": "cat", "values": ["random", "critical"]}}}
struct JsCoreA {
    using Sol = Model::Solution;
    const Model& md;
    int N, M, n;
    std::vector<int> job, mach, proc, jp, js, mp, ms, indeg, q, mark, rank, cpath, carcs;
    std::vector<long long> st;
    std::vector<double> key;
    std::vector<std::pair<int,int>> cand;
    std::vector<std::pair<double,int>> kheap;
    int stamp = 0, endop = -1;
    long long mk = 0;
    double avgp = 1.0;

    explicit JsCoreA(const Model& m) : md(m), N(m.total_ops), M(m.m), n(m.n) {
        job.assign(N, -1); mach.assign(N, 0); proc.assign(N, 0); jp.assign(N, -1); js.assign(N, -1);
        mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0); q.assign(N, 0); mark.assign(N, 0);
        rank.assign(N, 0); st.assign(N, 0); key.assign(N, 0.5);
        long long tot = 0;
        for (int j = 0; j < n; ++j) {
            int prev = -1;
            for (const auto& pr : md.routes[j]) {
                int o = md.op_of[j][pr.first];
                job[o] = j; mach[o] = pr.first; proc[o] = pr.second; jp[o] = prev;
                if (prev >= 0) js[prev] = o;
                prev = o; tot += pr.second;
            }
        }
        if (N > 0) avgp = std::max(1.0, (double)tot / N);
    }
    bool load(const Sol& s) {
        std::fill(mp.begin(), mp.end(), -1);
        std::fill(ms.begin(), ms.end(), -1);
        if ((int)s.size() != M) return false;
        ++stamp; int cnt = 0;
        for (int i = 0; i < M; ++i) {
            int prev = -1;
            for (int j : s[i]) {
                if (j < 0 || j >= n) return false;
                int o = md.opflat[(size_t)i * n + j];
                if (o < 0 || mark[o] == stamp) return false;
                mark[o] = stamp; ++cnt;
                mp[o] = prev; if (prev >= 0) ms[prev] = o; prev = o;
            }
        }
        return cnt == N;
    }
    bool times() {
        int h = 0, t = 0;
        for (int o = 0; o < N; ++o) { indeg[o] = (jp[o] >= 0) + (mp[o] >= 0); if (!indeg[o]) q[t++] = o; }
        mk = 0; endop = -1;
        while (h < t) {
            int o = q[h++];
            long long s0 = 0;
            if (jp[o] >= 0) s0 = st[jp[o]] + proc[jp[o]];
            if (mp[o] >= 0) s0 = std::max(s0, st[mp[o]] + proc[mp[o]]);
            st[o] = s0;
            long long f = s0 + proc[o];
            if (endop < 0 || f > mk) { mk = f; endop = o; }
            int a = js[o]; if (a >= 0 && --indeg[a] == 0) q[t++] = a;
            a = ms[o]; if (a >= 0 && --indeg[a] == 0) q[t++] = a;
        }
        return t == N;
    }
    void critical(Rng& rng, std::vector<int>& path) {
        path.clear();
        int o = endop;
        while (o >= 0) {
            path.push_back(o);
            int a = jp[o], b = mp[o];
            bool ca = a >= 0 && st[a] + proc[a] == st[o];
            bool cb = b >= 0 && st[b] + proc[b] == st[o];
            if (ca && cb) o = rng.below(2) ? a : b;
            else if (ca) o = a;
            else if (cb) o = b;
            else o = -1;
        }
        std::reverse(path.begin(), path.end());
    }
    Sol to_sol(const std::vector<int>& L) const {
        Sol out(M);
        for (int i = 0; i < M; ++i) out[i].reserve(md.machine_jobs[i].size());
        for (int o : L) out[mach[o]].push_back(job[o]);
        return out;
    }
    bool valid_list(const Sol& s, std::vector<int>& L) {
        L.clear();
        if (!(load(s) && times())) return false;
        for (int k = 0; k < N; ++k) rank[q[k]] = k;
        L.assign(q.begin(), q.begin() + N);
        std::sort(L.begin(), L.end(), [&](int a, int b) {
            if (st[a] != st[b]) return st[a] < st[b];
            return rank[a] < rank[b];
        });
        return true;
    }
    // topological list sorted by start time; repairs infeasible input. Leaves times valid.
    bool list_from(const Sol& s, std::vector<int>& L) {
        if (valid_list(s, L)) return true;
        L.clear();
        std::fill(key.begin(), key.end(), 0.5);
        if ((int)s.size() == M)
            for (int i = 0; i < M; ++i) {
                int sz = (int)s[i].size();
                for (int p = 0; p < sz; ++p) {
                    int j = s[i][p];
                    if (j < 0 || j >= n) continue;
                    int o = md.opflat[(size_t)i * n + j];
                    if (o >= 0) key[o] = (p + 0.5) / sz;
                }
            }
        kheap.clear();
        auto cmp = std::greater<std::pair<double,int>>();
        for (int o = 0; o < N; ++o) if (jp[o] < 0) { kheap.push_back({key[o], o}); std::push_heap(kheap.begin(), kheap.end(), cmp); }
        while (!kheap.empty()) {
            std::pop_heap(kheap.begin(), kheap.end(), cmp);
            int o = kheap.back().second; kheap.pop_back();
            L.push_back(o);
            int a = js[o];
            if (a >= 0) { kheap.push_back({key[a], a}); std::push_heap(kheap.begin(), kheap.end(), cmp); }
        }
        Sol r = to_sol(L);
        valid_list(r, L);
        return false;
    }
    bool force_change(Sol& cur, Rng& rng) {
        if (load(cur) && times()) {
            critical(rng, cpath);
            carcs.clear();
            for (size_t k = 0; k + 1 < cpath.size(); ++k) if (mp[cpath[k + 1]] == cpath[k]) carcs.push_back(cpath[k]);
            if (!carcs.empty()) {
                int a = carcs[rng.below((int)carcs.size())];
                int i = mach[a];
                for (size_t p = 0; p + 1 < cur[i].size(); ++p) if (cur[i][p] == job[a]) {
                    std::swap(cur[i][p], cur[i][p + 1]);
                    if (load(cur) && times()) return true;
                    std::swap(cur[i][p], cur[i][p + 1]);
                    break;
                }
            }
        }
        cand.clear();
        for (int i = 0; i < (int)cur.size(); ++i)
            for (int p = 0; p + 1 < (int)cur[i].size(); ++p) cand.push_back({i, p});
        for (size_t k = 0; k < cand.size(); ++k) {
            size_t r = k + rng.below((int)(cand.size() - k));
            std::swap(cand[k], cand[r]);
            int i = cand[k].first, p = cand[k].second;
            std::swap(cur[i][p], cur[i][p + 1]);
            if (load(cur) && times()) return true;
            std::swap(cur[i][p], cur[i][p + 1]);
        }
        return false;
    }
};

class JobRuinReinsert : public hsf::Perturbation<Model> {
    using Sol = Model::Solution;
    JsCoreA c; double frac, noise, ovw; bool crit;
    std::vector<int> L, posL, path, sel, tmp;
    std::vector<char> chosen;
    std::vector<long long> fin, mlast;
    std::vector<std::vector<int>> mseq;

    void retime() {
        std::fill(mlast.begin(), mlast.end(), 0);
        for (auto& v : mseq) v.clear();
        for (int k = 0; k < (int)L.size(); ++k) {
            int o = L[k]; posL[o] = k;
            int i = c.mach[o];
            long long s0 = mlast[i];
            int a = c.jp[o];
            if (a >= 0) s0 = std::max(s0, fin[a]);
            c.st[o] = s0; fin[o] = s0 + c.proc[o]; mlast[i] = fin[o];
            mseq[i].push_back(o);
        }
    }
public:
    JobRuinReinsert(const Model& m, double f, double nz, double ow, bool cr)
        : c(m), frac(f), noise(nz), ovw(ow), crit(cr) {
        posL.assign(c.N, 0); chosen.assign(c.n, 0); fin.assign(c.N, 0);
        mlast.assign(c.M, 0); mseq.assign(c.M, std::vector<int>());
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (c.N == 0 || c.n == 0) return s;
        c.list_from(s, L);
        int n = c.n;
        int r = (int)std::lround(std::max(1.0, strength) * frac * n);
        r = std::max(1, std::min(n, r));
        sel.clear();
        std::fill(chosen.begin(), chosen.end(), 0);
        if (crit) {
            c.critical(rng, path);
            tmp.clear();
            for (int o : path) { int j = c.job[o]; if (!chosen[j]) { chosen[j] = 1; tmp.push_back(j); } }
            for (int j : tmp) chosen[j] = 0;
            std::shuffle(tmp.begin(), tmp.end(), rng.g);
            for (int j : tmp) if ((int)sel.size() < r) { sel.push_back(j); chosen[j] = 1; }
        }
        while ((int)sel.size() < r) { int j = rng.below(n); if (!chosen[j]) { chosen[j] = 1; sel.push_back(j); } }
        std::shuffle(sel.begin(), sel.end(), rng.g);

        size_t w = 0;
        for (size_t k = 0; k < L.size(); ++k) if (!chosen[c.job[L[k]]]) L[w++] = L[k];
        L.resize(w);

        for (int j : sel) {
            retime();
            long long r0 = 0; int predIdx = -1;
            for (const auto& pr : c.md.routes[j]) {
                int o = c.md.op_of[j][pr.first];
                int i = pr.first; long long p = pr.second;
                const std::vector<int>& seq = mseq[i];
                int sz = (int)seq.size();
                double best = std::numeric_limits<double>::infinity();
                int bq = sz; long long bstart = r0;
                for (int qq = 0; qq <= sz; ++qq) {
                    long long pf = qq > 0 ? fin[seq[qq - 1]] : 0;
                    long long stt = std::max(r0, pf);
                    double over = 0.0;
                    if (qq < sz) { long long ns = c.st[seq[qq]]; if (stt + p > ns) over = (double)(stt + p - ns); }
                    double sc = (double)(stt + p) + ovw * over + noise * c.avgp * rng.uniform();
                    if (sc < best) { best = sc; bq = qq; bstart = stt; }
                }
                int idx = bq < sz ? posL[seq[bq]] : (sz > 0 ? posL[seq[sz - 1]] + 1 : 0);
                if (idx <= predIdx) idx = predIdx + 1;
                L.insert(L.begin() + idx, o);
                for (int k = idx; k < (int)L.size(); ++k) posL[L[k]] = k;
                c.st[o] = bstart; fin[o] = bstart + p; r0 = fin[o]; predIdx = idx;
            }
        }
        Sol out = c.to_sol(L);
        if (out == s) c.force_change(out, rng);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double f = params.get("jobs_frac", 0.1);
    double nz = params.get("noise", 0.5);
    double ow = params.get("overflow_weight", 1.0);
    bool cr = params.text("select", "critical") == "critical";
    return std::make_unique<JobRuinReinsert>(model, f, nz, ow, cr);
}
