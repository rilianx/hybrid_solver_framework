// COMPONENT: {"name": "soft_slack_criticality_tiebreak", "slot": "tiebreak", "params": {"tau": {"type": "float", "range": [0.1, 3.0]}}}
class SoftSlackCriticality : public hsf::TieBreak<Model> {
public:
    using Sol = Model::Solution;
    SoftSlackCriticality(const Model& m, double tau) : M(m), N(m.total_ops) {
        jprev.assign(N, -1); mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0);
        q.assign(N, 0); mark.assign(N, 0); head.assign(N, 0); tail.assign(N, 0);
        jobW.assign(N, 1.0);
        opMach.assign(N, -1);
        for (int i = 0; i < M.m; ++i)
            for (int j = 0; j < M.n; ++j) {
                int op = M.opflat[(size_t)i * M.n + j];
                if (op >= 0 && op < N) opMach[op] = i;
            }
        double sum = 0.0;
        for (int o = 0; o < N; ++o) { if (M.op_next[o] >= 0) jprev[M.op_next[o]] = o; sum += M.op_proc[o]; }
        int jc = 0;
        for (int o = 0; o < N; ++o) {
            if (jprev[o] >= 0) continue;
            ++jc;
            int u = o, guard = 0;
            while (u >= 0 && guard++ < N) { jobW[u] = double(jc); u = M.op_next[u]; }
        }
        numJobs = std::max(1, jc);
        sumW = 0.0;
        for (int o = 0; o < N; ++o) sumW += jobW[o];
        if (sumW <= 0.0) sumW = 1.0;
        double meanp = N > 0 ? std::max(1.0, sum / N) : 1.0;
        invScale = 1.0 / (std::max(0.01, tau) * meanp);
    }
    double score(const Sol& s) override {
        if (N == 0) return 0.0;
        if (!run(s)) return 1e9 + double(N - done);
        double acc = 0.0, flow = 0.0, wsum = 0.0;
        for (int u = 0; u < N; ++u) {
            long long fin = head[u] + M.op_proc[u];
            long long slack = cmax - (fin + tail[u]);
            if (slack < 0) slack = 0;
            double x = double(slack) * invScale;
            if (x < 40.0) acc += std::exp(-x);
            if (M.op_next[u] < 0) flow += double(fin);
            wsum += double(fin) * jobW[u];
        }
        double cm = cmax > 0 ? double(cmax) : 1.0;
        double flowN = flow / (double(numJobs) * cm);   // en (0,1]
        double wN = wsum / (sumW * cm);                 // en (0,1]
        return acc + 1e-3 * flowN + 1e-7 * wN;
    }
private:
    const Model& M; int N; double invScale = 1.0;
    std::vector<double> jobW; int numJobs = 1; double sumW = 1.0;
    std::vector<int> jprev, mp, ms, indeg, q, mark, opMach;
    // decodifica una entrada de la fila i: como job (opflat) o como id de operación
    inline int asJob(int i, int j) const {
        if (j < 0 || j >= M.n) return -1;
        int op = M.opflat[(size_t)i * M.n + j];
        return (op >= 0 && op < N) ? op : -1;
    }
    inline int asOp(int i, int j) const {
        if (j < 0 || j >= N) return -1;
        return (opMach[j] == i || opMach[j] < 0) ? j : -1;
    }
    std::vector<long long> head, tail;
    int stamp = 0, done = 0; long long cmax = 0;
    bool run(const Sol& s) {
        if (++stamp >= 2000000000) { std::fill(mark.begin(), mark.end(), 0); stamp = 1; }
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        int mm = std::min<int>(M.m, (int)s.size());
        for (int i = 0; i < mm; ++i) {
            int ca = 0, cb = 0;
            for (int j : s[i]) { if (asJob(i, j) >= 0) ++ca; if (asOp(i, j) >= 0) ++cb; }
            bool jobMode = ca >= cb;
            int prev = -1;
            for (int j : s[i]) {
                int op = jobMode ? asJob(i, j) : asOp(i, j);
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
        if (qt < N) return false;
        for (int k = N - 1; k >= 0; --k) {
            int u = q[k]; long long t = 0;
            int v = M.op_next[u]; if (v >= 0) t = std::max(t, tail[v] + M.op_proc[v]);
            v = ms[u]; if (v >= 0) t = std::max(t, tail[v] + M.op_proc[v]);
            tail[u] = t;
        }
        return true;
    }
};

std::unique_ptr<hsf::TieBreak<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<SoftSlackCriticality>(model, params.get("tau", 1.0));
}
