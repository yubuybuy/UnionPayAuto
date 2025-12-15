#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云闪付自动领券脚本
基于HAR文件分析结果开发
仅供学习研究使用
"""

import requests
import time
import json
import random
import hashlib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('unionpay_auto.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置类"""
    # 活动配置
    ACTIVITY_ID = "17"
    CATE_CODE = "A07"
    AREA_CODE = "510099"  # 成都

    # 地理位置 (成都)
    LONGITUDE = "103.3986303710937"
    LATITUDE = "29.87659369574653"
    COORD_TYPE = "gcj02ll"

    # API端点
    BASE_URL = "https://scene.cup.com.cn"
    CAPTCHA_URL = "https://captcha.95516.com"

    # 设备信息
    DEVICE_ID = "55a5ccab50564d1cafcec81e1ec1c96f"
    DFP_ID = "110007D004q0cywc15357tJo4aKFa1764899981925"

    # 重试配置
    MAX_RETRY = 100  # 最大重试次数
    INIT_SESSION_INTERVAL = 1.0  # initses轮询间隔(秒)
    ACQUIRE_INTERVAL = 5.0  # 领券失败后的等待时间(秒)

    # User-Agent
    USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "/sa-sdk-ios/sensors-verify/analytics.95516.com?production   "
        "(com.unionpay.chsp) (cordova 4.5.4) (updebug 0) (version 1026) "
        "(UnionPay/1.0 CloudPay) (clientVersion 326) (language zh_CN) "
        "(languageFamily zh_CN) (upHtml) (walletMode 00)"
    )


class UnionPayCouponBot:
    """云闪付自动领券机器人"""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://scene.cup.com.cn',
        })

        # 统计信息
        self.stats = {
            'total_attempts': 0,
            'init_session_calls': 0,
            'captcha_solved': 0,
            'acquire_attempts': 0,
            'failures': {
                '1004': 0,  # 名额爆满
                '1000': 0,  # 操作频繁
                '0011': 0,  # 名额爆满(initses)
            },
            'start_time': datetime.now()
        }

    def init_session(self) -> Tuple[bool, str]:
        """
        初始化会话，检查名额状态

        Returns:
            (是否可以继续, 响应消息)
        """
        url = f"{self.config.BASE_URL}/gfmnewsc/appback/initses"

        try:
            self.stats['init_session_calls'] += 1
            response = self.session.post(url, json={}, timeout=10)
            response.raise_for_status()

            data = response.json()
            resp_cd = data.get('respCd', '')
            resp_msg = data.get('respMsg', '')

            logger.info(f"[InitSession] {resp_cd}: {resp_msg}")

            if resp_cd == '0000':
                return True, resp_msg
            elif resp_cd == '0011':
                self.stats['failures']['0011'] += 1
                return False, resp_msg
            else:
                return False, resp_msg

        except Exception as e:
            logger.error(f"[InitSession] 异常: {e}")
            return False, str(e)

    def get_captcha_token(self) -> Optional[Dict[str, str]]:
        """
        完成验证码流程，获取token和签名

        这里需要实现：
        1. 上传设备指纹
        2. 初始化验证码
        3. 识别/模拟滑动
        4. 验证并获取token

        Returns:
            {'sesId': xxx, 'token': xxx, 'sign': xxx} 或 None
        """
        try:
            # 步骤1: 生成会话ID
            ses_id = self._generate_session_id()

            # 步骤2: 上传设备指纹
            if not self._upload_device_fingerprint(ses_id):
                logger.error("[Captcha] 设备指纹上传失败")
                return None

            # 步骤3: 初始化验证码
            captcha_data = self._init_captcha(ses_id)
            if not captcha_data:
                logger.error("[Captcha] 验证码初始化失败")
                return None

            # 步骤4: 模拟滑动验证
            # 这里需要实现滑动验证码识别或模拟
            slide_result = self._simulate_slide(ses_id)
            if not slide_result:
                logger.error("[Captcha] 滑动验证失败")
                return None

            # 步骤5: 验证并获取token
            token_data = self._verify_captcha(ses_id, slide_result)
            if token_data:
                self.stats['captcha_solved'] += 1
                logger.info(f"[Captcha] 验证成功，获取到token")
                return {
                    'sesId': ses_id,
                    'token': token_data['token'],
                    'sign': token_data['sign']
                }

            return None

        except Exception as e:
            logger.error(f"[Captcha] 异常: {e}")
            return None

    def _generate_session_id(self) -> str:
        """生成验证码会话ID"""
        # 从HAR分析中看到sesId是32字节的十六进制字符串
        # 实际可能需要从服务器获取
        import uuid
        return ''.join(random.choices('0123456789abcdef', k=64))

    def _upload_device_fingerprint(self, ses_id: str) -> bool:
        """上传设备指纹"""
        url = f"{self.config.CAPTCHA_URL}/session/dfp"
        params = {
            'callback': f'jsonpCallback{int(time.time()*1000)}_{"".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=15))}',
            'sesId': ses_id,
            'dfpId': self.config.DFP_ID
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[DFP] 上传失败: {e}")
            return False

    def _init_captcha(self, ses_id: str) -> Optional[dict]:
        """初始化验证码"""
        url = f"{self.config.CAPTCHA_URL}/session/initspincap"
        params = {
            'callback': f'jsonpCallback{int(time.time()*1000)}_{"".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=15))}',
            'v': str(int(time.time() * 1000)),
            'cType': '3',
            'cVersion': '1.0.0',
            'sesId': ses_id
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # 从JSONP中提取JSON数据
                text = response.text
                json_str = text[text.find('(')+1:text.rfind(')')]
                return json.loads(json_str)
            return None
        except Exception as e:
            logger.error(f"[InitCaptcha] 失败: {e}")
            return None

    def _simulate_slide(self, ses_id: str) -> Optional[Dict]:
        """
        模拟滑动验证码

        TODO: 这里需要实现实际的验证码识别逻辑
        可选方案：
        1. 使用OCR识别缺口位置
        2. 使用机器学习模型
        3. 人工打码平台API
        4. 模拟真实滑动轨迹
        """
        # 模拟人类滑动时间: 1-2秒
        pass_time = random.randint(1000, 2000)

        # 模拟滑动距离: 通常在50-300之间
        slide_value = random.uniform(65.0, 299.0)

        # 模拟行为轨迹（这里需要生成真实的轨迹数据）
        # 实际的bhv参数是加密的鼠标轨迹数据
        behavior = self._generate_slide_behavior(slide_value, pass_time)

        return {
            'passTime': pass_time,
            'value': slide_value,
            'bhv': behavior
        }

    def _generate_slide_behavior(self, distance: float, duration: int) -> str:
        """
        生成滑动行为轨迹

        TODO: 需要逆向分析实际的加密算法
        从HAR中看到的格式如: "P(/.112/00///,--,,---,**,)*))*,)*)*),)))..."
        这是加密后的轨迹数据，需要研究具体算法
        """
        # 这里返回一个占位符
        # 实际需要根据云闪付的加密算法生成
        return "P" + "".join(random.choices("()*-.,/0123456789:;?@ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=200))

    def _verify_captcha(self, ses_id: str, slide_data: Dict) -> Optional[Dict]:
        """验证验证码并获取token"""
        url = f"{self.config.CAPTCHA_URL}/session/vfy"
        params = {
            'callback': f'jsonpCallback{int(time.time()*1000)}_{"".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=15))}',
            'v': str(int(time.time() * 1000)),
            'sesId': ses_id,
            'passTime': slide_data['passTime'],
            'value': slide_data['value'],
            'bhv': slide_data['bhv']
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # 从JSONP中提取JSON数据
                text = response.text
                json_str = text[text.find('(')+1:text.rfind(')')]
                data = json.loads(json_str)

                if data.get('resCode') == '0000':
                    res_data = data.get('resData', {})
                    return {
                        'token': res_data.get('token'),
                        'sign': res_data.get('sign')
                    }
            return None
        except Exception as e:
            logger.error(f"[VerifyCaptcha] 失败: {e}")
            return None

    def acquire_coupon(self, captcha_info: Dict) -> Tuple[bool, str]:
        """
        领取优惠券

        Args:
            captcha_info: 验证码信息 {'sesId', 'token', 'sign'}

        Returns:
            (是否成功, 响应消息)
        """
        url = f"{self.config.BASE_URL}/gfmnewsc/appback/couponAcquire"

        payload = {
            "areaCode": self.config.AREA_CODE,
            "longitude": self.config.LONGITUDE,
            "latitude": self.config.LATITUDE,
            "acquireType": "1",
            "cateCode": self.config.CATE_CODE,
            "activityId": self.config.ACTIVITY_ID,
            "engGrade": None,
            "coordType": self.config.COORD_TYPE,
            "capSesId": captcha_info['sesId'],
            "capToken": captcha_info['token'],
            "capSign": captcha_info['sign']
        }

        try:
            self.stats['acquire_attempts'] += 1
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            resp_cd = data.get('respCd', '')
            resp_msg = data.get('respMsg', '')

            logger.info(f"[AcquireCoupon] {resp_cd}: {resp_msg}")

            # 更新失败统计
            if resp_cd in self.stats['failures']:
                self.stats['failures'][resp_cd] += 1

            # 检查是否成功
            if resp_cd == '0000' or '成功' in resp_msg:
                return True, resp_msg
            else:
                return False, resp_msg

        except Exception as e:
            logger.error(f"[AcquireCoupon] 异常: {e}")
            return False, str(e)

    def run(self):
        """主运行循环"""
        logger.info("=" * 80)
        logger.info("云闪付自动领券脚本启动")
        logger.info(f"活动ID: {self.config.ACTIVITY_ID}")
        logger.info(f"类别代码: {self.config.CATE_CODE}")
        logger.info(f"最大重试次数: {self.config.MAX_RETRY}")
        logger.info("=" * 80)

        retry_count = 0

        while retry_count < self.config.MAX_RETRY:
            self.stats['total_attempts'] += 1
            retry_count += 1

            logger.info(f"\n{'='*80}")
            logger.info(f"第 {retry_count}/{self.config.MAX_RETRY} 次尝试")
            logger.info(f"{'='*80}")

            # 步骤1: 检查会话状态，等待名额
            logger.info("[Step 1] 检查名额状态...")
            while True:
                can_continue, msg = self.init_session()
                if can_continue:
                    logger.info("[Step 1] ✓ 检测到名额，可以继续")
                    break
                else:
                    logger.info(f"[Step 1] ✗ {msg}，等待中...")
                    time.sleep(self.config.INIT_SESSION_INTERVAL)

            # 步骤2: 完成验证码
            logger.info("[Step 2] 处理验证码...")
            captcha_info = self.get_captcha_token()
            if not captcha_info:
                logger.warning("[Step 2] ✗ 验证码处理失败，跳过本次")
                time.sleep(self.config.ACQUIRE_INTERVAL)
                continue

            logger.info("[Step 2] ✓ 验证码处理成功")

            # 步骤3: 领取优惠券
            logger.info("[Step 3] 尝试领取优惠券...")
            success, msg = self.acquire_coupon(captcha_info)

            if success:
                logger.info(f"[Step 3] ✓✓✓ 领取成功！{msg}")
                self._print_stats()
                return True
            else:
                logger.warning(f"[Step 3] ✗ 领取失败: {msg}")

                # 根据失败原因调整等待时间
                if '频繁' in msg:
                    wait_time = random.uniform(8, 12)
                    logger.info(f"检测到频率限制，等待 {wait_time:.1f} 秒...")
                elif '名额' in msg or '爆满' in msg:
                    wait_time = self.config.ACQUIRE_INTERVAL
                    logger.info(f"名额已满，等待 {wait_time:.1f} 秒后重试...")
                else:
                    wait_time = random.uniform(3, 6)

                time.sleep(wait_time)

        logger.info("\n" + "=" * 80)
        logger.info(f"已达到最大重试次数 ({self.config.MAX_RETRY})，停止运行")
        logger.info("=" * 80)
        self._print_stats()
        return False

    def _print_stats(self):
        """打印统计信息"""
        elapsed = datetime.now() - self.stats['start_time']

        logger.info("\n" + "=" * 80)
        logger.info("运行统计")
        logger.info("=" * 80)
        logger.info(f"运行时长: {elapsed}")
        logger.info(f"总尝试次数: {self.stats['total_attempts']}")
        logger.info(f"InitSession调用: {self.stats['init_session_calls']}")
        logger.info(f"验证码成功次数: {self.stats['captcha_solved']}")
        logger.info(f"领券尝试次数: {self.stats['acquire_attempts']}")
        logger.info(f"\n失败统计:")
        logger.info(f"  - 名额爆满(1004): {self.stats['failures']['1004']}")
        logger.info(f"  - 操作频繁(1000): {self.stats['failures']['1000']}")
        logger.info(f"  - 名额爆满(0011): {self.stats['failures']['0011']}")
        logger.info("=" * 80)


def main():
    """主函数"""
    # 创建配置
    config = Config()

    # 创建机器人实例
    bot = UnionPayCouponBot(config)

    try:
        # 运行
        success = bot.run()

        if success:
            logger.info("\n🎉 任务完成！优惠券领取成功！")
            return 0
        else:
            logger.info("\n😔 任务未完成，请检查日志")
            return 1

    except KeyboardInterrupt:
        logger.info("\n\n用户中断运行")
        bot._print_stats()
        return 2
    except Exception as e:
        logger.error(f"\n\n发生异常: {e}", exc_info=True)
        bot._print_stats()
        return 3


if __name__ == "__main__":
    exit(main())
