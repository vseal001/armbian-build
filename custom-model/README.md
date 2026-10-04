# custom-model — KC2 / K10Plus (RK3399) 板卡适配资料

本目录保存 KC2 / K10Plus 电视盒子的原始适配资料与反编译产物。
板卡定义已落地到构建框架中（全部为**新增文件**，不改动上游任何文件，方便与
`armbian/build` 上游持续合并）。

## 文件说明

| 文件 | 说明 |
|---|---|
| `kc2-k10plus_fdt.dtb` | 实机提取的 BSP 设备树（Android，内核 4.19）二进制 |
| `kc2-k10plus_fdt.dts` | 上者的反编译结果（pyfdt 反编译，phandle 为数字形式，仅作逆向参考，不直接编译） |
| `rc_haigesen3528_ir.dtsi` | 海格森3528 遥控器键表片段（BSP remotectl 节点格式，供 4.19 SDK 使用） |

## 板卡文件在构建框架中的位置

| 用途 | 路径 |
|---|---|
| 板卡配置 | `config/boards/kc2-k10plus.conf` |
| 板卡 DTS（mainline，可直接编译） | `patch/kernel/archive/rockchip64-6.18/dt/rk3399-kc2-k10plus.dts` 与 `rockchip64-7.2/dt/` 同名文件（`dt/` 目录中的 DTS 会被构建系统原样拷入内核树并自动注册进 Makefile） |
| IR 键表（ir-keytable TOML） | `config/optional/boards/kc2-k10plus/_packages/bsp-cli/etc/rc_keymaps/haigesen3528.toml` |
| IR 键表加载规则 | `config/optional/boards/kc2-k10plus/_packages/bsp-cli/etc/udev/rules.d/99-kc2-ir-keymap.rules` |

## 硬件概要（反编译实测）

- SoC RK3399，PMIC **RK808**（中断 GPIO1_C5），CPU 大小核供电 syr837/syr828
- eMMC（HS400 enhanced-strobe）+ TF 卡（CD 脚 GPIO0_A7）
- WiFi/BT **AP6354**（SDIO，WL_REG_ON = GPIO0_B2，host_wake = GPIO0_A3）
- 有线 **RGMII**（复位 GPIO3_B7，rx_delay 0x11，外部 125MHz 时钟）
- USB：两个 USB3 口均为 host（vbus GPIO4_D2 / GPIO2_A7）
- 显示：**HDMI-only 盒子**（DSI/eDP/触摸全部禁用），音频 HDMI + es8316（i2c1@0x10）
- 红外接收头在 **PWM3 引脚（GPIO0_A6）**

## 红外适配说明（海格森3528）

原厂 BSP 用 `rockchip_pwm_remotectl`（PWM 捕获解码），该驱动只存在于
Rockchip BSP 内核，mainline 6.x 没有对应驱动也没有 PWM 捕获 API，因此
mainline 方案改用 `gpio-ir-receiver`（同一引脚复用为 GPIO）+ rc-core 标准
NEC 解码。

BSP 驱动解码窗口错位 1 位：实机 NEC 地址 0x01 被解码为 usercode 0xFE01、
键值呈现为 0xBF/0xB3/…（见 `rc_haigesen3528_ir.dtsi`）。mainline 标准 NEC
解码直接看到线上真实值（从波形级捕获重建并通过 NEC 补码校验）：

| 按键 | BSP scancode | 线上真实 cmd | mainline scancode (0x01xx) | keycode |
|---|---|---|---|---|
| 电源 | 0xBF | 0x81 | 0x0181 | KEY_POWER |
| 菜单 | 0xB3 | 0x99 | 0x0199 | KEY_MENU |
| 返回 | 0xE6 | 0x33 | 0x0133 | KEY_BACK |
| HOME | 0xEE | 0x23 | 0x0123 | KEY_HOME |
| 音量+ | 0xE7 | 0x31 | 0x0131 | KEY_VOLUMEUP |
| 音量− | 0xEF | 0x21 | 0x0121 | KEY_VOLUMEDOWN |
| 确认 | 0xEC | 0x27 | 0x0127 | KEY_ENTER |
| 上 | 0xE9 | 0x2D | 0x012D | KEY_UP |
| 下 | 0xE5 | 0x35 | 0x0135 | KEY_DOWN |
| 左 | 0xAE | 0xA3 | 0x01A3 | KEY_LEFT |
| 右 | 0xAF | 0xA1 | 0x01A1 | KEY_RIGHT |
| 鼠标键 | 0xFF | 0x01 | 0x0101 | KEY_CONTEXT_MENU |

键值加载：镜像内置 `ir-keytable`（板卡配置 `PACKAGE_LIST_BOARD`）；注：bsp-cli 打包只取 `packages/bsp/common` 与 `config/optional/**/_packages/bsp-cli`，板级文件必须放后者，udev 在
IR 设备出现时自动执行
`ir-keytable -c -w /etc/rc_keymaps/haigesen3528.toml -p nec,necx`。

验证命令（刷机后）：

```bash
ir-keytable -t        # 按遥控器应打印 scancode 0x0181 等
```

若个别按键无响应，用 `ir-keytable -t` 读出实际 scancode 后修改 toml 即可
（理论差异只可能来自地址字节，数据字节均经补码校验）。

## 与上游合并

以上全部为新增文件；`compile.sh`、上游 `config/`、`patch/` 内容零改动。
上游同步（merge `armbian/build` main）时无需解决冲突。

## CI 工作流（.github/workflows/）

- **rebuild.yml**：手动/ nightly 构建镜像。下拉分层：平台架构 → CPU 主控
  （选错家族会在校验步列出该家族全部板卡）→ 型号（按 CPU 家族聚类、家族内
  ABC 排序，kc2-k10plus 恒为默认第一位；无对应项选 custom 并填
  board_override）→ 桌面（arm64 上游支持的全部 7 种 + 无桌面）→ 额外组件
  （空格分隔，经 PACKAGE_LIST_ADDITIONAL 注入；openssh 等必备组件
  BUILD_MINIMAL=no 下默认已含）→ 内核分支 → 发行版。构建成功后：
  镜像发布为 GitHub Release（tag `img-<board>-<时间戳>`，持久下载链接）+
  在「📦 构建通知」issue 中评论链接（仓库所有者会收到 GitHub 邮件）。
- **sync-upstream.yml**：每天 05:43（北京）+ 手动。合并上游 armbian/build
  main：无冲突 → 直接合并进 main 并自动运行
  `custom-model/tools/gen_rebuild_yml.py` 刷新型号菜单；**有冲突 → 不直接
  合并**，推送 `sync-upstream/<日期>` 分支并创建 PR 交人工处理。
