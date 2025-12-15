#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云闪付自动化控制器
通过Frida RPC控制自动化Hook脚本
"""

import frida
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime


class UnionPayController:
    """云闪付自动化控制器"""

    def __init__(self):
        self.device = None
        self.session = None
        self.script = None
        self.bhv_log_file = Path("bhv_history.json")
        self.bhv_history = []

        # 创建日志目录
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

    def connect(self, app_name="云闪付"):
        """连接到应用"""
        print(f"[*] 连接到USB设备...")
        try:
            self.device = frida.get_usb_device()
            print(f"[+] 设备: {self.device}")
        except Exception as e:
            print(f"[-] 连接失败: {e}")
            return False

        print(f"[*] 附加到: {app_name}")
        try:
            self.session = self.device.attach(app_name)
            print(f"[+] 已附加")
            return True
        except Exception as e:
            print(f"[-] 附加失败: {e}")
            return False

    def load_advanced_hook(self):
        """加载高级Hook脚本"""
        script_path = Path("frida_advanced_hook.js")

        if not script_path.exists():
            print(f"[-] 脚本不存在: {script_path}")
            return False

        print(f"[*] 加载脚本...")
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()

        self.script = self.session.create_script(code)
        self.script.on('message', self._on_message)
        self.script.load()

        print(f"[+] 脚本已加载\n")
        return True

    def _on_message(self, message, data):
        """处理脚本消息"""
        if message['type'] == 'send':
            payload = message['payload']
            msg_type = payload.get('type', '')

            if msg_type == 'bhv_captured':
                # 保存bhv
                self._save_bhv(payload)

            elif msg_type == 'captcha_success':
                print("\n[✅] 验证码验证成功！")
                print("[*] 可以继续领券流程...\n")

            elif msg_type == 'network_request':
                url = payload.get('url', '')
                method = payload.get('method', 'GET')
                print(f"[🌐] {method} {url}")

            elif msg_type == 'button_clicked':
                title = payload.get('title', '')
                print(f"[🔘] 按钮点击: {title}")

            else:
                # 其他消息直接打印
                print(f"[脚本] {payload}")

        elif message['type'] == 'error':
            print(f"[❌] {message['stack']}")

    def _save_bhv(self, bhv_data):
        """保存bhv到文件"""
        timestamp = bhv_data.get('timestamp', datetime.now().isoformat())
        bhv = bhv_data.get('bhv', '')

        # 添加到历史
        self.bhv_history.append({
            'timestamp': timestamp,
            'bhv': bhv,
            'length': len(bhv)
        })

        # 保存到JSON文件
        with open(self.bhv_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.bhv_history, f, indent=2, ensure_ascii=False)

        print(f"\n[💾] 已保存bhv #{len(self.bhv_history)}")
        print(f"[💾] 文件: {self.bhv_log_file}")
        print(f"[💾] 长度: {len(bhv)}")
        print(f"[💾] 预览: {bhv[:80]}...\n")

    def click_acquire_button(self):
        """点击领券按钮"""
        if not self.script:
            print("[-] 脚本未加载")
            return False

        print("[*] 触发领券按钮点击...")
        try:
            result = self.script.exports.click_acquire_button()
            if result:
                print("[+] 已触发点击")
                return True
            else:
                print("[-] 未找到领券按钮")
                return False
        except Exception as e:
            print(f"[-] 调用失败: {e}")
            return False

    def get_bhv_history(self):
        """获取bhv历史"""
        if not self.script:
            print("[-] 脚本未加载")
            return []

        try:
            history = self.script.exports.get_bhv_history()
            print(f"\n[*] bhv历史记录: {len(history)} 条")

            for i, item in enumerate(history, 1):
                print(f"\n[{i}] {item['timestamp']}")
                print(f"    长度: {item['length']}")
                print(f"    内容: {item['bhv'][:60]}...")

            return history

        except Exception as e:
            print(f"[-] 获取失败: {e}")
            return []

    def set_config(self, key, value):
        """设置配置"""
        if not self.script:
            print("[-] 脚本未加载")
            return False

        try:
            result = self.script.exports.set_config(key, value)
            if result:
                print(f"[+] 配置已更新: {key} = {value}")
                return True
            else:
                print(f"[-] 无效的配置项: {key}")
                return False
        except Exception as e:
            print(f"[-] 设置失败: {e}")
            return False

    def get_config(self):
        """获取当前配置"""
        if not self.script:
            print("[-] 脚本未加载")
            return None

        try:
            config = self.script.exports.get_config()
            print("\n当前配置:")
            print(json.dumps(config, indent=2))
            return config
        except Exception as e:
            print(f"[-] 获取失败: {e}")
            return None

    def interactive_mode(self):
        """交互模式"""
        print("\n" + "="*60)
        print("云闪付自动化控制台")
        print("="*60)
        print("\n命令列表:")
        print("  click   - 点击领券按钮")
        print("  bhv     - 查看bhv历史")
        print("  config  - 查看配置")
        print("  set     - 设置配置 (用法: set key value)")
        print("  help    - 显示帮助")
        print("  quit    - 退出")
        print("\n直接操作APP即可触发自动化逻辑\n")

        while True:
            try:
                cmd = input(">>> ").strip()

                if not cmd:
                    continue

                parts = cmd.split()
                command = parts[0].lower()

                if command == 'quit' or command == 'exit':
                    break

                elif command == 'click':
                    self.click_acquire_button()

                elif command == 'bhv':
                    self.get_bhv_history()

                elif command == 'config':
                    self.get_config()

                elif command == 'set':
                    if len(parts) < 3:
                        print("用法: set <key> <value>")
                    else:
                        key = parts[1]
                        value = parts[2]

                        # 尝试转换为正确的类型
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)

                        self.set_config(key, value)

                elif command == 'help':
                    print("\n命令列表:")
                    print("  click   - 点击领券按钮")
                    print("  bhv     - 查看bhv历史")
                    print("  config  - 查看配置")
                    print("  set     - 设置配置")
                    print("  help    - 显示帮助")
                    print("  quit    - 退出\n")

                else:
                    print(f"未知命令: {command}")
                    print("输入 'help' 查看帮助\n")

            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"错误: {e}")

    def auto_mode(self):
        """自动模式（监控并自动处理）"""
        print("\n[*] 自动模式启动")
        print("[*] 脚本将自动监控并处理验证码")
        print("[*] 按 Ctrl+C 退出\n")

        try:
            sys.stdin.read()
        except KeyboardInterrupt:
            print("\n[*] 退出自动模式")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='云闪付自动化控制器')
    parser.add_argument('-a', '--app',
                       default='云闪付',
                       help='应用名称')
    parser.add_argument('-m', '--mode',
                       choices=['interactive', 'auto'],
                       default='interactive',
                       help='运行模式')

    args = parser.parse_args()

    controller = UnionPayController()

    try:
        # 连接
        if not controller.connect(args.app):
            return 1

        # 加载脚本
        if not controller.load_advanced_hook():
            return 1

        # 运行模式
        if args.mode == 'interactive':
            controller.interactive_mode()
        else:
            controller.auto_mode()

    except Exception as e:
        print(f"\n[!] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        print("\n[*] 清理资源...")
        if controller.script:
            controller.script.unload()
        if controller.session:
            controller.session.detach()

        print("[*] 再见！")

    return 0


if __name__ == '__main__':
    sys.exit(main())
