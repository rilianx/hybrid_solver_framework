#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <numeric>
#include <utility>
#include <climits>
#include <cstdlib>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n = 0, m = 0, total_ops = 0;
    std::vector<std::vector<std::pair<int,int>>> routes;
    std::vector<std::vector<int>> op_of;
    std::vector<int> op_proc, op_next, op_k;
    std::vector<std::vector<int>> machine_jobs;

    std::vector<int> opflat;
    std::vector<int> base_in;
    std::vector<int> first_ops;
    std::vector<int> last_ops;
    std::vector<int> mj_size;
    bool nonneg = true;

    mutable std::vector<int> mpred, msucc, indeg, qbuf, opmark, alist;
    mutable std::vector<long long> en, olden;
    mutable int stamp = 1;

    static const int MAXC = 4;
    mutable std::vector<std::vector<int>> cache;
    mutable bool cache_valid = false;
    mutable long long cache_mk = 0;
    mutable int chg_i[MAXC], chg_lo[MAXC], chg_hi[MAXC];

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
            if (L > 0) { md.first_ops.push_back(id); md.last_ops.push_back(id + L - 1); }
            for (int k = 0; k < L; ++k) {
                md.op_of[j][md.routes[j][k].first] = id;
                md.op_proc.push_back(md.routes[j][k].second);
                if (md.routes[j][k].second < 0) md.nonneg = false;
                md.op_next.push_back(k + 1 < L ? id + 1 : -1);
                md.op_k.push_back(k);
                if (md.routes[j][k].first < md.m) md.machine_jobs[md.routes[j][k].first].push_back(j);
                ++id;
            }
        }
        md.total_ops = id;
        md.opflat.assign((size_t)md.m * md.n, -1);
        for (int i = 0; i < md.m; ++i)
            for (int j = 0; j < md.n; ++j) md.opflat[(size_t)i * md.n + j] = md.op_of[j][i];
        md.base_in.assign(id, 0);
        for (int o = 0; o < id; ++o) md.base_in[o] = md.op_k[o] > 0 ? 1 : 0;
        md.mj_size.assign(md.m, 0);
        for (int i = 0; i < md.m; ++i) md.mj_size[i] = (int)md.machine_jobs[i].size();
        md.mpred.assign(id, -1); md.msucc.assign(id, -1); md.indeg.assign(id, 0);
        md.qbuf.assign(id, 0); md.en.assign(id, 0); md.opmark.assign(id, 0);
        md.alist.assign(id, 0); md.olden.assign(id, 0);
        md.cache = md.machine_jobs;
        md.cache_valid = false;
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

    // incremental evaluation against cached valid solution; returns false if not applicable
    bool try_inc(const Solution& s, long long& mk_out, long long& ordv_out) const {
        if ((int)s.size() != m) return false;
        int nc = 0;
        for (int i = 0; i < m; ++i) {
            const std::vector<int>& a = s[i];
            const std::vector<int>& c = cache[i];
            const int sz = (int)c.size();
            if ((int)a.size() != sz) return false;
            const int* ap = a.data(); const int* cp = c.data();
            int lo = 0;
            while (lo < sz && ap[lo] == cp[lo]) ++lo;
            if (lo == sz) continue;
            if (nc == MAXC) return false;
            int hi = sz - 1;
            while (ap[hi] == cp[hi]) --hi;
            chg_i[nc] = i; chg_lo[nc] = lo; chg_hi[nc] = hi; ++nc;
        }
        if (nc == 0) { mk_out = cache_mk; ordv_out = 0; return true; }

        int* MP = mpred.data();
        int* MS = msucc.data();
        int* MK = opmark.data();
        int* ID = indeg.data();
        int* Q = qbuf.data();
        int* A = alist.data();
        long long* EN = en.data();
        long long* OE = olden.data();
        const int* BI = base_in.data();
        const int* OF = opflat.data();
        const int* PR = op_proc.data();
        const int* NX = op_next.data();
        const int nn = n;

        // validate permutations of changed ranges
        const int stp1 = ++stamp;
        for (int c = 0; c < nc; ++c) {
            const int* row = OF + (size_t)chg_i[c] * nn;
            const int* cp = cache[chg_i[c]].data();
            for (int t = chg_lo[c]; t <= chg_hi[c]; ++t) MK[row[cp[t]]] = stp1;
        }
        const int stp2 = ++stamp;
        for (int c = 0; c < nc; ++c) {
            const int* row = OF + (size_t)chg_i[c] * nn;
            const int* ap = s[chg_i[c]].data();
            for (int t = chg_lo[c]; t <= chg_hi[c]; ++t) {
                int j = ap[t];
                if ((unsigned)j >= (unsigned)nn) return false;
                int op = row[j];
                if (op < 0 || MK[op] != stp1) return false;
                MK[op] = stp2;
            }
        }
        // apply new machine links
        for (int c = 0; c < nc; ++c) {
            const int* row = OF + (size_t)chg_i[c] * nn;
            const int* ap = s[chg_i[c]].data();
            const int sz = (int)s[chg_i[c]].size();
            int t0 = chg_lo[c] > 0 ? chg_lo[c] - 1 : 0;
            int t1 = chg_hi[c] + 1 < sz ? chg_hi[c] + 1 : sz - 1;
            for (int t = t0; t <= t1; ++t) {
                int op = row[ap[t]];
                MP[op] = t > 0 ? row[ap[t - 1]] : -1;
                MS[op] = t < sz - 1 ? row[ap[t + 1]] : -1;
            }
        }
        // affected set = descendants of changed range ops
        const int stp3 = ++stamp;
        int na = 0;
        for (int c = 0; c < nc; ++c) {
            const int* row = OF + (size_t)chg_i[c] * nn;
            const int* ap = s[chg_i[c]].data();
            for (int t = chg_lo[c]; t <= chg_hi[c]; ++t) {
                int op = row[ap[t]];
                if (MK[op] != stp3) { MK[op] = stp3; A[na++] = op; }
            }
        }
        for (int k = 0; k < na; ++k) {
            int o = A[k];
            int a = NX[o];
            if (a >= 0 && MK[a] != stp3) { MK[a] = stp3; A[na++] = a; }
            int b = MS[o];
            if (b >= 0 && MK[b] != stp3) { MK[b] = stp3; A[na++] = b; }
        }
        int qt = 0;
        for (int k = 0; k < na; ++k) {
            int o = A[k];
            OE[k] = EN[o];
            int d = (BI[o] && MK[o - 1] == stp3) ? 1 : 0;
            int p = MP[o];
            if (p >= 0 && MK[p] == stp3) ++d;
            ID[o] = d;
            if (d == 0) Q[qt++] = o;
        }
        const int stp4 = ++stamp;
        int qh = 0;
        while (qh < qt) {
            int o = Q[qh++];
            MK[o] = stp4;
            long long sv = 0;
            if (BI[o]) sv = EN[o - 1];
            int p = MP[o];
            if (p >= 0 && EN[p] > sv) sv = EN[p];
            EN[o] = sv + PR[o];
            int a = NX[o];
            if (a >= 0 && --ID[a] == 0) Q[qt++] = a;
            int b = MS[o];
            if (b >= 0 && --ID[b] == 0) Q[qt++] = b;
        }
        const int T = total_ops;
        if (qt == na) {
            long long mk = 0;
            if (nonneg) {
                for (int o : last_ops) if (EN[o] > mk) mk = EN[o];
            } else {
                for (int o = 0; o < T; ++o) if (EN[o] > mk) mk = EN[o];
            }
            for (int c = 0; c < nc; ++c) {
                const int* ap = s[chg_i[c]].data();
                int* cp = cache[chg_i[c]].data();
                for (int t = chg_lo[c]; t <= chg_hi[c]; ++t) cp[t] = ap[t];
            }
            cache_mk = mk;
            mk_out = mk; ordv_out = 0;
            return true;
        }
        // cycle: compute exact result, then restore cached state
        long long mk = 0;
        for (int o = 0; o < T; ++o) if (MK[o] != stp3 && EN[o] > mk) mk = EN[o];
        for (int k = 0; k < na; ++k) EN[A[k]] = OE[k];
        for (int c = 0; c < nc; ++c) {
            const int* row = OF + (size_t)chg_i[c] * nn;
            const int* cp = cache[chg_i[c]].data();
            const int sz = (int)cache[chg_i[c]].size();
            int t0 = chg_lo[c] > 0 ? chg_lo[c] - 1 : 0;
            int t1 = chg_hi[c] + 1 < sz ? chg_hi[c] + 1 : sz - 1;
            for (int t = t0; t <= t1; ++t) {
                int op = row[cp[t]];
                MP[op] = t > 0 ? row[cp[t - 1]] : -1;
                MS[op] = t < sz - 1 ? row[cp[t + 1]] : -1;
            }
        }
        mk_out = mk; ordv_out = (long long)(na - qt);
        return true;
    }

    double evaluate(const Solution& s, double* seqv_out, double* ordv_out) const {
        if (stamp >= INT_MAX - 16) { std::fill(opmark.begin(), opmark.end(), 0); stamp = 1; }
        if (cache_valid) {
            long long mk, ov;
            if (try_inc(s, mk, ov)) {
                if (seqv_out) *seqv_out = 0.0;
                if (ordv_out) *ordv_out = (double)ov;
                return (double)mk;
            }
            if (stamp >= INT_MAX - 16) { std::fill(opmark.begin(), opmark.end(), 0); stamp = 1; }
        }
        return full_eval(s, seqv_out, ordv_out);
    }

    double full_eval(const Solution& s, double* seqv_out, double* ordv_out) const {
        cache_valid = false;
        long long seqv = 0;
        const int stp = ++stamp;
        int* MP = mpred.data();
        int* MS = msucc.data();
        int* MK = opmark.data();
        int* ID = indeg.data();
        const int* BI = base_in.data();
        const int* OF = opflat.data();
        const int nn = n;
        int ms = (int)s.size();
        int lim = ms < m ? ms : m;
        long long marked = 0;
        for (int i = 0; i < lim; ++i) {
            const int* row = OF + (size_t)i * nn;
            int prev = -1, present = 0;
            const std::vector<int>& seq = s[i];
            const int* sp = seq.data();
            const int sz = (int)seq.size();
            for (int t = 0; t < sz; ++t) {
                int j = sp[t];
                if ((unsigned)j >= (unsigned)nn) { ++seqv; continue; }
                int op = row[j];
                if (op < 0 || MK[op] == stp) { ++seqv; continue; }
                MK[op] = stp;
                MP[op] = prev; MS[op] = -1;
                if (prev >= 0) { MS[prev] = op; ID[op] = BI[op] + 1; }
                else ID[op] = BI[op];
                prev = op; ++present;
            }
            seqv += (long long)mj_size[i] - present;
            marked += present;
        }
        for (int i = m; i < ms; ++i) seqv += (long long)s[i].size();
        for (int i = ms; i < m; ++i) seqv += (long long)mj_size[i];

        const int T = total_ops;
        int* Q = qbuf.data();
        long long* EN = en.data();
        const int* PR = op_proc.data();
        const int* NX = op_next.data();
        int qh = 0, qt = 0;
        if (marked == (long long)T) {
            for (int o : first_ops) if (ID[o] == 0) Q[qt++] = o;
        } else {
            for (int o = 0; o < T; ++o) {
                if (MK[o] != stp) { MP[o] = -1; MS[o] = -1; ID[o] = BI[o]; }
                if (ID[o] == 0) Q[qt++] = o;
            }
        }
        long long mk = 0;
        while (qh < qt) {
            int o = Q[qh++];
            long long sv = 0;
            if (BI[o]) sv = EN[o - 1];
            int p = MP[o];
            if (p >= 0 && EN[p] > sv) sv = EN[p];
            long long e = sv + PR[o];
            EN[o] = e;
            if (e > mk) mk = e;
            int a = NX[o];
            if (a >= 0 && --ID[a] == 0) Q[qt++] = a;
            int b = MS[o];
            if (b >= 0 && --ID[b] == 0) Q[qt++] = b;
        }
        if (seqv == 0 && qt == T) {
            for (int i = 0; i < m; ++i) cache[i].assign(s[i].begin(), s[i].end());
            cache_valid = true;
            cache_mk = mk;
        }
        if (seqv_out) *seqv_out = (double)seqv;
        if (ordv_out) *ordv_out = (double)(T - qt);
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
