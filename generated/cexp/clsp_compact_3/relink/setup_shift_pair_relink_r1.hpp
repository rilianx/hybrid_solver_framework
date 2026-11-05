// COMPONENT: {"name": "setup_shift_pair_relink", "slot": "relink", "params": {"pair_prob": {"type": "float", "range": [0.3, 1.0]}, "near_prob": {"type": "float", "range": [0.0, 1.0]}}}
class SetupShiftPairRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    double pairProb, nearProb;
    std::vector<std::pair<int,int>> diff;
    std::vector<int> candItems, adds, rems;
public:
    SetupShiftPairRelink(const Model& model, double pp, double np) : m(model), pairProb(pp), nearProb(np) {}

    int distance(const Sol& a, const Sol& b) override {
        int c = 0;
        for (size_t i = 0; i < a.size(); ++i) {
            const auto& ra = a[i]; const auto& rb = b[i];
            for (size_t t = 0; t < ra.size(); ++t) c += (ra[t] != rb[t]);
        }
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        diff.clear();
        candItems.clear();
        for (size_t i = 0; i < cur.size(); ++i) {
            bool hasAdd = false, hasRem = false;
            for (size_t t = 0; t < cur[i].size(); ++t) {
                int c = cur[i][t], g = guide[i][t];
                if (c == g) continue;
                diff.emplace_back((int)i, (int)t);
                if (c == 0 && g != 0) hasAdd = true;
                else if (c != 0 && g == 0) hasRem = true;
            }
            if (hasAdd && hasRem) candItems.push_back((int)i);
        }
        Sol r = cur;
        if (diff.empty()) return r;

        if (!candItems.empty() && rng.uniform() < pairProb) {
            int i = candItems[rng.below((int)candItems.size())];
            adds.clear(); rems.clear();
            for (size_t t = 0; t < cur[i].size(); ++t) {
                int c = cur[i][t], g = guide[i][t];
                if (c == 0 && g != 0) adds.push_back((int)t);
                else if (c != 0 && g == 0) rems.push_back((int)t);
            }
            int ta = adds[rng.below((int)adds.size())];
            int tr;
            if (rng.uniform() < nearProb) {
                int best = std::numeric_limits<int>::max(), cnt = 0;
                tr = rems[0];
                for (int t : rems) {
                    int dd = std::abs(t - ta);
                    if (dd < best) { best = dd; tr = t; cnt = 1; }
                    else if (dd == best) { ++cnt; if (rng.below(cnt) == 0) tr = t; }
                }
            } else {
                tr = rems[rng.below((int)rems.size())];
            }
            r[i][ta] = guide[i][ta];
            r[i][tr] = guide[i][tr];
            return r;
        }

        const auto& p = diff[rng.below((int)diff.size())];
        r[p.first][p.second] = guide[p.first][p.second];
        return r;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double pp = params.get("pair_prob", 0.7);
    double np = params.get("near_prob", 0.6);
    return std::make_unique<SetupShiftPairRelink>(model, pp, np);
}
