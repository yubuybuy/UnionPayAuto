#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAR文件解析工具
从HAR文件中提取配置信息（Cookie、设备指纹等）
"""

import json
import sys
import re
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse


class HARParser:
    """HAR文件解析器"""

    def __init__(self, har_file_path: str):
        """
        初始化解析器

        Args:
            har_file_path: HAR文件路径
        """
        self.har_file_path = har_file_path
        self.data = None
        self.load_har()

    def load_har(self):
        """加载HAR文件"""
        try:
            with open(self.har_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✓ 成功加载HAR文件: {self.har_file_path}")
        except Exception as e:
            print(f"✗ 加载HAR文件失败: {e}")
            sys.exit(1)

    def get_entries(self):
        """获取所有请求记录"""
        if self.data:
            return self.data.get('log', {}).get('entries', [])
        return []

    def extract_cookies(self) -> Dict[str, str]:
        """提取Cookie"""
        cookies = {}
        entries = self.get_entries()

        for entry in entries:
            # 从请求中提取
            request_cookies = entry.get('request', {}).get('cookies', [])
            for cookie in request_cookies:
                name = cookie.get('name')
                value = cookie.get('value')
                if name and value:
                    cookies[name] = value

            # 从响应中提取Set-Cookie
            response_cookies = entry.get('response', {}).get('cookies', [])
            for cookie in response_cookies:
                name = cookie.get('name')
                value = cookie.get('value')
                if name and value:
                    cookies[name] = value

        print(f"\n✓ 提取到 {len(cookies)} 个Cookie:")
        for name, value in list(cookies.items())[:5]:
            print(f"  - {name}: {value[:30]}...")

        return cookies

    def extract_device_info(self) -> Dict[str, str]:
        """提取设备信息"""
        device_info = {
            'device_id': None,
            'dfp_id': None,
            'user_agent': None
        }

        entries = self.get_entries()

        for entry in entries:
            url = entry.get('request', {}).get('url', '')

            # 提取设备ID
            if 'did=' in url and not device_info['device_id']:
                match = re.search(r'did=([a-f0-9]+)', url)
                if match:
                    device_info['device_id'] = match.group(1)

            # 提取设备指纹ID
            if 'dfpId=' in url and not device_info['dfp_id']:
                match = re.search(r'dfpId=([A-Za-z0-9]+)', url)
                if match:
                    device_info['dfp_id'] = match.group(1)

            # 提取User-Agent
            if not device_info['user_agent']:
                headers = entry.get('request', {}).get('headers', [])
                for header in headers:
                    if header.get('name', '').lower() == 'user-agent':
                        device_info['user_agent'] = header.get('value')
                        break

        print(f"\n✓ 提取到设备信息:")
        print(f"  - Device ID: {device_info['device_id']}")
        print(f"  - DFP ID: {device_info['dfp_id']}")
        print(f"  - User-Agent: {device_info['user_agent'][:50] if device_info['user_agent'] else None}...")

        return device_info

    def extract_location_info(self) -> Dict[str, str]:
        """提取地理位置信息"""
        location_info = {
            'area_code': None,
            'longitude': None,
            'latitude': None
        }

        entries = self.get_entries()

        for entry in entries:
            if 'couponAcquire' in entry.get('request', {}).get('url', ''):
                post_data = entry.get('request', {}).get('postData', {}).get('text', '')
                if post_data:
                    try:
                        data = json.loads(post_data)
                        location_info['area_code'] = data.get('areaCode')
                        location_info['longitude'] = data.get('longitude')
                        location_info['latitude'] = data.get('latitude')
                        break
                    except:
                        pass

        print(f"\n✓ 提取到位置信息:")
        print(f"  - Area Code: {location_info['area_code']}")
        print(f"  - Longitude: {location_info['longitude']}")
        print(f"  - Latitude: {location_info['latitude']}")

        return location_info

    def extract_activity_info(self) -> Dict[str, str]:
        """提取活动信息"""
        activity_info = {
            'activity_id': None,
            'cate_code': None
        }

        entries = self.get_entries()

        for entry in entries:
            if 'couponAcquire' in entry.get('request', {}).get('url', ''):
                post_data = entry.get('request', {}).get('postData', {}).get('text', '')
                if post_data:
                    try:
                        data = json.loads(post_data)
                        activity_info['activity_id'] = data.get('activityId')
                        activity_info['cate_code'] = data.get('cateCode')
                        break
                    except:
                        pass

        print(f"\n✓ 提取到活动信息:")
        print(f"  - Activity ID: {activity_info['activity_id']}")
        print(f"  - Cate Code: {activity_info['cate_code']}")

        return activity_info

    def extract_all(self) -> Dict:
        """提取所有配置信息"""
        print("\n" + "=" * 80)
        print("开始解析HAR文件...")
        print("=" * 80)

        config = {
            'cookies': self.extract_cookies(),
            'device': self.extract_device_info(),
            'location': self.extract_location_info(),
            'activity': self.extract_activity_info()
        }

        print("\n" + "=" * 80)
        print("解析完成！")
        print("=" * 80)

        return config

    def generate_config_file(self, output_path: str = 'extracted_config.py'):
        """生成配置文件"""
        config = self.extract_all()

        config_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从HAR文件自动提取的配置
生成时间: {__import__('datetime').datetime.now()}
HAR文件: {self.har_file_path}
"""

# 活动配置
ACTIVITY_ID = "{config['activity']['activity_id']}"
CATE_CODE = "{config['activity']['cate_code']}"
AREA_CODE = "{config['location']['area_code']}"

# 地理位置
LONGITUDE = "{config['location']['longitude']}"
LATITUDE = "{config['location']['latitude']}"

# 设备信息
DEVICE_ID = "{config['device']['device_id']}"
DFP_ID = "{config['device']['dfp_id']}"

# User-Agent
USER_AGENT = """{config['device']['user_agent']}"""

# Cookie
COOKIES = {{
'''

        for name, value in config['cookies'].items():
            config_content += f'    "{name}": "{value}",\n'

        config_content += '''}

# 运行配置
MAX_RETRY = 100
INIT_SESSION_INTERVAL = 1.0
ACQUIRE_INTERVAL = 5.0
'''

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"\n✓ 配置文件已生成: {output_path}")
        except Exception as e:
            print(f"\n✗ 生成配置文件失败: {e}")

    def analyze_captcha_flow(self):
        """分析验证码流程"""
        print("\n" + "=" * 80)
        print("分析验证码流程...")
        print("=" * 80)

        entries = self.get_entries()
        captcha_entries = []

        for entry in entries:
            url = entry['request']['url']
            if any(keyword in url for keyword in ['dfp', 'initspincap', 'vfy', 'captcha']):
                captcha_entries.append({
                    'time': entry['startedDateTime'],
                    'url': url,
                    'method': entry['request']['method']
                })

        print(f"\n找到 {len(captcha_entries)} 个验证码相关请求:")
        for i, entry in enumerate(captcha_entries[:10], 1):
            print(f"{i}. {entry['time']} - {entry['url'][:80]}")

        return captcha_entries


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='HAR文件解析工具')
    parser.add_argument('har_file', help='HAR文件路径')
    parser.add_argument(
        '--output',
        '-o',
        default='extracted_config.py',
        help='输出配置文件路径（默认: extracted_config.py）'
    )
    parser.add_argument(
        '--analyze-captcha',
        action='store_true',
        help='分析验证码流程'
    )

    args = parser.parse_args()

    # 创建解析器
    parser = HARParser(args.har_file)

    # 生成配置文件
    parser.generate_config_file(args.output)

    # 分析验证码流程（如果需要）
    if args.analyze_captcha:
        parser.analyze_captcha_flow()

    print("\n使用方法:")
    print(f"  1. 复制 {args.output} 中的配置到 config.py")
    print(f"  2. 运行主脚本: python unionpay_auto.py")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python har_parser.py <har文件路径>")
        print("示例: python har_parser.py ProxyPin12-5_10_07_00.har")
        sys.exit(1)

    main()
