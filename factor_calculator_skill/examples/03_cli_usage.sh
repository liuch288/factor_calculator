#!/bin/bash
# =============================================================================
# 用户需求：
#     "帮我用 CLI 算一下 SpreadDMU 试试"
#
# Agent 操作：
#     1. 检查 SpreadDMU 签名为 (self)，无参数
#     2. 使用 factor-calculator CLI 命令行工具计算
#
# 前置条件：
#     - 已通过 pip install . 安装 factor_calculator 包
#     - 激活 quantdev conda 环境
#     - CLI 命令 factor-calculator 可在任意目录下运行，不依赖当前路径
#
# 结果：
#     18/32 天成功，输出列 SpreadDMU_v0__spread（买卖价差）
# =============================================================================

# 查看可用的 DMU 和 PEU 类
factor-calculator list

# 只看 DMU
factor-calculator list --dmu

# 只看 PEU
factor-calculator list --peu

# 计算 SpreadDMU（单日模式）
factor-calculator calculate \
    --units "SpreadDMU" \
    --contract TL2603 \
    --date 2026-01-05

# 计算 SpreadDMU（多日模式）
factor-calculator calculate \
    --units "SpreadDMU" \
    --contract TL2603 \
    --start-date 2026-01-05 \
    --end-date 2026-02-05

# 多个 unit 一起算（逗号分隔）
factor-calculator calculate \
    --units "MdDMU,SpreadDMU" \
    --contract TL2603 \
    --start-date 2026-01-05 \
    --end-date 2026-02-05

# 带参数的 unit
factor-calculator calculate \
    --units "KlineDMU(5)" \
    --contract TL2603 \
    --start-date 2026-01-05 \
    --end-date 2026-02-05

# 结果输出到文件（pickle 格式）
factor-calculator calculate \
    --units "SpreadDMU" \
    --contract TL2603 \
    --start-date 2026-01-05 \
    --end-date 2026-02-05 \
    -o result.pkl

# 查看已有因子
factor-calculator factors \
    --contract TL2603 \
    --date 2026-01-05

# CLI 完整参数说明：
#   --db          结果数据库路径（可选，默认使用框架默认路径）
#   --md          行情数据路径（可选，默认使用框架默认路径）
#   --units       unit 规格，逗号分隔，如 "MdDMU,KlineDMU(5)"
#   --contract    合约代码，如 TL2603
#   --date        单日模式日期（与 --start-date/--end-date 互斥）
#   --start-date  多日模式起始日期
#   --end-date    多日模式结束日期
#   --frequency   数据频率，默认 tick
#   --recalculate 重算已有因子
#   --fail-fast   遇到失败立即停止
#   -o/--output   输出文件路径（pickle 格式）
