// COMPONENT: {"name": "jssp_critical_block_insertion", "slot": "perturbation", "params": {"moves_scale": {"type": "float", "range": [0.5, 3.0]}, "endpoint_prob": {"type": "float", "range": [0.0, 1.0]}, "max_tries": {"type": "int", "range": [3, 30]}}}
struct CoreC {
    using Sol = Model::Solution;
    const Model& md;
    int N, M;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit CoreC(const Model& m) : md(m), N(m.total_ops), M(m.m) {
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
        for (int t = 0; t < lim; ++t) { auto c = cand[rng.below((int)cand.size())]; if (try_swap(cur, c.first, c.second)) return true; }
        std::shuffle(cand.begin(), cand.end(), rng.g);
        for (auto& c : cand) if (try_swap(cur, c.first, c.second)) return true;
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

class CriticalBlockInsertion : public hsf::Perturbation<Model> {
    CoreC c; double scale, endp; int maxTries;
    std::vector<int> path;
    std::vector<std::pair<int,int>> blocks; // (start index in path, length)
    std::vector<int> backup;
public:
    CriticalBlockInsertion(const Model& m, double sc, double ep, int mt) : c(m), scale(sc), endp(ep), maxTries(mt) {}

    bool one_move(Model::Solution& cur, Rng& rng) {
        c.critical(rng, path);
        blocks.clear();
        int k = 0, P = (int)path.size();
        while (k < P) {
            int e = k;
            while (e + 1 < P && c.mp[path[e + 1]] == path[e]) ++e;
            if (e > k) blocks.push_back({k, e - k + 1});
            k = e + 1;
        }
        if (blocks.empty()) return false;
        for (int t = 0; t < maxTries; ++t) {
            auto bl = blocks[rng.below((int)blocks.size())];
            int L = bl.second;
            int first = path[bl.first];
            int mi = c.mach[first], base = c.pos[first];
            int i = rng.below(L), tpos;
            if (L == 2 || rng.uniform() < endp) {
                if (i == 0) tpos = L - 1;
                else if (i == L - 1) tpos = 0;
                else tpos = rng.below(2) ? 0 : L - 1;
            } else {
                tpos = rng.below(L - 1); if (tpos >= i) ++tpos;
            }
            backup = cur[mi];
            auto& row = cur[mi];
            int a = base + i, b = base + tpos;
            if (a < b) std::rotate(row.begin() + a, row.begin() + a + 1, row.begin() + b + 1);
            else std::rotate(row.begin() + b, row.begin() + a, row.begin() + a + 1);
            if (c.check(cur)) return true;
            cur[mi] = backup;
            c.check(cur);
            // fallback inside the block: adjacent critical swap (feasible by theory, verified)
            if (t + 1 == maxTries) {
                int p = rng.below(L - 1);
                if (c.try_swap(cur, mi, base + p)) return true;
            }
        }
        return false;
    }

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        Model::Solution cur = s;
        if (!c.check(cur)) return c.repair(s, rng);
        int moves = std::max(1, (int)std::lround(std::max(1.0, strength) * scale));
        for (int t = 0; t < moves; ++t) {
            if (!one_move(cur, rng) && !c.any_swap(cur, rng)) break;
        }
        if (cur == s) c.any_swap(cur, rng);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("moves_scale", 1.5);
    double ep = params.get("endpoint_prob", 0.6);
    int mt = (int)params.get("max_tries", 8);
    if (mt < 1) mt = 1;
    return std::make_unique<CriticalBlockInsertion>(model, sc, ep, mt);
}
