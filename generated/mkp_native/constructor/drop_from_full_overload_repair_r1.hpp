// COMPONENT: {"name": "drop_from_full_overload_repair", "slot": "constructor", "params": {"start_prob": {"type": "float", "range": [0.6, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "fill": {"type": "cat", "values": ["slack", "static"]}}}
class Codec {
public:
    explicit Codec(const Model& md) : M(md), base(md.trivial()) {
        const int n = M.n;
        std::vector<char> T(n, 0);
        for (int j = 0; j < n; ++j) T[j] = M.chosen(base, j) ? 1 : 0;
        if (base.empty()) return;
        const std::vector<int>& r0 = base[0];
        if ((int)r0.size() == n) {
            bool ok = true;
            for (int j = 0; j < n && ok; ++j)
                if (!((r0[j] == 0 && !T[j]) || (r0[j] == 1 && T[j]))) ok = false;
            if (ok) { mode = 1; return; }
        }
        std::vector<char> seen(n, 0);
        bool ok = true;
        for (int v : r0) { if (v < 0 || v >= n || seen[v]) { ok = false; break; } seen[v] = 1; }
        for (int j = 0; j < n && ok; ++j) if (seen[j] != T[j]) ok = false;
        if (!ok) return;
        mode = 2;
        if (base.size() >= 2) {
            std::vector<char> s2(n, 0);
            bool c = true;
            for (int v : base[1]) { if (v < 0 || v >= n || s2[v] || T[v]) { c = false; break; } s2[v] = 1; }
            for (int j = 0; j < n && c; ++j) if (!T[j] && !s2[j]) c = false;
            comp = c;
        }
    }
    Model::Solution finalize(const std::vector<char>& x) const {
        if (mode == 0) return base;
        Model::Solution s = base;
        const int n = M.n;
        if (mode == 1) {
            s[0].assign(n, 0);
            for (int j = 0; j < n; ++j) if (x[j]) s[0][j] = 1;
        } else {
            s[0].clear();
            for (int j = 0; j < n; ++j) if (x[j]) s[0].push_back(j);
            if (comp) { s[1].clear(); for (int j = 0; j < n; ++j) if (!x[j]) s[1].push_back(j); }
        }
        for (int j = 0; j < n; ++j) if (M.chosen(s, j) != (x[j] != 0)) return base;
        if (!M.feasible(s)) return base;
        return s;
    }
private:
    const Model& M;
    Model::Solution base;
    int mode = 0;
    bool comp = false;
};

class DropFromFull : public hsf::Constructor<Model> {
public:
    DropFromFull(const Model& md, double sp, double nz, bool slackFill)
        : M(md), codec(md), n(md.n), m(md.m), start_prob(sp), noise(nz), slack_fill(slackFill) {
        lim.resize(m);
        capn.resize(m);
        for (int i = 0; i < m; ++i) {
            lim[i] = M.capacity[i] + 1e-9 * std::max(1.0, std::fabs(M.capacity[i]));
            capn[i] = std::max(M.capacity[i], 1e-12);
        }
    }
    Model::Solution build(Rng& rng) override {
        const double* w = M.wcol.data();
        std::vector<char> x(n, 0);
        std::vector<double> load(m, 0.0), over(m, 0.0);
        std::vector<int> chosen;
        chosen.reserve(n);
        for (int j = 0; j < n; ++j) {
            if (start_prob >= 1.0 || rng.uniform() < start_prob) {
                x[j] = 1;
                chosen.push_back(j);
                const double* wj = w + (size_t)j * m;
                for (int i = 0; i < m; ++i) load[i] += wj[i];
            }
        }
        // drop phase
        while (true) {
            bool infeas = false;
            for (int i = 0; i < m; ++i) {
                if (load[i] > lim[i]) { over[i] = (load[i] - M.capacity[i]) / capn[i] / capn[i]; infeas = true; }
                else over[i] = 0.0;
            }
            if (!infeas) break;
            double best = std::numeric_limits<double>::infinity();
            int bk = -1;
            for (size_t k = 0; k < chosen.size(); ++k) {
                const double* wj = w + (size_t)chosen[k] * m;
                double c = 0.0;
                for (int i = 0; i < m; ++i) c += wj[i] * over[i];
                if (c <= 0.0) continue;
                double s = M.profit[chosen[k]] / c;
                if (noise > 0.0) s *= 1.0 + noise * rng.uniform();
                if (s < best) { best = s; bk = (int)k; }
            }
            if (bk < 0) break;
            int j = chosen[bk];
            x[j] = 0;
            const double* wj = w + (size_t)j * m;
            for (int i = 0; i < m; ++i) load[i] -= wj[i];
            chosen[bk] = chosen.back();
            chosen.pop_back();
        }
        // fill phase
        std::vector<double> wt(m);
        for (int i = 0; i < m; ++i)
            wt[i] = slack_fill ? 1.0 / std::max(M.capacity[i] - load[i], 1e-9) : 1.0 / capn[i];
        std::vector<std::pair<double, int>> rest;
        rest.reserve(n);
        for (int j = 0; j < n; ++j) {
            if (x[j]) continue;
            const double* wj = w + (size_t)j * m;
            double d = 0.0;
            for (int i = 0; i < m; ++i) d += wj[i] * wt[i];
            rest.push_back({d > 0.0 ? M.profit[j] / d : std::numeric_limits<double>::infinity(), j});
        }
        std::sort(rest.begin(), rest.end(), [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
            if (a.first != b.first) return a.first > b.first;
            return a.second < b.second;
        });
        for (auto& p : rest) {
            int j = p.second;
            const double* wj = w + (size_t)j * m;
            bool ok = true;
            for (int i = 0; i < m; ++i) if (load[i] + wj[i] > lim[i]) { ok = false; break; }
            if (!ok) continue;
            for (int i = 0; i < m; ++i) load[i] += wj[i];
            x[j] = 1;
        }
        return codec.finalize(x);
    }
private:
    const Model& M;
    Codec codec;
    int n, m;
    double start_prob, noise;
    bool slack_fill;
    std::vector<double> lim, capn;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sp = params.get("start_prob", 1.0);
    double nz = params.get("noise", 0.15);
    bool slack = params.text("fill", "slack") == "slack";
    return std::make_unique<DropFromFull>(model, sp, nz, slack);
}
