# -*- coding: utf-8 -*-
"""
三输入多数表决基因线路 —— 动力学模型与仿真内核
==================================================

模型依据
--------
1. 门级参数：Cello 官方门库 design/Eco1C1G1T1.UCF.json（20 个 NOR 门，
   每个门带 Hill 响应函数 ymin+(ymax-ymin)/(1+(x/K)^n) 及实测参数）
2. 线路拓扑：Cello 官方对 majority.v 的自动布线结果
   design/majority_A000_logic_circuit.txt（assignment A000）
3. 时序常数：大肠杆菌倍增时间 30 min → 稀释/降解速率常数 γ = ln2/30 min⁻¹

模型假设（写进设计书，答辩可直接引用）
--------------------------------------
H1  每个门的稳态输出由 Hill 响应函数给出（Cello 的标准抽象）。
H2  多输入 NOR 门的输入信号取各输入之和 S = Σx_i（阻遏蛋白竞争同一操纵子，
    Cello 论文采用同一处理）。
H3  NOT 门 = 一个输入接恒定 0 的 NOR 门（De Morgan 等价，与 Cello 的 DNA 实现一致）。
H4  输出端为"双启动子 OR"（YFP 由两路启动子共同驱动），荧光与两路转录之和
    成正比；该线性关系由官方布线结果 OUTPUT_OR 的输入-输出表直接验证
    （见 docs 中"输出级校核"）。
H5  门浓度动力学为一阶弛豫：τ dy/dt = f(S) - y，τ = 1/γ = 43.3 min。
"""

import json
import os

import numpy as np
from scipy.integrate import solve_ivp

# ----------------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------------
DOUBLING_TIME_MIN = 30.0                 # 大肠杆菌倍增时间
GAMMA = np.log(2.0) / DOUBLING_TIME_MIN  # 稀释+降解速率常数, min^-1
TAU = 1.0 / GAMMA                        # 一阶时间常数, min
INPUT_ON = 1.0                           # 输入"1"对应的信号水平 (RPU)
INPUT_OFF = 0.0                          # 输入"0"对应的信号水平 (RPU)

# 官方布线结果 A000 中用到的 6 个门 + 输出级
GATE_ROLES = {
    "A1_AmtR":   dict(logic="NOT", inputs=["pTet", "CONST0"], out="n6"),
    "S2_SrpR":   dict(logic="NOT", inputs=["pBAD", "CONST0"], out="n5"),
    "H1_HlyIIR": dict(logic="NOT", inputs=["pTac", "CONST0"], out="n2"),
    "B3_BM3R1":  dict(logic="NOR", inputs=["pTet", "pBAD"],    out="n3"),
    "E1_BetI":   dict(logic="NOR", inputs=["n6", "n5"],        out="n4"),
    "P3_PhlF":   dict(logic="NOR", inputs=["n2", "n3"],        out="n1"),
}

# 节点顺序（求 ODE 用）
NODES = ["n6", "n5", "n2", "n3", "n4", "n1"]
INPUTS = ["pTet", "pBAD", "pTac"]   # 对应真值表位序 [pTac, pTet, pBAD] 的索引重排见 truth_table()


# ----------------------------------------------------------------------------
# 门库解析
# ----------------------------------------------------------------------------
def load_ucf(path):
    """读取 Cello UCF 门库，返回 {gate_name: {type, params, thresholds}}。"""
    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    gates = {}
    for r in records:
        if r.get("collection") == "gates":
            gates[r["gate_name"]] = {
                "type": r["gate_type"],
                "regulator": r["regulator"],
                "params": None,
                "thresholds": None,
            }
    for r in records:
        if r.get("collection") == "response_functions":
            name = r["gate_name"]
            if name in gates:
                gates[name]["params"] = {p["name"]: float(p["value"]) for p in r["parameters"]}
                gates[name]["thresholds"] = {
                    v["name"]: (float(v["off_threshold"]), float(v["on_threshold"]))
                    for v in r["variables"]
                }
    return gates


def hill_nor(S, ymax, ymin, K, n):
    """阻遏型 (NOR / NOT) 响应函数。S 为输入信号之和。"""
    S = np.asarray(S, dtype=float)
    return ymin + (ymax - ymin) / (1.0 + (np.maximum(S, 0.0) / K) ** n)


# ----------------------------------------------------------------------------
# 网络求值
# ----------------------------------------------------------------------------
def node_values(state, gates):
    """
    给定输入信号 {pTet, pBAD, pTac}，按拓扑顺序计算所有节点稳态值。
    state: dict, 输入名 -> 信号水平
    """
    v = dict(state)
    v["CONST0"] = 0.0
    # 拓扑顺序：n6,n5,n2（第一层）→ n3（第二层）→ n4,n1（第三层）
    order = ["n6", "n5", "n2", "n3", "n4", "n1"]
    for node in order:
        # 找到产生该节点的门
        for gname, role in GATE_ROLES.items():
            if role["out"] == node:
                p = gates[gname]["params"]
                S = sum(v[i] for i in role["inputs"])
                v[node] = float(hill_nor(S, p["ymax"], p["ymin"], p["K"], p["n"]))
                break
    # 输出级：双启动子 OR，两路转录之和（H4）
    v["out"] = v["n4"] + v["n1"]
    return v


def rhs_factory(gates, state_fn):
    """构造 ODE 右端。state_fn(t) -> 输入信号 dict。"""
    def rhs(t, y):
        v = dict(zip(NODES, y))
        v.update(state_fn(t))
        v["CONST0"] = 0.0
        dydt = []
        for node in NODES:
            for gname, role in GATE_ROLES.items():
                if role["out"] == node:
                    p = gates[gname]["params"]
                    S = sum(v[i] for i in role["inputs"])
                    target = float(hill_nor(S, p["ymax"], p["ymin"], p["K"], p["n"]))
                    dydt.append((target - v[node]) / TAU)
                    break
        return dydt
    return rhs


def steady_state(state, gates, t_end=3000.0):
    """积分到稳态，返回完整节点值。"""
    y0 = [0.0] * len(NODES)
    sol = solve_ivp(rhs_factory(gates, lambda t: state), (0.0, t_end), y0,
                    method="LSODA", rtol=1e-9, atol=1e-12, max_step=10.0)
    v = dict(zip(NODES, sol.y[:, -1]))
    v["out"] = v["n4"] + v["n1"]
    return v


# ----------------------------------------------------------------------------
# 真值表
# ----------------------------------------------------------------------------
def majority_truth_table():
    """位序 [pTac, pTet, pBAD]，与官方布线结果一致。"""
    rows = []
    for bits in range(8):
        c = (bits >> 2) & 1   # pTac
        a = (bits >> 1) & 1   # pTet
        b = bits & 1          # pBAD
        rows.append({"pTac": c, "pTet": a, "pBAD": b,
                     "expected": 1 if (a + b + c) >= 2 else 0})
    return rows


def simulate_truth_table(gates, mode="steady"):
    """对 8 种输入组合求输出，返回结果列表。"""
    results = []
    for row in majority_truth_table():
        state = {
            "pTet": INPUT_ON if row["pTet"] else INPUT_OFF,
            "pBAD": INPUT_ON if row["pBAD"] else INPUT_OFF,
            "pTac": INPUT_ON if row["pTac"] else INPUT_OFF,
        }
        if mode == "steady":
            v = steady_state(state, gates)
            out = v["out"]
        else:  # 解析（无限快，用于对照）
            v = node_values(state, gates)
            out = v["out"]
        results.append({**row, "out": float(out), "nodes": v})
    return results


# ----------------------------------------------------------------------------
# 时间序列
# ----------------------------------------------------------------------------
def simulate_timecourse(gates, sequence=None, dwell=90.0, dt=0.5):
    """
    sequence: [(pTac,pTet,pBAD), ...] 依次施加，每段 dwell 分钟。
    返回 t, out, nodes 数组。
    """
    if sequence is None:
        # Gray 码遍历，避免多位同时翻转
        sequence = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0),
                    (1, 1, 0), (1, 1, 1), (1, 0, 1), (1, 0, 0)]

    def state_fn(t):
        idx = min(int(t // dwell), len(sequence) - 1)
        c, a, b = sequence[idx]
        return {"pTet": INPUT_ON if a else INPUT_OFF,
                "pBAD": INPUT_ON if b else INPUT_OFF,
                "pTac": INPUT_ON if c else INPUT_OFF}

    T = dwell * len(sequence)
    sol = solve_ivp(rhs_factory(gates, state_fn), (0.0, T), [0.0] * len(NODES),
                    method="LSODA", rtol=1e-8, atol=1e-11, max_step=5.0,
                    t_eval=np.arange(0.0, T + dt, dt))
    out = sol.y[NODES.index("n4")] + sol.y[NODES.index("n1")]
    return sol.t, out, {n: sol.y[i] for i, n in enumerate(NODES)}
