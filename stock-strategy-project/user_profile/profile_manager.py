#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像层 - User Profile Layer
负责用户标签录入和量化规则匹配
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class MarketPreference(Enum):
    """市场偏好"""
    A = "A股"
    US = "美股"
    BOTH = "双市场"


class RiskLevel(Enum):
    """风险等级"""
    CONSERVATIVE = "保守型"  # 最大回撤≤10%，年化收益≥5%
    STEADY = "稳健型"        # 最大回撤≤15%，年化收益≥10%
    AGGRESSIVE = "激进型"    # 最大回撤≤20%，年化收益≥15%


class ReturnTarget(Enum):
    """收益目标"""
    LOW = 0.05      # 5%
    MEDIUM = 0.10   # 10%
    HIGH = 0.15     # 15%+


class HoldingPeriod(Enum):
    """持仓周期"""
    SHORT = "短期(<1月)"
    MEDIUM = "中期(1-6月)"
    LONG = "长期(>6月)"


@dataclass
class UserProfile:
    """
    用户画像数据类
    """
    user_id: str
    username: str
    market_preference: str  # A股/美股/双市场
    risk_level: str         # 保守/稳健/激进
    return_target: float    # 收益目标（如0.10表示10%）
    holding_period: str      # 短期/中期/长期

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'market_preference': self.market_preference,
            'risk_level': self.risk_level,
            'return_target': self.return_target,
            'holding_period': self.holding_period
        }


class ProfileManager:
    """
    用户画像管理器
    负责用户标签录入、量化规则和画像匹配
    """

    def __init__(self):
        """初始化用户画像管理器"""
        # 用户数据库（内存）
        self.users = {}
        self._init_default_user()

        # 风险等级阈值配置
        self.risk_config = {
            '保守型': {
                'max_drawdown': 0.10,      # 最大回撤≤10%
                'min_return': 0.05,        # 年化收益≥5%
                'preferred_factors': ['VOLATILITY', 'PE', 'PB', 'MA20'],
                'factor_weight': {
                    'VOLATILITY': 0.3,
                    'PE': 0.25,
                    'PB': 0.25,
                    'MA20': 0.2
                }
            },
            '稳健型': {
                'max_drawdown': 0.15,      # 最大回撤≤15%
                'min_return': 0.10,        # 年化收益≥10%
                'preferred_factors': ['MA5', 'MA20', 'RSI', 'ROE', 'TURNOVER'],
                'factor_weight': {
                    'MA5': 0.2,
                    'MA20': 0.2,
                    'RSI': 0.2,
                    'ROE': 0.2,
                    'TURNOVER': 0.2
                }
            },
            '激进型': {
                'max_drawdown': 0.20,      # 最大回撤≤20%
                'min_return': 0.15,        # 年化收益≥15%
                'preferred_factors': ['MA60', 'MACD', 'RSI', 'MAX_DRAWDOWN'],
                'factor_weight': {
                    'MA60': 0.3,
                    'MACD': 0.3,
                    'RSI': 0.2,
                    'MAX_DRAWDOWN': 0.2
                }
            }
        }

    def _init_default_user(self):
        """初始化默认用户"""
        default_user = UserProfile(
            user_id="root",
            username="root",
            market_preference="双市场",
            risk_level="稳健型",
            return_target=0.10,
            holding_period="中期"
        )
        self.users["root"] = default_user

    def create_user(self, user_id: str, username: str,
                   market_preference: str = "双市场",
                   risk_level: str = "稳健型",
                   return_target: float = 0.10,
                   holding_period: str = "中期") -> UserProfile:
        """
        创建用户画像

        Args:
            user_id: 用户ID
            username: 用户名
            market_preference: 市场偏好
            risk_level: 风险等级
            return_target: 收益目标
            holding_period: 持仓周期

        Returns:
            用户画像对象
        """
        # 验证参数
        if market_preference not in ["A股", "美股", "双市场"]:
            market_preference = "双市场"
        if risk_level not in ["保守型", "稳健型", "激进型"]:
            risk_level = "稳健型"
        if holding_period not in ["短期", "中期", "长期"]:
            holding_period = "中期"

        user = UserProfile(
            user_id=user_id,
            username=username,
            market_preference=market_preference,
            risk_level=risk_level,
            return_target=return_target,
            holding_period=holding_period
        )

        self.users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """
        获取用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像对象
        """
        return self.users.get(user_id)

    def update_user(self, user_id: str, **kwargs) -> Optional[UserProfile]:
        """
        更新用户画像

        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            更新后的用户画像
        """
        user = self.users.get(user_id)
        if not user:
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return user

    def get_risk_config(self, risk_level: str) -> Dict:
        """
        获取风险等级配置

        Args:
            risk_level: 风险等级

        Returns:
            配置字典
        """
        return self.risk_config.get(risk_level, self.risk_config['稳健型'])

    def calculate_risk_score(self, user_id: str) -> float:
        """
        计算用户风险评分

        Args:
            user_id: 用户ID

        Returns:
            风险评分 (0-1)
        """
        user = self.get_user(user_id)
        if not user:
            return 0.5

        # 风险评分计算
        risk_scores = {
            '保守型': 0.3,
            '稳健型': 0.6,
            '激进型': 0.9
        }

        return risk_scores.get(user.risk_level, 0.5)

    def get_matching_factors(self, user_id: str) -> List[str]:
        """
        获取用户偏好的因子

        Args:
            user_id: 用户ID

        Returns:
            因子列表
        """
        user = self.get_user(user_id)
        if not user:
            return []

        config = self.get_risk_config(user.risk_level)
        return config.get('preferred_factors', [])

    def get_factor_weights(self, user_id: str) -> Dict[str, float]:
        """
        获取用户偏好的因子权重

        Args:
            user_id: 用户ID

        Returns:
            因子权重字典
        """
        user = self.get_user(user_id)
        if not user:
            return {}

        config = self.get_risk_config(user.risk_level)
        return config.get('factor_weight', {})

    def validate_strategy_compatibility(self, user_id: str, strategy_info: Dict) -> Dict:
        """
        验证策略与用户画像的兼容性

        Args:
            user_id: 用户ID
            strategy_info: 策略信息

        Returns:
            兼容性评估结果
        """
        user = self.get_user(user_id)
        if not user:
            return {
                'compatible': False,
                'reason': '用户不存在'
            }

        config = self.get_risk_config(user.risk_level)

        # 检查市场兼容性
        if strategy_info.get('market') not in [user.market_preference, 'BOTH']:
            return {
                'compatible': False,
                'reason': f"策略适用于{strategy_info.get('market')}，但您偏好{user.market_preference}"
            }

        # 检查最大回撤
        strategy_mdd = strategy_info.get('max_drawdown', 1.0)
        if strategy_mdd > config['max_drawdown']:
            return {
                'compatible': False,
                'reason': f"策略最大回撤{strategy_mdd*100:.1f}%超过您的容忍度{config['max_drawdown']*100:.1f}%"
            }

        # 检查收益率
        strategy_return = strategy_info.get('annual_return', 0)
        if strategy_return < config['min_return']:
            return {
                'compatible': False,
                'reason': f"策略年化收益{strategy_return*100:.1f}%低于您的目标{config['min_return']*100:.1f}%"
            }

        return {
            'compatible': True,
            'reason': '策略符合您的投资偏好'
        }

    def get_user_summary(self, user_id: str) -> str:
        """
        获取用户画像摘要

        Args:
            user_id: 用户ID

        Returns:
            摘要字符串
        """
        user = self.get_user(user_id)
        if not user:
            return "用户不存在"

        config = self.get_risk_config(user.risk_level)

        summary = f"""
用户画像摘要
================
用户名: {user.username}
市场偏好: {user.market_preference}
风险等级: {user.risk_level}
收益目标: {user.return_target*100:.0f}%
持仓周期: {user.holding_period}

风险阈值:
- 最大回撤: ≤{config['max_drawdown']*100:.0f}%
- 年化收益: ≥{config['min_return']*100:.0f}%

偏好因子: {', '.join(config['preferred_factors'])}
"""
        return summary

    def list_all_users(self) -> List[Dict]:
        """
        列出所有用户

        Returns:
            用户列表
        """
        return [user.to_dict() for user in self.users.values()]


# 测试代码
if __name__ == "__main__":
    # 创建用户画像管理器
    manager = ProfileManager()

    print("=" * 60)
    print("用户画像管理演示")
    print("=" * 60)

    # 获取默认用户
    user = manager.get_user("root")
    print(f"\n默认用户: {user.username}")
    print(manager.get_user_summary("root"))

    # 测试创建新用户
    print("\n" + "=" * 60)
    print("创建新用户演示")
    print("=" * 60)

    new_user = manager.create_user(
        user_id="test_user",
        username="测试用户",
        market_preference="美股",
        risk_level="激进型",
        return_target=0.15,
        holding_period="长期"
    )

    print(f"\n新用户: {new_user.username}")
    print(manager.get_user_summary("test_user"))

    # 测试策略兼容性
    print("\n" + "=" * 60)
    print("策略兼容性测试")
    print("=" * 60)

    test_strategy = {
        'name': '均线交叉策略',
        'market': 'BOTH',
        'annual_return': 0.12,
        'max_drawdown': 0.08
    }

    compatibility = manager.validate_strategy_compatibility("root", test_strategy)
    print(f"\n策略: {test_strategy['name']}")
    print(f"兼容性: {compatibility['compatible']}")
    print(f"原因: {compatibility['reason']}")
