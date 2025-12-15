#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BHV 接收服务器
用于接收 Tweak 发送的 bhv 参数

使用方法：
1. 修改 IP 地址为你电脑的局域网 IP
2. 运行: python bhv_server.py
3. 确保 iPhone 和电脑在同一局域网
4. 在 Tweak.x 中修改 serverURL 为你的电脑 IP
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime
import os

app = Flask(__name__)

# 保存 bhv 的文件
BHV_LOG_FILE = "bhv_captured.json"
BHV_HISTORY = []

# 加载历史记录
if os.path.exists(BHV_LOG_FILE):
    try:
        with open(BHV_LOG_FILE, 'r', encoding='utf-8') as f:
            BHV_HISTORY = json.load(f)
    except:
        BHV_HISTORY = []


@app.route('/bhv', methods=['POST'])
def receive_bhv():
    """接收 bhv 参数"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        bhv = data.get('bhv')
        timestamp = data.get('timestamp')
        device = data.get('device', 'unknown')

        if not bhv:
            return jsonify({"status": "error", "message": "No bhv in data"}), 400

        # 记录数据
        record = {
            "bhv": bhv,
            "timestamp": timestamp,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device": device,
            "length": len(bhv)
        }

        BHV_HISTORY.append(record)

        # 保存到文件
        with open(BHV_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(BHV_HISTORY, f, indent=2, ensure_ascii=False)

        # 打印到控制台
        print("\n" + "="*60)
        print(f"🎯 收到 bhv！ [{record['datetime']}]")
        print("="*60)
        print(f"设备: {device}")
        print(f"长度: {len(bhv)} 字符")
        print(f"内容: {bhv[:100]}..." if len(bhv) > 100 else f"内容: {bhv}")
        print("="*60)
        print(f"总计已捕获: {len(BHV_HISTORY)} 个 bhv")
        print("="*60 + "\n")

        # 保存最新的 bhv 到单独文件（方便其他程序读取）
        with open('latest_bhv.txt', 'w', encoding='utf-8') as f:
            f.write(bhv)

        return jsonify({
            "status": "success",
            "message": "bhv received",
            "count": len(BHV_HISTORY)
        }), 200

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/list', methods=['GET'])
def list_bhv():
    """查看所有捕获的 bhv"""
    return jsonify({
        "count": len(BHV_HISTORY),
        "history": BHV_HISTORY
    })


@app.route('/latest', methods=['GET'])
def get_latest():
    """获取最新的 bhv"""
    if BHV_HISTORY:
        return jsonify({
            "status": "success",
            "data": BHV_HISTORY[-1]
        })
    else:
        return jsonify({
            "status": "error",
            "message": "No bhv captured yet"
        }), 404


@app.route('/clear', methods=['POST'])
def clear_history():
    """清空历史记录"""
    global BHV_HISTORY
    BHV_HISTORY = []

    with open(BHV_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

    return jsonify({"status": "success", "message": "History cleared"})


@app.route('/', methods=['GET'])
def index():
    """首页"""
    return f"""
    <h1>BHV 接收服务器</h1>
    <p>运行中...</p>
    <p>已捕获: {len(BHV_HISTORY)} 个 bhv</p>
    <hr>
    <ul>
        <li><a href="/list">查看所有 bhv</a></li>
        <li><a href="/latest">获取最新 bhv</a></li>
    </ul>
    """


def get_local_ip():
    """获取本地 IP 地址"""
    import socket
    try:
        # 创建一个 UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到外部地址（不会真正发送数据）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 8888

    print("\n" + "="*60)
    print("🚀 BHV 接收服务器启动")
    print("="*60)
    print(f"本地地址: http://{local_ip}:{port}")
    print(f"接收地址: http://{local_ip}:{port}/bhv")
    print("="*60)
    print("\n请在 Tweak.x 中将 serverURL 修改为:")
    print(f'  static NSString *serverURL = @"http://{local_ip}:{port}/bhv";')
    print("\n" + "="*60 + "\n")

    # 启动服务器
    app.run(host='0.0.0.0', port=port, debug=False)
