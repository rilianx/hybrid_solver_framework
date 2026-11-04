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

    mutable std::vector<int> msucc, indeg, mark, q, indegM, done, mseq, mstart, mptr;
    mutable std::vector<long long> ready;
    std::vector<int> opJob, opMach, jstart;
    mutable std::vector<int> jptr;
    mutable std::vector<long long> mfree, jfree;
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
            md.jstart.push_back(md.nops);
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
                md.opJob.push_back(j);
                md.opMach.push_back(-1);
                if (prev >= 0) md.opNext[prev] = id;
                prev = id;
                if (mach >= 0 && mach < md.m && md.opid[j][mach] < 0) {
                    md.opid[j][mach] = id;
                    md.opMach[id] = mach;
                    md.needed[mach]++;
                    md.machJobs[mach].push_back(j);
                }
            }
        }
        md.jstart.push_back(md.nops);
        md.jptr.assign(md.n + 1, 0);
        md.mfree.assign(md.m + 1, 0);
        md.jfree.assign(md.n + 1, 0);
        md.msucc.assign(md.nops, -1);
        md.indeg.assign(md.nops, 0);
        md.mark.assign(md.nops, 0);
        md.q.assign(md.nops + 1, 0);
        md.indegM.assign(md.nops, 0);
        md.done.assign(md.nops, 0);
        md.mseq.assign(md.nops + 1, 0);
        md.mstart.assign(md.m + 1, 0);
        md.mptr.assign(md.m + 1, 0);
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
        for (int u = 0; u < nops; ++u) { msucc[u] = -1; indeg[u] = opFirst[u] ? 0 : 1; indegM[u] = 0; done[u] = 0; ready[u] = 0; }
        int ms = (int)s.size();
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            mstart[i] = cnt;
            if (i >= ms) { seq += needed[i]; continue; }
            int prev = -1, present = 0;
            for (int j : s[i]) {
                if (j < 0 || j >= n) { seq += 1; continue; }
                int op = opid[j][i];
                if (op < 0) { seq += 1; continue; }
                if (mark[op] == stamp) { seq += 1; continue; }
                mark[op] = stamp;
                ++present;
                mseq[cnt++] = op;
                if (prev >= 0) { msucc[prev] = op; indegM[op] = 1; }
                prev = op;
            }
            seq += needed[i] - present;
        }
        mstart[m] = cnt;
        for (int i = m; i < ms; ++i) seq += (double)s[i].size();
        for (int i = 0; i < m; ++i) { mptr[i] = mstart[i]; mfree[i] = 0; }
        for (int j = 0; j < n; ++j) { jptr[j] = jstart[j]; jfree[j] = 0; }
        long long mk = 0;
        int processed = 0;
        double ord = 0;
        auto sched = [&](int op) {
            int j = opJob[op];
            bool inSeq = (mark[op] == stamp);
            long long st = jfree[j];
            int mc = inSeq ? opMach[op] : -1;
            if (mc >= 0 && mfree[mc] > st) st = mfree[mc];
            long long fin = st + opProc[op];
            done[op] = 1;
            ++processed;
            if (fin > jfree[j]) jfree[j] = fin;
            if (mc >= 0 && fin > mfree[mc]) mfree[mc] = fin;
            if (fin > mk) mk = fin;
        };
        while (processed < nops) {
            bool progress = true;
            while (progress) {
                progress = false;
                for (int j = 0; j < n; ++j) {
                    while (jptr[j] < jstart[j + 1]) {
                        int op = jptr[j];
                        if (done[op]) { ++jptr[j]; continue; }
                        if (mark[op] != stamp) { sched(op); ++jptr[j]; progress = true; continue; }
                        break;
                    }
                }
                for (int i = 0; i < m; ++i) {
                    while (mptr[i] < mstart[i + 1]) {
                        int op = mseq[mptr[i]];
                        if (done[op]) { ++mptr[i]; continue; }
                        int j = opJob[op];
                        while (jptr[j] < jstart[j + 1] && done[jptr[j]]) ++jptr[j];
                        if (jptr[j] == op) { sched(op); ++mptr[i]; ++jptr[j]; progress = true; continue; }
                        break;
                    }
                }
            }
            if (processed >= nops) break;
            int forced = -1, fmach = -1;
            long long bestPend = 0, bestSt = 0;
            for (int i = 0; i < m; ++i) {
                while (mptr[i] < mstart[i + 1] && done[mseq[mptr[i]]]) ++mptr[i];
                if (mptr[i] < mstart[i + 1]) {
                    int op = mseq[mptr[i]];
                    int j = opJob[op];
                    long long pend = 0;
                    for (int u = jptr[j]; u < op; ++u) if (!done[u]) ++pend;
                    long long st = jfree[j];
                    if (mfree[i] > st) st = mfree[i];
                    if (forced < 0 || pend < bestPend || (pend == bestPend && st < bestSt)) {
                        forced = op; fmach = i; bestPend = pend; bestSt = st;
                    }
                }
            }
            if (fmach >= 0) ++mptr[fmach];
            if (forced < 0) { ord += nops - processed; break; }
            ord += 1;
            sched(forced);
        }
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
