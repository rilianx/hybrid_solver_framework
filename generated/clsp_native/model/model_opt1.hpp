#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <utility>
#include <limits>
#include <cmath>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n = 0, T = 0;
    std::vector<std::vector<double>> d;
    std::vector<double> s, h, st, cap;
    double totalDemand = 0.0;

    struct Edge { int to; int rev; double cap; double cost; };
    int V = 0, SRC = 0, SNK = 0;
    std::vector<std::vector<int>> adj;   // edge indices
    mutable std::vector<Edge> E;
    std::vector<int> srcEdge;            // per period: source->period
    std::vector<std::vector<int>> prodEdge; // [i][t]: period t -> node(i,t)
    std::vector<Edge> E0;

    mutable std::vector<double> dist, pot;
    mutable std::vector<int> prevE;
    mutable std::vector<std::pair<double,int>> heap;
    std::vector<int> adjStart, adjFlat;
    mutable std::vector<int> level, itp, que;
    mutable std::vector<char> reach;
    mutable double curCost = 0.0;
    static constexpr double INF = 1e300;
    static constexpr double EPS = 1e-9;

    int itemNode(int i, int t) const { return 1 + T + i * T + t; }

    int addEdge(int u, int v, double c, double cost) {
        int id = (int)E0.size();
        E0.push_back({v, id + 1, c, cost});
        E0.push_back({u, id, 0.0, -cost});
        adj[u].push_back(id);
        adj[v].push_back(id + 1);
        return id;
    }

    static Model parse(const std::string& text) {
        Model m;
        std::istringstream in(text);
        double a, b;
        in >> a >> b;
        m.n = (int)a; m.T = (int)b;
        m.cap.resize(m.T);
        for (int t = 0; t < m.T; ++t) in >> m.cap[t];
        m.s.resize(m.n); m.h.resize(m.n); m.st.resize(m.n);
        m.d.assign(m.n, std::vector<double>(m.T, 0.0));
        for (int i = 0; i < m.n; ++i) {
            in >> m.s[i] >> m.h[i] >> m.st[i];
            for (int t = 0; t < m.T; ++t) { in >> m.d[i][t]; m.totalDemand += m.d[i][t]; }
        }
        m.V = 2 + m.T + m.n * m.T;
        m.SRC = 0; m.SNK = m.V - 1;
        m.adj.assign(m.V, {});
        m.srcEdge.resize(m.T);
        for (int t = 0; t < m.T; ++t) m.srcEdge[t] = m.addEdge(m.SRC, 1 + t, 0.0, 0.0);
        m.prodEdge.assign(m.n, std::vector<int>(m.T, -1));
        for (int i = 0; i < m.n; ++i) {
            for (int t = 0; t < m.T; ++t) {
                m.prodEdge[i][t] = m.addEdge(1 + t, m.itemNode(i, t), 0.0, 0.0);
                if (m.d[i][t] > 0) m.addEdge(m.itemNode(i, t), m.SNK, m.d[i][t], 0.0);
                if (t + 1 < m.T) m.addEdge(m.itemNode(i, t), m.itemNode(i, t + 1), INF, m.h[i]);
            }
        }
        m.E = m.E0;
        m.adjStart.assign(m.V + 1, 0);
        for (int v = 0; v < m.V; ++v) m.adjStart[v + 1] = m.adjStart[v] + (int)m.adj[v].size();
        m.adjFlat.reserve(m.adjStart[m.V]);
        for (int v = 0; v < m.V; ++v) for (int id : m.adj[v]) m.adjFlat.push_back(id);
        m.level.resize(m.V); m.itp.resize(m.V); m.que.resize(m.V); m.reach.resize(m.V);
        m.dist.resize(m.V); m.pot.resize(m.V); m.prevE.resize(m.V);
        m.heap.reserve(m.E0.size() + m.V + 4);
        Solution tr = m.trivial();
        double unmet, hold;
        m.solveFlow(tr, unmet, hold);
        double c = m.setupCost(tr) + hold;
        m.penalty = 10.0 * (std::fabs(c) + 1.0);
        return m;
    }

    double setupCost(const Solution& y) const {
        double c = 0.0;
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < T; ++t)
                if (y[i][t]) c += s[i];
        return c;
    }

    inline bool admissible(int u, const Edge& e) const {
        if (e.cap <= EPS || !reach[e.to]) return false;
        double rc = e.cost + pot[u] - pot[e.to];
        double tol = 1e-9 * (1.0 + std::fabs(pot[u]) + std::fabs(pot[e.to]));
        return std::fabs(rc) <= tol;
    }

    double dfsAug(int u, double f) const {
        if (u == SNK) return f;
        int end = adjStart[u + 1];
        for (int& k = itp[u]; k < end; ++k) {
            int id = adjFlat[k];
            Edge& e = E[id];
            if (level[e.to] != level[u] + 1) continue;
            if (!admissible(u, e)) continue;
            double r = dfsAug(e.to, std::min(f, e.cap));
            if (r > EPS) {
                e.cap -= r;
                E[e.rev].cap += r;
                curCost += r * e.cost;
                return r;
            }
        }
        return 0.0;
    }

    // Min-cost max-flow (primal-dual): maximize served demand, then minimize holding cost.
    void solveFlow(const Solution& y, double& unmet, double& hold) const {
        std::copy(E0.begin(), E0.end(), E.begin());
        for (int t = 0; t < T; ++t) {
            double c = cap[t];
            for (int i = 0; i < n; ++i) if (y[i][t]) c -= st[i];
            E[srcEdge[t]].cap = std::max(0.0, c);
        }
        for (int i = 0; i < n; ++i) {
            const std::vector<int>& yi = y[i];
            const std::vector<int>& pe = prodEdge[i];
            for (int t = 0; t < T; ++t)
                E[pe[t]].cap = yi[t] ? INF : 0.0;
        }
        std::fill(pot.begin(), pot.end(), 0.0);
        double flow = 0.0;
        curCost = 0.0;
        auto cmp = [](const std::pair<double,int>& x, const std::pair<double,int>& z) { return x.first > z.first; };
        while (true) {
            std::fill(dist.begin(), dist.end(), INF);
            dist[SRC] = 0.0;
            heap.clear();
            heap.push_back({0.0, SRC});
            while (!heap.empty()) {
                std::pop_heap(heap.begin(), heap.end(), cmp);
                auto [du, u] = heap.back();
                heap.pop_back();
                if (du > dist[u] + 1e-12) continue;
                double pu = pot[u];
                for (int k = adjStart[u], ke = adjStart[u + 1]; k < ke; ++k) {
                    const Edge& e = E[adjFlat[k]];
                    if (e.cap <= EPS) continue;
                    double rc = e.cost + pu - pot[e.to];
                    if (rc < 0) rc = 0;
                    double nd = du + rc;
                    if (nd < dist[e.to] - 1e-12) {
                        dist[e.to] = nd;
                        heap.push_back({nd, e.to});
                        std::push_heap(heap.begin(), heap.end(), cmp);
                    }
                }
            }
            if (dist[SNK] >= INF) break;
            for (int v = 0; v < V; ++v) {
                if (dist[v] < INF) { pot[v] += dist[v]; reach[v] = 1; }
                else reach[v] = 0;
            }
            // blocking flows on the admissible (zero reduced cost) subgraph
            double phaseFlow = 0.0;
            while (true) {
                std::fill(level.begin(), level.end(), -1);
                level[SRC] = 0;
                int qh = 0, qt = 0;
                que[qt++] = SRC;
                while (qh < qt) {
                    int u = que[qh++];
                    for (int k = adjStart[u], ke = adjStart[u + 1]; k < ke; ++k) {
                        const Edge& e = E[adjFlat[k]];
                        if (level[e.to] >= 0) continue;
                        if (!admissible(u, e)) continue;
                        level[e.to] = level[u] + 1;
                        que[qt++] = e.to;
                    }
                }
                if (level[SNK] < 0) break;
                for (int v = 0; v < V; ++v) itp[v] = adjStart[v];
                bool any = false;
                while (true) {
                    double f = dfsAug(SRC, INF);
                    if (f <= EPS) break;
                    flow += f; phaseFlow += f; any = true;
                }
                if (!any) break;
            }
            if (phaseFlow <= EPS) break;
        }
        double cost = curCost;
        unmet = totalDemand - flow;
        if (unmet < 1e-6) unmet = 0.0;
        hold = cost;
        if (std::fabs(hold) < 1e-9) hold = 0.0;
    }

    Solution trivial() const {
        return Solution(n, std::vector<int>(T, 1));
    }

    Solution random(hsf::Rng& rng) const {
        Solution y(n, std::vector<int>(T, 0));
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < T; ++t) y[i][t] = rng.below(2);
        return y;
    }

    bool wellFormed(const Solution& y) const {
        if ((int)y.size() != n) return false;
        for (auto& r : y) if ((int)r.size() != T) return false;
        return true;
    }

    void violations(const Solution& y, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        if (!wellFormed(y)) { out.push_back({"demanda", totalDemand + 1.0}); return; }
        double unmet, hold;
        solveFlow(y, unmet, hold);
        out.push_back({"demanda", unmet});
    }

    void cost_terms(const Solution& y, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        if (!wellFormed(y)) { out.push_back({"setup", 0.0}); out.push_back({"inventario", 0.0}); return; }
        double unmet, hold;
        solveFlow(y, unmet, hold);
        out.push_back({"setup", setupCost(y)});
        out.push_back({"inventario", hold});
    }

    double objective(const Solution& y) const {
        if (!wellFormed(y)) return penalty * (totalDemand + 1.0) + 1e12;
        double unmet, hold;
        solveFlow(y, unmet, hold);
        return setupCost(y) + hold + penalty * unmet;
    }

    bool feasible(const Solution& y) const {
        if (!wellFormed(y)) return false;
        double unmet, hold;
        solveFlow(y, unmet, hold);
        return unmet <= 1e-6;
    }
};

} // namespace gen
