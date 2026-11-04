#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <numeric>
#include <utility>
#include <climits>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n = 0, m = 0, total_ops = 0;
    std::vector<std::vector<std::pair<int,int>>> routes;
    std::vector<std::vector<int>> op_of;        // op_of[j][mach] = global op id or -1
    std::vector<int> op_proc, op_next, op_k;    // per op
    std::vector<std::vector<int>> machine_jobs; // jobs visiting each machine (ascending)

    mutable std::vector<int> mpred, msucc, indeg, qbuf, mark;
    mutable std::vector<long long> st;
    mutable int stamp = 1;

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        in >> md.n >> md.m;
        md.routes.resize(md.n);
        std::string line;
        std::getline(in, line);
        int read = 0;
        while (read < md.n && std::getline(in, line)) {
            bool blank = line.find_first_not_of(" \t\r") == std::string::npos;
            if (blank) continue;
            std::istringstream ls(line);
            int a, b;
            while (ls >> a >> b) md.routes[read].push_back({a, b});
            ++read;
        }
        int maxm = md.m;
        for (auto& r : md.routes) for (auto& o : r) maxm = std::max(maxm, o.first + 1);
        md.op_of.assign(md.n, std::vector<int>(maxm, -1));
        md.machine_jobs.assign(md.m, {});
        int id = 0;
        for (int j = 0; j < md.n; ++j) {
            int L = (int)md.routes[j].size();
            for (int k = 0; k < L; ++k) {
                md.op_of[j][md.routes[j][k].first] = id;
                md.op_proc.push_back(md.routes[j][k].second);
                md.op_next.push_back(k + 1 < L ? id + 1 : -1);
                md.op_k.push_back(k);
                if (md.routes[j][k].first < md.m) md.machine_jobs[md.routes[j][k].first].push_back(j);
                ++id;
            }
        }
        md.total_ops = id;
        md.mpred.assign(id, -1); md.msucc.assign(id, -1); md.indeg.assign(id, 0);
        md.qbuf.assign(id, 0); md.st.assign(id, 0); md.mark.assign(md.n, 0);
        double triv = md.evaluate(md.trivial(), nullptr, nullptr);
        md.penalty = 10.0 * (std::abs(triv) + 1.0);
        return md;
    }

    Solution trivial() const { return machine_jobs; }

    Solution random(hsf::Rng& rng) const {
        Solution s = machine_jobs;
        for (auto& v : s)
            for (int i = (int)v.size() - 1; i > 0; --i) std::swap(v[i], v[rng.below(i + 1)]);
        return s;
    }

    // returns makespan; fills seq / ord violations
    double evaluate(const Solution& s, double* seqv_out, double* ordv_out) const {
        long long seqv = 0;
        for (int o = 0; o < total_ops; ++o) { mpred[o] = -1; msucc[o] = -1; }
        int ms = (int)s.size();
        for (int i = 0; i < ms; ++i) {
            if (i >= m) { seqv += (long long)s[i].size(); continue; }
            if (stamp >= INT_MAX - 2) { std::fill(mark.begin(), mark.end(), 0); stamp = 1; }
            ++stamp;
            int prev = -1, present = 0;
            for (int j : s[i]) {
                if (j < 0 || j >= n || i >= (int)op_of[j].size() || op_of[j][i] < 0) { ++seqv; continue; }
                if (mark[j] == stamp) { ++seqv; continue; }
                mark[j] = stamp;
                int op = op_of[j][i];
                if (prev >= 0) { msucc[prev] = op; mpred[op] = prev; }
                prev = op; ++present;
            }
            seqv += (long long)machine_jobs[i].size() - present;
        }
        for (int i = ms; i < m; ++i) seqv += (long long)machine_jobs[i].size();

        int qh = 0, qt = 0;
        for (int o = 0; o < total_ops; ++o) {
            indeg[o] = (op_k[o] > 0 ? 1 : 0) + (mpred[o] >= 0 ? 1 : 0);
            st[o] = 0;
            if (indeg[o] == 0) qbuf[qt++] = o;
        }
        long long mk = 0;
        while (qh < qt) {
            int o = qbuf[qh++];
            long long e = st[o] + op_proc[o];
            if (e > mk) mk = e;
            int a = op_next[o];
            if (a >= 0) { if (st[a] < e) st[a] = e; if (--indeg[a] == 0) qbuf[qt++] = a; }
            int b = msucc[o];
            if (b >= 0) { if (st[b] < e) st[b] = e; if (--indeg[b] == 0) qbuf[qt++] = b; }
        }
        if (seqv_out) *seqv_out = (double)seqv;
        if (ordv_out) *ordv_out = (double)(total_ops - qt);
        return (double)mk;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double a, b;
        evaluate(s, &a, &b);
        out.push_back({"secuencia", a});
        out.push_back({"orden", b});
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.push_back({"makespan", evaluate(s, nullptr, nullptr)});
    }

    double objective(const Solution& s) const {
        double a, b;
        double mk = evaluate(s, &a, &b);
        return mk + penalty * (a + b);
    }

    bool feasible(const Solution& s) const {
        double a, b;
        evaluate(s, &a, &b);
        return a == 0.0 && b == 0.0;
    }
};

} // namespace gen
