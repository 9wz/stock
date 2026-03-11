#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐引擎层 - Recommendation Engine Layer
负责根据用户画像推荐合适的策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from user_profile.profile_manager import ProfileManager
from strategies.strategy_pool import StrategyPool


class RecommendationEngine:
    """
    推荐引擎
    根据用户画像筛选和推荐策略
    """

    def __init__(self, profile_manager: ProfileManager = None,
                 strategy_pool: StrategyPool = None):
        """
        初始化推荐引擎

        Args:
            profile_manager: 用户画像管理器
            strategy_pool: 策略池
        """
        self.profile_manager = profile_manager or ProfileManager()
        self.strategy_pool = strategy_pool or StrategyPool()

        # 推荐权重配置
        self.matching_weight = 0.6  # 匹配度权重
        self.strategy_weight = 0.4  # 策略评分权重

    def filter_strategies(self, user_id: str) -> List[Dict]:
        """
        根据用户画像筛选策略

        Args:
            user_id: 用户ID

        Returns:
            符合条件的策略列表
        """
        user = self.profile_manager.get_user(user_id)
        if not user:
            return []

        # 获取市场偏好对应的策略
        market_map = {
            'A股': 'A',
            '美股': 'US',
            '双市场': 'BOTH'
        }

        market = market_map.get(user.market_preference, 'BOTH')
        strategies = self.strategy_pool.get_strategies_by_market(market)

        # 进一步过滤
        filtered = []
        for strategy in strategies:
            compatibility = self.profile_manager.validate_strategy_compatibility(
                user_id, strategy
            )
            if compatibility['compatible']:
                strategy['compatibility'] = compatibility
                filtered.append(strategy)

        return filtered

    def calculate_matching_score(self, user_id: str, strategy_info: Dict) -> float:
        """
        计算策略与用户的匹配度

        Args:
            user_id: 用户ID
            strategy_info: 策略信息

        Returns:
            匹配度分数 (0-100)
        """
        user = self.profile_manager.get_user(user_id)
        if not user:
            return 0.0

        # 计算收益匹配度
        target_return = user.return_target
        strategy_return = strategy_info.get('annual_return', 0)

        # 收益匹配度（越接近目标越好）
        if strategy_return >= target_return:
            return_score = 100 - (strategy_return - target_return) * 100
        else:
            return_score = max(0, 100 - (target_return - strategy_return) * 200)

        # 计算风险匹配度
        target_mdd = self.profile_manager.get_risk_config(user.risk_level)['max_drawdown']
        strategy_mdd = strategy_info.get('max_drawdown', 1.0)

        if strategy_mdd <= target_mdd:
            risk_score = 100 - (target_mdd - strategy_mdd) * 100
        else:
            risk_score = max(0, 100 - (strategy_mdd - target_mdd) * 200)

        # 综合匹配度
        matching_score = (return_score + risk_score) / 2

        return max(0, min(100, matching_score))

    def calculate_strategy_score(self, strategy_info: Dict) -> float:
        """
        计算策略综合评分

        Args:
            strategy_info: 策略信息

        Returns:
            策略评分 (0-100)
        """
        # 收益评分
        annual_return = strategy_info.get('annual_return', 0)
        return_score = min(100, annual_return * 500)  # 15%对应75分

        # 风险调整收益评分（夏普比率）
        sharpe = strategy_info.get('sharpe_ratio', 0)
        sharpe_score = min(100, sharpe * 50)  # 2.0对应100分

        # 稳定性评分（最大回撤反向）
        max_dd = strategy_info.get('max_drawdown', 1.0)
        stability_score = max(0, 100 - max_dd * 400)  # 25%对应0分

        # 综合评分
        strategy_score = return_score * 0.4 + sharpe_score * 0.3 + stability_score * 0.3

        return strategy_score

    def recommend(self, user_id: str, top_n: int = 3) -> List[Dict]:
        """
        推荐策略

        Args:
            user_id: 用户ID
            top_n: 推荐数量

        Returns:
            推荐策略列表
        """
        user = self.profile_manager.get_user(user_id)
        if not user:
            return []

        # 1. 筛选符合条件的策略
        filtered_strategies = self.filter_strategies(user_id)

        if not filtered_strategies:
            # 如果没有完全符合条件的，返回所有策略
            market_map = {
                'A股': 'A',
                '美股': 'US',
                '双市场': 'BOTH'
            }
            market = market_map.get(user.market_preference, 'BOTH')
            filtered_strategies = self.strategy_pool.get_strategies_by_market(market)

        # 2. 计算每个策略的推荐分数
        recommendations = []
        for strategy in filtered_strategies:
            matching_score = self.calculate_matching_score(user_id, strategy)
            strategy_score = self.calculate_strategy_score(strategy)

            # 综合推荐分数
            final_score = (
                matching_score * self.matching_weight +
                strategy_score * self.strategy_weight
            )

            # 获取用户偏好因子
            user_factors = self.profile_manager.get_matching_factors(user_id)
            strategy_factors = strategy.get('factors', [])

            # 因子匹配度
            factor_match = len(set(user_factors) & set(strategy_factors)) / max(1, len(user_factors))

            recommendation = {
                'strategy_key': strategy.get('key'),
                'strategy_name': strategy.get('name'),
                'market': strategy.get('market'),
                'description': strategy.get('description'),
                'annual_return': strategy.get('annual_return'),
                'sharpe_ratio': strategy.get('sharpe_ratio'),
                'max_drawdown': strategy.get('max_drawdown'),
                'factors': strategy.get('factors', []),
                'factor_ic': strategy.get('factor_ic', {}),
                'matching_score': matching_score,
                'strategy_score': strategy_score,
                'final_score': final_score,
                'factor_match': factor_match,
                'recommendation_reason': self._generate_reason(user, strategy, matching_score)
            }

            recommendations.append(recommendation)

        # 3. 按推荐分数排序
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)

        return recommendations[:top_n]

    def _generate_reason(self, user, strategy: Dict, matching_score: float) -> str:
        """
        生成推荐理由

        Args:
            user: 用户画像
            strategy: 策略信息
            matching_score: 匹配度

        Returns:
            推荐理由字符串
        """
        reasons = []

        # 收益相关
        if strategy.get('annual_return', 0) >= user.return_target:
            reasons.append(f"该策略年化收益{strategy.get('annual_return', 0)*100:.0f}%，符合您{user.return_target*100:.0f}%的收益目标")

        # 风险相关
        config = self.profile_manager.get_risk_config(user.risk_level)
        if strategy.get('max_drawdown', 1) <= config['max_drawdown']:
            reasons.append(f"最大回撤{strategy.get('max_drawdown', 0)*100:.0f}%，在您可承受范围内")

        # 市场相关
        if strategy.get('market') == 'BOTH':
            reasons.append("同时适用于A股和美股")
        elif strategy.get('market') == user.market_preference:
            reasons.append(f"专门针对{user.market_preference}设计")

        # 因子相关
        if strategy.get('factors'):
            factors_str = '、'.join(strategy.get('factors', [])[:2])
            reasons.append(f"核心因子：{factors_str}")

        return '；'.join(reasons) if reasons else '综合表现优秀'

    def generate_recommendation_report(self, user_id: str) -> str:
        """
        生成推荐报告

        Args:
            user_id: 用户ID

        Returns:
            Markdown格式的推荐报告
        """
        user = self.profile_manager.get_user(user_id)
        if not user:
            return "用户不存在"

        # 获取推荐
        recommendations = self.recommend(user_id, top_n=3)

        # 获取用户画像摘要
        profile_summary = self.profile_manager.get_user_summary(user_id)

        # 生成报告
        report = f"""# 量化策略推荐报告

## 一、用户画像

{profile_summary}

---

## 二、策略推荐

"""

        for i, rec in enumerate(recommendations, 1):
            report += f"""
### 推荐 {i}: {rec['strategy_name']}

| 指标 | 数值 |
|------|------|
| 适用市场 | {rec['market']} |
| 年化收益 | {rec['annual_return']*100:.1f}% |
| 夏普比率 | {rec['sharpe_ratio']:.2f} |
| 最大回撤 | {rec['max_drawdown']*100:.1f}% |
| 推荐分数 | {rec['final_score']:.1f} |

- **推荐理由**: {rec['recommendation_reason']}
- **核心因子**: {', '.join(rec['factors'])}
- **因子IC值**: {', '.join([f"{k}:{v:.2f}" for k,v in rec['factor_ic'].items()])}

---

"""

        report += """
## 三、风险提示

1. 历史业绩不代表未来表现
2. 请根据自身风险承受能力选择策略
3. 建议分散投资，降低单一策略风险

---

*本报告由量化策略推荐系统自动生成*
"""

        return report

    def get_strategy_comparison(self, user_id: str) -> pd.DataFrame:
        """
        获取策略对比表格

        Args:
            user_id: 用户ID

        Returns:
            策略对比DataFrame
        """
        recommendations = self.recommend(user_id, top_n=10)

        if not recommendations:
            return pd.DataFrame()

        df = pd.DataFrame(recommendations)
        return df[['strategy_name', 'market', 'annual_return',
                   'sharpe_ratio', 'max_drawdown', 'factors', 'final_score']]


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("推荐引擎演示")
    print("=" * 60)

    # 初始化推荐引擎
    engine = RecommendationEngine()

    # 测试推荐
    print("\n推荐策略（用户: root）:")
    print("=" * 60)

    recommendations = engine.recommend("root", top_n=3)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n推荐 {i}: {rec['strategy_name']}")
        print(f"  年化收益: {rec['annual_return']*100:.1f}%")
        print(f"  夏普比率: {rec['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {rec['max_drawdown']*100:.1f}%")
        print(f"  匹配度: {rec['matching_score']:.1f}")
        print(f"  推荐理由: {rec['recommendation_reason']}")

    # 生成报告
    print("\n" + "=" * 60)
    print("生成推荐报告")
    print("=" * 60)

    report = engine.generate_recommendation_report("root")
    print(report[:1000] + "...")
