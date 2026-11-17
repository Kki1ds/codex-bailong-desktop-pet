# macOS 社区版维护交接

给接手维护 macOS 社区版的人（或 Claude）。用户手册见 [MACOS.md](MACOS.md)；上游遗留的 HANDOFF.md / AGENTS.md 针对 Windows 版，不适用于 macOS 发布。

## 1.8.0 同步（2026-11-18）

- 本地候选 1.8.0-mac.1 合并上游 main `752f0893`，对应发布标签 v1.8.0（`cb130091`）。公开入口见 [MACOS.md](MACOS.md)，候选见 [验收记录](releases/v1.8.0-mac.1.md)。
- `surface_policy` 共享窗口状态和前台开关。Cocoa 用 `mac_native` 设置 AppKit 层级；Qt 的置底标志在 Mac 上不生效。Qt 显示、重建窗口或切换鼠标穿透后重新应用层级。浮窗跟随所属卡片，置底编辑时临时使用正常层。遍历浮窗前用 `shiboken6.isValid` 排除底层已释放的 Qt 对象；离屏测试不访问 NSView。
- 用户主动打开聊天和设置时，先解除卡片的鼠标穿透，再请求键盘焦点。Cocoa 会拒绝让仍处于输入穿透状态的窗口成为 key window。用实际 `NSWindow.isKeyWindow` 和设置数值输入验证。
- Mac 只在开启「仅在 Codex 前台时显示」时查询 AppKit 前台 bundle ID。全屏让位优先；退出全屏后按当前前台状态和用户设置恢复。继续保留 Mac 原生菜单栏入口及主动打开设置、聊天时的输入焦点。
- 素材页的归档续传走 `MaterialStore`，与 `UpdateController` 的程序和动画补丁入口独立。保留 Mac 补丁守卫，续传后的素材仍需完整校验。

## 1.7.0 同步（2026-11-14）

- 维护基线为上游 v1.7.0（14fc85a4）加已合并的 macOS 路径 PR #28（817ee63），Mac 版本 1.7.0-mac.1（`MAC_VERSION` 由 `version.py` 的 1.7.0 推出）。分支 `codex/macos-1.7.0`，验证见 [1.7.0-mac.1 验证记录](releases/v1.7.0-mac.1.md)。
- `platform_paths.py` 现为上游与 fork 共有文件：上游提供 `data_dir(fallback)` / `local_appdata(fallback)`（Windows/Linux 保持原 LOCALAPPDATA 表达式，`enhanced.py` 以 `data_dir(ROOT)` 调用），fork 在同一文件保留 `install_root`、LaunchAgent 系列、`background_python`、`app_root`、`NO_WINDOW`、`BUNDLE_ID`。下次合并以上游函数为准，只叠加 fork 辅助函数。
- `codex_connection.data_home` 的 WSL 守卫已由上游 #28 实现（清理引号、空白、变量展开后再判断 `\\wsl$` 路径），fork 不再有独立改动。
- 应用内更新：上游 `app_updates.program_updates_supported()` 已在非 Windows 返回 False；设置页只用它判断，macOS 文案保留；`update_controller.UNSUPPORTED` 仍整体关闭 macOS 的检查与下载（含动画补丁），不要删。
- 上游 1.7.0 新增 `cryptography`（ChatGPT 套餐的 ID Token 验签），本地 `.venv` 需按 requirements 补装，否则冻结包缺依赖。ChatGPT 套餐凭据在 Mac 上经 `desktop_services.SecretStore` 落到登录钥匙串，服务名与闲聊密钥相同（账户名 `active`），尚未在 Mac 实测。
- fork 在共用文件中的改动（下次同步需逐条保留或确认上游已等价处理）：
  - `panel_transition.present_barrier`：先判断 `sys.platform == 'win32'` 再调用 DWM。测试会把 `platformName` 模拟成 windows，非 Windows 主机上没有 `ctypes.windll`。
  - `test_upgrade_settings`：macOS 上把临时目录 resolve 到 `/private/var`，否则部署路径保护把 `/var` 系统别名当成链接拒绝（被测的是 Windows 部署逻辑，生产规则不变）。
  - `test_update_integration.UpdateCancellationTests`：与同文件其他用例一样，用 `update_controller.UNSUPPORTED=False` 夹具测试 Windows 更新流程。
  - `test_linked_cards` 互补混合用例：非 Windows 的 alpha 下限为 253（Windows 仍为 254）。Apple Silicon 光栅路径在混合中段恒定少 2 个最低位，与权重无关；把 `CompositionMode_Plus` 改回 source-over 的变异测试会降到 246 而失败，仍能拦截原缺陷。
  - `check_source.py --macos`：Mac 追加列表去掉已在上游 MODULES 中的模块，避免 `test_enhanced_core` 重复执行。
- 共享文件按上游换行统一：上游 1.7.0 已把部分文件改回 LF（如 `enhanced.py`、`hover_hints.py`、`panel_transition.py`），合并后用脚本比较每个共享文件与 upstream 的换行风格，混排的直接按上游转换。

## 1.6.0 移植（2026-11-08 合并并发布 1.6.0-mac.1 预发布）

- 当前维护基线为上游 v1.6.0（18a9ba43）及发布后首页提交 214d1534，Mac 版本 1.6.0-mac.1，公开入口为 v1.6.0-mac.1 预发布。
- 新增前台窗口几何读取用于窗口避让：AppKit 前台 PID、Quartz 普通可见窗口边界，仅取所在屏幕交集；不查询标题或截图。Retina 坐标保持全局逻辑点，不再除以 DPR。
- 新版 API 价表、计价设置和额度 CLI 启动失败记录必须通过 platform_paths.data_dir；上游新文件若写 `LOCALAPPDATA` 回退主目录，Mac 会在 `~` 下建 BailongEnhanced，合并后需 grep 检查。所有自动测试都设置了 LOCALAPPDATA，回归须清空环境变量断言 Application Support。
- 上游自 v1.6.0 起以 CRLF 提交，fork 原为 LF。合并后共享文件按上游换行统一（与上游仅换行不同的文件直接取上游字节），否则会混排且 PR 差异被换行淹没；Mac 独有文件保持 LF。检查：`git diff --stat 214d153 HEAD` 应与加 `--ignore-cr-at-eol` 时接近。
- 旧库整理在 Mac 复用 storage_locations.plain，仅规范化系统别名，继续拒绝用户链接。
- 新速率/服务状态浮窗继承 HintBubble，已共用 mac_native.overlay；活动区编辑器在卡片内部，无需另建原生窗口。
- Mac 检查入口：`.venv/bin/python tools/check_source.py --macos`。Windows 安装事务、历史安装清理及 PE 裁剪留在 Windows job；减少动态效果测试不使用强制启用动效的夹具。
- 验证及人工验收结果见 [候选验证记录](releases/v1.6.0-mac.1.md)。PR #2 经用户确认以合并提交方式并入 main（保留上游合并历史，不要 squash）；用户授权在高清素材、Chrome 前台窗口避让路线和性能对照未验收时发布，这些已列入 Release 已知限制，下次发布前优先补测。

## 1.2.1 移植记录（2026-10-30）

- 当前维护基线为上游 v1.2.1（c725ede），Mac 版本 1.2.1-mac.1。验证见 docs/releases/v1.2.1-mac.1.md。
- Mac 仅提供通用全屏让位：开关对应 off/game_video，非关闭旧模式统一迁移为 game_video，完成提醒不抢回显示。
- 当前 macOS 的 Chrome 将原生全屏拆成工具栏和内容窗口；检测需按同一 PID 合并矩形覆盖，不能只比较单个窗口。必须保留普通最大化留下菜单栏间隙的反例。
- storage_locations 的用户目录必须走 platform_paths；仅规范化 /var、/tmp、/etc 的系统别名，继续拒绝用户符号链接。
- 原生 HWND/GDI 测试的 platformName 模拟不会提供 WinDLL；跨平台过渡测试需要单独模拟 native_landing.publish，Windows ABI 测试只在 Windows 执行。
- GitHub macOS runner 可能开启减少动态效果；断言中间动画帧的测试须显式固定 motion_enabled，另保留减少动态效果测试。
- Mac 菜单栏使用原生 tooltip，不安装 Win32 鼠标钩子；卡片提示窗口仍注册 mac_native.overlay。

## 仓库与分支

- 本仓库是上游 Wunsch2048/codex-bailong-desktop-pet 的 fork。`main` = 上游代码 + macOS 移植 + macOS 版 README。
- 保留 Windows 与上游的全部文件，便于干净同步；个人调整用配置隐藏，不删除代码。
- `macos-1-platform`、`macos-2-window`、`macos-3-build` 三个分支对应上游 PR #7 至 #9（仍开放）。`macos-3-build` 被上游 README 链接过：不要 force-push，不要删除这三个分支。
- 终端里的 `gh` 默认仓库可能指向上游，务必带 `-R Kki1ds/codex-bailong-desktop-pet`。

## 维护策略

- 只跟上游次版本和主版本（1.1.0、2.0.0 等）；补丁版本只在严重问题时跟。尽力维护。
- 每个 Release 注明基于的上游版本、测试设备和已知限制。

## 发布流程

1. `git remote add upstream https://github.com/Wunsch2048/codex-bailong-desktop-pet.git`（如未添加），`git fetch upstream`。
2. `git merge -X ignore-cr-at-eol upstream/main`，逐个解决冲突，不整文件覆盖。
3. 对照下面“合并时必须保留的 Mac 专属代码”逐项检查。
4. 在 Mac（Apple Silicon）上实测：测试、源码启动、全屏让位、Codex 联动、登录启动等，见 MACOS.md 验收记录。
5. `build_macos.py` 从 `app/version.py` 派生 `MAC_VERSION`（形如 `{上游版本}-mac.N`）。同步新上游版本时从 `-mac.1` 开始，同一上游版本再次发布时递增 N。记录基线提交和验收结果，公开版入口在发布后更新。
6. `python build_macos.py --cards-only --dmg`，产物在 `release/macos-<版本>-<时间>/`，含 .dmg 与 .sha256；脚本不会删除旧构建。
7. 发布以当轮用户授权为准。获准发布后创建草稿、上传校验完整的资产，再公开为预发布。
8. 不要向 Release 以外的位置上传安装包；仓库里不提交构建产物、凭据或日志。

## 合并时必须保留的 Mac 专属代码

- `KeychainStore.read()` / `remove()`（闲聊密钥走登录钥匙串）。
- `typography.py` 中的 `platform_paths.app_root()`（冻结应用的资源路径）。
- `codex_connection.wsl_supported()` 守卫：macOS 上不显示、不使用 WSL 来源，不调用 wsl.exe。
- `FullScreenGuard`：跳过 `AquaAppearanceHelper`，并跳过所有者位于 `/System/Library` 下的窗口（否则切换外观时的淡入淡出会误触发让位）。
- `desktop_services.py` 的分支顺序：先 macOS，再 WSL，最后 Windows；`update_controller.py` 的 macOS UNSUPPORTED 守卫（应用内更新在 macOS 关闭）。
- 应用标识 `BUNDLE_ID = io.github.wunsch2048.bailong-enhanced`（在 `platform_paths.py`），不要改，否则登录项、钥匙串授权和数据目录都会受影响。

## 已报给上游、fork 暂自行修复的共用代码

同步上游时逐条查看上游是否已修：已修则改用上游实现并删除 fork 改动，保留回归测试作为验证；未修则保留 fork 改动。

- [上游 #25](https://github.com/Wunsch2048/codex-bailong-desktop-pet/issues/25)（2026-11-08 提交）：Codex 在 `task_complete` 后为同一 turn 补写后台命令的 `item_completed`，会话被重新判为执行中。**上游 v1.7.0 已修复**（`Session.completed_turn` 及 `item_completed` 分支同 turn 忽略），1.7.0 同步时 `enhanced_core.py` 改为与上游字节一致，删除 fork 的 `b99f6a6` 改动；fork 回归测试保留在 `test_enhanced_core`（`test_late_tool_completion_after_complete_emits_nothing`，为避免与上游同名用例互相覆盖而改名；`test_tail_seeded_completion_ignores_late_tool_record`），继续由 `check_source.py --macos` 执行。目前没有 fork 自行修复的共用代码。

## 给用户的命令规则

- 在 Mac 上给用户的命令用 `python`，绝不用 `python3`：`python` 是 Homebrew Python 3.12，系统 `python3` 是 3.9 且 pip 证书损坏。
- 别名在非交互 shell（脚本、Remote Control）里不生效，那里请写 `/opt/homebrew/bin/python3.12`。
- `pip install` 需要加 `-i https://pypi.org/simple`。

## 环境事实

- 签名：只有免费 Apple 开发者账号，没有 Developer ID，无法公证；发布的 dmg 为 ad-hoc 签名，用户需右键打开。
- 云端（Linux）会话只能离屏跑测试，不能验证窗口行为；全屏让位、钥匙串、登录启动必须在真实 Mac 上由用户验收。
- 上游已在 README 中指向本 fork 的 macOS 版，作者没有 Mac，不会合入 macOS 代码。
- 性能结论按版本与场景重新测量；本次短场景数据见发布说明，不沿用旧版约 37% CPU 的记录。
