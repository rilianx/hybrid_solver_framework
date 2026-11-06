// COMPONENT: {"name": "critical_ops_count_tiebreak", "slot": "tiebreak", "params": {"arc_weight": {"type": "float", "range": [0.0, 1.0]}}}
class CriticalOpsCount : public hsf::TieBreak<Model> {
public:
    using Sol = Model::Solution;
    CriticalOpsCount(const Model& m, double w) : M(m), N(m.total_ops), aw(w) {
        jprev.assign(N, -1); mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0);
        q.assign(N, 0); mark.assign(N, 0); head.assign(N, 0); tail.assign(N, 0);
        for (int o = 0; o < N; ++o) if (M.op_next[o] >= 0) jprev[M.op_next[o]] = o;
    }
    double score(const Sol& s) override {
        if (N == 0) return 0.0;
        double fp = fingerprint(s);  // en [0, 1)
        if (!run(s)) {
            double hs = 0.0;
            for (int k = 0; k < done; ++k) hs += double(head[q[k]] + M.op_proc[q[k]]);
            double hf = hs / (double(N) * double(cmax) + 1.0);
            return 1e6 + double(N - done) + 0.5 * (1.0 - hf) + 0.01 * fp;
        }
        long long ncrit = 0, narc = 0;
        double sumc = 0.0;
        for (int u = 0; u < N; ++u) {
            long long p = M.op_proc[u];
            sumc += double(head[u] + p);
            if (head[u] + p + tail[u] == cmax) {
                ++ncrit;
                int v = mp[u];
                if (v >= 0 && head[v] + M.op_proc[v] == head[u] &&
                    head[v] + M.op_proc[v] + tail[v] == cmax) ++narc;
            }
        }
        double tc = sumc / (double(N) * double(cmax) + 1.0);  // en [0, 1)
        return double(ncrit) + aw * double(narc) / double(N + 1) + 0.49 * tc + 1e-7 * fp;
    }
    double fingerprint(const Sol& s) const {
        uint64_t h = 1469598103934665603ULL;
        for (size_t i = 0; i < s.size(); ++i) {
            h ^= 0x9E3779B97F4A7C15ULL + i; h *= 1099511628211ULL;
            for (int j : s[i]) {
                uint64_t x = (uint64_t)(int64_t)j + 0x632BE59BD9B4E019ULL;
                x ^= x >> 31; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 29;
                h = (h ^ x) * 1099511628211ULL;
            }
        }
        h ^= h >> 33; h *= 0xFF51AFD7ED558CCDULL; h ^= h >> 33;
        return double(h >> 11) * (1.0 / 9007199254740992.0);
    }
private:
    const Model& M; int N; double aw;
    std::vector<int> jprev, mp, ms, indeg, q, mark;
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
    return std::make_unique<CriticalOpsCount>(model, params.get("arc_weight", 0.5));
}
