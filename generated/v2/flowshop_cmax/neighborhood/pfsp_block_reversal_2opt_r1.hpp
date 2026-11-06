// COMPONENT: {"name": "pfsp_block_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 200]}}}
class BlockReversal2Opt : public hsf::Neighborhood<Model> {
    using Sol = Model::Solution;
    const Model& M;
    int max_len;
    bool fast_ok = false;
    std::vector<int> seq;
    bool have = false, perm = false;
    long long cmax = 0;
    std::vector<long long> e, f, cur;
    std::vector<char> mark;

    long long P(int job, int q) const { return M.pt[(size_t)job * M.m + q]; }

    bool ensure(const Sol& s) {
        if (!fast_ok || s.size() != 1) return false;
        const auto& v = s[0];
        if (have && v == seq) return perm;
        seq = v; have = true; perm = false;
        int L = (int)v.size();
        if (L != M.n) return false;
        mark.assign(M.n, 0);
        for (int x : v) { if (x < 0 || x >= M.n || mark[x]) return false; mark[x] = 1; }
        perm = true;
        int m = M.m;
        e.assign((size_t)(L + 1) * m, 0);
        f.assign((size_t)(L + 1) * m, 0);
        for (int k = 1; k <= L; ++k) {
            int job = v[k - 1];
            long long* row = &e[(size_t)k * m];
            const long long* prev = &e[(size_t)(k - 1) * m];
            row[0] = prev[0] + P(job, 0);
            for (int q = 1; q < m; ++q) row[q] = std::max(row[q - 1], prev[q]) + P(job, q);
        }
        for (int k = L - 1; k >= 0; --k) {
            int job = v[k];
            long long* row = &f[(size_t)k * m];
            const long long* nxt = &f[(size_t)(k + 1) * m];
            row[m - 1] = nxt[m - 1] + P(job, m - 1);
            for (int q = m - 2; q >= 0; --q) row[q] = std::max(row[q + 1], nxt[q]) + P(job, q);
        }
        cmax = e[(size_t)L * m + m - 1];
        cur.assign(m, 0);
        return true;
    }

public:
    BlockReversal2Opt(const Model& model, int ml) : M(model), max_len(std::max(2, ml)) {
        if (M.m > 0 && M.n > 0) {
            Sol t = M.trivial();
            fast_ok = (M.objective(t) == (double)M.makespan(t));
        }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        for (int i = 0; i < L; ++i)
            for (int j = i + 1; j < L && j - i + 1 <= max_len; ++j) {
                Move mv{}; mv[0] = i; mv[1] = j; out.push_back(mv);
            }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        if (r.empty()) return r;
        auto& v = r[0];
        int L = (int)v.size();
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i < 0 || j >= L || i == j) return r;
        std::reverse(v.begin() + i, v.begin() + j + 1);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        if (!ensure(s)) return M.objective(apply(s, mv)) - M.objective(s);
        int L = (int)seq.size();
        int i = std::min(mv[0], mv[1]), j = std::max(mv[0], mv[1]);
        if (i < 0 || j >= L || i == j) return 0.0;
        int m = M.m;
        const long long* eh = &e[(size_t)i * m];
        for (int q = 0; q < m; ++q) cur[q] = eh[q];
        for (int k = j; k >= i; --k) {
            int job = seq[k];
            cur[0] += P(job, 0);
            for (int q = 1; q < m; ++q) cur[q] = std::max(cur[q], cur[q - 1]) + P(job, q);
        }
        const long long* ft = &f[(size_t)(j + 1) * m];
        long long best = 0;
        for (int q = 0; q < m; ++q) best = std::max(best, cur[q] + ft[q]);
        return (double)best - (double)cmax;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ml = (int)params.get("max_len", 20);
    return std::make_unique<BlockReversal2Opt>(model, ml);
}
