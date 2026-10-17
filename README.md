# 三输入多数表决基因线路 · 合成生物学课程设计

用 Cello 自动设计平台完成一条**三输入多数表决**（3-input majority voting）基因线路的设计，并用官方门库的实测参数独立建立 Hill 动力学模型，完成稳态、时序与鲁棒性验证。

三个输入中至少两个为真时输出为真。生物学语义：细胞对多路胁迫信号做"投票"，单路波动不误触发。

## 目录

```
合成生物学课程设计_多数表决线路/     设计文档 + 可复现代码
├── design/                         官方输入
│   ├── majority.v                  Verilog 需求描述
│   ├── Eco1C1G1T1.UCF.json         Cello 官方门库（20 个 NOR 门实测参数）
│   └── majority_A000_logic_circuit.txt   官方布线结果（对照基准）
├── sim/
│   ├── majority_model.py           门库解析 · Hill 函数 · ODE
│   ├── run_all.py                  一键生成全部图表与数据
│   └── outputs/                    6 张图 + truth_table.csv + summary.json
├── docs/
│   ├── 合成生物学课程设计书_三输入多数表决线路.docx    设计书（17 页）
│   └── 课程设计书.md               设计书源文件
├── tools/md2docx.py                Markdown → Word 转换器
└── README.md                       复现说明

三输入多数表决基因线路汇报/          汇报 PPT（13 页，学术风）
├── 三输入多数表决基因线路汇报.pptx
├── slides/                         逐页源文件（01–13）
├── assets/                         图表素材
└── STORY.md                        叙事脚本
```

## 复现

```bash
pip install numpy scipy matplotlib
cd 合成生物学课程设计_多数表决线路
python sim/run_all.py
```

约 30 秒后 `sim/outputs/` 生成全部结果。门参数直接读自官方 UCF 文件，无手工填值。

## 核心结果

| 指标 | 数值 |
|---|---|
| 逻辑正确性 | 8/8 |
| ON/OFF 比值 | 23.6×（ON 3.65–10.11 RPU，OFF 0.096–0.154 RPU） |
| 与 Cello 官方结果归一化相关系数 | 0.9996 |
| 上升时间（10%–90%） | 110.5 min |
| 参数 ±15% 扰动 | 300 组 100% 逻辑正确（最差 ON/OFF 7.3） |
| 输入工作窗口 | ≥0.6 RPU |
| 输入噪声误判率 | 0.2%（CV 10%）→ 4.4%（CV 20%） |

## 模型假设

1. 门稳态输出由 Hill 函数给出（Cello 标准抽象）；
2. 多输入 NOR 的输入取各信号之和；
3. NOT = 一个输入接恒定 0 的 NOR；
4. 输出级为双启动子 OR，荧光与两路转录之和成正比（官方数据斜率 ≈1.02）；
5. 门浓度一阶弛豫，τ = 1/γ，γ = ln2/30 min。

## 说明

- 门库版本与官方示例不同，绝对 RPU 不可直接比较，故采用归一化对比。
- 本工作为计算设计，不含湿实验数据；设计书第 7 章给出可执行的实验验证方案。

## 参考

- Nielsen A A K, Der B S, Lee J, et al. Genetic circuit design automation. *Science*, 2016, 352(6281): aac7341.
- 李春 主编. 合成生物学. 化学工业出版社, 2019.
- Cello 代码与门库：https://github.com/CIDARLAB/Cello-v2
