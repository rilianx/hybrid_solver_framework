// COMPONENT: {"name": "pfsp_job_insertion_taillard", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [0, 500]}}}
class JobInsertionTaillard : public hsf::Neighborhood<Model> {
    using Sol = Model::Solution;
    const Model& M;
    int window;
    bool fast_ok = false;
    std::vector<int> seq;
    bool have = false, perm = false;
    long long cmax = 0;
    int ri = -1;
    std::vector<long long> e, f, cur;
    std::vector<int> red;
    std::vector<char> mark;

    long long P(int job, int q) const { return M.pt[(size_t)job * M.m + q]; }

    bool ensure(const Sol& s) {
        if (!fast_ok || s.size() != 1) return false;
        const auto& v = s[0];
        if (have && v == seq) return perm;
        seq = v; have = true; ri = -1; perm = false;
        int L = (int)v.size();
        if (L != M.n) return false;
        mark.assign(M.n, 0);
        for (int x : v) { if (x < 0 || x >= M.n || mark[x]) return false; mark[x] = 1; }
        perm = true;
        int m = M.m;
        cur.assign(m, 0);
        for (int k = 0; k < L; ++k) {
            int job = v[k];
            cur[0] += P(job, 0);
            for (int q = 1; q < m; ++q) cur[q] = std::max(cur[q], cur[q - 1]) + P(job, q);
        }
        cmax = cur[m - 1];
        return true;
    }

    void prepare(int i) {
        if (ri == i) return;
        ri = i;
        int L = (int)seq.size(), m = M.m;
        red.clear();
        for (int k = 0; k < L; ++k) if (k != i) red.push_back(seq[k]);
        e.assign((size_t)L * m, 0);
        f.assign((size_t)L * m, 0);
        for (int k = 1; k < L; ++k) {
            int job = red[k - 1];
            long long* row = &e[(size_t)k * m];
            const long long* prev = &e[(size_t)(k - 1) * m];
            row[0] = prev[0] + P(job, 0);
            for (int q = 1; q < m; ++q) row[q] = std::max(row[q - 1], prev[q]) + P(job, q);
        }
        for (int k = L - 2; k >= 0; --k) {
            int job = red[k];
            long long* row = &f[(size_t)k * m];
            const long long* nxt = &f[(size_t)(k + 1) * m];
            row[m - 1] = nxt[m - 1] + P(job, m - 1);
            for (int q = m - 2; q >= 0; --q) row[q] = std::max(row[q + 1], nxt[q]) + P(job, q);
        }
    }

public:
    JobInsertionTaillard(const Model& model, int w) : M(model), window(w) {
        if (M.m > 0 && M.n > 0) {
            Sol t = M.trivial();
            fast_ok = (M.objective(t) == (double)M.makespan(t));
        }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        if (s.empty()) return;
        int L = (int)s[0].size();
        for (int i = 0; i < L; ++i)
            for (int j = 0; j < L; ++j) {
                if (j == i || j == i - 1) continue;
                if (window > 0 && std::abs(j - i) > window) continue;
                Move mv{}; mv[0] = i; mv[1] = j; out.push_back(mv);
            }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        if (r.empty()) return r;
        auto& v = r[0];
        int L = (int)v.size(), i = mv[0], j = mv[1];
        if (i < 0 || j < 0 || i >= L || j >= L || i == j) return r;
        if (i < j) std::rotate(v.begin() + i, v.begin() + i + 1, v.begin() + j + 1);
        else std::rotate(v.begin() + j, v.begin() + i, v.begin() + i + 1);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        int i = mv[0], j = mv[1];
        if (!ensure(s)) return M.objective(apply(s, mv)) - M.objective(s);
        int L = (int)seq.size();
        if (i < 0 || j < 0 || i >= L || j >= L || i == j) return 0.0;
        prepare(i);
        int m = M.m, x = seq[i];
        const long long* eh = &e[(size_t)j * m];
        const long long* ft = &f[(size_t)j * m];
        long long c = eh[0] + P(x, 0);
        long long best = c + ft[0];
        for (int q = 1; q < m; ++q) {
            c = std::max(c, eh[q]) + P(x, q);
            best = std::max(best, c + ft[q]);
        }
        return (double)best - (double)cmax;
    }

    Move tabu_key(const Move& mv) override {
        Move k{};
        int i = mv[0], j = mv[1];
        if (j == i + 1) { k[0] = i; k[1] = j; }
        else { k[0] = j; k[1] = i; }
        return k;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 0);
    return std::make_unique<JobInsertionTaillard>(model, w);
}
