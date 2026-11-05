// COMPONENT: {"name": "jssp_job_ruin_greedy_reinsert", "slot": "perturbation", "params": {"jobs_scale": {"type": "float", "range": [0.3, 2.0]}, "insert_noise": {"type": "float", "range": [0.0, 0.5]}, "job_select": {"type": "cat", "values": ["critical", "random"]}}}
struct JCoreB {
    using Sol = Model::Solution;
    const Model& md;
    int n, m, N;
    std::vector<int> opJob, opMach, opPrev, opNext, opProc;
    std::vector<int> mp, ms, indeg, topo, pos;
    std::vector<long long> head, tail;
    explicit JCoreB(const Model& mod) : md(mod), n(mod.n), m(mod.m), N(mod.total_ops) {
        opJob.assign(N, -1); opMach.assign(N, -1); opPrev.assign(N, -1); opNext.assign(N, -1); opProc.assign(N, 0);
        for (int j = 0; j < n; ++j) {
            int prev = -1;
            for (const auto& pr : md.routes[j]) {
                int o = md.op_of[j][pr.first];
                opJob[o] = j; opMach[o] = pr.first; opProc[o] = pr.second; opPrev[o] = prev;
                if (prev >= 0) opNext[prev] = o;
                prev = o;
            }
        }
        mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0); pos.assign(N, 0);
        head.assign(N, 0); tail.assign(N, 0); topo.reserve(N);
    }
    bool load(const Sol& s) {
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        std::fill(indeg.begin(), indeg.end(), 0);
        if ((int)s.size() != m) return false;
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            int prev = -1;
            for (int j : s[i]) {
                if (j < 0 || j >= n) return false;
                int o = md.op_of[j][i];
                if (o < 0 || indeg[o]) return false;
                indeg[o] = 1;
                mp[o] = prev; if (prev >= 0) ms[prev] = o; prev = o; ++cnt;
            }
        }
        return cnt == N;
    }
    bool times() {
        topo.clear();
        for (int o = 0; o < N; ++o) {
            indeg[o] = (opPrev[o] >= 0) + (mp[o] >= 0);
            head[o] = 0;
            if (!indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h]; long long e = head[o] + opProc[o];
            int a = opNext[o];
            if (a >= 0) { if (head[a] < e) head[a] = e; if (--indeg[a] == 0) topo.push_back(a); }
            a = ms[o];
            if (a >= 0) { if (head[a] < e) head[a] = e; if (--indeg[a] == 0) topo.push_back(a); }
        }
        if ((int)topo.size() != N) return false;
        for (int t = 0; t < N; ++t) pos[topo[t]] = t;
        return true;
    }
    long long tails() {
        long long mk = 0;
        for (int t = N - 1; t >= 0; --t) {
            int o = topo[t]; long long q = 0;
            int a = opNext[o]; if (a >= 0) q = std::max(q, (long long)opProc[a] + tail[a]);
            a = ms[o]; if (a >= 0) q = std::max(q, (long long)opProc[a] + tail[a]);
            tail[o] = q; mk = std::max(mk, head[o] + opProc[o] + q);
        }
        return mk;
    }
    bool minspan_swap(Sol& cur) const {
        int best = std::numeric_limits<int>::max(), bi = -1, bt = -1;
        for (int i = 0; i < m; ++i)
            for (int t = 0; t + 1 < (int)cur[i].size(); ++t) {
                int u = md.op_of[cur[i][t]][i], v = md.op_of[cur[i][t + 1]][i];
                int d = pos[v] - pos[u];
                if (d < best) { best = d; bi = i; bt = t; }
            }
        if (bi < 0) return false;
        std::swap(cur[bi][bt], cur[bi][bt + 1]);
        return true;
    }
};

static int pick_weighted_b(const std::vector<double>& w, Rng& rng) {
    double tot = 0; for (double x : w) tot += x;
    if (tot <= 0) return -1;
    double x = rng.uniform() * tot; int last = -1;
    for (int i = 0; i < (int)w.size(); ++i) {
        if (w[i] <= 0) continue;
        last = i; x -= w[i];
        if (x < 0) return i;
    }
    return last;
}

class JobRuinGreedyReinsert : public hsf::Perturbation<Model> {
    JCoreB g; double scale, noise; bool crit;
    std::vector<char> present, removed;
    std::vector<int> mark, stk, jobs;
    std::vector<long long> rest;
    std::vector<double> w, tmp;
    int stamp = 0;

    void link(const Model::Solution& seq) {
        std::fill(g.mp.begin(), g.mp.end(), -1); std::fill(g.ms.begin(), g.ms.end(), -1);
        for (int i = 0; i < g.m; ++i) {
            int prev = -1;
            for (int j : seq[i]) {
                int o = g.md.op_of[j][i];
                g.mp[o] = prev; if (prev >= 0) g.ms[prev] = o; prev = o;
            }
        }
    }
    void partial_times() {
        auto& topo = g.topo; topo.clear();
        for (int o = 0; o < g.N; ++o) {
            if (!present[o]) continue;
            g.head[o] = 0;
            g.indeg[o] = (g.opPrev[o] >= 0) + (g.mp[o] >= 0);
            if (!g.indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h]; long long e = g.head[o] + g.opProc[o];
            int a = g.opNext[o];
            if (a >= 0 && present[a]) { if (g.head[a] < e) g.head[a] = e; if (--g.indeg[a] == 0) topo.push_back(a); }
            a = g.ms[o];
            if (a >= 0) { if (g.head[a] < e) g.head[a] = e; if (--g.indeg[a] == 0) topo.push_back(a); }
        }
        for (int t = (int)topo.size() - 1; t >= 0; --t) {
            int o = topo[t]; long long q = 0;
            int a = g.opNext[o];
            if (a >= 0 && present[a]) q = std::max(q, (long long)g.opProc[a] + g.tail[a]);
            a = g.ms[o];
            if (a >= 0) q = std::max(q, (long long)g.opProc[a] + g.tail[a]);
            g.tail[o] = q;
        }
    }
    void insert_op(Model::Solution& seq, int v, double nz, Rng& rng) {
        link(seq); partial_times();
        int i = g.opMach[v], j = g.opJob[v], prv = g.opPrev[v];
        long long prevEnd = prv >= 0 ? g.head[prv] + g.opProc[prv] : 0;
        auto& row = seq[i];
        int len = (int)row.size(), L = 0;
        if (prv >= 0) {
            // ops on machine i that reach prv must stay before v
            ++stamp; stk.clear(); stk.push_back(prv); mark[prv] = stamp;
            while (!stk.empty()) {
                int x = stk.back(); stk.pop_back();
                int y = g.opPrev[x];
                if (y >= 0 && mark[y] != stamp) { mark[y] = stamp; stk.push_back(y); }
                y = g.mp[x];
                if (y >= 0 && mark[y] != stamp) { mark[y] = stamp; stk.push_back(y); }
            }
            for (int t = len - 1; t >= 0; --t)
                if (mark[g.md.op_of[row[t]][i]] == stamp) { L = t + 1; break; }
        }
        double best = std::numeric_limits<double>::max(); int bp = len;
        for (int p = L; p <= len; ++p) {
            int a = p > 0 ? g.md.op_of[row[p - 1]][i] : -1;
            int b = p < len ? g.md.op_of[row[p]][i] : -1;
            long long st = std::max(a >= 0 ? g.head[a] + g.opProc[a] : 0LL, prevEnd);
            long long tl = std::max(b >= 0 ? g.opProc[b] + g.tail[b] : 0LL, rest[v]);
            double val = (double)(st + g.opProc[v] + tl) * (1.0 + nz * rng.uniform());
            if (val < best) { best = val; bp = p; }
        }
        row.insert(row.begin() + bp, j);
        present[v] = 1;
    }
public:
    JobRuinGreedyReinsert(const Model& md, double sc, double nz, bool cr) : g(md), scale(sc), noise(nz), crit(cr) {
        mark.assign(g.N, 0); present.assign(g.N, 0); rest.assign(g.N, 0);
        for (int j = 0; j < g.n; ++j) {
            long long acc = 0;
            const auto& R = md.routes[j];
            for (int k = (int)R.size() - 1; k >= 0; --k) {
                int o = md.op_of[j][R[k].first];
                rest[o] = acc; acc += R[k].second;
            }
        }
    }

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        const int n = g.n, m = g.m, N = g.N;
        bool ok = g.load(s) && g.times();
        int r = n;
        if (ok) {
            r = std::max(1, std::min(n, (int)std::lround(scale * strength)));
            if (crit) {
                long long mk = g.tails();
                w.assign(n, 0.1);
                for (int o = 0; o < N; ++o)
                    if (g.head[o] + g.opProc[o] + g.tail[o] == mk) w[g.opJob[o]] += 1.0;
            } else w.assign(n, 1.0);
        }
        for (int att = 0; att < 4; ++att) {
            removed.assign(n, 0);
            if (r >= n) std::fill(removed.begin(), removed.end(), 1);
            else {
                tmp = w;
                for (int t = 0; t < r; ++t) {
                    int j = pick_weighted_b(tmp, rng);
                    if (j < 0) break;
                    removed[j] = 1; tmp[j] = 0;
                }
            }
            Model::Solution seq(m);
            if (ok)
                for (int i = 0; i < m; ++i) {
                    seq[i].reserve(s[i].size());
                    for (int j : s[i]) if (!removed[j]) seq[i].push_back(j);
                }
            for (int o = 0; o < N; ++o) present[o] = (g.opJob[o] >= 0 && !removed[g.opJob[o]]) ? 1 : 0;
            jobs.clear();
            for (int j = 0; j < n; ++j) if (removed[j]) jobs.push_back(j);
            std::shuffle(jobs.begin(), jobs.end(), rng.g);
            double nz = noise + 0.25 * att;
            for (int j : jobs)
                for (const auto& pr : g.md.routes[j]) insert_op(seq, g.md.op_of[j][pr.first], nz, rng);
            if (!ok || seq != s) return seq;
        }
        Model::Solution cur = s;
        g.load(s); g.times();
        g.minspan_swap(cur);
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("jobs_scale", 0.8);
    double nz = params.get("insert_noise", 0.1);
    bool cr = params.text("job_select", "critical") == "critical";
    return std::make_unique<JobRuinGreedyReinsert>(model, sc, nz, cr);
}
