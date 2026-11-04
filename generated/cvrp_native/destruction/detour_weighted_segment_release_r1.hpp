// COMPONENT: {"name": "detour_weighted_segment_release", "slot": "destruction", "params": {"alpha": {"type": "float", "range": [0.5, 4.0]}, "span": {"type": "int", "range": [0, 3]}}}
static int budgetNodesDW(int n, double ratio) {
    double total = (double)n * (double)(n + 1);
    double target = std::max(1.0, ratio * total);
    int m = (int)std::ceil((1.0 + std::sqrt(1.0 + 4.0 * target)) / 2.0);
    return std::max(2, std::min(n + 1, m));
}
static void emitArcsDW(int n, const std::vector<int>& nodes, std::vector<int>& out) {
    out.clear();
    out.reserve(nodes.size() * (nodes.size() - 1));
    for (int i : nodes)
        for (int j : nodes)
            if (i != j) out.push_back(i * n + (j < i ? j : j - 1));
    std::sort(out.begin(), out.end());
}

class DetourSegmentDestruction : public hsf::Destruction<Model> {
    const Model& m;
    double alpha;
    int span;
    std::vector<int> pred, succ, nodes;
    std::vector<double> gain;
    std::vector<char> mark;
    std::vector<std::pair<double, int>> keys;
    std::vector<int> tmp;

    bool add(int c, int& sel, int k) {
        if (c < 1 || c > m.n || mark[c] || sel >= k) return false;
        mark[c] = 1;
        nodes.push_back(c);
        ++sel;
        return true;
    }
public:
    DetourSegmentDestruction(const Model& mod, double a, int sp) : m(mod), alpha(a), span(sp) {}
    std::vector<int> destroy(const Model::Solution& s, double ratio, Rng& rng) override {
        std::vector<int> out;
        int n = m.n;
        if (n < 1) return out;
        int k = budgetNodesDW(n, ratio) - 1;
        pred.assign(n + 1, -1);
        succ.assign(n + 1, -1);
        gain.assign(n + 1, -1.0);
        mark.assign(n + 1, 0);
        std::vector<char>& seen = mark;  // reutilizado temporalmente
        double sum = 0.0;
        int cntG = 0;
        for (const auto& r : s) {
            tmp.clear();
            for (int c : r)
                if (c >= 1 && c <= n && !seen[c]) { seen[c] = 1; tmp.push_back(c); }
            int L = (int)tmp.size();
            for (int i = 0; i < L; ++i) {
                int c = tmp[i];
                int p = i > 0 ? tmp[i - 1] : 0;
                int q = i + 1 < L ? tmp[i + 1] : 0;
                pred[c] = p; succ[c] = q;
                double g = m.dist(p, c) + m.dist(c, q) - m.dist(p, q);
                gain[c] = std::max(0.0, g);
                sum += gain[c]; ++cntG;
            }
        }
        double avg = cntG ? sum / cntG : 1.0;
        double eps = 1e-9 + 0.01 * avg;
        double big = 10.0 * (avg + 1.0);  // clientes ausentes: prioridad alta
        std::fill(mark.begin(), mark.end(), 0);
        keys.clear();
        keys.reserve(n);
        for (int c = 1; c <= n; ++c) {
            double g = gain[c] < 0 ? big : gain[c];
            double w = std::pow(g + eps, alpha);
            double u = std::max(1e-300, rng.uniform());
            keys.emplace_back(-std::log(u) / w, c);
        }
        std::sort(keys.begin(), keys.end());
        nodes.clear();
        nodes.push_back(0);
        int sel = 0;
        for (auto& kp : keys) {
            if (sel >= k) break;
            int c = kp.second;
            if (mark[c]) continue;
            add(c, sel, k);
            int p = c, q = c;
            for (int t = 0; t < span && sel < k; ++t) {
                if (p >= 1 && pred[p] >= 1) { p = pred[p]; add(p, sel, k); } else p = 0;
                if (q >= 1 && succ[q] >= 1) { q = succ[q]; add(q, sel, k); } else q = 0;
                if (p == 0 && q == 0) break;
            }
        }
        if (nodes.size() < 2) nodes.push_back(1 + rng.below(n));
        emitArcsDW(n, nodes, out);
        return out;
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = params.get("alpha", 1.5);
    int span = (int)params.get("span", 1);
    return std::make_unique<DetourSegmentDestruction>(model, alpha, std::max(0, std::min(3, span)));
}
