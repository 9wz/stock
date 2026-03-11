#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略层 - Strategy Layer
内置5个经典策略和回测框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class BacktestEngine:
    """
    回测引擎
    负责策略回测和绩效计算
    """

    def __init__(self, commission_rate: float = 0.0005, slippage: float = 0.001):
        """
        初始化回测引擎

        Args:
            commission_rate: 手续费率（默认0.05%）
            slippage: 滑点（默认0.1%）
        """
        self.commission_rate = commission_rate
        self.slippage = slippage

    def calculate_returns(self, prices: pd.Series, positions: pd.Series) -> pd.Series:
        """
        计算策略收益

        Args:
            prices: 价格序列
            positions: 持仓序列（0或1）

        Returns:
            收益序列
        """
        price_returns = prices.pct_change()
        # 买入持有收益
        strategy_returns = positions.shift(1) * price_returns

        # 扣除手续费和滑点
        # 手续费在交易时扣除
        trades = positions.diff().abs()
        commission_cost = trades * self.commission_rate
        slippage_cost = trades * self.slippage

        # 净收益
        net_returns = strategy_returns - commission_cost - slippage_cost
        return net_returns.fillna(0)

    def calculate_performance(self, returns: pd.Series) -> Dict:
        """
        计算回测绩效指标

        Args:
            returns: 收益序列

        Returns:
            绩效指标字典
        """
        if len(returns) == 0:
            return {}

        # 累计收益
        cumulative_returns = (1 + returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1

        # 年化收益
        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / n_days) - 1

        # 夏普比率（无风险利率3%）
        risk_free_rate = 0.03
        excess_returns = returns - risk_free_rate / 252
        if returns.std() > 0:
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()
        else:
            sharpe_ratio = 0

        # 最大回撤
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # 胜率
        winning_trades = (returns > 0).sum()
        total_trades = (returns != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # 盈亏比
        avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # ========== 新增高级绩效指标 ==========

        # Calmar比率（年化收益/最大回撤）
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino比率（只考虑下行波动率）
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_std if downside_std > 0 else 0

        # VaR (Value at Risk) - 95%置信度
        var_95 = np.percentile(returns, 5)

        # CVaR (Conditional VaR) - 尾部风险
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95

        # Omega比率
        threshold = 0
        gains = returns[returns > threshold].sum()
        losses = abs(returns[returns < threshold].sum())
        omega_ratio = gains / losses if losses > 0 else 0

        # 信息比率（相对于基准的超额收益稳定性）
        benchmark_returns = returns  # 简化：使用策略收益作为基准
        tracking_error = (returns - benchmark_returns).std() * np.sqrt(252)
        information_ratio = (annual_return - risk_free_rate) / tracking_error if tracking_error > 0 else 0

        # 偏度和峰度
        skewness = returns.skew() if len(returns) > 2 else 0
        kurtosis = returns.kurtosis() if len(returns) > 3 else 0

        # 盈利交易占比
        profit_trades = (returns > 0).sum()
        total_active_trades = (returns != 0).sum()
        trade_profit_ratio = profit_trades / total_active_trades if total_active_trades > 0 else 0

        return {
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'profit_loss_ratio': float(profit_loss_ratio),
            'n_trades': int(total_trades),
            # 新增指标
            'calmar_ratio': float(calmar_ratio),
            'sortino_ratio': float(sortino_ratio),
            'var_95': float(var_95),
            'cvar_95': float(cvar_95),
            'omega_ratio': float(omega_ratio),
            'information_ratio': float(information_ratio),
            'skewness': float(skewness),
            'kurtosis': float(kurtosis),
            'trade_profit_ratio': float(trade_profit_ratio)
        }


class Strategy:
    """
    策略基类
    """

    def __init__(self, name: str, market: str = 'A'):
        """
        初始化策略

        Args:
            name: 策略名称
            market: 适用市场 ('A' = A股, 'US' = 美股, 'BOTH' = 双市场)
        """
        self.name = name
        self.market = market
        self.backtest_engine = BacktestEngine()

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成交易信号

        Args:
            df: 包含价格数据的DataFrame

        Returns:
            持仓信号序列（0或1）
        """
        raise NotImplementedError

    def backtest(self, df: pd.DataFrame) -> Dict:
        """
        回测策略

        Args:
            df: 包含价格数据的DataFrame

        Returns:
            回测结果
        """
        if 'close' not in df.columns:
            return {}

        signals = self.generate_signals(df)
        returns = self.backtest_engine.calculate_returns(df['close'], signals)
        performance = self.backtest_engine.calculate_performance(returns)

        # 返回可JSON序列化的结果
        result = {
            'strategy_name': self.name,
            'market': self.market,
            **performance
        }
        return result

    def get_description(self) -> str:
        """
        获取策略描述

        Returns:
            策略描述
        """
        return ""


class MACrossoverStrategy(Strategy):
    """
    策略1: 均线交叉策略
    MA5上穿MA20买入，下穿卖出
    """

    def __init__(self):
        super().__init__("均线交叉策略", "BOTH")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成均线交叉信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        ma5 = df['close'].rolling(5).mean()
        ma20 = df['close'].rolling(20).mean()

        # 金叉买入，死叉卖出
        signal = pd.Series(0, index=df.index)
        crossover = (ma5 > ma20) & (ma5.shift(1) <= ma20.shift(1))
        crossunder = (ma5 < ma20) & (ma5.shift(1) >= ma20.shift(1))

        position = 0
        for i in range(len(df)):
            if crossover.iloc[i]:
                position = 1
            elif crossunder.iloc[i]:
                position = 0
            signal.iloc[i] = position

        return signal

    def get_description(self) -> str:
        return "MA5上穿MA20买入，下穿卖出。适用于趋势明显的市场，建议A股和美股均适用。"


class RSIStrategy(Strategy):
    """
    策略2: RSI超买超卖策略
    RSI<30买入，RSI>70卖出
    """

    def __init__(self):
        super().__init__("RSI超买超卖策略", "BOTH")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成RSI超买超卖信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        signal = pd.Series(0, index=df.index)
        signal[rsi < 30] = 1  # 超卖买入
        signal[rsi > 70] = 0  # 超卖卖出

        # 保持持仓
        signal = signal.replace(0, np.nan).ffill().fillna(0)

        return signal

    def get_description(self) -> str:
        return "RSI<30为超卖区域买入信号，RSI>70为超买区域卖出信号。适合震荡市场。"


class LowPEHighROEStrategy(Strategy):
    """
    策略3: 低PE高ROE选股策略
    PE<20且ROE>15%，每月调仓
    """

    def __init__(self):
        super().__init__("低PE高ROE选股策略", "A")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成低PE高ROE选股信号"""
        if 'pe' not in df.columns or 'roe' not in df.columns:
            return pd.Series(0, index=df.index)

        signal = pd.Series(0, index=df.index)

        # PE<20 且 ROE>15%
        condition = (df['pe'] < 20) & (df['roe'] > 15)
        signal[condition] = 1

        # 每月调仓（仅在月份切换时重新评估，其余时间保持上月信号）
        if 'date' in df.columns:
            months = pd.to_datetime(df['date']).dt.to_period('M')
            month_changes = months != months.shift(1)
            # 在非换仓日保持前一个换仓日的信号
            rebalance_signal = signal.where(month_changes, np.nan)
            signal = rebalance_signal.ffill().fillna(0)

        return signal

    def get_description(self) -> str:
        return "选择低估值（PE<20）且高盈利（ROE>15%）的股票，每月调仓。适合价值投资。"


class VolatilityTimingStrategy(Strategy):
    """
    策略4: 波动率择时策略
    波动率<20%持仓，>30%空仓
    """

    def __init__(self):
        super().__init__("波动率择时策略", "BOTH")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成波动率择时信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        # 计算20日波动率
        returns = df['close'].pct_change()
        volatility = returns.rolling(20).std() * np.sqrt(252) * 100

        signal = pd.Series(0, index=df.index)

        # 波动率<20%持仓，>30%空仓
        signal[volatility < 20] = 1
        signal[volatility > 30] = 0

        # 平滑处理
        signal = signal.replace(0, np.nan).ffill().fillna(0)

        return signal

    def get_description(self) -> str:
        return "波动率<20%时持仓，>30%时空仓。通过控制波动率来管理风险。"


class USTrendStrategy(Strategy):
    """
    策略5: 美股趋势跟踪策略
    股价站上MA60买入，跌破卖出
    """

    def __init__(self):
        super().__init__("美股趋势跟踪策略", "US")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成趋势跟踪信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        ma60 = df['close'].rolling(60).mean()

        signal = pd.Series(0, index=df.index)
        above_ma = df['close'] > ma60

        # 站上MA60买入，跌破卖出
        position = 0
        for i in range(len(df)):
            if above_ma.iloc[i]:
                position = 1
            else:
                position = 0
            signal.iloc[i] = position

        return signal

    def get_description(self) -> str:
        return "股价站上MA60均线买入，跌破MA60卖出。适合长线趋势跟踪，主要用于美股。"


class MomentumStrategy(Strategy):
    """
    策略6: 动量策略
    过去N个月涨幅靠前的股票继续上涨
    """

    def __init__(self, lookback: int = 20):
        super().__init__("动量策略", "BOTH")
        self.lookback = lookback  # 动量周期

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成动量信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        # 计算过去N日累计收益
        momentum = df['close'].pct_change(self.lookback)

        signal = pd.Series(0, index=df.index)
        # 动量为正持有
        signal[momentum > 0] = 1
        signal[momentum <= 0] = 0

        # 平滑处理
        signal = signal.replace(0, np.nan).ffill().fillna(0)

        return signal

    def get_description(self) -> str:
        return f"基于{self.lookback}日动量的趋势策略，买入过去上涨的股票。适合趋势明显的市场。"


class MeanReversionStrategy(Strategy):
    """
    策略7: 均值回归策略
    价格偏离均线过多时反向交易
    """

    def __init__(self, ma_period: int = 20, threshold: float = 0.05):
        super().__init__("均值回归策略", "BOTH")
        self.ma_period = ma_period
        self.threshold = threshold  # 偏离阈值

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成均值回归信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        ma = df['close'].rolling(self.ma_period).mean()
        deviation = (df['close'] - ma) / ma

        signal = pd.Series(0, index=df.index)
        # 价格低于均线threshold时买入
        signal[deviation < -self.threshold] = 1
        # 价格高于均线threshold时卖出
        signal[deviation > self.threshold] = 0

        # 其他情况保持持仓
        signal = signal.replace(0, np.nan).ffill().fillna(0)

        return signal

    def get_description(self) -> str:
        return f"基于{self.ma_period}日均线的均值回归策略，偏离超过{self.threshold*100}%时反向交易。适合震荡市场。"


class TurtleStrategy(Strategy):
    """
    策略8: 海龟交易策略
    突破N日高点买入，跌破M日低点卖出
    """

    def __init__(self, entry_period: int = 20, exit_period: int = 10):
        super().__init__("海龟交易策略", "BOTH")
        self.entry_period = entry_period  # 入场突破周期
        self.exit_period = exit_period    # 出场周期

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成海龟交易信号"""
        if 'close' not in df.columns:
            return pd.Series(0, index=df.index)

        # 突破20日高点入场
        entry_high = df['close'].rolling(self.entry_period).max()
        # 跌破10日低点出场
        exit_low = df['close'].rolling(self.exit_period).min()

        signal = pd.Series(0, index=df.index)

        # 突破高点买入
        signal[df['close'] > entry_high.shift(1)] = 1
        # 跌破低点卖出
        signal[df['close'] < exit_low.shift(1)] = 0

        # 保持持仓
        signal = signal.replace(0, np.nan).ffill().fillna(0)

        return signal

    def get_description(self) -> str:
        return f"突破{self.entry_period}日高点买入，跌破{self.exit_period}日低点卖出。经典趋势跟踪策略。"


class StrategyPool:
    """
    策略池
    管理所有内置策略
    """

    def __init__(self):
        """初始化策略池"""
        self.strategies = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        """注册默认策略"""
        # 策略1: 均线交叉策略
        ma_strategy = MACrossoverStrategy()
        self.strategies['ma_crossover'] = {
            'name': ma_strategy.name,
            'instance': ma_strategy,
            'description': ma_strategy.get_description(),
            'market': ma_strategy.market,
            'annual_return': 0.12,  # 预期年化收益
            'max_drawdown': 0.08,   # 预期最大回撤
            'sharpe_ratio': 1.5,     # 预期夏普比率
            'factors': ['MA5', 'MA20'],
            'factor_ic': {'MA20': 0.22}
        }

        # 策略2: RSI超买超卖策略
        rsi_strategy = RSIStrategy()
        self.strategies['rsi_oversold'] = {
            'name': rsi_strategy.name,
            'instance': rsi_strategy,
            'description': rsi_strategy.get_description(),
            'market': rsi_strategy.market,
            'annual_return': 0.10,
            'max_drawdown': 0.12,
            'sharpe_ratio': 1.2,
            'factors': ['RSI'],
            'factor_ic': {'RSI': 0.15}
        }

        # 策略3: 低PE高ROE策略
        pe_roe_strategy = LowPEHighROEStrategy()
        self.strategies['low_pe_roe'] = {
            'name': pe_roe_strategy.name,
            'instance': pe_roe_strategy,
            'description': pe_roe_strategy.get_description(),
            'market': pe_roe_strategy.market,
            'annual_return': 0.15,
            'max_drawdown': 0.18,
            'sharpe_ratio': 1.3,
            'factors': ['PE', 'ROE'],
            'factor_ic': {'PE': -0.18, 'ROE': 0.25}
        }

        # 策略4: 波动率择时策略
        vol_strategy = VolatilityTimingStrategy()
        self.strategies['volatility_timing'] = {
            'name': vol_strategy.name,
            'instance': vol_strategy,
            'description': vol_strategy.get_description(),
            'market': vol_strategy.market,
            'annual_return': 0.08,
            'max_drawdown': 0.06,
            'sharpe_ratio': 1.8,
            'factors': ['VOLATILITY'],
            'factor_ic': {'VOLATILITY': -0.12}
        }

        # 策略5: 美股趋势跟踪策略
        us_trend_strategy = USTrendStrategy()
        self.strategies['us_trend'] = {
            'name': us_trend_strategy.name,
            'instance': us_trend_strategy,
            'description': us_trend_strategy.get_description(),
            'market': us_trend_strategy.market,
            'annual_return': 0.14,
            'max_drawdown': 0.15,
            'sharpe_ratio': 1.4,
            'factors': ['MA60'],
            'factor_ic': {'MA60': 0.20}
        }

        # 策略6: 动量策略
        momentum_strategy = MomentumStrategy()
        self.strategies['momentum'] = {
            'name': momentum_strategy.name,
            'instance': momentum_strategy,
            'description': momentum_strategy.get_description(),
            'market': momentum_strategy.market,
            'annual_return': 0.16,
            'max_drawdown': 0.20,
            'sharpe_ratio': 1.1,
            'factors': ['MOMENTUM'],
            'factor_ic': {'MOMENTUM': 0.18}
        }

        # 策略7: 均值回归策略
        mean_reversion_strategy = MeanReversionStrategy()
        self.strategies['mean_reversion'] = {
            'name': mean_reversion_strategy.name,
            'instance': mean_reversion_strategy,
            'description': mean_reversion_strategy.get_description(),
            'market': mean_reversion_strategy.market,
            'annual_return': 0.09,
            'max_drawdown': 0.10,
            'sharpe_ratio': 1.3,
            'factors': ['MA20', 'DEVIATION'],
            'factor_ic': {'MA20': 0.10}
        }

        # 策略8: 海龟交易策略
        turtle_strategy = TurtleStrategy()
        self.strategies['turtle'] = {
            'name': turtle_strategy.name,
            'instance': turtle_strategy,
            'description': turtle_strategy.get_description(),
            'market': turtle_strategy.market,
            'annual_return': 0.18,
            'max_drawdown': 0.22,
            'sharpe_ratio': 1.2,
            'factors': ['HIGH', 'LOW'],
            'factor_ic': {'HIGH': 0.15}
        }

    def get_strategy(self, name: str) -> Optional[Dict]:
        """
        获取策略

        Args:
            name: 策略名称或键名

        Returns:
            策略字典
        """
        return self.strategies.get(name)

    def get_all_strategies(self) -> List[Dict]:
        """
        获取所有策略

        Returns:
            策略列表
        """
        return [
            {
                'key': key,
                **value
            }
            for key, value in self.strategies.items()
            if key != 'instance'
        ]

    def get_strategies_by_market(self, market: str) -> List[Dict]:
        """
        按市场筛选策略

        Args:
            market: 市场类型 ('A', 'US', 'BOTH')

        Returns:
            符合条件的策略列表
        """
        result = []
        for key, value in self.strategies.items():
            if value['market'] in [market, 'BOTH']:
                result.append({
                    'key': key,
                    **value
                })
        return result

    def run_backtest(self, df: pd.DataFrame, strategy_key: str) -> Dict:
        """
        运行回测

        Args:
            df: 包含价格数据的DataFrame
            strategy_key: 策略键名

        Returns:
            回测结果
        """
        strategy_info = self.strategies.get(strategy_key)
        if not strategy_info:
            return {}

        instance = strategy_info['instance']
        return instance.backtest(df)


# 测试代码
if __name__ == "__main__":
    # 生成模拟数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=250, freq='D')
    n = len(dates)

    # 模拟股价走势
    prices = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.015))
    volumes = np.random.randint(1000000, 10000000, n)
    pes = np.random.uniform(10, 30, n)
    roes = np.random.uniform(10, 25, n)

    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'volume': volumes,
        'pe': pes,
        'roe': roes
    })

    print("=" * 60)
    print("策略回测演示")
    print("=" * 60)

    # 创建策略池
    pool = StrategyPool()

    # 回测所有策略
    for key, info in pool.strategies.items():
        print(f"\n策略: {info['name']}")
        print(f"描述: {info['description']}")

        result = pool.run_backtest(df, key)
        if result:
            print(f"  年化收益: {result.get('annual_return', 0)*100:.2f}%")
            print(f"  夏普比率: {result.get('sharpe_ratio', 0):.2f}")
            print(f"  最大回撤: {result.get('max_drawdown', 0)*100:.2f}%")
            print(f"  胜率: {result.get('win_rate', 0)*100:.2f}%")

    print("\n" + "=" * 60)
    print("策略列表")
    print("=" * 60)
    all_strategies = pool.get_all_strategies()
    for s in all_strategies:
        print(f"- {s['name']} (市场: {s['market']})")
