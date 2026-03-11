#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""策略池和回测引擎的基础测试"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.strategy_pool import (
    BacktestEngine,
    MACrossoverStrategy,
    RSIStrategy,
    LowPEHighROEStrategy,
    VolatilityTimingStrategy,
    MomentumStrategy,
    StrategyPool,
)


class TestBacktestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = BacktestEngine(commission_rate=0.0005, slippage=0.001)

    def test_calculate_returns_all_holding(self):
        prices = pd.Series([100, 102, 101, 105, 103])
        positions = pd.Series([1, 1, 1, 1, 1])
        returns = self.engine.calculate_returns(prices, positions)
        self.assertEqual(len(returns), len(prices))
        # 第一个值应该是 0（无前值）
        self.assertAlmostEqual(returns.iloc[0], 0, places=5)

    def test_calculate_returns_no_holding(self):
        prices = pd.Series([100, 102, 101, 105, 103])
        positions = pd.Series([0, 0, 0, 0, 0])
        returns = self.engine.calculate_returns(prices, positions)
        # 不持仓时收益应该为 0（扣除首日）
        self.assertTrue((returns.abs() < 1e-10).all())

    def test_calculate_performance_basic(self):
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        perf = self.engine.calculate_performance(returns)
        self.assertIn('total_return', perf)
        self.assertIn('annual_return', perf)
        self.assertIn('sharpe_ratio', perf)
        self.assertIn('max_drawdown', perf)
        self.assertIn('win_rate', perf)
        self.assertLessEqual(perf['max_drawdown'], 0)

    def test_calculate_performance_empty(self):
        returns = pd.Series([], dtype=float)
        perf = self.engine.calculate_performance(returns)
        self.assertEqual(perf, {})


class TestMACrossoverStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = MACrossoverStrategy()
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'date': dates,
            'close': np.cumsum(np.random.normal(0.5, 1, 100)) + 100,
        })

    def test_generate_signals_shape(self):
        signals = self.strategy.generate_signals(self.df)
        self.assertEqual(len(signals), len(self.df))

    def test_signal_values_binary(self):
        signals = self.strategy.generate_signals(self.df)
        unique_vals = set(signals.unique())
        self.assertTrue(unique_vals.issubset({0, 1}))


class TestLowPEHighROEStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = LowPEHighROEStrategy()

    def test_signal_values_are_binary(self):
        """修复后的信号应保持 0/1，不会出现 >1 的值"""
        dates = pd.date_range('2023-01-01', periods=120, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'close': np.random.normal(100, 5, 120),
            'pe': np.random.uniform(10, 30, 120),
            'roe': np.random.uniform(10, 25, 120),
        })
        signals = self.strategy.generate_signals(df)
        self.assertTrue((signals >= 0).all())
        self.assertTrue((signals <= 1).all(), f"信号最大值为 {signals.max()}，应该 <=1")

    def test_no_pe_roe_columns(self):
        df = pd.DataFrame({'close': [100, 101, 102]})
        signals = self.strategy.generate_signals(df)
        self.assertTrue((signals == 0).all())


class TestStrategyPool(unittest.TestCase):
    def test_strategies_dict_not_empty(self):
        pool = StrategyPool()
        self.assertIsInstance(pool.strategies, dict)
        self.assertGreater(len(pool.strategies), 0)

    def test_strategies_have_names(self):
        pool = StrategyPool()
        for key, info in pool.strategies.items():
            self.assertIn('name', info)
            self.assertTrue(len(info['name']) > 0)


if __name__ == '__main__':
    unittest.main()
