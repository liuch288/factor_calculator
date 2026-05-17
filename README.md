# FactorCalculator

因子计算工具，基于 RBT 量化交易框架的 DMU（决策单元）和 PEU（盈亏估算单元）进行因子计算。

## 功能特性

- **字符串解析**：解析 unit 规格字符串，如 `KlineDMU(45)` 或 `BiquotePEU(watching_time=60)`
- **动态类加载**：根据后缀自动判断模块（DMU → `rbt.dmu`，PEU → `rbt.peu`）
- **因子计算**：集成 RBT 的 Strategy 进行因子计算
- **历史因子注入**：从数据库加载已有因子并注入到 Strategy

## 安装

```bash
pip install -e .
```

或先安装 RBT：

```bash
cd /path/to/rbt
pip install -e .
cd /path/to/factor_calculator
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
    root_path="/path/to/results",
    md_directory="/path/to/market/data",
)

# 单日计算
result = calc.calculate(
    units=["KlineDMU(5)", "BiquotePEU(watching_time=60)"],
    contract="IF2403",
    trade_date="2024-03-15",
)

# 多日计算
result = calc.calculate(
    units=["KlineDMU(5)"],
    contract="IF2403",
    start_date="2024-03-01",
    end_date="2024-03-31",
)
```

## 命令行用法

### 列出可用的 units

```bash
# 列出所有可用的 DMU 和 PEU 类
fcc list

# 仅列出 DMU 类
fcc list --dmu

# 仅列出 PEU 类
fcc list --peu
```

### 计算因子

```bash
# 单日计算
fcc calculate \
    --db /path/to/results \
    --md /path/to/market/data \
    --units "KlineDMU(5),BiquotePEU(60)" \
    --contract IF2403 \
    --date 2024-03-15

# 多日计算
fcc calculate \
    --db /path/to/results \
    --md /path/to/market/data \
    --units "KlineDMU(5)" \
    --contract IF2403 \
    --start-date 2024-03-01 \
    --end-date 2024-03-31

# 重新计算已存在的因子
fcc calculate --recalculate ...

# 遇到错误立即停止
fcc calculate --fail-fast ...

# 禁用进度条
fcc calculate --no-progress ...

# 保存结果到文件
fcc calculate -o result.pkl ...
```

### 查看已存在的因子

```bash
fcc factors \
    --db /path/to/results \
    --contract IF2403 \
    --date 2024-03-15
```

### 进度管理

```bash
# 列出计算任务
fcc progress list
fcc progress list --contract IF2403
fcc progress list --status success
fcc progress list --limit 10

# 查看任务详情
fcc progress show <task_id>

# 查看任务日志
fcc progress logs <task_id>
```

#### 进度任务状态

- `running` - 执行中
- `success` - 成功完成
- `failed` - 失败
- `cancelled` - 已取消

## API

### core.py - FactorCalculator

因子计算主类。

```python
class FactorCalculator:
    def __init__(self, root_path: str = None, md_directory: str = None,
                 frequency: str = "tick", db_directory: str = None):
        """初始化计算器。
        
        Args:
            root_path: FactorStore 根路径（原 db_directory）
            md_directory: 行情数据目录
            frequency: 数据频率，默认 "tick"
            db_directory: (已弃用) 请使用 root_path
        """
        
    def calculate(self, units: List[str], contract: str,
                  trade_date: str = None, frequency: str = "tick",
                  recalculate: bool = False, bgm: Dict = None,
                  start_date: str = None, end_date: str = None,
                  fail_fast: bool = False, show_progress: bool = True) -> pd.DataFrame:
        """执行因子计算。
        
        Args:
            units: unit 规格字符串列表
            contract: 合约代码或主力合约别名（如 "TL01"）
            trade_date: 交易日期 (单日模式，YYYY-MM-DD)
            frequency: 数据频率，默认 "tick"
            recalculate: 是否重新计算已存在的因子
            bgm: 背景参数字典，注入到每个 tick 的 unit_results
            start_date: 开始日期 (多日模式，YYYY-MM-DD)
            end_date: 结束日期 (多日模式，YYYY-MM-DD)
            fail_fast: 遇到错误是否立即停止
            show_progress: 是否显示进度条
        """
        
    def get_existing_factors(self, contract: str, trade_date: str) -> List[str]:
        """获取已存在的因子列表。"""
        
    def save_factors(self, factors: pd.DataFrame, contract: str, trade_date: str):
        """保存计算后的因子。"""
        
    @property
    def last_task_id(self) -> str:
        """获取最后一次计算的进度任务 ID。"""
```

### factory.py - Unit 工厂

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

### dominant.py - 主力合约工具

```python
from factor_calculator.dominant import parse_alias, get_dominant_contract

# 解析合约别名
parse_alias("IF2403")   # -> ("IF", "2403")
parse_alias("T01")       # -> ("T", "01")

# 获取主力合约
get_dominant_contract("IF", "2024-03-15")  # -> "IF2403"
```

### progress - 进度追踪

```python
from factor_calculator.progress import ProgressTracker

# 创建进度追踪器（默认存储路径：~/.fc/progress）
tracker = ProgressTracker(storage_path=".progress")

# 启动任务
task_id = tracker.start_task(
    units='["KlineDMU(5)"]',  # JSON 字符串
    contract="IF2403",
    date_range=("2024-03-01", "2024-03-31"),
    frequency="tick",
    total_days=31
)

# 更新进度
tracker.update_progress(
    task_id=task_id,
    current_day=5,
    total_days=31,
    day_progress=50,  # 当前天的进度 (0-100)
    message="正在处理..."
)

# 完成任务（成功）
tracker.complete_task(
    task_id=task_id,
    status="success",
    result_summary={"total_factors": 10}
)

# 标记失败
tracker.complete_task(
    task_id=task_id,
    status="failed",
    result_summary={"error": "Connection timeout"}
)

# 查询任务
tasks = tracker.list_tasks(contract="IF2403", status="running", limit=10)
task = tracker.get_task(task_id)

# 添加日志
tracker.log(task_id, "INFO", "开始计算...")

# 获取日志
logs = tracker.get_logs(task_id)
```

## 项目结构

```
factor_calculator/
├── factor_calculator/
│   ├── __init__.py       # 包导出
│   ├── cli.py            # 命令行接口
│   ├── core.py           # FactorCalculator 主类
│   ├── dominant.py       # 主力合约工具
│   ├── factory.py        # Unit 解析和创建
│   └── progress/        # 进度追踪模块
│       ├── __init__.py
│       ├── models.py     # 数据模型
│       └── tracker.py    # 进度追踪器
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

## 变更日志

### v0.2.1

- 新增进度追踪功能 (`progress` 模块)
  - 支持追踪多日计算任务的进度
  - 提供 `fcc progress` 命令查看任务状态、详情和日志
- 新增多日计算模式 (`--start-date` 和 `--end-date`)
- 新增 `--fail-fast` 选项，遇到错误立即停止
- 新增 `--no-progress` 选项，禁用进度条
- 新增 `--recalculate` 选项，重新计算已存在的因子
- 新增 `dominant.py` 主力合约工具

### v0.1.1

- 修复主力合约别名解析不支持单字母品种的问题（如 `T01`）
  - `parse_alias` 最小长度从 4 放宽到 3
  - 品种正则从 `{2,4}` 改为 `{1,4}`，支持 T、V 等单字母品种
