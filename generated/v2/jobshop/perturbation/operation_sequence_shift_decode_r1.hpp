// COMPONENT: {"name": "operation_sequence_shift_decode", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 4.0]}, "max_shift": {"type": "int", "range": [2, 60]}, "move": {"type": "cat", "values": ["insert", "swap", "mixed"]}}}
namespace {
using Sol = std::vector<std::vector<int>>;

struct Sched {
    const Model& M;
    int N, Mn;
    std::vector<int> jpred, opjob, mpred, msucc, indeg, order;
    std::vector<long long> st;
    explicit Sched(const Model& m)
        : M(m), N(m.n_ops), Mn(m.n_machines), jpred(N, -1), opjob(N, 0), mpred(N, -1), msucc(N, -1),
          indeg(N, 0), st(N, 0) {
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

class OpSeqShiftDecode : public hsf::Perturbation<Model> {
    const Model& M;
    Sched S;
    double scale;
    int maxShift;
    int moveType;  // 0 insert, 1 swap, 2 mixed
    std::vector<int> seq, work, cnt;

    int target(int i, Rng& rng) const {
        int n = (int)work.size();
        int lim = std::max(1, std::min(maxShift, n - 1));
        int d = 1 + rng.below(lim);
        int j = rng.below(2) ? i + d : i - d;
        if (j < 0) j = i + d;
        if (j >= n) j = i - d;
        if (j < 0) j = 0;
        if (j >= n) j = n - 1;
        return j;
    }

    void oneMove(Rng& rng) {
        int n = (int)work.size();
        if (n < 2) return;
        int mt = moveType == 2 ? rng.below(2) : moveType;
        for (int tries = 0; tries < 8; ++tries) {
            int i = rng.below(n);
            int j = target(i, rng);
            if (i == j || work[i] == work[j]) continue;
            if (mt == 1) {
                std::swap(work[i], work[j]);
            } else {
                if (i < j) std::rotate(work.begin() + i, work.begin() + i + 1, work.begin() + j + 1);
                else std::rotate(work.begin() + j, work.begin() + i, work.begin() + i + 1);
            }
            return;
        }
    }

    Sol decode() {
        Sol out(S.Mn);
        for (int m = 0; m < S.Mn; ++m) out[m].reserve(M.mach_jobs[m].size());
        std::fill(cnt.begin(), cnt.end(), 0);
        for (int j : work) {
            int o = M.job_off[j] + cnt[j]++;
            out[M.op_mach[o]].push_back(j);
        }
        return out;
    }

public:
    OpSeqShiftDecode(const Model& m, double sc, int ms, int mt)
        : M(m), S(m), scale(sc), maxShift(ms), moveType(mt), cnt(m.n_jobs, 0) {
        seq.reserve(m.n_ops);
        work.reserve(m.n_ops);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (!S.run(s)) return M.random(rng);
        seq.resize(S.N);
        for (int h = 0; h < S.N; ++h) seq[h] = S.opjob[S.order[h]];
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * scale));
        for (int attempt = 0; attempt < 30; ++attempt) {
            work = seq;
            for (int t = 0; t < k; ++t) oneMove(rng);
            Sol out = decode();
            if (out != s) return out;
            if (attempt % 3 == 2) ++k;
        }
        for (int r = 0; r < 10; ++r) {
            Sol t = M.random(rng);
            if (t != s) return t;
        }
        return M.random(rng);
    }
};
}  // namespace

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double scale = params.get("scale", 1.5);
    int ms = (int)params.get("max_shift", 10);
    std::string mv = params.text("move", "mixed");
    int mt = mv == "insert" ? 0 : (mv == "swap" ? 1 : 2);
    return std::make_unique<OpSeqShiftDecode>(model, scale, ms, mt);
}
