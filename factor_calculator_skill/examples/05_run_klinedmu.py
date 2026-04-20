"""
用户需求：
    "来个 KlineDMU，1min 和 5min 的"

Agent 操作：
    分别运行 KlineDMU(1) 和 KlineDMU(5)，对 TL2603 合约 2026-01-05 ~ 2026-02-05。

结果：
    KlineDMU(1) - 1 分钟 K 线：18/32 天成功，432,615 行，耗时 14.2s
    KlineDMU(5) - 5 分钟 K 线：18/32 天成功，432,615 行，耗时 14.2s

    输出列（以 1min 为例，5min 前缀为 KlineDMU_v0_5min__）：
        KlineDMU_v0_1min__open       - 开盘价
        KlineDMU_v0_1min__high       - 最高价
        KlineDMU_v0_1min__low        - 最低价
        KlineDMU_v0_1min__close      - 收盘价
        KlineDMU_v0_1min__volume     - 成交量
        KlineDMU_v0_1min__oi_diff    - 持仓量变化
        KlineDMU_v0_1min__end_time   - K 线结束时间
        KlineDMU_v0_1min__completed  - K 线是否完成
        trade_date                   - 交易日期
"""

import logging

from factor_calculator import FactorCalculator

logging.basicConfig(level=logging.INFO)


def run_klinedmu():
    calc = FactorCalculator()

    # 1 分钟 K 线
    print("=== KlineDMU(1) ===")
    r1 = calc.calculate(
        units=["KlineDMU(1)"],
        contract="TL2603",
        start_date="2026-01-05",
        end_date="2026-02-05",
        frequency="tick",
    )
    print(f"KlineDMU(1) done. Shape: {r1.shape}")
    if not r1.empty:
        print("Columns:", list(r1.columns))
        print(r1.head())

    print()

    # 5 分钟 K 线
    print("=== KlineDMU(5) ===")
    r2 = calc.calculate(
        units=["KlineDMU(5)"],
        contract="TL2603",
        start_date="2026-01-05",
        end_date="2026-02-05",
        frequency="tick",
    )
    print(f"KlineDMU(5) done. Shape: {r2.shape}")
    if not r2.empty:
        print("Columns:", list(r2.columns))
        print(r2.head())


if __name__ == "__main__":
    run_klinedmu()
