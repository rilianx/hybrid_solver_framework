// COMPONENT: {"name": "job_flowtime_power_tiebreak", "slot": "tiebreak", "params": {"power": {"type": "int", "range": [1, 3]}, "start_weight": {"type": "float", "range": [0.0, 0.5]}}}
class JobFlowtimePower : public hsf::TieBreak<Model> {
public:
    using Sol = Model::Solution;
    JobFlowtimePower(const Model& m, int pw, double sw) : M(m), N(m.total_ops), power(pw), sw(sw) {
        jprev.assign(N, -1); mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0);
        q.assign(N, 0); mark.assign(N, 0); head.assign(N, 0); tail.assign(N, 0);
        for (int o = 0; o < N; ++o) if (M.op_next[o] >= 0) jprev[M.op_next[o]] = o;
        for (int o = 0; o < N; ++o) if (M.op_next[o] < 0) lastOps.push_back(o);
    }
    double score(const Sol& s) override {
        if (N == 0) return 0.0;
        if (!run(s)) {
            double idx = 0.0;
            for (int k = 0; k < done; ++k) { int o = q[k]; idx += double(head[o] + 1) * double(o + 1); }
            double den = double(N) * double(N + 1) * double(std::max<long long>(cmax, 1) + 1);
            return 1e9 + double(N - done) + 0.5 * idx / den;
        }
        double C = double(std::max<long long>(cmax, 1));
        // tails (pasada hacia atrás en orden topológico inverso) y operaciones críticas
        int crit = 0;
        for (int k = N - 1; k >= 0; --k) {
            int u = q[k]; long long t = 0;
            int a = M.op_next[u], b = ms[u];
            if (a >= 0) t = std::max(t, (long long)M.op_proc[a] + tail[a]);
            if (b >= 0) t = std::max(t, (long long)M.op_proc[b] + tail[b]);
            tail[u] = t;
            if (head[u] + M.op_proc[u] + t == cmax) ++crit;
        }
        double critFrac = double(crit) / double(N);
        double idx = 0.0;
        for (int o = 0; o < N; ++o) idx += double(head[o]) * double(o + 1);
        idx /= (double(N) * double(N + 1) * 0.5 * C);
        double flow = 0.0;
        for (int o : lastOps) {
            double r = double(head[o] + M.op_proc[o]) / C;
            double v = r; for (int k = 1; k < power; ++k) v *= r;
            flow += v;
        }
        flow /= double(std::max<size_t>(lastOps.size(), 1));
        double starts = 0.0;
        for (int o = 0; o < N; ++o) starts += double(head[o]);
        starts /= (double(N) * C);
        return flow + sw * starts + 0.5 * critFrac + 1e-3 * idx;
    }
private:
    const Model& M; int N; int power; double sw;
    std::vector<int> jprev, mp, ms, indeg, q, mark, lastOps;
    std::vector<long long> head, tail;
    int stamp = 0, done = 0; long long cmax = 0;
    bool run(const Sol& s) {
        if (++stamp >= 2000000000) { std::fill(mark.begin(), mark.end(), 0); stamp = 1; }
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        int mm = std::min<int>(M.m, (int)s.size());
        for (int i = 0; i < mm; ++i) {
            int prev = -1;
            for (int j : s[i]) {
                if (j < 0 || j >= M.n) continue;
                int op = M.opflat[(size_t)i * M.n + j];
                if (op < 0 || mark[op] == stamp) continue;
                mark[op] = stamp; mp[op] = prev; if (prev >= 0) ms[prev] = op; prev = op;
            }
        }
        int qt = 0;
        for (int o = 0; o < N; ++o) {
            indeg[o] = (jprev[o] >= 0) + (mp[o] >= 0); head[o] = 0;
            if (!indeg[o]) q[qt++] = o;
        }
        cmax = 0;
        for (int qh = 0; qh < qt; ++qh) {
            int u = q[qh]; long long f = head[u] + M.op_proc[u];
            if (f > cmax) cmax = f;
            int vs[2] = {M.op_next[u], ms[u]};
            for (int v : vs) if (v >= 0) { if (head[v] < f) head[v] = f; if (--indeg[v] == 0) q[qt++] = v; }
        }
        done = qt;
        return qt == N;
    }
};

std::unique_ptr<hsf::TieBreak<Model>> make_component(const Model& model, const hsf::Config& params) {
    int pw = (int)params.get("power", 2);
    pw = std::max(1, std::min(3, pw));
    return std::make_unique<JobFlowtimePower>(model, pw, params.get("start_weight", 0.1));
}
