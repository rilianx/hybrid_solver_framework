#pragma once
#include <hsf/core.hpp>
#include <string>
#include <vector>
#include <utility>
#include <sstream>
#include <algorithm>
#include <numeric>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n = 0, m = 0, nops = 0;
    std::vector<std::vector<int>> opid;      // opid[j][mach] = id de operación o -1
    std::vector<int> opProc, opNext, opFirst; // proc, siguiente del trabajo (-1), 1 si es la primera
    std::vector<int> needed;                  // trabajos que pasan por cada máquina
    std::vector<std::vector<int>> machJobs;

    mutable std::vector<int> msucc, indeg, mark, q;
    mutable std::vector<long long> ready;
    mutable int stamp = 0;

    struct Eval { double seq; double ord; double mk; };

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        std::string line;
        std::vector<std::string> lines;
        while (std::getline(in, line)) {
            bool blank = true;
            for (char c : line) if (!isspace((unsigned char)c)) { blank = false; break; }
            if (!blank) lines.push_back(line);
        }
        {
            std::istringstream h(lines[0]);
            h >> md.n >> md.m;
        }
        md.opid.assign(md.n, std::vector<int>(md.m, -1));
        md.needed.assign(md.m, 0);
        md.machJobs.assign(md.m, {});
        for (int j = 0; j < md.n; ++j) {
            std::vector<int> vals;
            if (j + 1 < (int)lines.size()) {
                std::istringstream ls(lines[j + 1]);
                int v;
                while (ls >> v) vals.push_back(v);
            }
            int prev = -1;
            for (size_t i = 0; i + 1 < vals.size(); i += 2) {
                int mach = vals[i], p = vals[i + 1];
                int id = md.nops++;
                md.opProc.push_back(p);
                md.opNext.push_back(-1);
                md.opFirst.push_back(prev < 0 ? 1 : 0);
                if (prev >= 0) md.opNext[prev] = id;
                prev = id;
                if (mach >= 0 && mach < md.m && md.opid[j][mach] < 0) {
                    md.opid[j][mach] = id;
                    md.needed[mach]++;
                    md.machJobs[mach].push_back(j);
                }
            }
        }
        md.msucc.assign(md.nops, -1);
        md.indeg.assign(md.nops, 0);
        md.mark.assign(md.nops, 0);
        md.q.assign(md.nops, 0);
        md.ready.assign(md.nops, 0);
        Eval e = md.eval(md.trivial());
        md.penalty = 10.0 * (std::abs(e.mk) + 1.0);
        return md;
    }

    Solution trivial() const {
        Solution s(m);
        for (int i = 0; i < m; ++i) s[i] = machJobs[i];
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        Solution s = trivial();
        for (auto& v : s)
            for (int i = (int)v.size() - 1; i > 0; --i) std::swap(v[i], v[rng.below(i + 1)]);
        return s;
    }

    Eval eval(const Solution& s) const {
        double seq = 0;
        ++stamp;
        if (stamp == 0x7fffffff) { std::fill(mark.begin(), mark.end(), 0); stamp = 1; }
        for (int u = 0; u < nops; ++u) { msucc[u] = -1; indeg[u] = opFirst[u] ? 0 : 1; ready[u] = 0; }
        int ms = (int)s.size();
        for (int i = 0; i < m; ++i) {
            if (i >= ms) { seq += needed[i]; continue; }
            int prev = -1, present = 0;
            for (int j : s[i]) {
                if (j < 0 || j >= n) { seq += 1; continue; }
                int op = opid[j][i];
                if (op < 0) { seq += 1; continue; }
                if (mark[op] == stamp) { seq += 1; continue; }
                mark[op] = stamp;
                ++present;
                if (prev >= 0) { msucc[prev] = op; indeg[op]++; }
                prev = op;
            }
            seq += needed[i] - present;
        }
        for (int i = m; i < ms; ++i) seq += (double)s[i].size();
        int head = 0, tail = 0;
        for (int u = 0; u < nops; ++u) if (indeg[u] == 0) q[tail++] = u;
        long long mk = 0;
        while (head < tail) {
            int u = q[head++];
            long long fin = ready[u] + opProc[u];
            if (fin > mk) mk = fin;
            int a = opNext[u], b = msucc[u];
            if (a >= 0) { if (fin > ready[a]) ready[a] = fin; if (--indeg[a] == 0) q[tail++] = a; }
            if (b >= 0) { if (fin > ready[b]) ready[b] = fin; if (--indeg[b] == 0) q[tail++] = b; }
        }
        double ord = (double)(nops - tail);
        return {seq, ord, (double)mk};
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        Eval e = eval(s);
        out.clear();
        out.emplace_back("secuencia", e.seq);
        out.emplace_back("orden", e.ord);
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        Eval e = eval(s);
        out.clear();
        out.emplace_back("makespan", e.mk);
    }

    double objective(const Solution& s) const {
        Eval e = eval(s);
        return e.mk + penalty * (e.seq + e.ord);
    }

    bool feasible(const Solution& s) const {
        Eval e = eval(s);
        return e.seq == 0 && e.ord == 0;
    }
};

} // namespace gen
