#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <utility>
#include <algorithm>
#include <cstdint>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n_jobs = 0, n_machines = 0, n_ops = 0;
    long long horizon = 0;
    std::vector<int> job_off;              // first op id of each job
    std::vector<int> job_len;
    std::vector<int> op_mach, op_proc, op_next, op_hasprev;
    std::vector<int> op_index;             // [j*M + m] -> op id or -1
    std::vector<std::vector<int>> mach_jobs;  // jobs that pass through each machine (ascending)
    bool offset_needed = false;

    // work memory
    mutable std::vector<int> w_indeg, w_msucc, w_queue;
    mutable std::vector<long long> w_start;
    mutable std::vector<unsigned long long> w_stamp;
    mutable unsigned long long w_cur = 0;

    struct Eval { double seq; double ord; long long mk; };

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        std::string line;
        bool header = false;
        while (!header && std::getline(in, line)) {
            std::istringstream ls(line);
            int a, b;
            if (ls >> a >> b) { md.n_jobs = a; md.n_machines = b; header = true; }
        }
        std::vector<std::vector<std::pair<int,int>>> routes(md.n_jobs);
        for (int j = 0; j < md.n_jobs; ++j) {
            if (!std::getline(in, line)) break;
            std::istringstream ls(line);
            int mm, p;
            while (ls >> mm >> p) routes[j].push_back({mm, p});
        }
        md.job_off.assign(md.n_jobs, 0);
        md.job_len.assign(md.n_jobs, 0);
        md.op_index.assign((size_t)md.n_jobs * md.n_machines, -1);
        md.mach_jobs.assign(md.n_machines, {});
        int id = 0;
        for (int j = 0; j < md.n_jobs; ++j) {
            md.job_off[j] = id;
            md.job_len[j] = (int)routes[j].size();
            for (size_t k = 0; k < routes[j].size(); ++k) {
                int mm = routes[j][k].first, p = routes[j][k].second;
                md.op_mach.push_back(mm);
                md.op_proc.push_back(p);
                md.op_hasprev.push_back(k > 0 ? 1 : 0);
                md.op_next.push_back(k + 1 < routes[j].size() ? id + 1 : -1);
                md.horizon += p;
                if (mm >= 0 && mm < md.n_machines) {
                    if (md.op_index[(size_t)j * md.n_machines + mm] < 0) {
                        md.op_index[(size_t)j * md.n_machines + mm] = id;
                        md.mach_jobs[mm].push_back(j);
                    }
                }
                ++id;
            }
        }
        md.n_ops = id;
        md.w_indeg.assign(id, 0);
        md.w_msucc.assign(id, -1);
        md.w_queue.assign(id, 0);
        md.w_start.assign(id, 0);
        md.w_stamp.assign(md.n_jobs, 0);
        Eval e = md.evaluate(md.trivial());
        md.penalty = 10.0 * ((double)std::llabs(e.mk) + 1.0);
        md.offset_needed = !(md.penalty > (double)md.horizon);
        return md;
    }

    Solution trivial() const {
        Solution s(n_machines);
        for (int m = 0; m < n_machines; ++m) s[m] = mach_jobs[m];
        return s;
    }

    // random dispatch: always yields a feasible, well-formed solution
    Solution random(hsf::Rng& rng) const {
        Solution s(n_machines);
        std::vector<int> nextk(n_jobs, 0), active;
        for (int j = 0; j < n_jobs; ++j) if (job_len[j] > 0) active.push_back(j);
        while (!active.empty()) {
            int idx = rng.below((int)active.size());
            int j = active[idx];
            int op = job_off[j] + nextk[j];
            int mm = op_mach[op];
            if (mm >= 0 && mm < n_machines && op_index[(size_t)j * n_machines + mm] == op)
                s[mm].push_back(j);
            if (++nextk[j] >= job_len[j]) { active[idx] = active.back(); active.pop_back(); }
        }
        return s;
    }

    Eval evaluate(const Solution& s) const {
        Eval e{0.0, 0.0, 0};
        for (int o = 0; o < n_ops; ++o) {
            w_indeg[o] = op_hasprev[o];
            w_msucc[o] = -1;
            w_start[o] = 0;
        }
        long long seq = 0;
        int ms = (int)s.size();
        for (int m = 0; m < n_machines; ++m) {
            if (m >= ms) { seq += (long long)mach_jobs[m].size(); continue; }
            ++w_cur;
            int prev = -1, distinct = 0;
            for (int j : s[m]) {
                if (j < 0 || j >= n_jobs) { ++seq; continue; }
                int op = op_index[(size_t)j * n_machines + m];
                if (op < 0) { ++seq; continue; }
                if (w_stamp[j] == w_cur) { ++seq; continue; }
                w_stamp[j] = w_cur;
                ++distinct;
                if (prev >= 0) { w_msucc[prev] = op; ++w_indeg[op]; }
                prev = op;
            }
            seq += (long long)mach_jobs[m].size() - distinct;
        }
        for (int m = n_machines; m < ms; ++m) seq += (long long)s[m].size();

        int head = 0, tail = 0;
        for (int o = 0; o < n_ops; ++o) if (w_indeg[o] == 0) w_queue[tail++] = o;
        long long mk = 0;
        while (head < tail) {
            int o = w_queue[head++];
            long long end = w_start[o] + op_proc[o];
            if (end > mk) mk = end;
            int a = op_next[o];
            if (a >= 0) {
                if (w_start[a] < end) w_start[a] = end;
                if (--w_indeg[a] == 0) w_queue[tail++] = a;
            }
            int b = w_msucc[o];
            if (b >= 0) {
                if (w_start[b] < end) w_start[b] = end;
                if (--w_indeg[b] == 0) w_queue[tail++] = b;
            }
        }
        e.seq = (double)seq;
        e.ord = (double)(n_ops - tail);
        e.mk = mk;
        return e;
    }

    double mk_term(const Eval& e) const {
        double v = (double)e.mk;
        if (offset_needed && (e.seq > 0 || e.ord > 0)) v += (double)horizon;
        return v;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        Eval e = evaluate(s);
        out.clear();
        out.push_back({"secuencia", e.seq});
        out.push_back({"orden", e.ord});
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        Eval e = evaluate(s);
        out.clear();
        out.push_back({"makespan", mk_term(e)});
    }

    double objective(const Solution& s) const {
        Eval e = evaluate(s);
        return mk_term(e) + penalty * (e.seq + e.ord);
    }

    bool feasible(const Solution& s) const {
        Eval e = evaluate(s);
        return e.seq == 0.0 && e.ord == 0.0;
    }
};

}  // namespace gen
