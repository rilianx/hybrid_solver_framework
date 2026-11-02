// COMPONENT: {"name": "random_multi_insertion", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "extra": {"type": "int", "range": [0, 3]}}}
class RandomMultiInsertion : public hsf::Perturbation<Model> {
public:
    RandomMultiInsertion(const Model& m, double scale, int extra) : md(m), scale_(scale), extra_(extra) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol out = s;
        int R = (int)out.size();
        if (R == 0) return out;
        int total = 0;
        for (int r = 0; r < R; ++r) total += (int)out[r].size();
        if (total == 0) return out;
        if (total < 2) return out;
        int k = std::max(1, (int)std::lround(scale_ * std::max(1.0, strength)) + extra_);
        k = std::min(k, total);
        for (int t = 0; t < k; ++t) moveOne(out, R, total, rng);
        if (out == s) {
            for (int tries = 0; tries < 8 && out == s; ++tries) moveOne(out, R, total, rng);
        }
        return out;
    }
private:
    // mueve un elemento uniforme a otra posición; nunca deja una secuencia vacía
    void moveOne(Sol& out, int R, int total, Rng& rng) {
        int idx = rng.below(total), src = 0;
        while (idx >= (int)out[src].size()) { idx -= (int)out[src].size(); ++src; }
        int srcSize = (int)out[src].size();
        int dst;
        if (srcSize <= 1) {
            // no vaciar la secuencia de origen: solo se reordena dentro de ella (nada que hacer)
            return;
        }
        dst = rng.below(R);
        auto x = out[src][idx];
        out[src].erase(out[src].begin() + idx);
        int L = (int)out[dst].size();
        int pos = rng.below(L + 1);
        if (dst == src && pos == idx && L > 0) pos = (pos + 1 + rng.below(L)) % (L + 1);
        out[dst].insert(out[dst].begin() + pos, x);
    }
    const Model& md;
    double scale_;
    int extra_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double scale = params.get("scale", 1.0);
    int extra = (int)params.get("extra", 0);
    return std::make_unique<RandomMultiInsertion>(model, scale, extra);
}
