// COMPONENT: {"name": "jssp_bottleneck_schrage_resequence", "slot": "perturbation", "params": {"machines_scale": {"type": "float", "range": [0.3, 2.0]}, "noise_scale": {"type": "float", "range": [0.0, 4.0]}, "machine_pick": {"type": "cat", "values": ["critical", "random"]}}}
struct Core {
    using Sol = Model::Solution;
    const Model& md;
    int N, M;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit Core(const Model& m) : md(m), N(m.total_ops), M(m.m) {
        job.assign(N, 0); mach.assign(N, 0);
        for (int j = 0; j < m.n; ++j) for (auto& pr : m.routes[j]) {
            if (pr.first < 0 || pr.first >= (int)m.op_of[j].size()) continue;
            int o = m.op_of[j][pr.first]; if (o >= 0) { job[o] = j; mach[o] = pr.first; }
        }
        mp.assign(N, -1); ms.assign(N, -1); pos.assign(N, 0); indeg.assign(N, 0); q.assign(N, 0);
        st.assign(N, 0); mark.assign(m.n, 0);
    }
    bool load(const Sol& s) {
        if ((int)s.size() != M) return false;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < M; ++i) {
            if (s[i].size() != md.machine_jobs[i].size()) return false;
            ++stamp; int prev = -1;
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= md.n || i >= (int)md.op_of[j].size()) return false;
                int op = md.op_of[j][i];
                if (op < 0 || mark[j] == stamp) return false;
                mark[j] = stamp; pos[op] = idx;
                if (prev >= 0) { ms[prev] = op; mp[op] = prev; }
                prev = op;
            }
        }
        return true;
    }
    bool times() {
        int qh = 0, qt = 0;
        for (int o = 0; o < N; ++o) {
            indeg[o] = (md.op_k[o] > 0 ? 1 : 0) + (mp[o] >= 0 ? 1 : 0); st[o] = 0;
            if (indeg[o] == 0) q[qt++] = o;
        }
        mk = 0; endop = -1;
        while (qh < qt) {
            int o = q[qh++]; long long e = st[o] + md.op_proc[o];
            if (endop < 0 || e > mk) { mk = e; endop = o; }
            int a = md.op_next[o];
            if (a >= 0) { if (st[a] < e) st[a] = e; if (--indeg[a] == 0) q[qt++] = a; }
            int b = ms[o];
            if (b >= 0) { if (st[b] < e) st[b] = e; if (--indeg[b] == 0) q[qt++] = b; }
        }
        return qt == N;
    }
    bool check(const Sol& s) { return load(s) && times(); }
    void critical(Rng& rng, std::vector<int>& path) {
        path.clear(); int o = endop;
        while (o >= 0) {
            path.push_back(o);
            int jp = md.op_k[o] > 0 ? o - 1 : -1, mq = mp[o];
            bool tj = jp >= 0 && st[jp] + md.op_proc[jp] == st[o];
            bool tm = mq >= 0 && st[mq] + md.op_proc[mq] == st[o];
            if (tj && tm) o = rng.below(2) ? jp : mq; else if (tj) o = jp; else if (tm) o = mq; else o = -1;
        }
        std::reverse(path.begin(), path.end());
    }
    bool try_swap(Sol& cur, int mi, int pi) {
        std::swap(cur[mi][pi], cur[mi][pi + 1]);
        if (check(cur)) return true;
        std::swap(cur[mi][pi], cur[mi][pi + 1]);
        check(cur);
        return false;
    }
    bool any_swap(Sol& cur, Rng& rng) {
        cand.clear();
        for (int i = 0; i < M; ++i) for (int p = 0; p + 1 < (int)cur[i].size(); ++p) cand.push_back({i, p});
        if (cand.empty()) return false;
        int lim = std::min<int>(20, (int)cand.size());
        for (int t = 0; t < lim; ++t) { auto cc = cand[rng.below((int)cand.size())]; if (try_swap(cur, cc.first, cc.second)) return true; }
        std::shuffle(cand.begin(), cand.end(), rng.g);
        for (auto& cc : cand) if (try_swap(cur, cc.first, cc.second)) return true;
        return false;
    }
    Sol dispatch(const std::vector<double>& key) {
        Sol out(M);
        for (int i = 0; i < M; ++i) out[i].reserve(md.machine_jobs[i].size());
        std::priority_queue<std::pair<double,int>, std::vector<std::pair<double,int>>, std::greater<std::pair<double,int>>> h;
        for (int o = 0; o < N; ++o) if (md.op_k[o] == 0) h.push({key[o], o});
        while (!h.empty()) {
            int o = h.top().second; h.pop();
            if (mach[o] < M) out[mach[o]].push_back(job[o]);
            if (md.op_next[o] >= 0) h.push({key[md.op_next[o]], md.op_next[o]});
        }
        return out;
    }
    Sol repair(const Sol& s, Rng& rng) {
        std::vector<double> key(N);
        for (int o = 0; o < N; ++o) key[o] = rng.uniform() * (double)std::max(1, md.n);
        for (int i = 0; i < std::min<int>(M, (int)s.size()); ++i)
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= md.n || i >= (int)md.op_of[j].size()) continue;
                int op = md.op_of[j][i]; if (op >= 0) key[op] = idx + 0.5 * rng.uniform();
            }
        return dispatch(key);
    }
};

class BottleneckSchrageResequence : public hsf::Perturbation<Model> {
    Core c;
    double mscale, noise; bool crit; double avgp = 1.0;
    std::vector<long long> head, tail;
    std::vector<int> topo, deg, R, cnt, newrow, oldrow, path, rows;
    std::vector<char> done, dom;
    std::vector<double> key;

    bool heads_tails(int mi) {
        const int N = c.N;
        const auto& PR = c.md.op_proc;
        const auto& NX = c.md.op_next;
        int qh = 0, qt = 0;
        for (int o = 0; o < N; ++o) {
            deg[o] = (c.md.op_k[o] > 0 ? 1 : 0) + ((c.mp[o] >= 0 && c.mach[o] != mi) ? 1 : 0);
            head[o] = 0;
            if (deg[o] == 0) topo[qt++] = o;
        }
        while (qh < qt) {
            int o = topo[qh++];
            long long e = head[o] + PR[o];
            int a = NX[o];
            if (a >= 0) { if (head[a] < e) head[a] = e; if (--deg[a] == 0) topo[qt++] = a; }
            if (c.mach[o] != mi) {
                int b = c.ms[o];
                if (b >= 0) { if (head[b] < e) head[b] = e; if (--deg[b] == 0) topo[qt++] = b; }
            }
        }
        if (qt != N) return false;
        for (int idx = qt - 1; idx >= 0; --idx) {
            int o = topo[idx];
            long long tl = 0;
            int a = NX[o];
            if (a >= 0) tl = std::max(tl, tail[a] + PR[a]);
            if (c.mach[o] != mi) {
                int b = c.ms[o];
                if (b >= 0) tl = std::max(tl, tail[b] + PR[b]);
            }
            tail[o] = tl;
        }
        return true;
    }

    bool reseq(Model::Solution& cur, int mi, double amp, Rng& rng) {
        auto& row = cur[mi];
        const int L = (int)row.size();
        if (L < 2) return false;
        if (!heads_tails(mi)) return false;
        const int n = c.md.n;
        const int* rowop = c.md.opflat.data() + (size_t)mi * n;
        const auto& PR = c.md.op_proc;
        R.resize(L);
        for (int t = 0; t < L; ++t) R[t] = rowop[row[t]];
        dom.assign((size_t)L * L, 0);
        std::vector<int> base(L, 0);
        for (int a = 0; a < L; ++a) {
            long long ra = head[R[a]], qa = tail[R[a]], pa = PR[R[a]];
            for (int b = 0; b < L; ++b) {
                if (a == b) continue;
                long long rb = head[R[b]], qb = tail[R[b]], pb = PR[R[b]];
                if (ra + pa <= rb && qa >= qb + pb && (ra < rb || qa > qb || a < b)) {
                    dom[(size_t)a * L + b] = 1; ++base[b];
                }
            }
        }
        newrow.resize(L);
        done.assign(L, 0);
        key.resize(L);
        bool changed = false;
        for (int attempt = 0; attempt < 4 && !changed; ++attempt) {
            cnt = base;
            std::fill(done.begin(), done.end(), 0);
            long long t = std::numeric_limits<long long>::max();
            for (int b = 0; b < L; ++b) {
                key[b] = (double)tail[R[b]] + (2.0 * rng.uniform() - 1.0) * amp;
                t = std::min(t, head[R[b]]);
            }
            bool ok = true;
            for (int step = 0; step < L; ++step) {
                int best = -1;
                long long minr = std::numeric_limits<long long>::max();
                for (int b = 0; b < L; ++b) {
                    if (done[b] || cnt[b] > 0) continue;
                    long long rb = head[R[b]];
                    if (rb < minr) minr = rb;
                    if (rb <= t && (best < 0 || key[b] > key[best])) best = b;
                }
                if (best < 0) {
                    if (minr == std::numeric_limits<long long>::max()) { ok = false; break; }
                    t = minr;
                    for (int b = 0; b < L; ++b) {
                        if (done[b] || cnt[b] > 0) continue;
                        if (head[R[b]] <= t && (best < 0 || key[b] > key[best])) best = b;
                    }
                    if (best < 0) { ok = false; break; }
                }
                done[best] = 1; newrow[step] = best;
                t = std::max(t, head[R[best]]) + PR[R[best]];
                for (int d = 0; d < L; ++d) if (dom[(size_t)best * L + d]) --cnt[d];
            }
            if (!ok) return false;
            for (int k = 0; k < L; ++k) if (newrow[k] != k) { changed = true; break; }
            if (!changed) amp = amp * 2.0 + avgp;
        }
        if (!changed) return false;
        oldrow = row;
        for (int k = 0; k < L; ++k) row[k] = c.job[R[newrow[k]]];
        if (c.check(cur)) return true;
        row = oldrow;
        c.check(cur);
        return false;
    }

    int pick_machine(const Model::Solution& cur, Rng& rng) {
        if (crit) {
            c.critical(rng, path);
            for (int t = 0; t < 8 && !path.empty(); ++t) {
                int o = path[rng.below((int)path.size())];
                int m = c.mach[o];
                if (m < c.M && cur[m].size() >= 2) return m;
            }
        }
        if (rows.empty()) return -1;
        return rows[rng.below((int)rows.size())];
    }
public:
    BottleneckSchrageResequence(const Model& m, double ms_, double ns, bool cr) : c(m), mscale(ms_), noise(ns), crit(cr) {
        int N = std::max(1, c.N);
        head.assign(N, 0); tail.assign(N, 0); topo.assign(N, 0); deg.assign(N, 0);
        for (int i = 0; i < m.m; ++i) if (m.machine_jobs[i].size() >= 2) rows.push_back(i);
        double sum = 0; for (int o = 0; o < m.total_ops; ++o) sum += m.op_proc[o];
        avgp = m.total_ops > 0 ? std::max(1.0, sum / m.total_ops) : 1.0;
    }
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        if (!c.check(s)) return c.repair(s, rng);
        double str = std::max(1.0, strength);
        int k = std::max(1, std::min(std::max(1, c.M), (int)std::lround(str * mscale)));
        double amp = noise * avgp * std::sqrt(str);
        Model::Solution cur = s;
        int done_cnt = 0;
        for (int t = 0; t < 2 * k + 2 && done_cnt < k; ++t) {
            int mi = pick_machine(cur, rng);
            if (mi < 0) break;
            if (reseq(cur, mi, amp, rng)) ++done_cnt;
        }
        if (cur == s) { c.check(cur); c.any_swap(cur, rng); }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ms_ = params.get("machines_scale", 0.6);
    double ns = params.get("noise_scale", 1.0);
    bool cr = params.text("machine_pick", "critical") == "critical";
    return std::make_unique<BottleneckSchrageResequence>(model, ms_, ns, cr);
}
