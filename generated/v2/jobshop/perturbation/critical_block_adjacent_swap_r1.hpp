// COMPONENT: {"name": "critical_block_adjacent_swap", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "mode": {"type": "cat", "values": ["n5", "n1"]}}}
namespace {
using Sol = std::vector<std::vector<int>>;

struct Sched {
    const Model& M;
    int N, Mn;
    std::vector<int> jpred, opjob, mpred, msucc, pos, indeg, order;
    std::vector<long long> st;
    explicit Sched(const Model& m)
        : M(m), N(m.n_ops), Mn(m.n_machines), jpred(N, -1), opjob(N, 0), mpred(N, -1), msucc(N, -1),
          pos(N, 0), indeg(N, 0), st(N, 0) {
        for (int j = 0; j < M.n_jobs; ++j)
            for (int k = 0; k < M.job_len[j]; ++k) opjob[M.job_off[j] + k] = j;
        for (int o = 0; o < N; ++o)
            if (M.op_next[o] >= 0) jpred[M.op_next[o]] = o;
        order.reserve(N);
    }
    bool run(const Sol& s) {
        if ((int)s.size() != Mn) return false;
        std::fill(mpred.begin(), mpred.end(), -1);
        std::fill(msucc.begin(), msucc.end(), -1);
        int total = 0;
        for (int m = 0; m < Mn; ++m) {
            const auto& seq = s[m];
            int prev = -1;
            total += (int)seq.size();
            for (int i = 0; i < (int)seq.size(); ++i) {
                int j = seq[i];
                if (j < 0 || j >= M.n_jobs) return false;
                int o = M.op_index[(size_t)j * Mn + m];
                if (o < 0) return false;
                pos[o] = i;
                if (prev >= 0) { msucc[prev] = o; mpred[o] = prev; }
                prev = o;
            }
        }
        if (total != N) return false;
        order.clear();
        for (int o = 0; o < N; ++o) {
            indeg[o] = (jpred[o] >= 0 ? 1 : 0) + (mpred[o] >= 0 ? 1 : 0);
            st[o] = 0;
            if (indeg[o] == 0) order.push_back(o);
        }
        for (size_t h = 0; h < order.size(); ++h) {
            int o = order[h];
            long long e = st[o] + M.op_proc[o];
            int a = M.op_next[o];
            if (a >= 0) { if (st[a] < e) st[a] = e; if (--indeg[a] == 0) order.push_back(a); }
            int b = msucc[o];
            if (b >= 0) { if (st[b] < e) st[b] = e; if (--indeg[b] == 0) order.push_back(b); }
        }
        return (int)order.size() == N;
    }
};

class CriticalBlockSwap : public hsf::Perturbation<Model> {
    const Model& M;
    Sched S;
    double scale;
    bool n1;
    std::vector<int> path, cand;

    void collect(Rng& rng) {
        cand.clear();
        path.clear();
        long long best = -1; int last = -1, ties = 0;
        for (int o = 0; o < S.N; ++o) {
            long long e = S.st[o] + M.op_proc[o];
            if (e > best) { best = e; last = o; ties = 1; }
            else if (e == best) { ++ties; if (rng.below(ties) == 0) last = o; }
        }
        int o = last;
        while (o >= 0) {
            path.push_back(o);
            int a = S.jpred[o], b = S.mpred[o];
            bool ta = a >= 0 && S.st[a] + M.op_proc[a] == S.st[o];
            bool tb = b >= 0 && S.st[b] + M.op_proc[b] == S.st[o];
            if (ta && tb) o = rng.below(2) ? a : b;
            else if (ta) o = a;
            else if (tb) o = b;
            else o = -1;
        }
        std::reverse(path.begin(), path.end());
        size_t i = 0;
        while (i + 1 < path.size()) {
            if (S.mpred[path[i + 1]] != path[i]) { ++i; continue; }
            size_t b = i;
            while (i + 1 < path.size() && S.mpred[path[i + 1]] == path[i]) ++i;
            // block ops path[b..i], pairs start at b..i-1
            if (n1) {
                for (size_t k = b; k < i; ++k) cand.push_back(path[k]);
            } else {
                cand.push_back(path[b]);
                if (i - 1 > b) cand.push_back(path[i - 1]);
            }
        }
    }

    Sol fallback(const Sol& s, Rng& rng) {
        int tries = 0;
        while (tries < 64) {
            int m = rng.below(S.Mn);
            if (s[m].size() < 2) { ++tries; continue; }
            int i = rng.below((int)s[m].size() - 1);
            Sol t = s;
            std::swap(t[m][i], t[m][i + 1]);
            if (S.run(t)) return t;
            ++tries;
        }
        for (int r = 0; r < 10; ++r) {
            Sol t = M.random(rng);
            if (t != s) return t;
        }
        return M.random(rng);
    }

public:
    CriticalBlockSwap(const Model& m, double sc, bool useN1) : M(m), S(m), scale(sc), n1(useN1) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (!S.run(s)) return M.random(rng);
        Sol cur = s;
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * scale));
        for (int t = 0; t < k; ++t) {
            if (t > 0) S.run(cur);
            collect(rng);
            if (cand.empty()) break;
            int o = cand[rng.below((int)cand.size())];
            int m = M.op_mach[o];
            int p = S.pos[o];
            std::swap(cur[m][p], cur[m][p + 1]);
        }
        if (cur == s) return fallback(s, rng);
        return cur;
    }
};
}  // namespace

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double scale = params.get("scale", 1.0);
    bool n1 = params.text("mode", "n5") == "n1";
    return std::make_unique<CriticalBlockSwap>(model, scale, n1);
}
