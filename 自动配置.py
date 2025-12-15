#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动配置脚本
帮助自动获取IP并更新Tweak.x配置
"""

import socket
import re
import os
import sys

def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None

def update_tweak_config(ip_address):
    """更新Tweak.x中的服务器地址"""
    tweak_file = "Tweak.x"

    if not os.path.exists(tweak_file):
        print(f"❌ 错误：找不到 {tweak_file}")
        return False

    try:
        with open(tweak_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换IP地址
        new_url = f"http://{ip_address}:8888/bhv"
        pattern = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:8888/bhv'
        new_content = re.sub(pattern, new_url, content)

        with open(tweak_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ 已更新服务器地址为: {new_url}")
        return True

    except Exception as e:
        print(f"❌ 更新失败: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("  云闪付 Tweak - 自动配置脚本")
    print("="*60 + "\n")

    # 获取本机IP
    print("🔍 正在获取本机 IP 地址...")
    ip = get_local_ip()

    if ip:
        print(f"✅ 检测到 IP: {ip}")
        print()

        # 确认
        confirm = input(f"是否使用此 IP 更新配置？(y/n) [y]: ").strip().lower()
        if confirm == '' or confirm == 'y':
            if update_tweak_config(ip):
                print()
                print("="*60)
                print("  配置完成！")
                print("="*60)
                print()
                print(f"服务器地址已设置为: http://{ip}:8888/bhv")
                print()
                print("下一步：")
                print("1. 运行 bhv_server.py 启动接收服务器")
                print("2. 推送代码到 GitHub（会自动编译）")
                print("3. 下载 .deb 并安装到 iPhone")
                print()
            else:
                print("❌ 配置失败")
                sys.exit(1)
        else:
            # 手动输入
            manual_ip = input("请输入 IP 地址: ").strip()
            if manual_ip:
                if update_tweak_config(manual_ip):
                    print(f"✅ 配置完成！服务器地址: http://{manual_ip}:8888/bhv")
                else:
                    print("❌ 配置失败")
                    sys.exit(1)
            else:
                print("❌ IP 地址不能为空")
                sys.exit(1)
    else:
        print("❌ 无法自动获取 IP 地址")
        print()
        manual_ip = input("请手动输入 IP 地址: ").strip()
        if manual_ip:
            if update_tweak_config(manual_ip):
                print(f"✅ 配置完成！服务器地址: http://{manual_ip}:8888/bhv")
            else:
                print("❌ 配置失败")
                sys.exit(1)
        else:
            print("❌ IP 地址不能为空")
            sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
