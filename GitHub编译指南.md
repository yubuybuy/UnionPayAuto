# 云闪付自动化 - GitHub 编译指南

## 📦 项目已配置好 GitHub Actions 自动编译

本项目使用 GitHub Actions 自动编译 Tweak，无需本地安装 Theos。

---

## 🚀 快速开始

### 第一步：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 创建新仓库（例如：UnionPayAuto）
3. 设置为 Public 或 Private（Private 需要付费账号）

### 第二步：上传项目文件

在项目目录下打开 PowerShell 或 CMD：

```bash
cd C:\Users\gao-huan\Desktop\云闪付

# 初始化 git 仓库
git init

# 添加所有文件
git add .

# 创建首次提交
git commit -m "Initial commit - UnionPay Auto Tweak"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/UnionPayAuto.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 第三步：等待自动编译

1. 推送完成后，访问你的仓库
2. 点击顶部的 **Actions** 标签
3. 会看到一个正在运行的工作流（Build UnionPay Tweak）
4. 等待 2-3 分钟，直到状态变成 ✅ 绿色勾

### 第四步：下载编译好的 .deb 文件

编译成功后：

1. 点击完成的构建任务
2. 滚动到页面底部 **Artifacts** 部分
3. 下载 **UnionPayAuto-DEB.zip**
4. 解压得到 `.deb` 文件

---

## 📱 安装到 iPhone

### 使用 TrollStore 安装

1. 将 `.deb` 文件传输到 iPhone（通过 AirDrop 或其他方式）
2. 使用 **Filza** 文件管理器打开 `.deb` 文件
3. 点击右上角 **安装**
4. 安装完成后，重启云闪付 APP

### 验证安装成功

1. 打开云闪付 APP
2. 使用 Console.app（macOS）或 `idevicesyslog`（Windows）查看日志
3. 应该能看到：
   ```
   🚀 云闪付自动化 Tweak 已加载
   版本: 1.0.0
   ```

---

## 🔧 配置 BHV 接收服务器

Tweak 会自动捕获验证码的 bhv 参数并发送到你的电脑。

### 1. 启动接收服务器

在电脑上运行：

```bash
cd C:\Users\gao-huan\Desktop\云闪付
python bhv_server.py
```

服务器会显示类似信息：

```
🚀 BHV 接收服务器启动
本地地址: http://192.168.1.100:8888
接收地址: http://192.168.1.100:8888/bhv

请在 Tweak.x 中将 serverURL 修改为:
  static NSString *serverURL = @"http://192.168.1.100:8888/bhv";
```

### 2. 修改 Tweak 配置

1. 记下服务器显示的 IP 地址（例如：`192.168.1.100`）
2. 编辑 `Tweak.x` 文件第 44 行：

```objectivec
static NSString *serverURL = @"http://你的电脑IP:8888/bhv";  // 修改这里
```

例如：

```objectivec
static NSString *serverURL = @"http://192.168.1.100:8888/bhv";
```

3. 保存文件后，重新提交到 GitHub：

```bash
git add Tweak.x
git commit -m "Update server URL"
git push
```

4. 等待 GitHub Actions 重新编译
5. 下载新的 .deb 并重新安装到 iPhone

### 3. 测试 bhv 捕获

1. 确保 iPhone 和电脑在同一 WiFi 网络
2. 确保 Python 服务器正在运行
3. 打开云闪付，尝试领取优惠券
4. 当出现滑动验证码时，Tweak 会自动捕获 bhv 并发送到服务器
5. 服务器控制台会显示：

```
🎯 收到 bhv！ [2024-01-15 10:30:45]
设备: iPhone
长度: 256 字符
内容: P1A2B3C4D5E6F...
总计已捕获: 1 个 bhv
```

---

## 📊 查看捕获的 bhv

### 方法 1：查看文件

服务器会自动保存 bhv 到以下文件：

- **bhv_captured.json** - 所有历史记录
- **latest_bhv.txt** - 最新的一个 bhv

### 方法 2：通过浏览器

访问以下地址：

- http://你的电脑IP:8888/ - 首页，显示捕获数量
- http://你的电脑IP:8888/list - 查看所有 bhv
- http://你的电脑IP:8888/latest - 获取最新 bhv

---

## 🔄 修改代码后重新编译

每次修改 Tweak.x 后：

```bash
cd C:\Users\gao-huan\Desktop\云闪付

# 查看修改的文件
git status

# 添加修改
git add .

# 提交修改
git commit -m "描述你的修改"

# 推送到 GitHub（会自动触发编译）
git push
```

然后：

1. 访问 GitHub Actions 页面
2. 等待编译完成
3. 下载新的 .deb
4. 重新安装到 iPhone

---

## 🎯 快捷命令（使用 GitHub CLI）

如果安装了 `gh` 命令：

```bash
# 查看编译状态
gh run list

# 查看最新构建日志
gh run view --log

# 下载最新的 artifact
gh run download

# 打开仓库网页
gh repo view --web
```

---

## ❓ 常见问题

### 1. Actions 构建失败

检查：

- Makefile 语法是否正确
- Tweak.x 代码是否有语法错误
- 查看 Actions 日志的错误信息

### 2. iPhone 无法发送 bhv 到服务器

检查：

- iPhone 和电脑是否在同一 WiFi 网络
- 服务器是否正在运行
- Tweak.x 中的 serverURL 是否正确
- 电脑防火墙是否允许端口 8888
- 使用 iPhone Safari 访问 http://你的电脑IP:8888 测试连接

### 3. Tweak 没有加载

检查：

- .deb 是否安装成功
- UnionPayAuto.plist 中的 Bundle ID 是否正确（com.unionpay.chsp）
- 是否重启了云闪付 APP
- 使用日志工具查看是否有错误信息

### 4. 找不到 bhv 参数

检查：

- Hook 的类名和方法名是否正确
- 使用 Frida 或其他工具再次确认 API
- 查看 Tweak 日志，看是否成功 hook

---

## 📝 项目文件说明

```
云闪付/
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions 配置
├── Tweak.x                    # Tweak 源代码
├── Makefile                   # 编译配置
├── control                    # Debian 包信息
├── UnionPayAuto.plist        # 注入配置（Bundle ID）
├── bhv_server.py             # Python 接收服务器
└── GitHub编译指南.md          # 本文档
```

---

## 🎉 完成！

现在你已经配置好了完整的云闪付自动化系统：

✅ GitHub Actions 自动编译
✅ Tweak 自动捕获 bhv
✅ Python 服务器接收数据
✅ 完整的开发-编译-安装流程

祝使用愉快！
