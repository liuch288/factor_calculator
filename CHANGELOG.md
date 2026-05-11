# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-05-12

### Added
- 进度跟踪功能：计算自动保存进度到 `~/.fc/progress/`
- ProgressTracker 类：支持任务创建、进度更新、日志记录、任务查询
- CLI 子命令：
  - `progress list` - 列出计算任务
  - `progress show <task_id>` - 显示任务详情
  - `progress logs <task_id>` - 显示任务日志

### Changed
- 多天计算进度计算优化：失败的天数也计入完成进度
- 每任务独立目录存储，避免多进程并发写入冲突

### Fixed
- 修复进度计算显示不正确的问题
- 修复时间格式显示问题

## [0.1.2] - 2026-04-24

### Changed
- 禁用 `positionPnldmu` 注入：`Strategy(position_pnl_dmu_class=None)` 设置为 None，移除 PnL DMU 的自动注入逻辑。

## [0.1.1] - 2025-??-??
- (placeholder, version aligned from 0.1.0)

## [0.1.0] - 2025-??-??
- Initial release
