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
    std::vector<std::vector<int>> adj;   // edge indices (original network)
    mutable std::vector<Edge> E;         // residual state of the original network after solveFlow
    std::vector<int> srcEdge;            // per period: source->period
    std::vector<std::vector<int>> prodEdge; // [i][t]: period t -> node(i,t)
    std::vector<Edge> E0;
    std::vector<int> sinkEdge;           // [i*T+t] original sink edge or -1
    std::vector<int> chainEdge;          // [i*T+t] original chain edge or -1

    // reduced network (one node per setup segment)
    int VMAX = 0, EMAX = 0, rSNK = 0;
    mutable int rE = 0, rV = 0;
    mutable std::vector<int> rHead, rNxt, rTo;
    mutable std::vector<double> rCap, rCost;
    mutable std::vector<int> rSrcArc, rProdArc, rSinkArc;
    mutable std::vector<double> Ct;

    mutable std::vector<double> dist, pot;
    mutable std::vector<std::pair<double,int>> heap;
    mutable std::vector<int> level, itp, que;
    mutable std::vector<char> reach;
    mutable double curCost = 0.0;

    mutable std::vector<int> lastY;
    mutable bool lastValid = false;
    mutable double lastUnmet = 0.0, lastHold = 0.0;

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
        m.sinkEdge.assign((size_t)m.n * m.T, -1);
        m.chainEdge.assign((size_t)m.n * m.T, -1);
        for (int i = 0; i < m.n; ++i) {
            for (int t = 0; t < m.T; ++t) {
                m.prodEdge[i][t] = m.addEdge(1 + t, m.itemNode(i, t), 0.0, 0.0);
                if (m.d[i][t] > 0) m.sinkEdge[i * m.T + t] = m.addEdge(m.itemNode(i, t), m.SNK, m.d[i][t], 0.0);
                if (t + 1 < m.T) m.chainEdge[i * m.T + t] = m.addEdge(m.itemNode(i, t), m.itemNode(i, t + 1), INF, m.h[i]);
            }
        }
        m.E = m.E0;

        m.VMAX = 2 + m.T + m.n * m.T;
        m.EMAX = 2 * (m.T + 3 * m.n * m.T) + 4;
        m.rSNK = 1 + m.T;
        m.rHead.assign(m.VMAX, -1);
        m.rNxt.resize(m.EMAX); m.rTo.resize(m.EMAX);
        m.rCap.resize(m.EMAX); m.rCost.resize(m.EMAX);
        m.rSrcArc.assign(m.T, -1);
        m.rProdArc.assign((size_t)m.n * m.T, -1);
        m.rSinkArc.assign((size_t)m.n * m.T, -1);
        m.Ct.assign(m.T, 0.0);
        m.level.resize(m.VMAX); m.itp.resize(m.VMAX); m.que.resize(m.VMAX); m.reach.resize(m.VMAX);
        m.dist.resize(m.VMAX); m.pot.resize(m.VMAX);
        m.heap.reserve(m.EMAX + m.VMAX + 4);
        m.lastY.assign((size_t)m.n * m.T, 0);

        Solution tr = m.trivial();
        double unmet, hold;
        m.solveFlow(tr, unmet, hold);
        double c = m.setupCost(tr) + hold;
        m.penalty = 10.0 * (std::fabs(c) + 1.0);
        return m;
    }

    double setupCost(const Solution& y) const {
        double c = 0.0;
        for (int i = 0; i < n; ++i) {
            const int* yi = y[i].data();
            for (int t = 0; t < T; ++t)
                if (yi[t]) c += s[i];
        }
        return c;
    }

    inline int rAdd(int u, int v, double c, double w) const {
        int id = rE;
        rTo[id] = v; rCap[id] = c; rCost[id] = w; rNxt[id] = rHead[u]; rHead[u] = id;
        rTo[id + 1] = u; rCap[id + 1] = 0.0; rCost[id + 1] = -w; rNxt[id + 1] = rHead[v]; rHead[v] = id + 1;
        rE += 2;
        return id;
    }

    inline bool admissible(int u, int k) const {
        int v = rTo[k];
        if (rCap[k] <= EPS || !reach[v]) return false;
        double rc = rCost[k] + pot[u] - pot[v];
        double tol = 1e-9 * (1.0 + std::fabs(pot[u]) + std::fabs(pot[v]));
        return std::fabs(rc) <= tol;
    }

    double dfsAug(int u, double f) const {
        if (u == rSNK) return f;
        for (int& k = itp[u]; k != -1; k = rNxt[k]) {
            int v = rTo[k];
            if (level[v] != level[u] + 1) continue;
            if (!admissible(u, k)) continue;
            double r = dfsAug(v, std::min(f, rCap[k]));
            if (r > EPS) {
                rCap[k] -= r;
                rCap[k ^ 1] += r;
                curCost += r * rCost[k];
                return r;
            }
        }
        return 0.0;
    }

    void writeBack() const {
        std::copy(E0.begin(), E0.end(), E.begin());
        for (int t = 0; t < T; ++t) {
            int a = rSrcArc[t];
            int id = srcEdge[t];
            E[id].cap = rCap[a];
            E[id + 1].cap = rCap[a ^ 1];
        }
        for (int i = 0; i < n; ++i) {
            double inv = 0.0;
            const std::vector<int>& pe = prodEdge[i];
            for (int t = 0; t < T; ++t) {
                int idx = i * T + t;
                int pa = rProdArc[idx];
                if (pa >= 0) {
                    int id = pe[t];
                    E[id].cap = rCap[pa];
                    E[id + 1].cap = rCap[pa ^ 1];
                    inv += rCap[pa ^ 1];
                }
                int sa = rSinkArc[idx];
                if (sa >= 0) {
                    int id = sinkEdge[idx];
                    E[id].cap = rCap[sa];
                    E[id + 1].cap = rCap[sa ^ 1];
                    inv -= rCap[sa ^ 1];
                }
                if (inv < 0) inv = 0.0;
                int ce = chainEdge[idx];
                if (ce >= 0) {
                    E[ce].cap = INF - inv;
                    E[ce + 1].cap = inv;
                }
            }
        }
    }

    // Min-cost max-flow (primal-dual): maximize served demand, then minimize holding cost.
    void solveFlow(const Solution& y, double& unmet, double& hold) const {
        if (lastValid) {
            bool same = true;
            for (int i = 0; i < n && same; ++i) {
                const int* yi = y[i].data();
                const int* li = lastY.data() + (size_t)i * T;
                for (int t = 0; t < T; ++t) if ((yi[t] != 0) != (li[t] != 0)) { same = false; break; }
            }
            if (same) {
                writeBack();
                unmet = lastUnmet; hold = lastHold;
                return;
            }
        }
        for (int i = 0; i < n; ++i) {
            const int* yi = y[i].data();
            int* li = lastY.data() + (size_t)i * T;
            for (int t = 0; t < T; ++t) li[t] = yi[t] ? 1 : 0;
        }

        // build reduced network
        std::fill(rHead.begin(), rHead.end(), -1);
        rE = 0; rV = 2 + T;
        for (int t = 0; t < T; ++t) {
            double c = cap[t];
            for (int i = 0; i < n; ++i) if (y[i][t]) c -= st[i];
            c = std::max(0.0, c);
            Ct[t] = c;
            rSrcArc[t] = rAdd(0, 1 + t, c, 0.0);
        }
        for (int i = 0; i < n; ++i) {
            const int* yi = y[i].data();
            const double* di = d[i].data();
            double hi = h[i];
            int seg = -1, tseg = -1;
            for (int t = 0; t < T; ++t) {
                int idx = i * T + t;
                rProdArc[idx] = -1; rSinkArc[idx] = -1;
                if (yi[t]) {
                    int u = rV++;
                    rProdArc[idx] = rAdd(1 + t, u, INF, 0.0);
                    if (seg >= 0) rAdd(seg, u, INF, hi * (t - tseg));
                    seg = u; tseg = t;
                }
                if (seg >= 0 && di[t] > 0) rSinkArc[idx] = rAdd(seg, rSNK, di[t], hi * (t - tseg));
            }
        }

        std::fill(pot.begin(), pot.begin() + rV, 0.0);
        double flow = 0.0;
        curCost = 0.0;
        auto cmp = [](const std::pair<double,int>& x, const std::pair<double,int>& z) { return x.first > z.first; };
        while (true) {
            std::fill(dist.begin(), dist.begin() + rV, INF);
            dist[0] = 0.0;
            heap.clear();
            heap.push_back({0.0, 0});
            while (!heap.empty()) {
                std::pop_heap(heap.begin(), heap.end(), cmp);
                auto [du, u] = heap.back();
                heap.pop_back();
                if (du > dist[u] + 1e-12) continue;
                double pu = pot[u];
                for (int k = rHead[u]; k != -1; k = rNxt[k]) {
                    if (rCap[k] <= EPS) continue;
                    int v = rTo[k];
                    double rc = rCost[k] + pu - pot[v];
                    if (rc < 0) rc = 0;
                    double nd = du + rc;
                    if (nd < dist[v] - 1e-12) {
                        dist[v] = nd;
                        heap.push_back({nd, v});
                        std::push_heap(heap.begin(), heap.end(), cmp);
                    }
                }
            }
            if (dist[rSNK] >= INF) break;
            for (int v = 0; v < rV; ++v) {
                if (dist[v] < INF) { pot[v] += dist[v]; reach[v] = 1; }
                else reach[v] = 0;
            }
            double phaseFlow = 0.0;
            while (true) {
                std::fill(level.begin(), level.begin() + rV, -1);
                level[0] = 0;
                int qh = 0, qt = 0;
                que[qt++] = 0;
                while (qh < qt) {
                    int u = que[qh++];
                    for (int k = rHead[u]; k != -1; k = rNxt[k]) {
                        int v = rTo[k];
                        if (level[v] >= 0) continue;
                        if (!admissible(u, k)) continue;
                        level[v] = level[u] + 1;
                        que[qt++] = v;
                    }
                }
                if (level[rSNK] < 0) break;
                for (int v = 0; v < rV; ++v) itp[v] = rHead[v];
                bool any = false;
                while (true) {
                    double f = dfsAug(0, INF);
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
        lastUnmet = unmet; lastHold = hold; lastValid = true;
        writeBack();
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
