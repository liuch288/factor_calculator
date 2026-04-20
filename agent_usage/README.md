# Agent Usage 示例

本目录记录了 AI Agent 与用户交互过程中实际执行的因子计算命令，供其他 Agent 参考复用。

## 文件列表与执行顺序

| 文件 | 说明 | 依赖 |
|------|------|------|
| `01_inspect_peu_params.py` | 动态查看任意 DMU/PEU 类的构造函数签名 | 无 |
| `02_run_mddmu.py` | 计算 MdDMU（行情衍生指标，最简单的因子计算） | 无 |
| `03_cli_usage.sh` | CLI 命令行调用示例（可在任意目录运行） | 需 `pip install .` 安装 |
| `04_run_biquotepeu.py` | 自动计算前置依赖 MoSplitDMU，再计算 BiquotePEU | 无（脚本内自动处理依赖） |
| `05_run_klinedmu.py` | 计算 KlineDMU 1min 和 5min K 线 | 无 |
| `06_run_klinepatterndmu.py` | 计算 KlinePatternDMU K 线形态识别 | 需先运行 05（KlineDMU(1)） |

## 关键信息

- **合约**: TL2603
- **日期范围**: 2026-01-05 ~ 2026-02-05（实际有 tick 数据的交易日）
- **频率**: tick

## 依赖关系图

```
MoSplitDMU ──→ BiquotePEU    (02 脚本内自动处理)
KlineDMU(1) ──→ KlinePatternDMU
KlineDMU(5)     (独立)
MdDMU           (独立)
```

## 通用模式

### Python API

```python
from factor_calculator import FactorCalculator

calc = FactorCalculator()

result = calc.calculate(
    units=["UnitName(param1, param2=value)"],
    contract="TL2603",
    start_date="2026-01-05",
    end_date="2026-02-05",
    frequency="tick",
)
```

### CLI（任意目录可用）

```bash
# 需先安装：pip install .（在项目目录下执行一次）
factor-calculator calculate \
    --units "UnitName(param1, param2=value)" \
    --contract TL2603 \
    --start-date 2026-01-05 \
    --end-date 2026-02-05
```
