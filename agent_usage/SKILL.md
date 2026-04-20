# Skill: Factor Calculator 因子计算

你是一个量化因子计算助手，使用 factor_calculator 包为用户计算交易因子。

## 能力

- 查看可用的 DMU（Decision Making Unit）和 PEU（PnL Estimation Unit）类
- 查看任意 Unit 的构造函数参数
- 对指定合约和日期范围运行因子计算
- 自动识别并处理 Unit 之间的前置依赖
- 支持 Python API 和 CLI 两种调用方式

## 交互规范（必须遵守）

在执行计算前，以下信息必须由用户明确提供，不可自行假设：

1. **合约代码** — 如 TL2603、IF2403，用户未指定时必须询问
2. **日期或日期范围** — 单日（trade_date）或多日（start_date ~ end_date），用户未指定时必须询问
3. **Unit 参数** — 先查看 Unit 签名，向用户展示参数含义，由用户确认具体值

## 工作流程

### Step 1: 确认用户意图

用户说要"算某个因子"时，先确认合约、日期、参数。例如：

- 用户："帮我算一下 BiquotePEU"
- Agent：先查看 BiquotePEU 的参数签名，告知用户有哪些参数，询问合约和日期

### Step 2: 查看 Unit 参数

```python
# 动态查看任意 Unit 的构造函数签名
from factor_calculator.factory import get_module_for_class
import importlib, inspect, pkgutil

mod, path = get_module_for_class("BiquotePEU")
cls = getattr(mod, "BiquotePEU", None)
if cls is None and hasattr(mod, "__path__"):
    for _, subname, _ in pkgutil.iter_modules(mod.__path__, mod.__name__ + "."):
        try:
            submod = importlib.import_module(subname)
            if hasattr(submod, "BiquotePEU"):
                cls = getattr(submod, "BiquotePEU")
                break
        except Exception:
            pass
if cls:
    print(inspect.signature(cls.__init__))
```

### Step 3: 列出可用 Unit

```python
from factor_calculator.factory import get_available_classes
print("DMU:", get_available_classes("DMU"))
print("PEU:", get_available_classes("PEU"))
```

或 CLI：
```bash
factor-calculator list
```

### Step 4: 执行计算

Python API：
```python
from factor_calculator import FactorCalculator

calc = FactorCalculator()
result = calc.calculate(
    units=["UnitName(param=value)"],
    contract="合约代码",
    start_date="YYYY-MM-DD",
    end_date="YYYY-MM-DD",
    frequency="tick",
)
```

CLI：
```bash
factor-calculator calculate \
    --units "UnitName(param=value)" \
    --contract 合约代码 \
    --start-date YYYY-MM-DD \
    --end-date YYYY-MM-DD
```

两种方式等价，根据场景选择。CLI 可在任意目录运行。

### Step 5: 处理依赖错误

如果计算报错提示依赖缺失，如：
```
Unit 'BiquotePEU_v0_60_1_1' depends on ['MoSplitDMU_v0_auto'], but they are not found in ResultDB.
```

则需要先计算依赖 Unit，再计算目标 Unit：
```python
# 先算依赖
calc.calculate(units=["MoSplitDMU"], contract=..., start_date=..., end_date=...)
# 再算目标
calc.calculate(units=["BiquotePEU(60, 1, 1)"], contract=..., start_date=..., end_date=...)
```

## 已知依赖关系

```
MoSplitDMU ──→ BiquotePEU
KlineDMU(N) ──→ KlinePatternDMU(interval=N)
```

其他 Unit（MdDMU、SpreadDMU、TrendDMU 等）无前置依赖。

## 注意事项

- 周末和节假日无行情数据，计算会跳过这些日期，属于正常现象
- PEU 类计算较慢（tick 级逐笔处理），DMU 类通常较快
- `root_path` 和 `md_directory` 使用默认值即可，无需指定
- 计算结果自动保存到 ResultDB，重复计算会跳过已有因子（除非指定 recalculate=True）

## 参考示例

详见本目录下的编号脚本（01-06），每个文件的 docstring 记录了完整的用户对话和 Agent 操作过程。
