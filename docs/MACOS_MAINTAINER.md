# macOS 社区版维护交接

给接手维护 macOS 社区版的人（或 Claude）。用户手册见 [MACOS.md](MACOS.md)；上游遗留的 HANDOFF.md / AGENTS.md 针对 Windows 版，不适用于 macOS 发布。

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
5. 修改 `build_macos.py` 里的 `MAC_VERSION`（形如 `{上游版本}-mac.N`），N 为该上游版本下的第几次 macOS 发布；同步更新 README 与 MACOS.md 里的版本、基线提交和验收记录。
6. `python build_macos.py --cards-only --dmg`，产物在 `release/macos-<版本>-<时间>/`，含 .dmg 与 .sha256；脚本不会删除旧构建。
7. 发布须有用户明确授权。本次用户已明确要求测试、打包并发布，允许代为创建草稿、上传校验完整的资产，再公开为预发布；无发布授权时只准备本地交付物。
8. 不要向 Release 以外的位置上传安装包；仓库里不提交构建产物、凭据或日志。

## 合并时必须保留的 Mac 专属代码

- `KeychainStore.read()` / `remove()`（闲聊密钥走登录钥匙串）。
- `typography.py` 中的 `platform_paths.app_root()`（冻结应用的资源路径）。
- `codex_connection.wsl_supported()` 守卫：macOS 上不显示、不使用 WSL 来源，不调用 wsl.exe。
- `FullScreenGuard`：跳过 `AquaAppearanceHelper`，并跳过所有者位于 `/System/Library` 下的窗口（否则切换外观时的淡入淡出会误触发让位）。
- `desktop_services.py` 的分支顺序：先 macOS，再 WSL，最后 Windows；`update_controller.py` 的 macOS UNSUPPORTED 守卫（应用内更新在 macOS 关闭）。
- 应用标识 `BUNDLE_ID = io.github.wunsch2048.bailong-enhanced`（在 `platform_paths.py`），不要改，否则登录项、钥匙串授权和数据目录都会受影响。

## 给用户的命令规则

- 在 Mac 上给用户的命令用 `python`，绝不用 `python3`：`python` 是 Homebrew Python 3.12，系统 `python3` 是 3.9 且 pip 证书损坏。
- 别名在非交互 shell（脚本、Remote Control）里不生效，那里请写 `/opt/homebrew/bin/python3.12`。
- `pip install` 需要加 `-i https://pypi.org/simple`。

## 环境事实

- 签名：只有免费 Apple 开发者账号，没有 Developer ID，无法公证；发布的 dmg 为 ad-hoc 签名，用户需右键打开。
- 云端（Linux）会话只能离屏跑测试，不能验证窗口行为；全屏让位、钥匙串、登录启动必须在真实 Mac 上由用户验收。
- 上游已在 README 中指向本 fork 的 macOS 版，作者没有 Mac，不会合入 macOS 代码。
- 性能结论按版本与场景重新测量；本次短场景数据见发布说明，不沿用旧版约 37% CPU 的记录。
