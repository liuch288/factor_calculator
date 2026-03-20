"""
FactorCalculator 使用示例
"""
import sys, os
# 确保从本地包导入（开发时）
_local_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _local_path not in sys.path:
    sys.path.insert(0, _local_path)

from factor_calculator import parse_unit_spec, get_available_classes, create_unit, create_units
from factor_calculator import SimpleFactorCalculator, FactorCalculator
import pandas as pd
import datetime


def section1_parse_unit_spec():
    """1. 解析单元规格（Unit Specifications）"""
    print("=" * 50)
    print("1. 解析单元规格")
    print("=" * 50)
    
    specs = [
        "KlineDMU(45)",
        "KlineDMU(interval=5)",
        "BiquotePEU(watching_time=60)",
        "PositionPnlDMU",
    ]
    
    for spec in specs:
        class_name, params = parse_unit_spec(spec)
        print(f"{spec!r}")
        print(f"  -> class: {class_name}, params: {params!r}")


def section2_list_classes():
    """2. 列出可用的 DMU / PEU 类"""
    print("\n" + "=" * 50)
    print("2. 列出可用类")
    print("=" * 50)
    
    print("所有可用单元:")
    for cls in get_available_classes():
        print(f"  - {cls}")
    
    print("\nDMU 类:")
    for cls in get_available_classes("DMU"):
        print(f"  - {cls}")
    
    print("\nPEU 类:")
    for cls in get_available_classes("PEU"):
        print(f"  - {cls}")


def section3_create_units():
    """3. 创建单元实例"""
    print("\n" + "=" * 50)
    print("3. 创建单元实例")
    print("=" * 50)
    
    # 创建单个单元
    unit = create_unit("KlineDMU(interval=5)")
    print(f"Created: {unit}")
    print(f"  Name: {unit.name}")
    print(f"  Interval: {unit.interval}")
    
    # 批量创建
    print()
    units = create_units(["PositionPnlDMU", "FixedHoldingPEU(watching_mds=100)", "TrendDMU"])
    print(f"创建了 {len(units)} 个单元:")
    for u in units:
        print(f"  - {u.name}")


def section4_simple_calculator():
    """4. SimpleFactorCalculator"""
    print("\n" + "=" * 50)
    print("4. SimpleFactorCalculator")
    print("=" * 50)
    
    # 构造示例行情数据
    md_data = pd.DataFrame({
        "name": pd.date_range("2024-03-15 09:30", periods=10, freq="1min"),
        "last_px": [100.0 + i * 0.1 for i in range(10)],
        "tot_sz": [100 * (i + 1) for i in range(10)],
        "oi": [1000 + i * 10 for i in range(10)],
    })
    md_data.set_index("name", inplace=True)
    
    print("示例行情数据:")
    print(md_data)
    
    print("\n注意: SimpleFactorCalculator 需要 root_path 和实际数据")
    print("用法:")
    print("  calc = SimpleFactorCalculator(root_path='/path/to/db', frequency='tick')")
    print("  result = calc.calculate_dmu(...)")


def section5_full_calculator():
    """5. FactorCalculator（完整集成）"""
    print("\n" + "=" * 50)
    print("5. FactorCalculator（完整版）")
    print("=" * 50)
    
    calc = FactorCalculator()
    
    result = calc.calculate(
        units=[
            "KlineDMU(interval=5)",
            "MdDMU('TL')"
            # "BiquotePEU(1)",
            # "FixedHoldingPEU(10)",
        ],
        load_factors=["KlineDMU__open", "KlineDMU__close"],
        contract="TL2603",
        trade_date=datetime.date(2026, 1, 5),
        frequency="tick",
    )
    
    print(f"结果形状: {result.shape}")
    print(result.head())


if __name__ == "__main__":
    section1_parse_unit_spec()
    section2_list_classes()
    section3_create_units()
#    section4_simple_calculator()
    section5_full_calculator()  # 需要数据文件
