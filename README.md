# FactorCalculator

因子计算工具，基于 RBT 量化交易框架的 DMU（决策单元）和 PEU（盈亏估算单元）进行因子计算。

## 功能特性

- **字符串解析**：解析 unit 规格字符串，如 `KlineDMU(45)` 或 `BiquotePEU(watching_time=60)`
- **动态类加载**：根据后缀自动判断模块（DMU → `rbt.dmu`，PEU → `rbt.peu`）
- **因子计算**：集成 RBT 的 Strategy 进行因子计算
- **历史因子注入**：从数据库加载已有因子并注入到 Strategy

## 安装

```bash
cd factor_calculator
pip install -e .
```

或先安装 RBT：

```bash
cd /Users/boat/dev/rbt
pip install -e .
cd ~/dev/factor_calculator
pip install -e .
```

## 快速开始

```python
from factor_calculator import create_unit, FactorCalculator

# 解析并创建 unit
unit = create_unit("KlineDMU(interval=5)")
print(f"Created: {unit.name}")

# 使用计算器
calc = FactorCalculator(
    db_directory="/path/to/results",
    md_directory="/path/to/market/data",
)

result = calc.calculate(
    units=["KlineDMU(5)", "BiquotePEU(watching_time=60)"],
    load_factors=["KlineDMU__open"],
    contract="IF2403",
    trade_date="2024-03-15",
)
```

## 命令行用法

```bash
# 列出可用的 units
factor-calculator list

# 计算因子
factor-calculator calculate \
    --db /path/to/results \
    --units "KlineDMU(5),BiquotePEU(60)" \
    --contract IF2403 \
    --date 2024-03-15

# 查看已存在的因子
factor-calculator factors \
    --db /path/to/results \
    --contract IF2403 \
    --date 2024-03-15
```

## API

### core.py

#### FactorCalculator

因子计算主类。

```python
class FactorCalculator:
    def __init__(self, db_directory: str, md_directory: str = None):
        """初始化计算器。"""
        
    def calculate(self, units: List[str], load_factors: List[str],
                  contract: str, trade_date: str, frequency: str = "tick") -> pd.DataFrame:
        """执行因子计算。"""
        
    def get_existing_factors(self, contract: str, trade_date: str) -> List[str]:
        """获取已存在的因子列表。"""
        
    def save_factors(self, factors: pd.DataFrame, contract: str, trade_date: str):
        """保存计算后的因子。"""
```

### factory.py

```python
# 解析 unit 规格字符串
parse_unit_spec("KlineDMU(45)")  # -> ("KlineDMU", "45")

# 创建 unit 实例
create_unit("KlineDMU(interval=5)")  # -> KlineDMU 实例
create_units(["KlineDMU(5)", "BiquotePEU(60)"])  # -> [DMU, PEU]

# 列出可用的类
get_available_classes()  # -> ["BiquotePEU", "KlineDMU", ...]
get_available_classes("DMU")  # -> 仅 DMU 类
```

## 项目结构

```
factor_calculator/
├── factor_calculator/
│   ├── __init__.py       # 包导出
│   ├── core.py           # FactorCalculator 主类
│   ├── factory.py        # Unit 解析和创建
│   └── cli.py            # 命令行接口
├── tests/
│   ├── __init__.py
│   ├── test_factory.py   # Factory 测试
│   └── test_core.py      # Core 模块测试
├── examples/
│   └── example_usage.py  # 使用示例
└── README.md
```

## 依赖

- Python 3.8+
- RBT 包（完整功能需要）
- pandas
- pytest（运行测试需要）

## 运行测试

```bash
cd factor_calculator
pytest tests/
```

## License

MIT
