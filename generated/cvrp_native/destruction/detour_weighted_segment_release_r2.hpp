// COMPONENT: {"name": "detour_weighted_segment_release", "slot": "destruction", "params": {"alpha": {"type": "float", "range": [0.5, 4.0]}, "span": {"type": "int", "range": [0, 3]}}}
static int budgetRowsDW(int n, double ratio) {
    double t = std::max(0.0, ratio) * (double)(n + 1);
    int r = (int)std::ceil(t);
    return std::max(2, std::min(n + 1, r));
}

class DetourSegmentDestruction : public hsf::Destruction<Model> {
    const Model& m;
    double alpha;
    int span;
    std::vector<int> pred, succ, nodes;
    std::vector<double> gain;
    std::vector<char> mark, seen;
    std::vector<std::pair<double, int>> keys;
    std::vector<int> tmp;

    // fila de arcos salientes del nodo c (0 = depósito, 1..n clientes)
    bool add(int c, int& sel, int R) {
        if (c < 0 || c > m.n || mark[c] || sel >= R) return false;
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
        int R = budgetRowsDW(n, ratio);
        pred.assign(n + 1, -1);
        succ.assign(n + 1, -1);
        gain.assign(n + 1, -1.0);
        mark.assign(n + 1, 0);
        seen.assign(n + 1, 0);
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
        int sel = 0;
        for (auto& kp : keys) {
            if (sel >= R) break;
            int c = kp.second;
            if (mark[c]) continue;
            // liberar el arco que entra en c (fila del predecesor) y el que sale de c
            if (pred[c] >= 0) add(pred[c], sel, R);
            add(c, sel, R);
            int p = pred[c] >= 1 ? pred[c] : 0, q = c;
            for (int t = 0; t < span && sel < R; ++t) {
                bool moved = false;
                if (p >= 1 && pred[p] >= 0) { p = pred[p]; add(p, sel, R); moved = true; if (p == 0) p = 0; }
                else p = 0;
                if (q >= 1 && succ[q] >= 1) { q = succ[q]; add(q, sel, R); moved = true; }
                else q = 0;
                if (!moved) break;
            }
        }
        int guard = 0;
        while ((int)nodes.size() < 2 && guard++ < 4 * (n + 1)) add(rng.below(n + 1), sel, std::max(R, 2));
        std::sort(nodes.begin(), nodes.end());
        out.reserve(nodes.size() * (size_t)n);
        for (int i : nodes) {
            int base = i * n;
            for (int j = 0; j < n; ++j) out.push_back(base + j);
        }
        return out;
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = params.get("alpha", 1.5);
    int span = (int)params.get("span", 1);
    return std::make_unique<DetourSegmentDestruction>(model, alpha, std::max(0, std::min(3, span)));
}
