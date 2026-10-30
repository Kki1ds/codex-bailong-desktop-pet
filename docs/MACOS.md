# macOS 社区版

在不改变 Windows 行为的前提下，让桌宠在 Apple Silicon Mac 上运行。macOS 版是社区维护的移植，由 [Kki1ds](https://github.com/Kki1ds) 在 fork 中维护，不是上游官方版本。授权边界见 NOTICE.md，与 Windows 版相同。

## 下载与安装

1. 在 [Releases](https://github.com/Kki1ds/codex-bailong-desktop-pet/releases) 下载 `BailongEnhanced-<版本>-macos-arm64.dmg`，只支持 Apple Silicon。可用同名 `.sha256` 文件校验：`shasum -a 256 -c <文件名>.sha256`。
2. 双击打开 .dmg，把 `BailongEnhanced.app` 拖到旁边的“Applications”文件夹，然后推出磁盘映像。
3. 首次打开时，Gatekeeper 会提示无法验证开发者（ad-hoc 签名，未公证）：在 Finder 中右键 .app 选择“打开”，或在 系统设置 → 隐私与安全性 中点“仍要打开”。
4. 安装包只含卡片；人物动画在 设置 → 角色与素材 中从上游 Release 下载，逐一校验 SHA-256 后使用。

升级时退出桌宠，用新版替换“应用程序”里的旧版即可，设置和已下载的动画保存在数据目录，不受影响。替换后首次读取闲聊密钥时，钥匙串会重新询问授权。

## 维护范围

- 尽力维护，不承诺跟进每个上游版本。
- 上游发布次版本或主版本（例如 1.1.0、2.0.0）时，同步代码、在 Mac 上实测并发布新的 macOS 包。
- 补丁版本（例如 1.0.2）一般不单独跟进，影响使用的严重问题除外。
- 每个 Release 注明基于的上游版本、测试设备和已知限制。
- macOS 版关闭了应用内更新，不会下载 Windows 补丁；更新请到 Releases 下载新版。
- macOS 相关问题请在 [本仓库 Issues](https://github.com/Kki1ds/codex-bailong-desktop-pet/issues) 反馈；Windows 版问题请到上游。

已在 M1 Pro（macOS，arm64）上验收，步骤和结果见文末。Intel Mac 未测试。

## 从源码运行

```bash
brew install python@3.12
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-enhanced.txt
.venv/bin/python app/enhanced.py
```

pip 若配置了不含这些版本的镜像，可加 `-i https://pypi.org/simple`。

源码目录不含动画时以仅卡片方式启动；在 设置 → 角色与素材 中下载轻量或高清动画，与 Windows 仅卡片安装相同，资源逐一校验 SHA-256 后缓存在数据目录。

开发时也可以按 docs/DEVELOPMENT.md 导入高清源，再在本机生成 512px 轻量素材：

```bash
.venv/bin/python tools/import_installed_assets.py --source <解压后的高清目录>
.venv/bin/python -c "import sys;sys.path[:0]=['.','app'];import build_materials;build_materials.build()"
```

第二条生成 `build/materials/light`，内容 ID 与 material_catalog.json 一致。它会以 LF 重写 `app/material_catalog.json`，内容不变，`git checkout app/material_catalog.json` 即可还原换行。

测试与 Windows 相同：`PYTHONPATH=app QT_QPA_PLATFORM=offscreen` 后运行 unittest。Windows 专属的安装、注册表和 DPAPI 测试在 macOS 上跳过；macOS 专属测试（test_macos_codex、test_live_unix、test_mac_platform_services、test_mac_full_screen）在其他系统上跳过。闲聊密钥的测试不会读写真实钥匙串。GitHub Actions 的 macOS 任务（macos-14，arm64）运行这四组测试，并构建一次仅卡片 .app 与 .dmg，做 `codesign --verify` 和 SHA-256 校验，不下载人物素材。

## 构建 .app

```bash
.venv/bin/python build_macos.py --cards-only   # 不内置动画，约 140 MB
.venv/bin/python build_macos.py                # 内置 512px 轻量素材，约 700 MB，需先生成 build/materials/light
.venv/bin/python build_macos.py --cards-only --dmg   # 另外生成发布用的 .dmg 和 .sha256
```

每次构建都写入新的 `build/macos-<版本>-<时间>` 与 `release/macos-<版本>-<时间>`，输出为其中的 `BailongEnhanced.app`，加 `--dmg` 时还有 `.dmg` 与 `.sha256`；脚本不删除、不覆盖任何已有目录，旧构建原样保留，需要时请自行清理。PyInstaller 通过 `tools/pyinstaller_keep_files.py` 运行，打包过程中的递归删除同样被拒绝。打包后做 ad-hoc 签名，未使用开发者证书，也未公证。把 .app 拷到“应用程序”文件夹后再开启登录启动；直接从下载位置运行时系统会把它放进随机只读路径（App Translocation），登录启动会提示先移动。

首次打开时，Gatekeeper 可能提示无法验证开发者：在 Finder 中右键 .app 选择“打开”，或在 系统设置 → 隐私与安全性 中允许。本机构建的 .app 通常不带隔离属性，不会出现此提示。

## 与 Windows 版的差异

| 功能 | macOS 实现 |
| --- | --- |
| 数据目录 | `~/Library/Application Support/BailongEnhanced`；显式设置 `LOCALAPPDATA` 时仍以它为准，便于隔离测试 |
| Codex CLI | 优先 ChatGPT.app 内置的 `Contents/Resources/codex-cli/bin/codex`，其次 `~/.codex/packages/app-server-daemon/current`、PATH、Homebrew、npm；`BAILONG_CODEX` 或设置中的路径仍然优先 |
| 连接来源 | 只连接本机 Codex；设置中不显示 Windows/WSL 来源，从 Windows 拷来的 WSL 配置会被忽略，不会调用 wsl.exe |
| Codex 桌面端识别 | 按 bundle id `com.openai.codex` 识别主进程，排除辅助进程和 CLI |
| 实时状态 | `~/.codex/ipc/ipc.sock`（协议与 Windows 命名管道相同），只发送初始化、关注/取消关注和否定的发现应答 |
| 会话跳转 | `/usr/bin/open codex://threads/<id>`；打开 Codex 用 `open -b com.openai.codex` |
| 闲聊密钥 | 登录钥匙串（服务名 BailongEnhanced），每个密钥版本一个条目，不写凭据文件；列出条目只读属性，不触发授权 |
| 登录启动 / 随 Codex 启动 | `~/Library/LaunchAgents/io.github.wunsch2048.bailong-enhanced(.codex-sync).plist`，下次登录生效；首次写入时系统提示新增后台项目，可在“登录项与扩展”中管理 |
| Dock 与桌面空间 | 不显示 Dock 图标；人物和卡片出现在所有桌面空间，不抢焦点 |
| 外观 | 界面固定为浅色；系统使用深色模式时，原生复选框和滚动条也按浅色绘制 |
| 减少动态效果 | 跟随 系统设置 → 辅助功能 → 显示 → 减少动态效果 |
| 全屏让位 | 菜单栏应用的窗口会跟随进入其他应用的全屏空间（视频、全屏应用都适用），因此每 0.8 秒检测一次：某块显示器上有其他应用占满整屏时，该屏上的人物和卡片变为透明且不拦截点击，退出全屏后恢复。关闭“全屏应用时让位”时照常显示；完成提醒不打断全屏，退出后恢复；让位与“始终置顶”相互独立，鼠标穿透在退出全屏后按原设置恢复 |
| 应用内更新、安装管理、清理历史版本 | 已关闭；公开 Release 是 Windows 包，macOS 版不会下载或运行。更新请拉取源码后重新运行或构建 |
| 点击音效 | `afplay`，自动动作仍静音 |
| 找回组件 | 再次打开正在运行的白龙桌宠（Finder、Spotlight 或 `open`），相当于 Windows 上重复启动；菜单栏图标单击打开菜单，双击找回 |
| 导出诊断 | 保存到数据目录，不写入 .app |

## 已知限制

- 只在 Apple Silicon（M1 Pro）上测试过，Intel Mac 未测。
- 未使用开发者证书签名，也未公证，首次打开需要手动放行；每次重新构建后，首次读取闲聊密钥时钥匙串会重新询问授权。
- 关闭鼠标穿透后，人物窗口的透明区域在重启前可能仍拦截点击（Qt 在 macOS 上的行为）。
- 系统通知走 Qt 的托盘消息，源码运行时可能不显示；面板内的完成提醒始终可见。
- 菜单栏图标为彩色缩略图，尚未提供单色模板图标。
- 全屏检测以“同一其他应用的一个或多个窗口共同占满整块显示器”为准（跳过 /System/Library 下的系统辅助进程，例如切换外观时的淡入淡出窗口；因此全屏的访达窗口也不会触发让位），最多约 0.8 秒延迟，切换动画期间可能短暂可见。已用 Chrome 全屏视频实测，其他播放器未逐一验证。
- 部分动作素材边缘带有原始抠图残留，在深色壁纸和 Retina 显示下更明显；与 Windows 版使用同一素材，不是移植引入的问题。

## 本次验收

1.2.1-mac.1 基于上游 v1.2.1（c725ede）。本次测试、实装和性能记录见 [1.2.1-mac.1 发布说明](releases/v1.2.1-mac.1.md)。

## 历史验收记录（1.0.1-mac.1）

环境：MacBook Pro M1 Pro，内置屏加外接 5K 显示器，Python 3.12.15（Homebrew），ChatGPT.app 内置 Codex CLI。验收于 2026-10-25，基于 v1.0.1（8dd8617）。

| 检查 | 步骤 | 结果 |
| --- | --- | --- |
| 单元测试 | `PYTHONPATH=app QT_QPA_PLATFORM=offscreen` 运行全部 `app/test_*.py` | 逐模块对比未改动的 v1.0.1：没有在 v1.0.1 上通过、在移植后失败的测试（89 个模块中 78 个通过）；其余失败在 v1.0.1 上同样失败，来自 Windows 专属代码（winreg、cmd、启动文件夹）和 macOS 上 /var 为符号链接触发的部署路径保护。WSL 测试在 macOS 上跳过，WSL 来源守卫测试通过 |
| 源码启动 | `.venv/bin/python app/enhanced.py`，无 Dock 图标，人物与卡片显示 | 实机窗口探针通过（持续动作 14 项）；日常运行使用 .app |
| 构建 | `build_macos.py --cards-only`，`codesign --verify --deep --strict` 通过 | 通过，136 MB；写入新的带时间戳目录，已有构建目录未改动 |
| 动画下载 | 设置 → 角色与素材 下载轻量动画，校验后切换播放 | 通过（轻量 512px）；未下载高清，高清切换未测 |
| Codex 联动 | 在 Codex 桌面端发起任务：卡片显示进行中，完成后提醒；点击跳转到对应会话 | 通过 |
| 额度与日报 | 额度环、重置时间、日报和额度对比显示本机数据 | 通过 |
| 登录启动 | 开启后生成 LaunchAgent，重新登录后自动启动；关闭后删除 | 通过：注销后重新登录，桌宠与 Codex 监听自动启动 |
| 闲聊 | 保存密钥写入钥匙串，发送消息成功，清除后条目删除 | 钥匙串读写删除用临时条目自动测试通过（`BAILONG_KEYCHAIN_TEST=1`）；未用真实模型服务测试发送 |
| 全屏让位 | Chrome 全屏视频时人物与卡片让位，退出后恢复；有未读提醒时照常显示 | 通过 |
| 全屏检测开销 | 每 0.8 秒一次的 Quartz 窗口枚举，连续采样 300 次；2 块显示器（内置 3024×1964 + 外接 5K），13 个屏上窗口 | 单次耗时中位数 3.1 ms、p95 12.7 ms；CPU 时间中位数 0.83 ms，约占 0.1% CPU。桌宠进程整体空闲 CPU 约 37%（单核计），采样显示主要来自 WebP 动画软件解码，与全屏检测无关 |
| 卡片展开与收回 | 展开、收回卡片后透明度与点击恢复 | 通过 |
| 多桌面空间 | 切换桌面空间时人物和卡片跟随，不抢焦点 | 通过 |
| 深色模式 | 系统切换深色后设置界面保持浅色，复选框清晰 | 通过；切换外观时系统淡入淡出窗口不会触发全屏让位 |
| 再次打开 | 运行中再次打开 .app，隐藏的组件恢复，不启动第二个进程 | 通过 |
