"""
用户需求：
    计算 TL2603 合约 2026-01-05 ~ 2026-02-05 的 BiquotePEU(order_maintaining_time=60, lb=1, la=1)。

Agent 操作：
    1. 首次直接运行 BiquotePEU，报错：
       Unit 'BiquotePEU_v0_60_1_1' depends on ['MoSplitDMU_v0_auto'], but they are not found
       in ResultDB. Please run the corresponding units first and save results.

    2. Agent 识别到前置依赖 MoSplitDMU，先单独运行 MoSplitDMU 将结果写入 ResultDB。
       MoSplitDMU 结果：18/32 天成功，Shape (94523, 2)，耗时约 167s。

    3. MoSplitDMU 完成后，再运行 BiquotePEU，此时依赖已满足，计算成功。
       BiquotePEU 每天约 2-3 分钟（tick 级别 + 60s watching_time）。

注意：
    - TL2603 的 tick 数据实际只覆盖 2026-01-05 到 2026-02-05（共 18 个交易日）
    - 1/27 ~ 2/3 为春节假期，无数据
    - BiquotePEU 参数说明：
        order_maintaining_time=60  挂单维持 60 秒
        lb=1                       买方在一档挂单
        la=1                       卖方在一档挂单
"""

import logging

from factor_calculator import FactorCalculator

logging.basicConfig(level=logging.INFO)


def run_biquotepeu_with_deps():
    calc = FactorCalculator()

    # Step 1: 计算前置依赖 MoSplitDMU
    print("=== Step 1: MoSplitDMU (前置依赖) ===")
    r1 = calc.calculate(
        units=["MoSplitDMU"],
        contract="TL2603",
        start_date="2026-01-05",
        end_date="2026-02-05",
        frequency="tick",
    )
    print(f"MoSplitDMU done. Shape: {r1.shape}")

    # Step 2: 计算 BiquotePEU
    print("\n=== Step 2: BiquotePEU ===")
    r2 = calc.calculate(
        units=["BiquotePEU(order_maintaining_time=60, lb=1, la=1)"],
        contract="TL2603",
        start_date="2026-01-05",
        end_date="2026-02-05",
        frequency="tick",
    )
    print(f"BiquotePEU done. Shape: {r2.shape}")
    if not r2.empty:
        print("Columns:", list(r2.columns))
        print(r2.head())


if __name__ == "__main__":
    run_biquotepeu_with_deps()
