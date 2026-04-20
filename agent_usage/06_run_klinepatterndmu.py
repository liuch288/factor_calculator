"""
用户需求：
    "运行一下 KlinePatternDMU"

Agent 操作：
    先检查 KlinePatternDMU 签名：
        KlinePatternDMU(interval=1, window_size=3, reset_on_eod=True)
        - interval: K 线时间间隔（分钟），默认 1
        - window_size: 追踪的 K 线数量，默认 3
        - reset_on_eod: 是否日终重置，默认 True

    用户回复：
        "3根1分钟K线，日中重置"

    Agent 解析用户意图：
        - "1分钟" → interval=1
        - "3根" → window_size=3
        - "日中重置" → reset_on_eod=True

    Agent 向用户确认：
        "确认一下：interval=1, window_size=3, reset_on_eod=True，对吗？"

    用户确认后运行。

前置依赖：
    KlinePatternDMU 依赖 KlineDMU（同 interval），需要先运行对应的 KlineDMU。
    本例中默认 interval=1，所以需要 KlineDMU(1) 已在 ResultDB 中。

结果：
    18/32 天成功，432,615 行，耗时 22s。
    新增列：KlinePatternDMU_v0_1min_3_r__pattern（1 分钟 K 线、3 根窗口的形态识别）
"""

import logging

from factor_calculator import FactorCalculator

logging.basicConfig(level=logging.INFO)


def run_klinepatterndmu():
    calc = FactorCalculator()

    result = calc.calculate(
        units=["KlinePatternDMU"],
        contract="TL2603",
        start_date="2026-01-05",
        end_date="2026-02-05",
        frequency="tick",
    )

    print(f"KlinePatternDMU done. Shape: {result.shape}")
    if not result.empty:
        print("Columns:", list(result.columns))
        print(result.head())


if __name__ == "__main__":
    run_klinepatterndmu()
