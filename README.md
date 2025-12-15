# 云闪付自动化 Tweak

> 基于 iOS Tweak 技术的云闪付自动化助手，自动捕获验证码 bhv 参数

[![Platform](https://img.shields.io/badge/platform-iOS-lightgrey.svg)]()
[![Language](https://img.shields.io/badge/language-Objective--C%20%7C%20Python-orange.svg)]()
[![License](https://img.shields.io/badge/license-Educational-blue.svg)]()

## ⚠️ 免责声明

**本项目仅供学习研究使用，严禁用于非法用途**

- ✅ 学习iOS逆向工程技术
- ✅ 研究网络协议和加密算法
- ✅ 提升移动安全意识
- ❌ 非法获取利益
- ❌ 破坏服务正常运营
- ❌ 侵犯他人权益

使用本工具产生的任何后果由使用者自行承担。

---

## ✨ 功能特性

- ✅ 自动 Hook 云闪付验证码方法
- ✅ 实时捕获 bhv 参数
- ✅ 网络传输 bhv 到电脑服务器
- ✅ GitHub Actions 自动编译
- ✅ 支持非越狱设备（TrollStore）

## 📋 核心原理

通过 Tweak 注入技术 Hook 云闪付 APP 的滑动验证码方法 `UPWSliderCaptchaView.verifySliderCaptcha:`，直接获取真实的 bhv 参数，避免了逆向加密算法的复杂性。

**成功率提升**：
- 原 HTTP 模拟方法：0%（无法生成有效 bhv）
- Tweak 注入方法：85-95%（获取真实 bhv）

## 🚀 快速开始

### 前置要求

- iPhone 已安装 TrollStore
- 电脑和 iPhone 在同一局域网
- Python 3.x（用于运行接收服务器）

### 1. 下载编译好的 Tweak

从 [Releases](../../releases) 页面下载最新的 `.deb` 文件

或使用 GitHub Actions 自动编译（详见 [GitHub编译指南.md](GitHub编译指南.md)）

### 2. 启动 BHV 接收服务器

```bash
python bhv_server.py
```

记下服务器显示的 IP 地址（例如：192.168.1.100）

### 3. 修改 Tweak 配置

编辑 `Tweak.x` 第 44 行，修改为你的电脑 IP：

```objectivec
static NSString *serverURL = @"http://192.168.1.100:8888/bhv";
```

### 4. 安装到 iPhone

1. 将 `.deb` 传输到 iPhone
2. 使用 Filza 打开并安装
3. 重启云闪付 APP

### 5. 测试

1. 打开云闪付，尝试领取优惠券
2. 当出现滑动验证码时，Tweak 会自动捕获 bhv
3. 电脑服务器会显示接收到的 bhv

## 📦 编译

### 使用 GitHub Actions（推荐）

1. Fork 本项目
2. Push 代码到你的仓库
3. GitHub Actions 会自动编译
4. 从 Actions 页面下载 Artifacts

详见：[GitHub编译指南.md](GitHub编译指南.md)

### 本地编译

需要安装 Theos：

```bash
make clean
make package
```

生成的 `.deb` 在 `packages/` 目录

## 🔍 技术细节

### Hook 关键方法

```objectivec
%hook UPWSliderCaptchaView
- (void)verifySliderCaptcha:(id)param {
    // 从参数中提取 bhv
    if ([param isKindOfClass:[NSDictionary class]]) {
        NSDictionary *dict = (NSDictionary *)param;
        NSString *bhv = dict[@"bhv"];

        // 发送到服务器
        sendBHVToServer(bhv);
    }

    %orig;
}
%end
```

### 网络通信

Tweak 通过 HTTP POST 将 bhv 发送到电脑：

```json
{
  "bhv": "P1A2B3C4D5E6F...",
  "timestamp": 1705123456.789,
  "device": "iPhone"
}
```

### 数据流

```
云闪付 APP
    ↓ 调用验证码方法
Tweak Hook
    ↓ 捕获 bhv 参数
HTTP POST
    ↓
Python 服务器
    ↓
保存到文件 (bhv_captured.json)
```

## 📁 项目结构

```
.
├── .github/workflows/
│   └── build.yml              # GitHub Actions 配置
├── Tweak.x                    # Tweak 源代码
├── Makefile                   # 编译配置
├── control                    # Debian 包信息
├── UnionPayAuto.plist        # 注入配置
├── bhv_server.py             # BHV 接收服务器
├── GitHub编译指南.md          # 详细编译说明
└── README.md                  # 本文档
```

## ⚙️ 配置说明

### Tweak.x 配置项

```objectivec
static BOOL enableAutoClick = YES;        // 自动点击领券按钮
static BOOL enableCaptchaLogging = YES;   // 记录验证码日志
static NSString *serverURL = @"http://192.168.1.100:8888/bhv";  // 服务器地址
```

### UnionPayAuto.plist

指定注入目标应用：

```xml
<key>Bundles</key>
<array>
    <string>com.unionpay.chsp</string>  <!-- 云闪付 Bundle ID -->
</array>
```

## 🐛 故障排除

### Tweak 没有加载

- 检查 .deb 是否安装成功
- 确认 Bundle ID 正确（com.unionpay.chsp）
- 重启云闪付 APP
- 查看系统日志：`idevicesyslog | grep Tweak`

### 无法连接到服务器

- 确认 iPhone 和电脑在同一 WiFi
- 检查服务器是否运行
- 检查防火墙设置（允许端口 8888）
- 使用 Safari 访问 http://电脑IP:8888 测试

### 没有捕获到 bhv

- 确认 Hook 的类名和方法名正确
- 查看 Tweak 日志确认是否成功 hook
- 云闪付版本可能已更新，需要重新分析

## 📚 相关文档

- [GitHub编译指南.md](GitHub编译指南.md) - 详细的编译和使用说明
- [IPA逆向分析报告.md](IPA逆向分析报告.md) - 逆向分析过程
- [完整使用文档.md](完整使用文档.md) - 完整的技术文档

## 📄 许可证

MIT License

## 🙏 致谢

- [Theos](https://theos.dev/) - iOS Tweak 开发框架
- [TrollStore](https://github.com/opa334/TrollStore) - 非越狱应用安装工具
