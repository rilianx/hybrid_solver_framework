// COMPONENT: {"name": "hamming_flip_setup_first", "slot": "relink", "params": {"add_first_prob": {"type": "float", "range": [0.0, 1.0]}, "max_flips": {"type": "int", "range": [1, 4]}}}
class HammingFlipSetupFirst : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    double addFirst;
    int maxFlips;
    std::vector<int> adds, dels;
public:
    HammingFlipSetupFirst(const Model& model, double af, int mf) : m(model), addFirst(af), maxFlips(mf) {
        adds.reserve((size_t)m.n * m.T);
        dels.reserve((size_t)m.n * m.T);
    }
    int distance(const Sol& a, const Sol& b) override {
        int dd = 0;
        size_t R = std::min(a.size(), b.size());
        for (size_t i = 0; i < R; ++i) {
            const int* ai = a[i].data();
            const int* bi = b[i].data();
            size_t L = std::min(a[i].size(), b[i].size());
            for (size_t t = 0; t < L; ++t) dd += (ai[t] != bi[t]);
        }
        return dd;
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        adds.clear(); dels.clear();
        int T = m.T;
        for (int i = 0; i < m.n; ++i) {
            const int* ci = cur[i].data();
            const int* gi = guide[i].data();
            for (int t = 0; t < T; ++t) {
                if (ci[t] != gi[t]) {
                    if (ci[t] == 0) adds.push_back(i * T + t);
                    else dels.push_back(i * T + t);
                }
            }
        }
        Sol out = cur;
        int total = (int)(adds.size() + dels.size());
        if (total == 0) return out;
        int k = 1 + rng.below(std::max(1, maxFlips));
        if (k > total) k = total;
        for (int f = 0; f < k; ++f) {
            std::vector<int>* L;
            if (!adds.empty() && (dels.empty() || rng.uniform() < addFirst)) L = &adds;
            else L = &dels;
            int p = rng.below((int)L->size());
            int idx = (*L)[p];
            (*L)[p] = L->back();
            L->pop_back();
            int i = idx / T, t = idx % T;
            out[i][t] = guide[i][t];
        }
        return out;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double af = params.get("add_first_prob", 0.6);
    int mf = (int)params.get("max_flips", 1);
    if (mf < 1) mf = 1;
    return std::make_unique<HammingFlipSetupFirst>(model, af, mf);
}
