#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输出层 - Output Layer
负责可视化、报告生成和交互功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import os

# 尝试导入可视化库
try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("警告: 未安装matplotlib，可视化功能将受限")

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("警告: 未安装plotly，高级可视化功能将受限")


class Visualizer:
    """
    可视化器
    负责策略回测收益曲线、因子IC值热力图等绘制
    """

    def __init__(self, output_dir: str = "output"):
        """
        初始化可视化器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_returns_curve(self, returns: pd.Series, benchmark_returns: pd.Series = None,
                          title: str = "策略收益曲线", save_path: str = None) -> str:
        """
        绘制策略回测收益曲线

        Args:
            returns: 策略收益序列
            benchmark_returns: 基准收益序列（如沪深300/标普500）
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not MATPLOTLIB_AVAILABLE:
            return ""

        # 计算累计收益
        cumulative = (1 + returns).cumprod()
        benchmark_cumulative = (1 + benchmark_returns).cumprod() if benchmark_returns is not None else None

        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))

        # 策略收益曲线
        ax.plot(cumulative.index, cumulative.values,
                label='策略收益', linewidth=2, color='#2E86AB')

        # 基准收益曲线
        if benchmark_cumulative is not None:
            ax.plot(benchmark_cumulative.index, benchmark_cumulative.values,
                    label='基准收益', linewidth=1.5, color='#A23B72', alpha=0.7)

        # 格式化
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('累计收益', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

        # 设置日期格式
        if hasattr(cumulative.index, 'year'):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=45)

        plt.tight_layout()

        # 保存
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

        plt.savefig(save_path, dpi=150)
        plt.close()

        return save_path

    def plot_factor_ic_heatmap(self, ic_data: Dict[str, float],
                               title: str = "因子IC值热力图",
                               save_path: str = None) -> str:
        """
        绘制因子IC值热力图

        Args:
            ic_data: 因子IC值字典
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not MATPLOTLIB_AVAILABLE:
            return ""

        # 准备数据
        factors = list(ic_data.keys())
        ic_values = list(ic_data.values())

        # 创建热力图数据
        n_factors = len(factors)
        data = np.array(ic_values).reshape(1, -1)

        # 创建图表
        fig, ax = plt.subplots(figsize=(max(8, n_factors), 3))

        # 绘制热力图
        im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=-0.3, vmax=0.3)

        # 设置标签
        ax.set_xticks(range(n_factors))
        ax.set_xticklabels(factors, rotation=45, ha='right')
        ax.set_yticks([])

        # 添加数值标签
        for i, (factor, ic) in enumerate(zip(factors, ic_values)):
            color = 'white' if abs(ic) > 0.15 else 'black'
            ax.text(i, 0, f'{ic:.3f}', ha='center', va='center',
                   color=color, fontsize=10, fontweight='bold')

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label('IC值', fontsize=10)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)

        plt.tight_layout()

        # 保存
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"ic_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

        plt.savefig(save_path, dpi=150)
        plt.close()

        return save_path

    def plot_factor_bar(self, factor_results: List[Dict],
                       title: str = "因子有效性排名",
                       save_path: str = None) -> str:
        """
        绘制因子有效性条形图

        Args:
            factor_results: 因子有效性结果列表
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not MATPLOTLIB_AVAILABLE or not factor_results:
            return ""

        # 排序
        sorted_factors = sorted(factor_results, key=lambda x: abs(x.get('ic', 0)), reverse=True)

        factors = [f['factor_name'] for f in sorted_factors]
        ic_values = [f['ic'] for f in sorted_factors]

        # 颜色：正IC绿色，负IC红色
        colors = ['#2E86AB' if ic > 0 else '#E94F37' for ic in ic_values]

        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.barh(factors, ic_values, color=colors, edgecolor='black', linewidth=0.5)

        # 添加数值标签
        for bar, ic in zip(bars, ic_values):
            width = bar.get_width()
            ax.text(width + 0.01 if width > 0 else width - 0.01,
                   bar.get_y() + bar.get_height()/2,
                   f'{ic:.3f}', ha='left' if width > 0 else 'right',
                   va='center', fontsize=10)

        ax.axvline(x=0, color='black', linewidth=0.8)
        ax.set_xlabel('IC值', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)

        plt.tight_layout()

        # 保存
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"factor_bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

        plt.savefig(save_path, dpi=150)
        plt.close()

        return save_path

    def plot_strategy_comparison(self, strategies: List[Dict],
                                title: str = "策略对比") -> str:
        """
        绘制策略对比图

        Args:
            strategies: 策略列表
            title: 图表标题

        Returns:
            保存的文件路径
        """
        if not MATPLOTLIB_AVAILABLE or not strategies:
            return ""

        # 提取数据
        names = [s.get('strategy_name', s.get('name', 'Unknown')) for s in strategies]
        returns = [s.get('annual_return', 0) * 100 for s in strategies]
        sharpes = [s.get('sharpe_ratio', 0) for s in strategies]
        drawdowns = [s.get('max_drawdown', 0) * 100 for s in strategies]

        # 创建子图
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # 年化收益
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(names)))
        axes[0].barh(names, returns, color=colors)
        axes[0].set_xlabel('年化收益 (%)')
        axes[0].set_title('年化收益')

        # 夏普比率
        axes[1].barh(names, sharpes, color=plt.cm.Greens(np.linspace(0.4, 0.8, len(names))))
        axes[1].set_xlabel('夏普比率')
        axes[1].set_title('夏普比率')

        # 最大回撤
        axes[2].barh(names, drawdowns, color=plt.cm.Reds(np.linspace(0.4, 0.8, len(names))))
        axes[2].set_xlabel('最大回撤 (%)')
        axes[2].set_title('最大回撤')

        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()

        save_path = os.path.join(self.output_dir, f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(save_path, dpi=150)
        plt.close()

        return save_path


class ReportGenerator:
    """
    报告生成器
    负责导出Markdown格式的推荐报告
    """

    def __init__(self, output_dir: str = "output"):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_markdown_report(self, recommendations: List[Dict],
                                 user_profile: Dict,
                                 title: str = "量化策略推荐报告") -> str:
        """
        生成Markdown格式的推荐报告

        Args:
            recommendations: 推荐策略列表
            user_profile: 用户画像
            title: 报告标题

        Returns:
            Markdown内容
        """
        report = f"""# {title}

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、用户画像

| 属性 | 值 |
|------|-----|
| 用户名 | {user_profile.get('username', 'N/A')} |
| 市场偏好 | {user_profile.get('market_preference', 'N/A')} |
| 风险等级 | {user_profile.get('risk_level', 'N/A')} |
| 收益目标 | {user_profile.get('return_target', 0)*100:.0f}% |
| 持仓周期 | {user_profile.get('holding_period', 'N/A')} |

---

## 二、策略推荐

"""

        for i, rec in enumerate(recommendations, 1):
            report += f"""
### {i}. {rec.get('strategy_name', 'Unknown Strategy')}

| 核心指标 | 数值 |
|----------|------|
| 适用市场 | {rec.get('market', 'N/A')} |
| 年化收益 | {rec.get('annual_return', 0)*100:.1f}% |
| 夏普比率 | {rec.get('sharpe_ratio', 0):.2f} |
| 最大回撤 | {rec.get('max_drawdown', 0)*100:.1f}% |
| 推荐分数 | {rec.get('final_score', 0):.1f} |

**推荐理由**: {rec.get('recommendation_reason', 'N/A')}

**核心因子**: {', '.join(rec.get('factors', []))}

**因子IC值**: {', '.join([f"{k}: {v:.2f}" for k, v in rec.get('factor_ic', {}).items()])}

---

"""

        report += """
## 三、风险提示

1. **历史业绩不代表未来**: 过去的表现不能保证未来的收益
2. **市场风险**: 股票投资存在系统性风险，可能面临本金损失
3. **策略风险**: 不同策略有不同的适用场景，请根据自身情况选择
4. **建议分散**: 不要将所有资金投入单一策略，建议分散投资

---

## 四、策略说明

| 策略名称 | 适用市场 | 核心逻辑 |
|----------|----------|----------|
| 均线交叉策略 | A股/美股 | MA5上穿MA20买入，下穿卖出 |
| RSI超买超卖策略 | A股/美股 | RSI<30买入，RSI>70卖出 |
| 低PE高ROE选股策略 | A股 | PE<20且ROE>15%选股 |
| 波动率择时策略 | A股/美股 | 波动率<20%持仓，>30%空仓 |
| 美股趋势跟踪策略 | 美股 | 站上MA60买入，跌破卖出 |

---

*本报告由量化策略推荐系统自动生成*
"""

        return report

    def save_report(self, content: str, filename: str = None) -> str:
        """
        保存报告到文件

        Args:
            content: 报告内容
            filename: 文件名

        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath


class InteractiveInterface:
    """
    交互式接口
    支持用户输入新的参数并实时重新推荐
    """

    def __init__(self, recommendation_engine):
        """
        初始化交互式接口

        Args:
            recommendation_engine: 推荐引擎
        """
        self.engine = recommendation_engine
        self.profile_manager = recommendation_engine.profile_manager

    def interactive_recommend(self):
        """
        交互式推荐流程

        Returns:
            推荐结果
        """
        print("\n" + "=" * 60)
        print("量化策略推荐系统")
        print("=" * 60)

        # 用户登录
        print("\n【用户登录】")
        user_id = input("请输入用户ID (默认root): ").strip() or "root"
        user = self.profile_manager.get_user(user_id)

        if user:
            print(f"\n欢迎回来，{user.username}！")
            print(self.profile_manager.get_user_summary(user_id))

            # 询问是否修改
            modify = input("\n是否修改用户画像？(y/n): ").strip().lower()
            if modify == 'y':
                user = self._update_profile(user_id)
        else:
            print("\n用户不存在，将创建新用户")
            user = self._create_profile(user_id)

        # 获取推荐
        print("\n【正在生成推荐】...")
        recommendations = self.engine.recommend(user_id)

        # 显示推荐结果
        self._display_recommendations(recommendations)

        # 生成报告
        generate_report = input("\n是否生成报告？(y/n): ").strip().lower()
        if generate_report == 'y':
            report = self.engine.generate_recommendation_report(user_id)
            print("\n" + "=" * 60)
            print(report)

        return recommendations

    def _update_profile(self, user_id: str):
        """更新用户画像"""
        user = self.profile_manager.get_user(user_id)

        print("\n【修改用户画像】")
        print("直接回车保留原值")

        market = input(f"市场偏好 (当前: {user.market_preference}): ").strip()
        risk = input(f"风险等级 (当前: {user.risk_level}): ").strip()
        return_target = input(f"收益目标 (当前: {user.return_target*100:.0f}%): ").strip()
        holding = input(f"持仓周期 (当前: {user.holding_period}): ").strip()

        updates = {}
        if market:
            updates['market_preference'] = market
        if risk:
            updates['risk_level'] = risk
        if return_target:
            try:
                updates['return_target'] = float(return_target) / 100
            except:
                pass
        if holding:
            updates['holding_period'] = holding

        if updates:
            self.profile_manager.update_user(user_id, **updates)

        return self.profile_manager.get_user(user_id)

    def _create_profile(self, user_id: str):
        """创建用户画像"""
        print("\n【创建用户画像】")

        username = input("用户名: ").strip() or "新用户"
        market = input("市场偏好 (A股/美股/双市场): ").strip() or "双市场"
        risk = input("风险等级 (保守型/稳健型/激进型): ").strip() or "稳健型"
        return_target = input("收益目标 (5/10/15): ").strip() or "10"
        holding = input("持仓周期 (短期/中期/长期): ").strip() or "中期"

        try:
            return_target = float(return_target) / 100
        except:
            return_target = 0.10

        return self.profile_manager.create_user(
            user_id=user_id,
            username=username,
            market_preference=market,
            risk_level=risk,
            return_target=return_target,
            holding_period=holding
        )

    def _display_recommendations(self, recommendations: List[Dict]):
        """显示推荐结果"""
        print("\n" + "=" * 60)
        print("推荐结果")
        print("=" * 60)

        for i, rec in enumerate(recommendations, 1):
            print(f"\n推荐 {i}: {rec.get('strategy_name')}")
            print(f"  年化收益: {rec.get('annual_return', 0)*100:.1f}%")
            print(f"  夏普比率: {rec.get('sharpe_ratio', 0):.2f}")
            print(f"  最大回撤: {rec.get('max_drawdown', 0)*100:.1f}%")
            print(f"  匹配度: {rec.get('matching_score', 0):.1f}")
            print(f"  推荐理由: {rec.get('recommendation_reason')}")


# 测试代码
if __name__ == "__main__":
    # 导入必要的模块
    from recommendation.recommender import RecommendationEngine

    print("=" * 60)
    print("输出层功能演示")
    print("=" * 60)

    # 初始化
    engine = RecommendationEngine()
    visualizer = Visualizer()
    report_gen = ReportGenerator()

    # 生成模拟数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=250, freq='D')
    returns = pd.Series(np.random.randn(250) * 0.02, index=dates)
    benchmark_returns = pd.Series(np.random.randn(250) * 0.015, index=dates)

    # 绘制收益曲线
    print("\n绘制收益曲线...")
    path = visualizer.plot_returns_curve(returns, benchmark_returns, "测试策略收益曲线")
    print(f"收益曲线已保存: {path}")

    # 绘制因子IC热力图
    print("\n绘制因子IC热力图...")
    ic_data = {
        'MA20': 0.22,
        'RSI': 0.15,
        'PE': -0.18,
        'ROE': 0.25,
        'VOLATILITY': -0.12
    }
    path = visualizer.plot_factor_ic_heatmap(ic_data)
    print(f"IC热力图已保存: {path}")

    # 生成报告
    print("\n生成推荐报告...")
    recommendations = engine.recommend("root")
    user = engine.profile_manager.get_user("root")

    report = report_gen.generate_markdown_report(
        recommendations,
        user.to_dict()
    )
    path = report_gen.save_report(report)
    print(f"报告已保存: {path}")

    print("\n报告预览（前1000字符）:")
    print(report[:1000])
