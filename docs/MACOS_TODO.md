# macOS 待改清单

来自 2026-10-30 对 1.2.1-mac.1 移植的审查。以下均不影响使用，不单独发布补丁，下次跟进上游版本时一并处理。完成后在对应条目注明提交并移出本清单。

## 1. 全屏让位设置的冲突提示名称不一致

- 位置：`app/desktop_settings.py:112`
- 现状：Mac 设置页显示“全屏应用时让位”，但 `field_titles['fullscreen_yield_mode']` 仍为“全屏时让位”。设置草稿冲突时，提示里出现的是后者。
- 改法：按平台取与行标题相同的文字，例如 `'全屏应用时让位' if MACOS else '全屏时让位'`。
- 验证：在 Mac 上制造该项设置冲突，确认提示名称与设置页一致；Windows 文案不变。

## 2. 多余的未读提醒信号连接

- 位置：`app/desktop.py:125`
- 现状：`self.bubble.status_indicator.changed.connect(self.sync_full_screen)` 是旧版“未读提醒时抢回显示”逻辑的遗留。1.2.1-mac.1 起，`sync_full_screen` 只看 `fullscreen_yield_mode` 与 `on_top`，与未读状态无关，所以每次状态变化都会多一次空调用。
- 改法：删除这条连接。设置变化仍由 `apply_settings` 调用 `sync_full_screen`，启动时由 `__init__` 中的 `apply_settings({},save=False)` 调用。
- 验证：`test_mac_full_screen`、`test_mac_platform_services` 通过；真机上切换让位开关、全屏期间产生完成提醒，行为与 1.2.1-mac.1 相同（提醒保持未读，退出全屏后显示）。

## 3. 诊断报告里的“视频全屏让位”状态在 Mac 上被置为 True

- 位置：`app/mac_native.py:232`；诊断字段 `app/desktop.py:1189`
- 现状：`FullScreenGuard.check()` 结尾执行 `self.pet._video_yielded=yielded`。Windows 的通用模式（`game_video`）在 `video_yield.py` 中把它固定为 False，只用 `_fullscreen_yielded` 表示隐藏。因此在 Mac 上让位时，导出的诊断报告中 `video_fullscreen_yielding` 为 True，与字段含义及 Windows 行为不一致。
- 改法：有 `set_fullscreen_yield` 时，把 `_video_yielded` 设为 False，与 Windows 的通用模式保持一致；没有时保留现有回退。改前确认 `_video_yielded` 在 Mac 上只被 `can_raise_bubble` 和诊断读取，且前者已由 `_fullscreen_yielded` 覆盖。
- 验证：真机全屏让位期间导出诊断，`fullscreen_window_yielding` 为 True、`video_fullscreen_yielding` 为 False；全屏期间面板不会被重新抬起。
