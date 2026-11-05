// COMPONENT: {"name": "jssp_time_window_greedy_redispatch", "slot": "perturbation", "params": {"window_frac": {"type": "float", "range": [0.03, 0.4]}, "noise": {"type": "float", "range": [0.0, 3.0]}, "focus": {"type": "cat", "values": ["random", "critical"]}}}
struct JsCoreC {
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

    explicit JsCoreC(const Model& m) : md(m), N(m.total_ops), M(m.m), n(m.n) {
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

class TimeWindowRedispatch : public hsf::Perturbation<Model> {
    using Sol = Model::Solution;
    JsCoreC c; double frac, noise; bool crit;
    std::vector<int> L, L2, posL, path, R, seg, inseg;
    std::vector<long long> fin, mfin;
    int segStamp = 0;

    void redispatch(int a, int len, double nz, Rng& rng) {
        L2 = L;
        std::fill(mfin.begin(), mfin.end(), 0);
        for (int k = 0; k < a; ++k) {
            int o = L[k];
            long long t = mfin[c.mach[o]];
            if (c.jp[o] >= 0) t = std::max(t, fin[c.jp[o]]);
            fin[o] = t + c.proc[o]; mfin[c.mach[o]] = fin[o];
        }
        ++segStamp;
        for (int k = a; k < a + len; ++k) inseg[L[k]] = segStamp;
        R.clear();
        for (int k = a; k < a + len; ++k) {
            int o = L[k];
            if (c.jp[o] < 0 || inseg[c.jp[o]] != segStamp) R.push_back(o);
        }
        seg.clear();
        while (!R.empty()) {
            int bi = 0; double best = std::numeric_limits<double>::infinity(); long long bt = 0;
            for (int k = 0; k < (int)R.size(); ++k) {
                int o = R[k];
                long long t = mfin[c.mach[o]];
                if (c.jp[o] >= 0) t = std::max(t, fin[c.jp[o]]);
                double sc = (double)t + nz * c.avgp * rng.uniform();
                if (sc < best) { best = sc; bi = k; bt = t; }
            }
            int o = R[bi];
            R[bi] = R.back(); R.pop_back();
            seg.push_back(o);
            fin[o] = bt + c.proc[o]; mfin[c.mach[o]] = fin[o];
            int nx = c.js[o];
            if (nx >= 0 && inseg[nx] == segStamp) R.push_back(nx);
        }
        for (int k = 0; k < (int)seg.size(); ++k) L2[a + k] = seg[k];
    }
public:
    TimeWindowRedispatch(const Model& m, double f, double nz, bool cr) : c(m), frac(f), noise(nz), crit(cr) {
        posL.assign(c.N, 0); inseg.assign(c.N, 0); fin.assign(c.N, 0); mfin.assign(c.M, 0);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int N = c.N;
        if (N < 2) return s;
        c.list_from(s, L);
        for (int k = 0; k < N; ++k) posL[L[k]] = k;
        if (crit) c.critical(rng, path);
        for (int attempt = 0; attempt < 4; ++attempt) {
            int len = (int)std::lround(std::max(1.0, strength) * frac * N * (1.0 + 0.5 * attempt));
            len = std::max(2, std::min(N, len));
            int a;
            if (crit && !path.empty()) {
                int o = path[rng.below((int)path.size())];
                a = posL[o] - len / 2;
                a = std::max(0, std::min(N - len, a));
            } else a = rng.below(N - len + 1);
            redispatch(a, len, noise + attempt, rng);
            Sol out = c.to_sol(L2);
            if (out != s) return out;
        }
        Sol out = c.to_sol(L);
        c.force_change(out, rng);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double f = params.get("window_frac", 0.1);
    double nz = params.get("noise", 0.5);
    bool cr = params.text("focus", "random") == "critical";
    return std::make_unique<TimeWindowRedispatch>(model, f, nz, cr);
}
