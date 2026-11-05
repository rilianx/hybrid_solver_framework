// COMPONENT: {"name": "jssp_bottleneck_machine_resequence", "slot": "perturbation", "params": {"machines_frac": {"type": "float", "range": [0.05, 0.5]}, "keep_prob": {"type": "float", "range": [0.0, 1.0]}, "rule": {"type": "cat", "values": ["orig", "mwkr", "spt"]}, "pick": {"type": "cat", "values": ["critical", "busiest", "random"]}}}
struct JsCoreB {
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

    explicit JsCoreB(const Model& m) : md(m), N(m.total_ops), M(m.m), n(m.n) {
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

class BottleneckResequence : public hsf::Perturbation<Model> {
    using Sol = Model::Solution;
    JsCoreB c; double mfrac, keep; int rule, pick;
    std::vector<char> freeM, done;
    std::vector<long long> fin, mfin, mload;
    std::vector<int> indeg2, posOrig, path, cand, L;
    std::vector<double> w, rw;
    std::vector<std::vector<int>> readyM, newSeq;
    std::vector<std::pair<long long,int>> heap;

    long long est(int o) const {
        long long e = mfin[c.mach[o]];
        int a = c.jp[o];
        if (a >= 0) e = std::max(e, fin[a]);
        return e;
    }
    void hpush(long long e, int o) {
        heap.push_back({e, o});
        std::push_heap(heap.begin(), heap.end(), std::greater<std::pair<long long,int>>());
    }
    void make_ready(int o) {
        if (freeM[c.mach[o]]) readyM[c.mach[o]].push_back(o);
        hpush(est(o), o);
    }
    void schedule(int x) {
        int i = c.mach[x];
        long long t = est(x);
        fin[x] = t + c.proc[x]; mfin[i] = fin[x]; done[x] = 1;
        newSeq[i].push_back(c.job[x]);
        int a = c.js[x];
        if (a >= 0 && --indeg2[a] == 0) make_ready(a);
        if (!freeM[i]) { int b = c.ms[x]; if (b >= 0 && --indeg2[b] == 0) make_ready(b); }
    }
    // requires c.mp/c.ms loaded from base
    void simulate(double kp, Rng& rng) {
        int N = c.N;
        std::fill(done.begin(), done.end(), 0);
        std::fill(mfin.begin(), mfin.end(), 0);
        for (int i = 0; i < c.M; ++i) { readyM[i].clear(); newSeq[i].clear(); }
        heap.clear();
        for (int o = 0; o < N; ++o) indeg2[o] = (c.jp[o] >= 0) + ((c.mp[o] >= 0 && !freeM[c.mach[o]]) ? 1 : 0);
        for (int o = 0; o < N; ++o) if (!indeg2[o]) make_ready(o);
        auto cmp = std::greater<std::pair<long long,int>>();
        while (!heap.empty()) {
            std::pop_heap(heap.begin(), heap.end(), cmp);
            long long e = heap.back().first; int o = heap.back().second; heap.pop_back();
            if (done[o]) continue;
            long long e2 = est(o);
            if (e2 > e) { hpush(e2, o); continue; }
            int i = c.mach[o];
            int x = o;
            if (freeM[i]) {
                std::vector<int>& R = readyM[i];
                long long cmin = std::numeric_limits<long long>::max(); int am = -1;
                for (int y : R) { long long cy = est(y) + c.proc[y]; if (cy < cmin) { cmin = cy; am = y; } }
                cand.clear();
                for (int y : R) if (y == am || est(y) < cmin) cand.push_back(y);
                if (cand.empty()) cand.push_back(o);
                if (rng.uniform() < kp) {
                    int b = cand[0];
                    for (int y : cand) {
                        bool better;
                        if (rule == 0) better = posOrig[y] < posOrig[b];
                        else if (rule == 1) better = rw[y] > rw[b];
                        else better = c.proc[y] < c.proc[b];
                        if (better) b = y;
                    }
                    x = b;
                } else x = cand[rng.below((int)cand.size())];
                for (size_t k = 0; k < R.size(); ++k) if (R[k] == x) { R[k] = R.back(); R.pop_back(); break; }
                if (x != o) hpush(e2, o);
            }
            schedule(x);
        }
    }
public:
    BottleneckResequence(const Model& m, double mf, double kp, int ru, int pk)
        : c(m), mfrac(mf), keep(kp), rule(ru), pick(pk) {
        freeM.assign(c.M, 0); done.assign(c.N, 0); fin.assign(c.N, 0); mfin.assign(c.M, 0);
        mload.assign(c.M, 0); indeg2.assign(c.N, 0); posOrig.assign(c.N, 0);
        w.assign(c.M, 0.0); rw.assign(c.N, 0.0);
        readyM.assign(c.M, std::vector<int>()); newSeq.assign(c.M, std::vector<int>());
        for (int j = 0; j < c.n; ++j) {
            const auto& rt = m.routes[j];
            double acc = 0;
            for (int k = (int)rt.size() - 1; k >= 0; --k) {
                int o = m.op_of[j][rt[k].first];
                acc += rt[k].second; rw[o] = acc;
                mload[rt[k].first] += rt[k].second;
            }
        }
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (c.N == 0) return s;
        Sol base;
        if (c.load(s) && c.times()) base = s;
        else { c.list_from(s, L); base = c.to_sol(L); c.load(base); c.times(); }
        for (int i = 0; i < c.M; ++i)
            for (int p = 0; p < (int)base[i].size(); ++p) posOrig[c.md.opflat[(size_t)i * c.n + base[i][p]]] = p;

        for (int attempt = 0; attempt < 3; ++attempt) {
            for (int i = 0; i < c.M; ++i) w[i] = 0.0;
            if (pick == 0) {
                c.critical(rng, path);
                for (int i = 0; i < c.M; ++i) w[i] = 0.2;
                for (int o : path) w[c.mach[o]] += 1.0;
            } else if (pick == 1) {
                for (int i = 0; i < c.M; ++i) w[i] = (double)mload[i] + 1e-9;
            } else {
                for (int i = 0; i < c.M; ++i) w[i] = 1.0;
            }
            int elig = 0;
            for (int i = 0; i < c.M; ++i) { if (base[i].size() < 2) w[i] = 0.0; if (w[i] > 0) ++elig; }
            if (elig == 0) return base;
            int k = (int)std::lround(std::max(1.0, strength) * mfrac * c.M);
            k = std::max(1, std::min(elig, k));
            std::fill(freeM.begin(), freeM.end(), 0);
            for (int t = 0; t < k; ++t) {
                double tot = 0; for (int i = 0; i < c.M; ++i) tot += w[i];
                double u = rng.uniform() * tot;
                int ch = -1;
                for (int i = 0; i < c.M; ++i) if (w[i] > 0) { ch = i; u -= w[i]; if (u < 0) break; }
                if (ch < 0) break;
                freeM[ch] = 1; w[ch] = 0.0;
            }
            simulate(attempt == 0 ? keep : 0.0, rng);
            Sol out = base;
            for (int i = 0; i < c.M; ++i) if (freeM[i]) out[i] = newSeq[i];
            if (out != s) return out;
        }
        Sol out = base;
        c.force_change(out, rng);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double mf = params.get("machines_frac", 0.15);
    double kp = params.get("keep_prob", 0.5);
    std::string r = params.text("rule", "orig");
    std::string p = params.text("pick", "critical");
    int ru = r == "mwkr" ? 1 : (r == "spt" ? 2 : 0);
    int pk = p == "busiest" ? 1 : (p == "random" ? 2 : 0);
    return std::make_unique<BottleneckResequence>(model, mf, kp, ru, pk);
}
