#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子层 - Factor Layer
负责核心因子计算和因子有效性验证
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
import warnings

warnings.filterwarnings('ignore')


class FactorEngine:
    """
    因子引擎类
    内置10个核心因子计算函数和有效性验证函数
    """

    def __init__(self):
        """初始化因子引擎"""
        self.factor_registry = {
            'MA5': self.calculate_ma5,
            'MA20': self.calculate_ma20,
            'MA60': self.calculate_ma60,
            'RSI': self.calculate_rsi,
            'MACD': self.calculate_macd,
            'TURNOVER': self.calculate_turnover,
            'PE': self.get_pe_factor,
            'PB': self.get_pb_factor,
            'ROE': self.get_roe_factor,
            'VOLATILITY': self.calculate_volatility,
            'MAX_DRAWDOWN': self.calculate_max_drawdown,
            'TURNOVER_RATIO': self.calculate_turnover_ratio,
            # 新增因子
            'MOMENTUM': self.calculate_momentum,
            'BOLLINGER': self.calculate_bollinger,
            'WILLIAMS_R': self.calculate_williams_r,
            'ATR': self.calculate_atr,
            'OBV': self.calculate_obv,
            'STOCHASTIC': self.calculate_stochastic,
            'CCI': self.calculate_cci,
            'ADX': self.calculate_adx
        }

    # ==================== 基础因子计算函数 ====================

    def calculate_ma5(self, df: pd.DataFrame) -> pd.Series:
        """
        计算MA5（5日均线）

        Args:
            df: 包含close列的DataFrame

        Returns:
            MA5序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)
        return df['close'].rolling(window=5, min_periods=1).mean()

    def calculate_ma20(self, df: pd.DataFrame) -> pd.Series:
        """
        计算MA20（20日均线）

        Args:
            df: 包含close列的DataFrame

        Returns:
            MA20序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)
        return df['close'].rolling(window=20, min_periods=1).mean()

    def calculate_ma60(self, df: pd.DataFrame) -> pd.Series:
        """
        计算MA60（60日均线）

        Args:
            df: 包含close列的DataFrame

        Returns:
            MA60序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)
        return df['close'].rolling(window=60, min_periods=1).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算RSI（相对强弱指标）

        Args:
            df: 包含close列的DataFrame
            period: RSI周期，默认14

        Returns:
            RSI序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算MACD指标

        Args:
            df: 包含close列的DataFrame

        Returns:
            包含MACD, Signal, Hist的字典
        """
        if 'close' not in df.columns:
            return {'macd': pd.Series(dtype=float), 'signal': pd.Series(dtype=float), 'hist': pd.Series(dtype=float)}

        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal

        return {
            'macd': macd,
            'signal': signal,
            'hist': hist
        }

    def calculate_turnover(self, df: pd.DataFrame) -> pd.Series:
        """
        计算换手率

        Args:
            df: 包含volume和close列的DataFrame

        Returns:
            换手率序列
        """
        if 'volume' not in df.columns or 'close' not in df.columns:
            return pd.Series(dtype=float)

        # 简化计算：当日成交量 / 流通股本（这里用收盘价估算）
        # 实际需要获取流通股本数据
        turnover = df['volume'] / (df['volume'].rolling(20).mean() * 20)
        return turnover * 100  # 转为百分比

    def get_pe_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        获取PE（市盈率）因子

        Args:
            df: 包含pe列的DataFrame

        Returns:
            PE序列
        """
        if 'pe' not in df.columns:
            return pd.Series(dtype=float)
        return df['pe']

    def get_pb_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        获取PB（市净率）因子

        Args:
            df: 包含pb列的DataFrame

        Returns:
            PB序列
        """
        if 'pb' not in df.columns:
            return pd.Series(dtype=float)
        return df['pb']

    def get_roe_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        获取ROE（净资产收益率）因子

        Args:
            df: 包含roe列的DataFrame

        Returns:
            ROE序列
        """
        if 'roe' not in df.columns:
            return pd.Series(dtype=float)
        return df['roe']

    def calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算波动率（20日）

        Args:
            df: 包含close列的DataFrame
            period: 计算周期

        Returns:
            波动率序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)

        returns = df['close'].pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252) * 100  # 年化波动率
        return volatility

    def calculate_max_drawdown(self, df: pd.DataFrame, period: int = 60) -> pd.Series:
        """
        计算最大回撤（60日）

        Args:
            df: 包含close列的DataFrame
            period: 回看周期

        Returns:
            最大回撤序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)

        rolling_max = df['close'].rolling(window=period, min_periods=1).max()
        drawdown = (df['close'] - rolling_max) / rolling_max * 100
        return drawdown

    def calculate_turnover_ratio(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算成交额占比（相对于市场平均）

        Args:
            df: 包含volume列的DataFrame
            period: 计算周期

        Returns:
            成交额占比序列
        """
        if 'volume' not in df.columns:
            return pd.Series(dtype=float)

        avg_volume = df['volume'].rolling(window=period, min_periods=1).mean()
        volume_ratio = (df['volume'] - avg_volume) / avg_volume * 100
        return volume_ratio

    def calculate_momentum(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算动量因子（过去N日累计收益）

        Args:
            df: 包含close列的DataFrame
            period: 动量周期

        Returns:
            动量因子序列
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)

        momentum = df['close'].pct_change(period) * 100
        return momentum

    def calculate_bollinger(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算布林带因子（价格相对于布林带的位置）

        Args:
            df: 包含close列的DataFrame
            period: 布林带周期

        Returns:
            布林带因子序列（0-100）
        """
        if 'close' not in df.columns:
            return pd.Series(dtype=float)

        ma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        upper_band = ma + 2 * std
        lower_band = ma - 2 * std

        # 计算价格在布林带中的位置 (0-100)
        bb_position = (df['close'] - lower_band) / (upper_band - lower_band) * 100
        return bb_position

    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算威廉指标（Williams %R）

        Args:
            df: 包含high, low, close列的DataFrame
            period: 计算周期

        Returns:
            威廉指标序列（-100到0）
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series(dtype=float)

        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()

        williams_r = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        return williams_r

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算平均真实波幅（ATR）

        Args:
            df: 包含high, low, close列的DataFrame
            period: 计算周期

        Returns:
            ATR序列
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series(dtype=float)

        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """
        计算能量潮指标（OBV）

        Args:
            df: 包含close, volume列的DataFrame

        Returns:
            OBV序列
        """
        if 'close' not in df.columns or 'volume' not in df.columns:
            return pd.Series(dtype=float)

        price_change = df['close'].diff()
        obv = pd.Series(0, index=df.index)

        obv[price_change > 0] = df['volume']
        obv[price_change < 0] = -df['volume']
        obv[price_change == 0] = 0

        obv = obv.cumsum()
        return obv

    def calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算随机指标（KDJ的K值）

        Args:
            df: 包含high, low, close列的DataFrame
            period: 计算周期

        Returns:
            随机指标序列（0-100）
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series(dtype=float)

        lowest_low = df['low'].rolling(window=period).min()
        highest_high = df['high'].rolling(window=period).max()

        stochastic = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
        return stochastic

    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算商品通道指标（CCI）

        Args:
            df: 包含high, low, close列的DataFrame
            period: 计算周期

        Returns:
            CCI序列
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series(dtype=float)

        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        cci = (typical_price - sma) / (0.015 * mean_deviation)
        return cci

    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算平均趋向指数（ADX）

        Args:
            df: 包含high, low, close列的DataFrame
            period: 计算周期

        Returns:
            ADX序列
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series(dtype=float)

        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        atr = self.calculate_atr(df, period)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx

    # ==================== 组合因子计算 ====================

    def calculate_all_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有因子

        Args:
            df: 原始数据DataFrame

        Returns:
            包含所有因子的DataFrame
        """
        result = df.copy()

        # 计算各类因子
        result['MA5'] = self.calculate_ma5(df)
        result['MA20'] = self.calculate_ma20(df)
        result['MA60'] = self.calculate_ma60(df)
        result['RSI'] = self.calculate_rsi(df)
        result['TURNOVER'] = self.calculate_turnover(df)
        result['VOLATILITY'] = self.calculate_volatility(df)
        result['MAX_DRAWDOWN'] = self.calculate_max_drawdown(df)
        result['TURNOVER_RATIO'] = self.calculate_turnover_ratio(df)

        # MACD指标
        macd = self.calculate_macd(df)
        result['MACD'] = macd['macd']
        result['MACD_SIGNAL'] = macd['signal']
        result['MACD_HIST'] = macd['hist']

        # 新增因子
        result['MOMENTUM'] = self.calculate_momentum(df)
        result['BOLLINGER'] = self.calculate_bollinger(df)
        result['WILLIAMS_R'] = self.calculate_williams_r(df)
        result['ATR'] = self.calculate_atr(df)
        result['OBV'] = self.calculate_obv(df)
        result['STOCHASTIC'] = self.calculate_stochastic(df)
        result['CCI'] = self.calculate_cci(df)
        result['ADX'] = self.calculate_adx(df)

        # 财务因子
        if 'pe' in df.columns:
            result['PE'] = df['pe']
        if 'pb' in df.columns:
            result['PB'] = df['pb']
        if 'roe' in df.columns:
            result['ROE'] = df['roe']

        return result

    # ==================== 因子有效性验证 ====================

    def calculate_ic(self, factor_values: pd.Series, future_returns: pd.Series) -> float:
        """
        计算IC值（信息系数）
        衡量因子与未来收益的相关性

        Args:
            factor_values: 因子值序列
            future_returns: 未来收益序列

        Returns:
            IC值（-1到1之间）
        """
        # 去除NaN
        valid_mask = ~(factor_values.isna() | future_returns.isna())
        if valid_mask.sum() < 10:
            return 0.0

        factor_valid = factor_values[valid_mask]
        returns_valid = future_returns[valid_mask]

        if len(factor_valid) < 10:
            return 0.0

        try:
            # 皮尔逊相关系数
            ic, _ = stats.pearsonr(factor_valid, returns_valid)
            return ic if not np.isnan(ic) else 0.0
        except Exception:
            return 0.0

    def calculate_rank_ic(self, factor_values: pd.Series, future_returns: pd.Series) -> float:
        """
        计算Rank IC（秩相关系数）
        更稳健的IC计算方式

        Args:
            factor_values: 因子值序列
            future_returns: 未来收益序列

        Returns:
            Rank IC值
        """
        valid_mask = ~(factor_values.isna() | future_returns.isna())
        if valid_mask.sum() < 10:
            return 0.0

        factor_valid = factor_values[valid_mask]
        returns_valid = future_returns[valid_mask]

        try:
            ic, _ = stats.spearmanr(factor_valid, returns_valid)
            return ic if not np.isnan(ic) else 0.0
        except Exception:
            return 0.0

    def factor_backtest分层(self, df: pd.DataFrame, factor_name: str,
                           n_groups: int = 5) -> Dict:
        """
        分层回测
        将标的按因子值分n_groups层，计算每层收益

        Args:
            df: 包含因子和收益的DataFrame
            factor_name: 因子名称
            n_groups: 分组数量

        Returns:
            每层收益字典
        """
        if factor_name not in df.columns or 'return' not in df.columns:
            return {}

        valid_df = df.dropna(subset=[factor_name, 'return'])
        if len(valid_df) < n_groups:
            return {}

        # 分层
        valid_df['group'] = pd.qcut(valid_df[factor_name], q=n_groups, labels=False, duplicates='drop')

        # 计算每层收益
        group_returns = {}
        for group_id in range(n_groups):
            group_data = valid_df[valid_df['group'] == group_id]
            if len(group_data) > 0:
                group_returns[f'Group_{group_id+1}'] = group_data['return'].mean()

        return group_returns

    def validate_factor(self, df: pd.DataFrame, factor_name: str) -> Dict:
        """
        因子有效性验证
        计算IC值和分层回测结果

        Args:
            df: 包含因子和未来收益的DataFrame
            factor_name: 因子名称

        Returns:
            因子有效性评估结果
        """
        result = {
            'factor_name': factor_name,
            'ic': 0.0,
            'rank_ic': 0.0,
            'group_returns': {},
            'effectiveness': '未知'
        }

        if factor_name not in df.columns or 'return' not in df.columns:
            result['effectiveness'] = '数据不足'
            return result

        # 计算IC
        result['ic'] = self.calculate_ic(df[factor_name], df['return'])
        result['rank_ic'] = self.calculate_rank_ic(df[factor_name], df['return'])

        # 分层回测
        result['group_returns'] = self.factor_backtest分层(df, factor_name)

        # 评估有效性
        abs_ic = abs(result['ic'])
        if abs_ic > 0.1:
            result['effectiveness'] = '强有效'
        elif abs_ic > 0.05:
            result['effectiveness'] = '中等有效'
        elif abs_ic > 0.02:
            result['effectiveness'] = '弱有效'
        else:
            result['effectiveness'] = '无效'

        return result

    def rank_all_factors(self, df: pd.DataFrame) -> List[Dict]:
        """
        对所有内置因子进行有效性排名

        Args:
            df: 包含所有因子的DataFrame

        Returns:
            按IC值排序的因子有效性列表
        """
        results = []

        for factor_name in self.factor_registry.keys():
            # 如果因子列存在
            if factor_name in df.columns:
                validation = self.validate_factor(df, factor_name)
                results.append(validation)

        # 按IC绝对值排序
        results.sort(key=lambda x: abs(x['ic']), reverse=True)

        return results

    def get_factor_description(self, factor_name: str) -> str:
        """
        获取因子描述

        Args:
            factor_name: 因子名称

        Returns:
            因子描述字符串
        """
        descriptions = {
            'MA5': '5日移动平均线，短期趋势指标',
            'MA20': '20日移动平均线，中期趋势指标',
            'MA60': '60日移动平均线，长期趋势指标',
            'RSI': '相对强弱指标，衡量价格变动速度，超买超卖信号',
            'MACD': '指数平滑异同移动平均线，趋势动量指标',
            'TURNOVER': '换手率，衡量股票流动性',
            'PE': '市盈率，价值投资核心指标',
            'PB': '市净率，衡量股票估值',
            'ROE': '净资产收益率，衡量盈利能力',
            'VOLATILITY': '波动率，风险指标',
            'MAX_DRAWDOWN': '最大回撤，风险指标',
            'TURNOVER_RATIO': '成交额占比，衡量相对活跃度',
            # 新增因子描述
            'MOMENTUM': '动量因子，过去N日累计收益，趋势强度指标',
            'BOLLINGER': '布林带位置，价格相对于布林带的相对位置',
            'WILLIAMS_R': '威廉指标，超买超卖指标，-100到0之间',
            'ATR': '平均真实波幅，衡量市场波动程度',
            'OBV': '能量潮指标，成交量与价格趋势的累积',
            'STOCHASTIC': '随机指标（K值），超买超卖指标',
            'CCI': '商品通道指标，衡量价格偏离均值的程度',
            'ADX': '平均趋向指数，衡量趋势强度'
        }
        return descriptions.get(factor_name, '未知因子')


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    n = len(dates)

    # 生成模拟股价数据
    prices = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.02))
    volumes = np.random.randint(1000000, 10000000, n)
    pes = np.random.uniform(10, 50, n)
    pbs = np.random.uniform(1, 10, n)
    roes = np.random.uniform(5, 30, n)

    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'volume': volumes,
        'pe': pes,
        'pb': pbs,
        'roe': roes
    })

    # 计算未来收益（用于测试IC计算）
    df['return'] = df['close'].pct_change().shift(-1)

    # 创建因子引擎
    engine = FactorEngine()

    # 计算所有因子
    df_with_factors = engine.calculate_all_factors(df)

    print("=" * 60)
    print("因子计算结果示例（最后5行）")
    print("=" * 60)
    print(df_with_factors[['date', 'close', 'MA5', 'MA20', 'RSI', 'MACD', 'VOLATILITY']].tail())

    print("\n" + "=" * 60)
    print("因子有效性验证")
    print("=" * 60)

    # 验证单个因子
    for factor in ['MA20', 'RSI', 'PE', 'VOLATILITY']:
        result = engine.validate_factor(df_with_factors, factor)
        print(f"\n{factor}因子:")
        print(f"  IC值: {result['ic']:.4f}")
        print(f"  Rank IC: {result['rank_ic']:.4f}")
        print(f"  有效性: {result['effectiveness']}")

    print("\n" + "=" * 60)
    print("因子有效性排名")
    print("=" * 60)
    rankings = engine.rank_all_factors(df_with_factors)
    for i, r in enumerate(rankings, 1):
        print(f"{i}. {r['factor_name']}: IC={r['ic']:.4f}, 有效性={r['effectiveness']}")
