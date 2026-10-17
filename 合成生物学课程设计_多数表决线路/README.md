# 三输入多数表决基因线路：自动化设计与仿真

本仓库是《合成生物学》课程设计的全部可运行文件。设计对象是一条三输入多数表决（majority voting）基因线路：三个输入中至少两个为"1"时输出为"1"，用于模拟细胞对多个胁迫信号的抗噪决策。

全部计算基于 Cello 官方门库 `Eco1C1G1T1.UCF.json` 的实测 Hill 参数，线路拓扑取自 Cello 对 `majority.v` 的官方布线结果（assignment A000）。

## 快速开始

```bash
# 依赖：Python 3.10+，numpy、scipy、matplotlib
pip install numpy scipy matplotlib -i https://mirrors.aliyun.com/pypi/simple/

# 一键复现全部结果（约 30 秒）
python sim/run_all.py
```

运行后 `sim/outputs/` 下会生成：

| 文件 | 内容 |
|---|---|
| `fig1_topology.png` | 线路拓扑图 |
| `fig2_hill_curves.png` | 6 个门的 Hill 响应曲线 |
| `fig3_truth_table.png` | 8 种输入组合的稳态输出 |
| `fig4_timecourse.png` | 输入切换下的时序响应 |
| `fig5_robustness.png` | 参数扰动 / 输入窗口 / n 敏感性 |
| `fig6_cello_comparison.png` | 与 Cello 官方结果的归一化对比 |
| `truth_table.csv` | 每个节点的稳态值 |
| `summary.json` | 关键指标汇总 |

## 目录结构

```
design/                         设计输入
  majority.v                    Verilog 需求描述
  Eco1C1G1T1.UCF.json           Cello 官方门库（20 个 NOR 门，含实测参数）
  majority_A000_logic_circuit.txt   官方布线结果（对照基准）
sim/
  majority_model.py             模型内核：门库解析、Hill 函数、ODE、时序
  run_all.py                    一键生成全部图表与数据
  outputs/                      运行产物
docs/
  课程设计书.md                  设计书源文件
  课程设计书.docx                设计书（Word 版）
```

## 核心结果

| 指标 | 数值 |
|---|---|
| 逻辑正确性 | 8/8 |
| ON/OFF 比值 | 23.6（ON 3.65–10.11 RPU，OFF 0.096–0.154 RPU） |
| 与 Cello 官方结果归一化相关系数 | 0.9996 |
| 上升时间（10%–90%） | 110.5 min |
| 参数 ±15% 扰动下正确率 | 100%（300 组） |
| 输入工作窗口 | ≥0.6 RPU |
| 输入噪声误判率 | 0.2%（CV=10%）/ 4.4%（CV=20%） |

## 模型假设

见 `docs/课程设计书.md` 第 5 章。简述：

1. 每个门稳态输出由 Hill 函数给出（Cello 标准抽象）；
2. 多输入 NOR 的输入取各输入之和；
3. NOT = 一个输入接恒定 0 的 NOR；
4. 输出级为双启动子 OR，荧光与两路转录之和成正比（由官方数据验证）；
5. 门浓度一阶弛豫，τ = 1/γ，γ = ln2/30 min。

## 在 Cello 网页版复现布线

1. 打开 https://www.cellocad.org/ ，注册/登录；
2. 新建设计，上传 `design/majority.v`；
3. 门库选择 `Eco1C1G1T1`；
4. 运行后导出布线结果，与 `design/majority_A000_logic_circuit.txt` 对照（不同版本门库的具体门分配可能不同，逻辑功能应一致）。

## 说明

- 门库参数为 Cello 官方发布的实测值，未做手工调整。
- 官方示例文件使用的门库版本与本仓库略有不同，绝对 RPU 值不可直接比较，故 6.2 节采用归一化对比。
- 本设计为计算工作，不包含湿实验数据；第 7 章给出可执行的实验验证方案。

## 参考

- Nielsen A A K, Der B S, Lee J, et al. Genetic circuit design automation. *Science*, 2016, 352(6281): aac7341.
- 李春 主编. 合成生物学. 化学工业出版社, 2019.
- Cello 代码与门库：https://github.com/CIDARLAB/Cello-v2
