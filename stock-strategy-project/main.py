#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化策略推荐系统主入口
A股+美股策略/因子推荐系统

使用方法:
    python main.py              # 交互式界面
    python main.py --user root # 为指定用户推荐
    python main.py --web       # 启动Web界面
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.data_loader import DataLoader
from factors.factor_engine import FactorEngine
from strategies.strategy_pool import StrategyPool
from user_profile.profile_manager import ProfileManager
from recommendation.recommender import RecommendationEngine
from output.visualization import Visualizer, ReportGenerator, InteractiveInterface


class QuantSystem:
    """
    量化策略推荐系统主类
    整合所有层级功能
    """

    def __init__(self):
        """初始化系统"""
        print("=" * 60)
        print("初始化量化策略推荐系统...")
        print("=" * 60)

        # 初始化各层级
        self.data_loader = DataLoader()
        self.factor_engine = FactorEngine()
        self.strategy_pool = StrategyPool()
        self.profile_manager = ProfileManager()
        self.recommendation_engine = RecommendationEngine(
            self.profile_manager,
            self.strategy_pool
        )
        self.visualizer = Visualizer()
        self.report_generator = ReportGenerator()

        print("系统初始化完成！\n")

    def run_interactive(self):
        """运行交互式界面"""
        interface = InteractiveInterface(self.recommendation_engine)
        interface.interactive_recommend()

    def get_recommendations(self, user_id: str = "root") -> list:
        """
        获取策略推荐

        Args:
            user_id: 用户ID

        Returns:
            推荐列表
        """
        return self.recommendation_engine.recommend(user_id)

    def get_factor_analysis(self, ticker: str = None, market: str = "A") -> dict:
        """
        获取因子分析

        Args:
            ticker: 股票代码
            market: 市场

        Returns:
            因子分析结果
        """
        # 尝试获取数据
        if ticker:
            if market == "A":
                df = self.data_loader.fetch_a_stock_daily(ticker)
            else:
                df = self.data_loader.fetch_us_stock_daily(ticker)
        else:
            # 使用示例数据
            import numpy as np
            import pandas as pd

            np.random.seed(42)
            dates = pd.date_range('2023-01-01', periods=200, freq='D')
            n = len(dates)

            prices = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.02))
            volumes = np.random.randint(1000000, 10000000, n)
            pes = np.random.uniform(10, 50, n)
            roes = np.random.uniform(5, 30, n)

            df = pd.DataFrame({
                'date': dates,
                'close': prices,
                'volume': volumes,
                'pe': pes,
                'roe': roes
            })

        # 计算因子
        df_with_factors = self.factor_engine.calculate_all_factors(df)

        # 添加收益
        df_with_factors['return'] = df_with_factors['close'].pct_change().shift(-1)

        # 因子有效性分析
        rankings = self.factor_engine.rank_all_factors(df_with_factors)

        return {
            'ticker': ticker or '示例',
            'market': market,
            'factor_count': len(rankings),
            'rankings': rankings
        }

    def generate_full_report(self, user_id: str = "root") -> str:
        """
        生成完整报告

        Args:
            user_id: 用户ID

        Returns:
            报告路径
        """
        # 获取推荐
        recommendations = self.recommendation_engine.recommend(user_id)
        user = self.profile_manager.get_user(user_id)

        # 生成Markdown报告
        report = self.report_generator.generate_markdown_report(
            recommendations,
            user.to_dict()
        )

        # 保存报告
        path = self.report_generator.save_report(report)

        return path


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='量化策略推荐系统')
    parser.add_argument('--user', type=str, default='root', help='用户ID')
    parser.add_argument('--ticker', type=str, help='股票代码')
    parser.add_argument('--market', type=str, default='A', choices=['A', 'US'], help='市场')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--interactive', action='store_true', help='交互式界面')

    args = parser.parse_args()

    # 初始化系统
    system = QuantSystem()

    if args.web:
        # 启动Web界面
        print("启动Web界面...")
        try:
            from web_app import app
            app.run(debug=True, host='0.0.0.0', port=5000)
        except ImportError:
            print("错误: 请先安装Flask (pip install flask)")

    elif args.interactive:
        # 交互式界面
        system.run_interactive()

    else:
        # 命令行模式
        print("=" * 60)
        print(f"为用户 {args.user} 生成推荐")
        print("=" * 60)

        # 获取推荐
        recommendations = system.get_recommendations(args.user)

        print("\n【推荐策略】")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['strategy_name']}")
            print(f"   年化收益: {rec['annual_return']*100:.1f}%")
            print(f"   夏普比率: {rec['sharpe_ratio']:.2f}")
            print(f"   最大回撤: {rec['max_drawdown']*100:.1f}%")
            print(f"   匹配度: {rec['matching_score']:.1f}")
            print(f"   核心因子: {', '.join(rec['factors'])}")

        # 因子分析
        if args.ticker:
            print(f"\n【因子分析: {args.ticker}】")
            analysis = system.get_factor_analysis(args.ticker, args.market)
            for r in analysis['rankings'][:5]:
                print(f"  {r['factor_name']}: IC={r['ic']:.4f} ({r['effectiveness']})")

        # 生成报告
        if args.report:
            print("\n【生成报告】")
            path = system.generate_full_report(args.user)
            print(f"报告已保存: {path}")


if __name__ == "__main__":
    main()
