#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码处理模块
支持多种验证码识别方案
"""

import io
import base64
import requests
from PIL import Image
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """验证码解决器基类"""

    def solve(self, image_url: str) -> Optional[Dict]:
        """
        解决验证码

        Args:
            image_url: 验证码图片URL

        Returns:
            {'distance': float, 'track': list} 或 None
        """
        raise NotImplementedError


class DDDDOCRSolver(CaptchaSolver):
    """使用ddddocr库识别滑块验证码"""

    def __init__(self):
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
            logger.info("[DDDDOCR] 初始化成功")
        except ImportError:
            logger.error("[DDDDOCR] 未安装ddddocr库，请运行: pip install ddddocr")
            self.ocr = None

    def solve(self, bg_image: bytes, slide_image: bytes) -> Optional[Dict]:
        """
        识别滑块缺口位置

        Args:
            bg_image: 背景图片字节
            slide_image: 滑块图片字节

        Returns:
            滑动信息
        """
        if not self.ocr:
            return None

        try:
            # 识别缺口位置
            result = self.ocr.slide_match(slide_image, bg_image)
            distance = result.get('target', [0])[0]

            logger.info(f"[DDDDOCR] 识别到缺口位置: {distance}px")

            # 生成滑动轨迹
            track = self._generate_track(distance)

            return {
                'distance': distance,
                'track': track
            }

        except Exception as e:
            logger.error(f"[DDDDOCR] 识别失败: {e}")
            return None

    def _generate_track(self, distance: float) -> list:
        """
        生成滑动轨迹（模拟人类滑动）

        Args:
            distance: 目标距离

        Returns:
            轨迹点列表 [(x, y, t), ...]
        """
        import random
        import math

        track = []
        current = 0
        mid = distance * 0.8  # 80%处开始减速
        t = 0
        v = 0

        while current < distance:
            if current < mid:
                # 加速阶段
                a = random.uniform(2, 4)
            else:
                # 减速阶段
                a = -random.uniform(3, 5)

            v0 = v
            v = v0 + a
            move = v0 + 0.5 * a
            current += move

            # 添加一些随机抖动
            y_offset = random.randint(-2, 2)

            track.append((int(current), y_offset, t))
            t += random.randint(10, 20)  # 毫秒

        return track


class ManualSolver(CaptchaSolver):
    """手动处理验证码"""

    def solve(self, image_url: str) -> Optional[Dict]:
        """
        手动输入滑动距离

        Args:
            image_url: 验证码图片URL

        Returns:
            滑动信息
        """
        print(f"\n验证码图片URL: {image_url}")
        print("请手动打开图片，观察缺口位置")

        try:
            distance = float(input("请输入滑动距离(px): "))
            return {
                'distance': distance,
                'track': self._generate_simple_track(distance)
            }
        except ValueError:
            logger.error("[Manual] 输入无效")
            return None

    def _generate_simple_track(self, distance: float) -> list:
        """生成简单轨迹"""
        import random
        track = []
        step = 5
        t = 0
        for x in range(0, int(distance), step):
            track.append((x, random.randint(-2, 2), t))
            t += random.randint(15, 25)
        track.append((int(distance), 0, t))
        return track


class ThirdPartySolver(CaptchaSolver):
    """第三方打码平台"""

    def __init__(self, api_key: str, platform: str = "yescaptcha"):
        self.api_key = api_key
        self.platform = platform
        logger.info(f"[ThirdParty] 使用 {platform} 打码平台")

    def solve(self, image_bytes: bytes) -> Optional[Dict]:
        """
        调用第三方API识别

        Args:
            image_bytes: 图片字节

        Returns:
            滑动信息
        """
        if self.platform == "yescaptcha":
            return self._solve_yescaptcha(image_bytes)
        else:
            logger.error(f"[ThirdParty] 不支持的平台: {self.platform}")
            return None

    def _solve_yescaptcha(self, image_bytes: bytes) -> Optional[Dict]:
        """YesCaptcha平台识别"""
        # TODO: 实现实际的API调用
        logger.warning("[YesCaptcha] 功能暂未实现")
        return None


class CaptchaManager:
    """验证码管理器"""

    def __init__(self, solver_type: str = "ddddocr", **kwargs):
        """
        初始化验证码管理器

        Args:
            solver_type: 解决器类型 (ddddocr, manual, thirdparty)
            **kwargs: 额外参数
        """
        self.solver = self._create_solver(solver_type, **kwargs)

    def _create_solver(self, solver_type: str, **kwargs) -> CaptchaSolver:
        """创建解决器"""
        if solver_type == "ddddocr":
            return DDDDOCRSolver()
        elif solver_type == "manual":
            return ManualSolver()
        elif solver_type == "thirdparty":
            api_key = kwargs.get('api_key', '')
            platform = kwargs.get('platform', 'yescaptcha')
            return ThirdPartySolver(api_key, platform)
        else:
            logger.warning(f"未知的解决器类型: {solver_type}，使用手动模式")
            return ManualSolver()

    def download_image(self, url: str) -> Optional[bytes]:
        """下载图片"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None

    def solve_captcha(self, bg_url: str, slide_url: str = None) -> Optional[Dict]:
        """
        解决验证码

        Args:
            bg_url: 背景图片URL
            slide_url: 滑块图片URL（可选）

        Returns:
            验证结果
        """
        logger.info("[CaptchaManager] 开始处理验证码")

        # 下载图片
        bg_image = self.download_image(bg_url)
        if not bg_image:
            return None

        if slide_url:
            slide_image = self.download_image(slide_url)
            if not slide_image and isinstance(self.solver, DDDDOCRSolver):
                logger.error("下载滑块图片失败")
                return None
        else:
            slide_image = None

        # 识别
        if isinstance(self.solver, DDDDOCRSolver) and slide_image:
            result = self.solver.solve(bg_image, slide_image)
        else:
            result = self.solver.solve(bg_url)

        return result

    def generate_behavior_data(self, track: list) -> str:
        """
        根据轨迹生成行为数据(bhv参数)

        这个需要逆向分析云闪付的加密算法
        当前返回模拟数据

        Args:
            track: 轨迹列表

        Returns:
            加密的行为数据
        """
        import random

        # TODO: 实现实际的加密算法
        # 从HAR分析看，格式类似: "P(/.112/00///,--,,---,**,)*))*,)*)*),)))..."

        # 临时方案：生成随机数据
        chars = "()*-.,/0123456789:;?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        behavior = "P" + "".join(random.choices(chars, k=200))

        return behavior


# 使用示例
if __name__ == "__main__":
    # 测试ddddocr
    manager = CaptchaManager(solver_type="ddddocr")

    # 模拟验证码URL
    bg_url = "https://captcha.95516.com/media?mediaId=test.png"

    result = manager.solve_captcha(bg_url)
    if result:
        print(f"识别结果: {result}")
        bhv = manager.generate_behavior_data(result['track'])
        print(f"行为数据: {bhv[:50]}...")
