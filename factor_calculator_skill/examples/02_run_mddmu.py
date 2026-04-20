"""
用户需求：
    "帮我再算一个 MdDMU 吧"

Agent 操作：
    检查 MdDMU 构造函数签名为 (self)，无需额外参数。
    Agent 告知用户："MdDMU 没有参数，直接跑。"
    对 TL2603 合约 2026-01-05 ~ 2026-02-05 运行 MdDMU。

结果：
    18/32 天成功，耗时 17.3s。
    Shape: (432615, 11)
    输出列：
        MdDMU_v0__bid        - 买一价
        MdDMU_v0__ask        - 卖一价
        MdDMU_v0__mid        - 中间价
        MdDMU_v0__mid_smo    - 平滑中间价
        MdDMU_v0__mean       - 均值
        MdDMU_v0__std        - 标准差
        MdDMU_v0__quantile   - 分位数
        MdDMU_v0__ob_avg     - 订单簿均价
        MdDMU_v0__cum_avg    - 累计均价
        MdDMU_v0__exec_avg   - 成交均价
        trade_date           - 交易日期
"""

import logging

from factor_calculator import FactorCalculator

logging.basicConfig(level=logging.INFO)


def run_mddmu():
    calc = FactorCalculator()

    result = calc.calculate(
        units=["MdDMU"],
        contract="TL2603",
        start_date="2026-01-05",
        end_date="2026-02-05",
        frequency="tick",
    )

    print(f"MdDMU done. Shape: {result.shape}")
    if not result.empty:
        print("Columns:", list(result.columns))
        print(result.head())


if __name__ == "__main__":
    run_mddmu()
