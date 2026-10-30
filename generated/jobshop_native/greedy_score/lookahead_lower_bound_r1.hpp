// COMPONENT: {"name": "lookahead_lower_bound", "slot": "greedy_score", "params": {"idle_w": {"type": "float", "range": [0.0, 1.0]}, "tie": {"type": "float", "range": [0.0, 0.5]}}}
class LookaheadLowerBound : public hsf::GreedyScore<JobShop> {
public:
    LookaheadLowerBound(const JobShop& md, double idle_w, double tie) : M(md), idle_w_(idle_w), tie_(tie) {
        tail_.assign(M.n_ops + 1, 0);
        for (int j = 0; j < M.n; ++j) {
            int acc = 0;
            for (int k = (int)M.routes[j].size() - 1; k >= 0; --k) {
                acc += M.routes[j][k].second;
                tail_[M.off[j] + k] = acc;
            }
        }
    }
    double score(const JobShop::Partial& p, const JobShop::Action& a) override {
        const int mm = a.machine;
        const int pt = a.end - a.start;
        // cota del propio trabajo
        double lb = a.end + (tail_[M.off[a.job] + a.op] - pt);
        long long remload = 0;  // carga pendiente en mm sin contar esta operación
        double waitlb = 0.0;
        for (int j = 0; j < M.n; ++j) {
            if (j == a.job) continue;
            int k = p.nxt[j];
            int sz = (int)M.routes[j].size();
            if (k >= sz) continue;
            int km = M.opk[j][mm];
            if (km >= k) {
                remload += M.routes[j][km].second;
                if (km == k) {
                    // trabajo que espera directamente esta máquina: queda retrasado hasta a.end
                    double s = std::max(a.end, p.job_ready[j]);
                    waitlb = std::max(waitlb, s + (double)tail_[M.off[j] + k]);
                }
            }
        }
        lb = std::max(lb, waitlb);
        lb = std::max(lb, (double)a.end + (double)remload);
        double idle = a.start - p.mach_ready[mm];
        return lb + idle_w_ * idle + tie_ * a.start;
    }
private:
    const JobShop& M;
    double idle_w_, tie_;
    std::vector<int> tail_;
};

std::unique_ptr<hsf::GreedyScore<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<LookaheadLowerBound>(model, params.get("idle_w", 0.2), params.get("tie", 0.05));
}
