// COMPONENT: {"name": "jssp_machine_window_resequence", "slot": "perturbation", "params": {"window_scale": {"type": "float", "range": [1.0, 5.0]}, "windows_per_strength": {"type": "float", "range": [0.0, 1.0]}, "machine_pick": {"type": "cat", "values": ["critical", "load", "uniform"]}, "rule": {"type": "cat", "values": ["mixed", "shuffle", "reverse", "head_sort"]}}}
struct CoreW {
    using Sol = Model::Solution;
    const Model& md;
    int N, M, J;
    std::vector<int> job, mach, mp, ms, pos, indeg, q, mark;
    std::vector<long long> st;
    std::vector<std::pair<int,int>> cand;
    std::vector<std::pair<double,int>> heap;
    int stamp = 0, endop = -1;
    long long mk = 0;
    explicit CoreW(const Model& m) : md(m), N(m.total_ops), M(m.m), J(m.n) {
        job.assign(N, 0); mach.assign(N, M);
        for (int j = 0; j < J; ++j) for (auto& pr : m.routes[j]) {
            int mi = pr.first;
            if (mi < 0 || mi >= (int)m.op_of[j].size()) continue;
            int o = m.op_of[j][mi];
            if (o >= 0) { job[o] = j; mach[o] = mi; }
        }
        mp.assign(N, -1); ms.assign(N, -1); pos.assign(N, 0); indeg.assign(N, 0); q.assign(N, 0);
        st.assign(N, 0); mark.assign(std::max(1, J), 0);
    }
    bool load(const Sol& s) {
        if ((int)s.size() != M) return false;
        if (stamp > std::numeric_limits<int>::max() - 4 * (M + 2)) { std::fill(mark.begin(), mark.end(), 0); stamp = 0; }
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        for (int i = 0; i < M; ++i) {
            if (s[i].size() != md.machine_jobs[i].size()) return false;
            ++stamp; int prev = -1;
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= J || i >= (int)md.op_of[j].size()) return false;
                int op = md.op_of[j][i];
                if (op < 0 || mark[j] == stamp) return false;
                mark[j] = stamp; pos[op] = idx;
                if (prev >= 0) { ms[prev] = op; mp[op] = prev; }
                prev = op;
            }
        }
        return true;
    }
    bool times() {
        int qh = 0, qt = 0;
        for (int o = 0; o < N; ++o) {
            indeg[o] = (md.op_k[o] > 0 ? 1 : 0) + (mp[o] >= 0 ? 1 : 0); st[o] = 0;
            if (indeg[o] == 0) q[qt++] = o;
        }
        mk = 0; endop = -1;
        while (qh < qt) {
            int o = q[qh++]; long long e = st[o] + md.op_proc[o];
            if (endop < 0 || e > mk) { mk = e; endop = o; }
            int a = md.op_next[o];
            if (a >= 0) { if (st[a] < e) st[a] = e; if (--indeg[a] == 0) q[qt++] = a; }
            int b = ms[o];
            if (b >= 0) { if (st[b] < e) st[b] = e; if (--indeg[b] == 0) q[qt++] = b; }
        }
        return qt == N;
    }
    bool check(const Sol& s) { return load(s) && times(); }
    void critical(Rng& rng, std::vector<int>& path) {
        path.clear(); int o = endop;
        while (o >= 0) {
            path.push_back(o);
            int jp = md.op_k[o] > 0 ? o - 1 : -1, mq = mp[o];
            bool tj = jp >= 0 && st[jp] + md.op_proc[jp] == st[o];
            bool tm = mq >= 0 && st[mq] + md.op_proc[mq] == st[o];
            if (tj && tm) o = rng.below(2) ? jp : mq; else if (tj) o = jp; else if (tm) o = mq; else o = -1;
        }
        std::reverse(path.begin(), path.end());
    }
    bool try_swap(Sol& cur, int mi, int pi) {
        std::swap(cur[mi][pi], cur[mi][pi + 1]);
        if (check(cur)) return true;
        std::swap(cur[mi][pi], cur[mi][pi + 1]);
        check(cur);
        return false;
    }
    bool any_swap(Sol& cur, Rng& rng) {
        cand.clear();
        for (int i = 0; i < M; ++i) for (int p = 0; p + 1 < (int)cur[i].size(); ++p) cand.push_back({i, p});
        if (cand.empty()) return false;
        int lim = std::min<int>(20, (int)cand.size());
        for (int t = 0; t < lim; ++t) { auto cc = cand[rng.below((int)cand.size())]; if (try_swap(cur, cc.first, cc.second)) return true; }
        std::shuffle(cand.begin(), cand.end(), rng.g);
        for (auto& cc : cand) if (try_swap(cur, cc.first, cc.second)) return true;
        return false;
    }
    Sol dispatch(const std::vector<double>& key) {
        Sol out(M);
        for (int i = 0; i < M; ++i) out[i].reserve(md.machine_jobs[i].size());
        heap.clear();
        auto cmp = std::greater<std::pair<double,int>>();
        for (int o = 0; o < N; ++o) if (md.op_k[o] == 0) { heap.push_back({key[o], o}); std::push_heap(heap.begin(), heap.end(), cmp); }
        while (!heap.empty()) {
            std::pop_heap(heap.begin(), heap.end(), cmp);
            int o = heap.back().second; heap.pop_back();
            if (mach[o] < M) out[mach[o]].push_back(job[o]);
            int nx = md.op_next[o];
            if (nx >= 0) { heap.push_back({key[nx], nx}); std::push_heap(heap.begin(), heap.end(), cmp); }
        }
        return out;
    }
    Sol repair(const Sol& s, Rng& rng) {
        std::vector<double> key(N);
        for (int o = 0; o < N; ++o) key[o] = rng.uniform() * (double)std::max(1, J);
        for (int i = 0; i < std::min<int>(M, (int)s.size()); ++i)
            for (int idx = 0; idx < (int)s[i].size(); ++idx) {
                int j = s[i][idx];
                if (j < 0 || j >= J || i >= (int)md.op_of[j].size()) continue;
                int op = md.op_of[j][i]; if (op >= 0) key[op] = idx + 0.5 * rng.uniform();
            }
        return dispatch(key);
    }
};

class MachineWindowResequence : public hsf::Perturbation<Model> {
    CoreW c; double wscale, wps; int pickMode, ruleMode;
    double avgp = 1.0, totLoad = 0.0;
    std::vector<int> elig, path, crit, saved;
    std::vector<double> mload;
    std::vector<std::pair<double,int>> tmp;
public:
    MachineWindowResequence(const Model& m, double ws, double wp, int pm, int rm)
        : c(m), wscale(ws), wps(wp), pickMode(pm), ruleMode(rm) {
        double sum = 0;
        for (int o = 0; o < m.total_ops; ++o) sum += m.op_proc[o];
        avgp = m.total_ops > 0 ? std::max(1.0, sum / m.total_ops) : 1.0;
        mload.assign(m.m, 0.0);
        for (int o = 0; o < m.total_ops; ++o) if (c.mach[o] < m.m) mload[c.mach[o]] += m.op_proc[o];
        for (int i = 0; i < m.m; ++i) if (m.machine_jobs[i].size() >= 2) { elig.push_back(i); totLoad += mload[i] + 1.0; }
    }

    int pick_machine(const Model::Solution& cur, Rng& rng, int& center) {
        center = -1;
        if (pickMode == 0) {
            c.critical(rng, path);
            crit.clear();
            int P = (int)path.size();
            for (int k = 0; k < P; ++k) {
                int o = path[k];
                bool inb = (k > 0 && c.mp[o] == path[k - 1]) || (k + 1 < P && c.mp[path[k + 1]] == o);
                if (inb) crit.push_back(o);
            }
            if (!crit.empty()) {
                int o = crit[rng.below((int)crit.size())];
                center = c.pos[o];
                return c.mach[o];
            }
        }
        if (pickMode <= 1) {
            double r = rng.uniform() * totLoad;
            for (int i : elig) { r -= mload[i] + 1.0; if (r <= 0) return i; }
            return elig.back();
        }
        (void)cur;
        return elig[rng.below((int)elig.size())];
    }

    bool one_window(Model::Solution& cur, double str, Rng& rng) {
        const Model& md = c.md;
        int len0 = (int)std::lround(1.0 + wscale * std::sqrt(str));
        for (int t = 0; t < 10; ++t) {
            int center;
            int mi = pick_machine(cur, rng, center);
            auto& row = cur[mi];
            int L = (int)row.size();
            if (L < 2) continue;
            int len = std::max(2, std::min(L, len0 - t / 2));
            int a;
            if (center >= 0) {
                a = center - rng.below(len);
                a = std::max(0, std::min(L - len, a));
            } else a = rng.below(L - len + 1);
            saved.assign(row.begin() + a, row.begin() + a + len);
            int rule = ruleMode == 0 ? 1 + rng.below(3) : ruleMode;
            if (rule == 1) {
                std::shuffle(row.begin() + a, row.begin() + a + len, rng.g);
            } else if (rule == 2) {
                std::reverse(row.begin() + a, row.begin() + a + len);
            } else {
                tmp.clear();
                for (int x = 0; x < len; ++x) {
                    int j = row[a + x];
                    int o = md.op_of[j][mi];
                    double head = md.op_k[o] > 0 ? (double)(c.st[o - 1] + md.op_proc[o - 1]) : 0.0;
                    tmp.push_back({head + (rng.uniform() - 0.5) * avgp, j});
                }
                std::sort(tmp.begin(), tmp.end());
                for (int x = 0; x < len; ++x) row[a + x] = tmp[x].second;
            }
            if (std::equal(saved.begin(), saved.end(), row.begin() + a)) {
                int x = rng.below(len - 1);
                std::swap(row[a + x], row[a + x + 1]);
            }
            if (c.check(cur)) return true;
            std::copy(saved.begin(), saved.end(), row.begin() + a);
            c.check(cur);
        }
        return false;
    }

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        Model::Solution cur = s;
        if (!c.check(cur)) return c.repair(s, rng);
        if (elig.empty()) return s;
        double str = std::max(1.0, strength);
        int nw = 1 + (int)std::floor((str - 1.0) * wps);
        for (int w = 0; w < nw; ++w) {
            if (!one_window(cur, str, rng)) { if (!c.any_swap(cur, rng)) break; }
        }
        if (cur == s) { c.check(cur); c.any_swap(cur, rng); }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ws = params.get("window_scale", 2.0);
    double wp = params.get("windows_per_strength", 0.3);
    std::string pk = params.text("machine_pick", "critical");
    int pm = pk == "critical" ? 0 : (pk == "load" ? 1 : 2);
    std::string ru = params.text("rule", "mixed");
    int rm = ru == "shuffle" ? 1 : (ru == "reverse" ? 2 : (ru == "head_sort" ? 3 : 0));
    return std::make_unique<MachineWindowResequence>(model, ws, wp, pm, rm);
}
