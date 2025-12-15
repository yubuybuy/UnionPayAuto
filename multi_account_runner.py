#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多账号并发领券脚本
通过多个账号同时运行，提高成功率
"""

import asyncio
import logging
from typing import List, Dict
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from unionpay_auto import UnionPayCouponBot, Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)-10s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('multi_account.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MultiAccountRunner:
    """多账号运行器"""

    def __init__(self, accounts: List[Dict]):
        """
        初始化多账号运行器

        Args:
            accounts: 账号配置列表
                [
                    {
                        'name': '账号1',
                        'device_id': 'xxx',
                        'dfp_id': 'xxx',
                        'cookies': {},
                        'area_code': '510099',
                        'longitude': '103.xxx',
                        'latitude': '29.xxx'
                    },
                    ...
                ]
        """
        self.accounts = accounts
        self.success_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.start_time = datetime.now()

    def create_bot(self, account: Dict) -> UnionPayCouponBot:
        """为每个账号创建独立的Bot实例"""
        config = Config()

        # 使用账号特定的配置
        config.DEVICE_ID = account.get('device_id', config.DEVICE_ID)
        config.DFP_ID = account.get('dfp_id', config.DFP_ID)
        config.AREA_CODE = account.get('area_code', config.AREA_CODE)
        config.LONGITUDE = account.get('longitude', config.LONGITUDE)
        config.LATITUDE = account.get('latitude', config.LATITUDE)

        bot = UnionPayCouponBot(config)

        # 设置账号特定的Cookie
        if 'cookies' in account:
            bot.session.cookies.update(account['cookies'])

        # 设置额外的请求头
        if 'headers' in account:
            bot.session.headers.update(account['headers'])

        return bot

    def run_single_account(self, account: Dict) -> Dict:
        """
        运行单个账号

        Args:
            account: 账号配置

        Returns:
            运行结果
        """
        account_name = account.get('name', 'Unknown')
        logger.info(f"[{account_name}] 开始运行")

        try:
            bot = self.create_bot(account)
            success = bot.run()

            with self.lock:
                if success:
                    self.success_count += 1
                    logger.info(f"[{account_name}] ✓✓✓ 领取成功！")
                else:
                    self.failed_count += 1
                    logger.info(f"[{account_name}] ✗ 未能成功领取")

            return {
                'account': account_name,
                'success': success,
                'stats': bot.stats
            }

        except Exception as e:
            logger.error(f"[{account_name}] 运行异常: {e}", exc_info=True)
            with self.lock:
                self.failed_count += 1

            return {
                'account': account_name,
                'success': False,
                'error': str(e)
            }

    def run_concurrent(self, max_workers: int = 3):
        """
        并发运行多个账号

        Args:
            max_workers: 最大并发数（建议不要太高，避免被限流）
        """
        logger.info("=" * 80)
        logger.info(f"多账号并发模式启动")
        logger.info(f"账号数量: {len(self.accounts)}")
        logger.info(f"并发数: {max_workers}")
        logger.info("=" * 80 + "\n")

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_account = {
                executor.submit(self.run_single_account, account): account
                for account in self.accounts
            }

            # 等待任务完成
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"任务执行异常: {e}")

        # 打印汇总
        self._print_summary(results)

        return results

    def run_sequential(self, delay: float = 2.0):
        """
        顺序运行多个账号（错峰执行，避免同时请求）

        Args:
            delay: 账号之间的延迟时间（秒）
        """
        logger.info("=" * 80)
        logger.info(f"多账号顺序模式启动")
        logger.info(f"账号数量: {len(self.accounts)}")
        logger.info(f"间隔延迟: {delay}秒")
        logger.info("=" * 80 + "\n")

        results = []

        for i, account in enumerate(self.accounts, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"运行第 {i}/{len(self.accounts)} 个账号")
            logger.info(f"{'='*80}")

            result = self.run_single_account(account)
            results.append(result)

            # 如果成功了就不继续其他账号
            if result['success']:
                logger.info(f"\n已有账号成功，停止其他账号运行")
                break

            # 账号之间延迟
            if i < len(self.accounts):
                logger.info(f"等待 {delay} 秒后运行下一个账号...")
                time.sleep(delay)

        # 打印汇总
        self._print_summary(results)

        return results

    def run_smart_mode(self):
        """
        智能模式：
        1. 先用一个账号快速轮询检测名额
        2. 检测到名额后，立即启动所有账号并发领取
        """
        logger.info("=" * 80)
        logger.info(f"智能模式启动")
        logger.info(f"账号数量: {len(self.accounts)}")
        logger.info("=" * 80 + "\n")

        if not self.accounts:
            logger.error("没有配置账号")
            return []

        # 使用第一个账号作为探测器
        probe_account = self.accounts[0]
        probe_bot = self.create_bot(probe_account)

        logger.info(f"[探测] 使用账号 '{probe_account.get('name')}' 检测名额...")

        # 轮询检测名额
        while True:
            can_continue, msg = probe_bot.init_session()
            if can_continue:
                logger.info(f"[探测] ✓✓✓ 检测到名额释放！立即启动所有账号！")
                break
            else:
                logger.info(f"[探测] {msg}，继续监测...")
                time.sleep(1)

        # 立即启动所有账号并发领取
        logger.info("\n" + "=" * 80)
        logger.info("触发并发领取模式")
        logger.info("=" * 80 + "\n")

        return self.run_concurrent(max_workers=len(self.accounts))

    def _print_summary(self, results: List[Dict]):
        """打印汇总信息"""
        elapsed = datetime.now() - self.start_time

        logger.info("\n" + "=" * 80)
        logger.info("多账号运行汇总")
        logger.info("=" * 80)
        logger.info(f"总运行时长: {elapsed}")
        logger.info(f"账号总数: {len(self.accounts)}")
        logger.info(f"成功数量: {self.success_count}")
        logger.info(f"失败数量: {self.failed_count}")
        logger.info(f"成功率: {self.success_count / len(self.accounts) * 100:.1f}%")

        logger.info("\n详细结果:")
        for i, result in enumerate(results, 1):
            account_name = result['account']
            success = result['success']
            status = "✓ 成功" if success else "✗ 失败"

            logger.info(f"  {i}. [{account_name}] {status}")

            if 'stats' in result:
                stats = result['stats']
                logger.info(f"     - 领券尝试: {stats.get('acquire_attempts', 0)}")
                logger.info(f"     - 验证码成功: {stats.get('captcha_solved', 0)}")

        logger.info("=" * 80)


def load_accounts_from_config():
    """从配置文件加载账号"""
    try:
        from config import ACCOUNTS, MULTI_ACCOUNT
        if MULTI_ACCOUNT and ACCOUNTS:
            return ACCOUNTS
        else:
            logger.warning("配置文件中未启用多账号模式或无账号配置")
            return []
    except ImportError:
        logger.error("无法导入配置文件")
        return []


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='云闪付多账号自动领券')
    parser.add_argument(
        '--mode',
        choices=['concurrent', 'sequential', 'smart'],
        default='smart',
        help='运行模式: concurrent(并发), sequential(顺序), smart(智能)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='并发模式的最大工作线程数（默认3）'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='顺序模式的账号间延迟（秒，默认2）'
    )

    args = parser.parse_args()

    # 加载账号配置
    accounts = load_accounts_from_config()

    if not accounts:
        logger.error("没有找到账号配置，请在 config.py 中配置 ACCOUNTS")
        return 1

    # 创建运行器
    runner = MultiAccountRunner(accounts)

    try:
        # 根据模式运行
        if args.mode == 'concurrent':
            results = runner.run_concurrent(max_workers=args.workers)
        elif args.mode == 'sequential':
            results = runner.run_sequential(delay=args.delay)
        elif args.mode == 'smart':
            results = runner.run_smart_mode()

        # 检查是否有成功的
        if runner.success_count > 0:
            logger.info(f"\n🎉 任务完成！共 {runner.success_count} 个账号成功领取！")
            return 0
        else:
            logger.info(f"\n😔 所有账号均未成功")
            return 1

    except KeyboardInterrupt:
        logger.info("\n\n用户中断运行")
        return 2
    except Exception as e:
        logger.error(f"\n\n发生异常: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    exit(main())
