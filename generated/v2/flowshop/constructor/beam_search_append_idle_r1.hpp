// COMPONENT: {"name": "beam_search_append_idle", "slot": "constructor", "params": {"beam_width": {"type": "int", "range": [1, 12]}, "idle_weight": {"type": "float", "range": [0.0, 3.0]}, "noise": {"type": "float", "range": [0.0, 0.1]}}}
class BeamAppend : public hsf::Constructor<Model> {
public:
    BeamAppend(const Model& md, int w, double beta, double noise)
        : M(md), W(std::max(1, w)), beta_(std::max(0.0, beta)), noise_(std::max(0.0, noise)) {}

    struct Cand { double score; int b; int j; };

    Model::Solution build(Rng& rng) override {
        const int n = M.n, m = M.m;
        Model::Solution out(1);
        if (n <= 0) return out;
        if (m <= 0) {
            std::vector<int> p(n);
            std::iota(p.begin(), p.end(), 0);
            out[0] = p;
            return out;
        }
        int nb = 1;
        std::vector<int> seq((size_t)W * n), nseq((size_t)W * n);
        std::vector<char> used((size_t)W * n, 0), nused((size_t)W * n, 0);
        std::vector<long long> C((size_t)W * m, 0), nC((size_t)W * m, 0);
        std::vector<long long> F(W, 0), nF(W, 0);
        std::vector<Cand> cands;
        cands.reserve((size_t)W * n);
        std::vector<long long> tmp(m);
        for (int k = 0; k < n; ++k) {
            cands.clear();
            double remFactor = (double)(n - k - 1) / (double)n;
            for (int b = 0; b < nb; ++b) {
                const long long* cb = &C[(size_t)b * m];
                const char* ub = &used[(size_t)b * n];
                for (int j = 0; j < n; ++j) {
                    if (ub[j]) continue;
                    const long long* p = &M.pj[(size_t)j * m];
                    long long prev = cb[0] + p[0];
                    double idle = 0.0;
                    for (int i = 1; i < m; ++i) {
                        if (prev > cb[i]) idle += (double)(prev - cb[i]);
                        prev = std::max(prev, cb[i]) + p[i];
                    }
                    double s = (double)(F[b] + prev) + beta_ * remFactor * idle;
                    if (noise_ > 0) s *= 1.0 + noise_ * rng.uniform();
                    cands.push_back({s, b, j});
                }
            }
            int keep = std::min<int>(W, (int)cands.size());
            auto cmp = [](const Cand& a, const Cand& c) {
                if (a.score != c.score) return a.score < c.score;
                if (a.b != c.b) return a.b < c.b;
                return a.j < c.j;
            };
            std::partial_sort(cands.begin(), cands.begin() + keep, cands.end(), cmp);
            for (int t = 0; t < keep; ++t) {
                const Cand& cd = cands[t];
                int b = cd.b, j = cd.j;
                std::copy(seq.begin() + (size_t)b * n, seq.begin() + (size_t)b * n + k, nseq.begin() + (size_t)t * n);
                nseq[(size_t)t * n + k] = j;
                std::copy(used.begin() + (size_t)b * n, used.begin() + (size_t)(b + 1) * n, nused.begin() + (size_t)t * n);
                nused[(size_t)t * n + j] = 1;
                const long long* cb = &C[(size_t)b * m];
                long long* nc = &nC[(size_t)t * m];
                const long long* p = &M.pj[(size_t)j * m];
                nc[0] = cb[0] + p[0];
                for (int i = 1; i < m; ++i) nc[i] = std::max(nc[i - 1], cb[i]) + p[i];
                nF[t] = F[b] + nc[m - 1];
            }
            nb = keep;
            seq.swap(nseq);
            used.swap(nused);
            C.swap(nC);
            F.swap(nF);
        }
        int bi = 0;
        for (int b = 1; b < nb; ++b) if (F[b] < F[bi]) bi = b;
        out[0].assign(seq.begin() + (size_t)bi * n, seq.begin() + (size_t)(bi + 1) * n);
        return out;
    }

private:
    const Model& M;
    int W;
    double beta_, noise_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("beam_width", 4);
    double b = params.get("idle_weight", 1.0);
    double nz = params.get("noise", 0.02);
    return std::make_unique<BeamAppend>(model, w, b, nz);
}
