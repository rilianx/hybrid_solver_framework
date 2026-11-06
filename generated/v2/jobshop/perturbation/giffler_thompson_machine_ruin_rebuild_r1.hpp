// COMPONENT: {"name": "giffler_thompson_machine_ruin_rebuild", "slot": "perturbation", "params": {"machines_per_strength": {"type": "float", "range": [0.3, 3.0]}, "key_noise": {"type": "float", "range": [0.0, 1.0]}}}
namespace {
using Sol = std::vector<std::vector<int>>;

struct Sched {
    const Model& M;
    int N, Mn;
    std::vector<int> jpred, mpred, msucc, indeg, order;
    std::vector<long long> st;
    explicit Sched(const Model& m)
        : M(m), N(m.n_ops), Mn(m.n_machines), jpred(N, -1), mpred(N, -1), msucc(N, -1), indeg(N, 0), st(N, 0) {
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

class GtRuinRebuild : public hsf::Perturbation<Model> {
    const Model& M;
    Sched S;
    double mps, keyNoise;
    std::vector<double> key;
    std::vector<int> nxt, conf, machPerm;
    std::vector<long long> jr, mr;
    std::vector<char> ruined;

    Sol gt(Rng& rng) {
        int nj = M.n_jobs, Mn = S.Mn;
        Sol out(Mn);
        for (int m = 0; m < Mn; ++m) out[m].reserve(M.mach_jobs[m].size());
        for (int j = 0; j < nj; ++j) { nxt[j] = M.job_len[j] > 0 ? M.job_off[j] : -1; jr[j] = 0; }
        std::fill(mr.begin(), mr.end(), 0LL);
        for (int step = 0; step < S.N; ++step) {
            long long cstar = std::numeric_limits<long long>::max();
            int mstar = -1, jstar = -1;
            for (int j = 0; j < nj; ++j) {
                int o = nxt[j];
                if (o < 0) continue;
                int m = M.op_mach[o];
                long long est = std::max(jr[j], mr[m]);
                long long c = est + M.op_proc[o];
                if (c < cstar) { cstar = c; mstar = m; jstar = j; }
            }
            if (jstar < 0) break;
            conf.clear();
            for (int j = 0; j < nj; ++j) {
                int o = nxt[j];
                if (o < 0 || M.op_mach[o] != mstar) continue;
                long long est = std::max(jr[j], mr[mstar]);
                if (est < cstar || j == jstar) conf.push_back(j);
            }
            int pick;
            if (ruined[mstar]) {
                pick = conf[rng.below((int)conf.size())];
            } else {
                pick = conf[0];
                for (size_t q = 1; q < conf.size(); ++q) {
                    int a = nxt[conf[q]], b = nxt[pick];
                    if (key[a] < key[b] || (key[a] == key[b] && a < b)) pick = conf[q];
                }
            }
            int o = nxt[pick];
            long long est = std::max(jr[pick], mr[mstar]);
            long long e = est + M.op_proc[o];
            jr[pick] = e;
            mr[mstar] = e;
            out[mstar].push_back(pick);
            nxt[pick] = M.op_next[o];
        }
        return out;
    }

public:
    GtRuinRebuild(const Model& m, double p, double kn)
        : M(m), S(m), mps(p), keyNoise(kn), key(m.n_ops, 0.0), nxt(m.n_jobs, -1), machPerm(m.n_machines),
          jr(m.n_jobs, 0), mr(m.n_machines, 0), ruined(m.n_machines, 0) {
        conf.reserve(m.n_jobs);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (!S.run(s)) return M.random(rng);
        int Mn = S.Mn;
        for (int o = 0; o < S.N; ++o)
            key[o] = (double)S.st[o] + (keyNoise > 0.0 ? keyNoise * rng.uniform() * M.op_proc[o] : 0.0);
        std::iota(machPerm.begin(), machPerm.end(), 0);
        for (int i = Mn - 1; i > 0; --i) std::swap(machPerm[i], machPerm[rng.below(i + 1)]);
        int r = std::max(1, std::min(Mn, (int)std::lround(std::max(1.0, strength) * mps)));
        std::fill(ruined.begin(), ruined.end(), 0);
        for (int i = 0; i < r; ++i) ruined[machPerm[i]] = 1;
        for (int attempt = 0; attempt < 8; ++attempt) {
            Sol out = gt(rng);
            if (out != s) return out;
            if (r < Mn) { ruined[machPerm[r]] = 1; ++r; }
        }
        for (int t = 0; t < 10; ++t) {
            Sol x = M.random(rng);
            if (x != s) return x;
        }
        return M.random(rng);
    }
};
}  // namespace

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double mps = params.get("machines_per_strength", 1.0);
    double kn = params.get("key_noise", 0.2);
    return std::make_unique<GtRuinRebuild>(model, mps, kn);
}
