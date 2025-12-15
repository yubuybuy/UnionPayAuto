#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云闪付Frida分析助手
自动运行Frida脚本并保存结果
"""

import frida
import sys
import json
import time
from pathlib import Path

class UnionPayAnalyzer:
    """云闪付分析器"""

    def __init__(self):
        self.device = None
        self.session = None
        self.script = None

    def connect(self, app_name="云闪付"):
        """连接到设备和应用"""
        print(f"[*] 连接到USB设备...")
        try:
            self.device = frida.get_usb_device()
            print(f"[+] 设备已连接: {self.device}")
        except Exception as e:
            print(f"[-] 连接失败: {e}")
            print("[!] 请确保:")
            print("    1. 手机已通过USB连接")
            print("    2. 已安装Frida Server")
            print("    3. Frida Server正在运行")
            return False

        print(f"[*] 附加到应用: {app_name}...")
        try:
            self.session = self.device.attach(app_name)
            print(f"[+] 已附加到应用")
            return True
        except frida.ProcessNotFoundError:
            print(f"[-] 未找到应用: {app_name}")
            print("[!] 请先打开云闪付APP")
            return False
        except Exception as e:
            print(f"[-] 附加失败: {e}")
            return False

    def load_script(self, script_path):
        """加载并运行Frida脚本"""
        print(f"[*] 加载脚本: {script_path}")

        script_file = Path(script_path)
        if not script_file.exists():
            print(f"[-] 脚本文件不存在: {script_path}")
            return False

        with open(script_file, 'r', encoding='utf-8') as f:
            script_code = f.read()

        print(f"[*] 创建脚本...")
        self.script = self.session.create_script(script_code)

        # 设置消息处理器
        self.script.on('message', self._on_message)

        print(f"[*] 加载脚本...")
        self.script.load()
        print(f"[+] 脚本已加载并运行\n")

        return True

    def _on_message(self, message, data):
        """处理脚本发来的消息"""
        if message['type'] == 'send':
            payload = message.get('payload', '')
            print(f"[脚本] {payload}")
        elif message['type'] == 'error':
            print(f"[错误] {message['stack']}")

    def dump_classes(self, output_file='class_dump.json'):
        """导出类信息"""
        if not self.script:
            print("[-] 脚本未加载")
            return

        print("[*] 调用 dumpClasses()...")
        try:
            result = self.script.exports.dump_classes()

            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"[+] 类信息已保存到: {output_path}")

        except Exception as e:
            print(f"[-] 导出失败: {e}")

    def run(self):
        """保持运行"""
        print("\n" + "="*60)
        print("脚本正在运行，按 Ctrl+C 退出")
        print("="*60 + "\n")

        try:
            sys.stdin.read()
        except KeyboardInterrupt:
            print("\n[*] 用户中断")

    def cleanup(self):
        """清理资源"""
        if self.script:
            self.script.unload()
        if self.session:
            self.session.detach()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='云闪付Frida分析助手')
    parser.add_argument('-s', '--script',
                       default='frida_captcha_observer.js',
                       help='Frida脚本文件路径')
    parser.add_argument('-a', '--app',
                       default='云闪付',
                       help='应用名称')
    parser.add_argument('-o', '--output',
                       default='class_dump.json',
                       help='输出文件路径')
    parser.add_argument('-d', '--dump',
                       action='store_true',
                       help='导出类信息并退出')

    args = parser.parse_args()

    analyzer = UnionPayAnalyzer()

    try:
        # 连接
        if not analyzer.connect(args.app):
            return 1

        # 加载脚本
        if not analyzer.load_script(args.script):
            return 1

        # 导出模式
        if args.dump:
            time.sleep(2)  # 等待脚本初始化
            analyzer.dump_classes(args.output)
            return 0

        # 持续运行
        analyzer.run()

    except Exception as e:
        print(f"\n[!] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        analyzer.cleanup()

    return 0


if __name__ == '__main__':
    sys.exit(main())
