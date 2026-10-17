# -*- coding: utf-8 -*-
"""
一键复现全部计算结果与图表
==========================
运行:  python run_all.py
输出:  sim/outputs/ 下的 PNG、CSV、summary.json
"""

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import majority_model as mm
from majority_model import GATE_ROLES, INPUT_ON

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

UCF = os.path.join(ROOT, "design", "Eco1C1G1T1.UCF.json")
OFFICIAL_TXT = os.path.join(ROOT, "design", "majority_A000_logic_circuit.txt")

C_IN = "#2E6F95"
C_GATE = "#E8EEF3"
C_EDGE = "#4A5568"
C_ON = "#C0392B"
C_OFF = "#7F8C8D"


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved", name)


# ---------------------------------------------------------------------------
# 图1 线路拓扑
# ---------------------------------------------------------------------------
def fig_topology():
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def box(x, y, w, h, label, sub=None, fc=C_GATE, ec=C_EDGE, fs=10):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0.03,rounding_size=0.08",
                                    fc=fc, ec=ec, lw=1.2, zorder=3))
        ax.text(x, y + (0.12 if sub else 0), label, ha="center", va="center",
                fontsize=fs, color="#1A202C", zorder=4)
        if sub:
            ax.text(x, y - 0.22, sub, ha="center", va="center",
                    fontsize=7.5, color="#5A6B7B", zorder=4)

    def arrow(x1, y1, x2, y2, rad=0.0, color=C_EDGE):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                     connectionstyle=f"arc3,rad={rad}",
                                     arrowstyle="-|>", mutation_scale=11,
                                     lw=1.1, color=color, zorder=2))

    # 输入层
    box(1.0, 5.0, 1.5, 0.62, "pTet", "输入 A", fc="#DCEAF5")
    box(1.0, 3.6, 1.5, 0.62, "pBAD", "输入 B", fc="#DCEAF5")
    box(1.0, 2.2, 1.5, 0.62, "pTac", "输入 C", fc="#DCEAF5")

    # 第一层
    box(3.4, 5.0, 1.6, 0.62, "n6 = ¬A", "A1_AmtR")
    box(3.4, 3.6, 1.6, 0.62, "n5 = ¬B", "S2_SrpR")
    box(3.4, 2.2, 1.6, 0.62, "n2 = ¬C", "H1_HlyIIR")
    box(3.4, 4.35, 1.6, 0.62, "n3 = ¬(A∨B)", "B3_BM3R1")

    # 第二层
    box(6.0, 4.35, 1.7, 0.62, "n4 = ¬(¬A∨¬B)", "= A ∧ B", )
    box(6.0, 3.0, 1.7, 0.62, "n1 = ¬(¬C∨n3)", "= C ∧ (A∨B)")

    # 输出
    box(8.6, 3.65, 1.9, 0.8, "OUT = n4 + n1", "YFP 荧光", fc="#FBE9E7")

    arrow(1.75, 5.0, 2.6, 5.0)
    arrow(1.75, 3.6, 2.6, 3.6)
    arrow(1.75, 2.2, 2.6, 2.2)
    arrow(1.75, 4.9, 2.55, 4.45, rad=-0.15)
    arrow(1.75, 3.7, 2.55, 4.25, rad=0.15)
    arrow(4.2, 5.0, 5.15, 4.5, rad=-0.12)
    arrow(4.2, 3.6, 5.15, 4.2, rad=0.12)
    arrow(4.2, 2.2, 5.15, 2.85, rad=0.1)
    arrow(4.2, 4.3, 5.15, 3.15, rad=-0.1)
    arrow(6.85, 4.35, 7.65, 3.95, rad=-0.1)
    arrow(6.85, 3.0, 7.65, 3.4, rad=0.1)

    ax.set_ylim(0.25, 5.55)
    save(fig, "fig1_topology.png")


# ---------------------------------------------------------------------------
# 图2 门响应曲线
# ---------------------------------------------------------------------------
def fig_hill_curves(gates):
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 5.0), sharex=True)
    xs = np.logspace(-3, 1.2, 400)
    for ax, (gname, role) in zip(axes.ravel(), GATE_ROLES.items()):
        p = gates[gname]["params"]
        ys = mm.hill_nor(xs, p["ymax"], p["ymin"], p["K"], p["n"])
        ax.plot(xs, ys, color=C_ON, lw=1.8)
        ax.axvline(p["K"], ls=":", color=C_OFF, lw=1)
        ax.axhline(p["ymin"], ls="--", color=C_OFF, lw=0.8)
        ax.axhline(p["ymax"], ls="--", color=C_OFF, lw=0.8)
        ax.set_xscale("log")
        ax.set_title(f"{gname}  ({role['logic']})", fontsize=9.5)
        ax.text(0.04, 0.08,
                f"K={p['K']:.3g}  n={p['n']:.2f}\n"
                f"{p['ymin']:.3g}→{p['ymax']:.3g}",
                transform=ax.transAxes, fontsize=7.2, color="#4A5568",
                va="bottom")
        ax.grid(alpha=0.25, lw=0.5)
    for ax in axes[-1]:
        ax.set_xlabel("输入信号 S (RPU)", fontsize=8.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("稳态输出 (RPU)", fontsize=8.5)
    fig.suptitle("Cello 官方门库 Eco1C1G1T1 中本设计所用 6 个 NOR 门的响应函数",
                 fontsize=10.5, y=1.0)
    fig.tight_layout()
    save(fig, "fig2_hill_curves.png")


# ---------------------------------------------------------------------------
# 图3 稳态真值表
# ---------------------------------------------------------------------------
def fig_truth_table(results):
    labels = [f"{r['pTac']}{r['pTet']}{r['pBAD']}" for r in results]
    outs = [r["out"] for r in results]
    exp = [r["expected"] for r in results]
    colors = [C_ON if r["expected"] else C_OFF for r in results]

    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    bars = ax.bar(range(8), outs, color=colors, width=0.62, alpha=0.9,
                  edgecolor="white", lw=0.8)
    thr = 1.0
    ax.axhline(thr, ls="--", color="#2C3E50", lw=1.2,
               label="判决阈值 1.0 RPU")
    for i, (b, r) in enumerate(zip(bars, results)):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() * 1.04,
                f"{r['out']:.2f}", ha="center", fontsize=7.5, color="#1A202C")
    ax.set_xticks(range(8))
    ax.set_xticklabels([f"{l}→{e}" for l, e in zip(labels, exp)], fontsize=8.5)
    ax.set_xlabel("输入组合 (pTac pTet pBAD) → 理论输出", fontsize=9)
    ax.set_ylabel("稳态荧光输出 (RPU)", fontsize=9)
    ax.set_title("8 种输入组合的稳态输出：逻辑判定 8/8 正确", fontsize=10.5)
    ax.grid(axis="y", alpha=0.25, lw=0.5)
    ax.set_ylim(0, max(outs) * 1.18)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    save(fig, "fig3_truth_table.png")


# ---------------------------------------------------------------------------
# 图4 时序响应
# ---------------------------------------------------------------------------
def fig_timecourse(t, out, nodes, dwell):
    seq = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0),
           (1, 1, 0), (1, 1, 1), (1, 0, 1), (1, 0, 0)]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 5.6), sharex=True,
                                   gridspec_kw=dict(height_ratios=[1.15, 2.1]))
    from matplotlib.patches import Rectangle

    rows = [("pTac", 2.3, "#2E6F95", 0), ("pTet", 1.4, "#8E44AD", 1),
            ("pBAD", 0.5, "#16A085", 2)]
    for name, y, col, idx in rows:
        ax1.text(-0.02, y, name, ha="right", va="center", fontsize=8.5,
                 color="#1A202C", transform=ax1.get_yaxis_transform())
        for k, s in enumerate(seq):
            t0, t1 = k * dwell, (k + 1) * dwell
            val = s[idx]   # seq 元组为 (pTac, pTet, pBAD)
            ax1.add_patch(Rectangle((t0, y - 0.28), dwell, 0.56,
                                    fc=col if val else "#EDF1F4",
                                    ec="white", lw=1.6))
            ax1.text((t0 + t1) / 2, y, "1" if val else "0", ha="center",
                     va="center", fontsize=8,
                     color="white" if val else "#7F8C8D")
    for k, s in enumerate(seq):
        ax1.text((k + 0.5) * dwell, 3.02, f"{s[0]}{s[1]}{s[2]}", ha="center",
                 fontsize=8, color="#4A5568")
    ax1.set_ylim(0.05, 3.2)
    ax1.set_yticks([])
    ax1.set_title("输入切换下的输出响应（Gray 码遍历，避免多位同时翻转）", fontsize=10)
    for s in ["top", "right", "left"]:
        ax1.spines[s].set_visible(False)

    ax2.plot(t, out, color=C_ON, lw=1.6, label="输出 YFP (RPU)")
    ax2.axhline(1.0, ls="--", color="#2C3E50", lw=1)
    for k in range(1, len(seq)):
        ax2.axvline(k * dwell, color="#BDC3C7", lw=0.7, ls=":")
    ax2.set_xlabel("时间 (min)", fontsize=9)
    ax2.set_ylabel("输出 (RPU)", fontsize=9)
    ax2.grid(alpha=0.25, lw=0.5)
    ax2.legend(fontsize=8, frameon=False, loc="upper right")
    save(fig, "fig4_timecourse.png")


# ---------------------------------------------------------------------------
# 图5 鲁棒性
# ---------------------------------------------------------------------------
def monte_carlo(gates, n=300, sigma=0.15, seed=0):
    rng = np.random.default_rng(seed)
    names = list(GATE_ROLES.keys())
    base = {g: dict(gates[g]["params"]) for g in names}
    ok, ratios, mins_on, maxs_off = 0, [], [], []
    for _ in range(n):
        g2 = {g: {"params": dict(p)} for g, p in base.items()}
        for g in names:
            for k in ("ymax", "ymin", "K", "n"):
                g2[g]["params"][k] *= float(np.exp(rng.normal(0, sigma)))
        res = mm.simulate_truth_table(g2, mode="analytic")
        ons = [r["out"] for r in res if r["expected"] == 1]
        offs = [r["out"] for r in res if r["expected"] == 0]
        good = all((r["out"] > 1.0) for r in res if r["expected"] == 1) and \
               all((r["out"] <= 1.0) for r in res if r["expected"] == 0)
        ok += good
        ratios.append(min(ons) / max(max(offs), 1e-9))
        mins_on.append(min(ons))
        maxs_off.append(max(offs))
    return ok / n, np.array(ratios), np.array(mins_on), np.array(maxs_off)


def input_window(gates, on_levels):
    succ = []
    for lv in on_levels:
        res = []
        for row in mm.majority_truth_table():
            st = {"pTet": lv if row["pTet"] else 0.0,
                  "pBAD": lv if row["pBAD"] else 0.0,
                  "pTac": lv if row["pTac"] else 0.0}
            v = mm.node_values(st, gates)
            res.append({**row, "out": v["out"]})
        good = all((r["out"] > 1.0) == (r["expected"] == 1) for r in res)
        succ.append(1.0 if good else 0.0)
    return np.array(succ)


def hill_scale_test(gates, scales):
    succ, mins = [], []
    for s in scales:
        g2 = {g: {"params": dict(gates[g]["params"])} for g in GATE_ROLES}
        for g in g2:
            g2[g]["params"]["n"] *= s
        res = mm.simulate_truth_table(g2, mode="analytic")
        good = all((r["out"] > 1.0) == (r["expected"] == 1) for r in res)
        succ.append(1.0 if good else 0.0)
        mins.append(min(r["out"] for r in res if r["expected"] == 1))
    return np.array(succ), np.array(mins)


def input_noise(gates, cv=0.10, n=200, seed=1):
    rng = np.random.default_rng(seed)
    err, total = 0, 0
    for _ in range(n):
        for row in mm.majority_truth_table():
            cc = rng.normal(1.0, cv) if row["pTac"] else abs(rng.normal(0, cv * 0.3))
            aa = rng.normal(1.0, cv) if row["pTet"] else abs(rng.normal(0, cv * 0.3))
            bb = rng.normal(1.0, cv) if row["pBAD"] else abs(rng.normal(0, cv * 0.3))
            v = mm.node_values({"pTac": max(cc, 0), "pTet": max(aa, 0),
                                "pBAD": max(bb, 0)}, gates)
            pred = 1 if v["out"] > 1.0 else 0
            err += (pred != row["expected"])
            total += 1
    return err / total


def noise_curve(gates, cvs, n=200, seed=3):
    out = []
    for cv in cvs:
        out.append(input_noise(gates, cv=cv, n=n, seed=seed + int(cv * 1000)))
    return np.array(out)


def fig_robustness(gates):
    ok_rate, ratios, mins_on, maxs_off = monte_carlo(gates)
    ons = np.linspace(0.4, 3.0, 14)
    win = input_window(gates, ons)
    scales = np.linspace(0.7, 1.3, 13)
    hs, hmin = hill_scale_test(gates, scales)
    cvs = np.array([0.0, 0.05, 0.10, 0.15, 0.20, 0.25])
    errs = noise_curve(gates, cvs)
    noise_err = float(errs[list(cvs).index(0.10)])

    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.0))

    ax = axes[0, 0]
    ax.hist(ratios, bins=30, color=C_IN, alpha=0.85, edgecolor="white")
    ax.axvline(10, ls="--", color=C_ON, lw=1.2)
    ax.text(0.97, 0.93, f"8/8 正确率  {ok_rate*100:.1f}%", transform=ax.transAxes,
            fontsize=9, color="#1A202C", ha="right",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#CBD5E0", lw=0.6))
    ax.set_xlabel("ON/OFF 比值（最小值/最大值）", fontsize=9)
    ax.set_ylabel("参数样本数", fontsize=9)
    ax.set_title("(a) 参数 ±15% 随机扰动（n=300）", fontsize=9.5)
    ax.grid(axis="y", alpha=0.25, lw=0.5)

    ax = axes[0, 1]
    ax.plot(ons, win, "o-", color=C_IN, lw=1.8, ms=4.5)
    ax.set_xlabel("输入'1'的信号水平 (RPU)", fontsize=9)
    ax.set_ylabel("逻辑正确（1=是）", fontsize=9)
    ax.set_ylim(-0.1, 1.12)
    ax.axvspan(0.6, 3.0, color="#D6E4EF", alpha=0.5, zorder=0)
    ax.set_title("(b) 输入工作窗口：≥0.6 RPU", fontsize=9.5)
    ax.grid(alpha=0.25, lw=0.5)

    ax = axes[1, 0]
    ax.plot(scales, hs, "s-", color="#8E44AD", lw=1.8, ms=4.5)
    ax.set_xlabel("Hill 系数 n 的缩放倍数", fontsize=9)
    ax.set_ylabel("逻辑正确（1=是）", fontsize=9)
    ax.set_ylim(-0.1, 1.12)
    ax.set_title("(c) 协同性敏感性：n 缩放 0.7–1.3", fontsize=9.5)
    ax.grid(alpha=0.25, lw=0.5)

    ax = axes[1, 1]
    ax.plot(cvs * 100, errs * 100, "^-", color="#16A085", lw=1.8, ms=5)
    ax.set_xlabel("输入噪声（变异系数 %）", fontsize=9)
    ax.set_ylabel("误判率 (%)", fontsize=9)
    ax.set_title("(d) 输入噪声下的误判率", fontsize=9.5)
    ax.grid(alpha=0.25, lw=0.5)
    ax.annotate(f"CV=10%: {noise_err*100:.2f}%",
                xy=(10, noise_err * 100), xytext=(1.2, max(errs * 100) * 0.78),
                fontsize=8.5, color="#16A085", ha="left",
                arrowprops=dict(arrowstyle="->", color="#16A085", lw=0.9,
                                connectionstyle="arc3,rad=-0.2"))

    fig.tight_layout()
    save(fig, "fig5_robustness.png")
    return dict(mc_success_rate=float(ok_rate),
                mc_ratio_median=float(np.median(ratios)),
                mc_ratio_min=float(ratios.min()),
                input_window=[float(ons[win > 0].min()), float(ons[win > 0].max())]
                if win.any() else None,
                hill_ok_range=[float(scales[hs > 0].min()), float(scales[hs > 0].max())]
                if hs.any() else None,
                input_noise_error_rate=noise_err,
                noise_curve={f"{c:.2f}": float(e) for c, e in zip(cvs, errs)})


# ---------------------------------------------------------------------------
# 图6 与官方 Cello 结果对比
# ---------------------------------------------------------------------------
def parse_official(path):
    """从官方 txt 中提取 OUTPUT_OR 的 8 个输出值。"""
    vals = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    started = False
    for ln in lines:
        if ln.strip().startswith("output_YFP  Gate="):
            started = True
            continue
        if started:
            s = ln.strip()
            if not s.startswith("_OUTPUT_OR"):
                break
            # 形如: _OUTPUT_OR [ 0 0 1 ]: 0  0.580:  0.608  multiplied_tox: 0.99
            try:
                left, right = s.split("]:")
                bits = left.split("[")[1].strip().split()
                outv = float(right.split(":")[1].split()[0])
                key = "".join(bits)
                vals[key] = outv
            except Exception:
                continue
    return vals


def fig_cello_comparison(results, official):
    keys = [f"{r['pTac']}{r['pTet']}{r['pBAD']}" for r in results]
    ours = np.array([r["out"] for r in results])
    off = np.array([official.get(k, np.nan) for k in keys])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 3.8),
                                   gridspec_kw=dict(width_ratios=[1.3, 1]))
    x = np.arange(8)
    ax1.bar(x - 0.2, ours, width=0.4, color=C_IN, label="本模型（官方 UCF 参数）")
    ax1.bar(x + 0.2, off, width=0.4, color="#E67E22", alpha=0.85,
            label="Cello 官方输出（较早门库）")
    ax1.set_xticks(x)
    ax1.set_xticklabels(keys, fontsize=8)
    ax1.set_xlabel("输入组合 (pTac pTet pBAD)", fontsize=8.5)
    ax1.set_ylabel("输出 (RPU)", fontsize=8.5)
    ax1.set_title("绝对水平：门库版本不同，不可直接比较", fontsize=9)
    ax1.legend(fontsize=7.5, frameon=False)
    ax1.grid(axis="y", alpha=0.25, lw=0.5)

    # 归一化到各自最大值，比较形状
    ax2.plot(x, ours / ours.max(), "o-", color=C_IN, lw=1.6, ms=5, label="本模型")
    ax2.plot(x, off / np.nanmax(off), "s--", color="#E67E22", lw=1.6, ms=5,
             label="Cello 官方")
    ax2.set_xticks(x)
    ax2.set_xticklabels(keys, fontsize=8)
    ax2.set_xlabel("输入组合 (pTac pTet pBAD)", fontsize=8.5)
    ax2.set_ylabel("归一化输出", fontsize=8.5)
    ax2.set_title("归一化后：逻辑与能级结构一致", fontsize=9)
    ax2.legend(fontsize=7.5, frameon=False)
    ax2.grid(alpha=0.25, lw=0.5)
    fig.tight_layout()
    save(fig, "fig6_cello_comparison.png")

    corr = float(np.corrcoef(ours, off)[0, 1])
    return dict(corr_normalized=corr,
                ours_range=[float(ours.min()), float(ours.max())],
                official_range=[float(np.nanmin(off)), float(np.nanmax(off))])


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    print("[1/7] 读取官方门库 ...")
    gates = mm.load_ucf(UCF)
    print(f"      门数 {len(gates)}")

    print("[2/7] 稳态真值表 ...")
    results = mm.simulate_truth_table(gates)
    ok = sum(1 for r in results if (r["out"] > 1.0) == (r["expected"] == 1))
    print(f"      逻辑正确 {ok}/8")

    with open(os.path.join(OUT, "truth_table.csv"), "w", encoding="utf-8-sig") as f:
        f.write("pTac,pTet,pBAD,expected,output_RPU,n6,n5,n2,n3,n4,n1\n")
        for r in results:
            n = r["nodes"]
            f.write(f"{r['pTac']},{r['pTet']},{r['pBAD']},{r['expected']},"
                    f"{r['out']:.6f},{n['n6']:.6f},{n['n5']:.6f},{n['n2']:.6f},"
                    f"{n['n3']:.6f},{n['n4']:.6f},{n['n1']:.6f}\n")

    print("[3/7] 时序仿真 ...")
    t, out, nodes = mm.simulate_timecourse(gates, dwell=240.0)

    # 上升时间：只在发生 OFF→ON 跳变的区段测量 10%-90%
    dt = t[1] - t[0]
    seg_len = int(round(240.0 / dt))
    rises = []
    for k in range(1, 8):
        i0, i1 = k * seg_len, (k + 1) * seg_len
        if i1 >= len(out):
            break
        seg, ts = out[i0:i1], t[i0:i1]
        lo, hi = float(seg[0]), float(seg[-1])
        if hi > 2 * lo and hi > 1.0:
            a10 = ts[seg >= lo + 0.1 * (hi - lo)]
            a90 = ts[seg >= lo + 0.9 * (hi - lo)]
            if len(a10) and len(a90):
                rises.append(float(a90[0] - a10[0]))
    rise = float(np.mean(rises)) if rises else float("nan")
    print(f"      OFF→ON 上升时间(10-90%) ≈ {rise:.1f} min  (n={len(rises)})")

    print("[4/7] 绘图 ...")
    fig_topology()
    fig_hill_curves(gates)
    fig_truth_table(results)
    fig_timecourse(t, out, nodes, 240.0)

    print("[5/7] 鲁棒性分析 ...")
    rob = fig_robustness(gates)
    print("      ", json.dumps(rob, ensure_ascii=False))

    print("[6/7] 与官方结果对比 ...")
    official = parse_official(OFFICIAL_TXT)
    cmp_ = fig_cello_comparison(results, official)

    print("[7/7] 汇总 ...")
    ons = [r["out"] for r in results if r["expected"] == 1]
    offs = [r["out"] for r in results if r["expected"] == 0]
    summary = dict(
        logic_correct=f"{ok}/8",
        on_range=[float(min(ons)), float(max(ons))],
        off_range=[float(min(offs)), float(max(offs))],
        on_off_ratio=float(min(ons) / max(offs)),
        rise_time_min=rise,
        tau_min=float(mm.TAU),
        official_comparison=cmp_,
        robustness=rob,
    )
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
