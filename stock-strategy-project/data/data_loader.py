#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据层 - Data Layer
负责A股、美股数据拉取、清洗、存储
"""

import sqlite3
import os
import warnings
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

# 尝试导入数据源
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告: 未安装akshare，A股数据将无法获取")

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("警告: 未安装yfinance，美股数据将无法获取")


class DataLoader:
    """
    数据加载器类
    负责从A股(akshare)和美股(yfinance)拉取数据并存储到SQLite
    """

    def __init__(self, db_path: str = "stock_data.db"):
        """
        初始化数据加载器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 股票日线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                market TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                turnover_rate REAL,
                pe REAL,
                pb REAL,
                roe REAL,
                is_st INTEGER DEFAULT 0,
                is_halted INTEGER DEFAULT 0,
                adjusted_close REAL,
                UNIQUE(ticker, date, market)
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_date
            ON stock_daily(ticker, date)
        ''')

        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")

    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    # ==================== A股数据拉取 ====================

    def fetch_a_stock_list(self) -> List[str]:
        """
        获取A股股票列表

        Returns:
            股票代码列表
        """
        if not AKSHARE_AVAILABLE:
            return self._get_sample_a_stocks()

        try:
            # 获取A股所有股票
            df = ak.stock_info_a_code_name()
            stocks = df['code'].tolist()[:100]  # 取前100只作为演示
            return [f"{s}.SH" if s.startswith('6') else f"{s}.SZ" for s in stocks]
        except Exception as e:
            print(f"获取A股列表失败: {e}")
            return self._get_sample_a_stocks()

    def _get_sample_a_stocks(self) -> List[str]:
        """获取示例A股列表（主要指数成分股）"""
        return [
            '600519.SH', '000858.SZ', '601318.SH', '600036.SH', '000333.SZ',
            '600900.SH', '601888.SH', '600276.SH', '601166.SH', '600030.SH',
            '000001.SZ', '399001.SZ', '399006.SZ'  # 指数
        ]

    def fetch_a_stock_daily(self, ticker: str, start_date: str = None,
                           end_date: str = None) -> pd.DataFrame:
        """
        获取A股日线数据

        Args:
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含OHLCV的DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        try:
            # 使用akshare获取数据
            symbol = ticker.split('.')[0]
            df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date,
                                    end_date=end_date, adjust="qfq")

            if df is not None and not df.empty:
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amplitude',
                             'change_pct', 'change', 'turnover']
                df['ticker'] = ticker
                df['market'] = 'A'
                df['date'] = pd.to_datetime(df['date'])
                return df
        except Exception as e:
            print(f"获取{ticker}数据失败: {e}")

        return pd.DataFrame()

    def fetch_a_stock_financial(self, ticker: str) -> Dict:
        """
        获取A股财务数据

        Args:
            ticker: 股票代码

        Returns:
            财务数据字典
        """
        if not AKSHARE_AVAILABLE:
            return {'pe': None, 'pb': None, 'roe': None}

        try:
            symbol = ticker.split('.')[0]
            df = ak.stock_individual_info_em(symbol=symbol)

            data = {}
            for _, row in df.iterrows():
                if '市盈率' in row.get('item', ''):
                    data['pe'] = row.get('value')
                elif '市净率' in row.get('item', ''):
                    data['pb'] = row.get('value')
                elif '净资产收益率' in row.get('item', ''):
                    data['roe'] = row.get('value')

            return data
        except Exception as e:
            print(f"获取{ticker}财务数据失败: {e}")
            return {'pe': None, 'pb': None, 'roe': None}

    # ==================== 美股数据拉取 ====================

    def fetch_us_stock_list(self) -> List[str]:
        """
        获取美股股票列表（标普500 + 纳指100）

        Returns:
            股票代码列表
        """
        # 标普500成分股 + 纳指100成分股
        us_stocks = [
            # 标普500主要成分股
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ',
            'V', 'XOM', 'JPM', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV', 'PEP',
            'KO', 'COST', 'AVGO', 'LLY', 'TMO', 'WMT', 'MCD', 'CSCO', 'ACN', 'ABT',
            'DHR', 'ADBE', 'CRM', 'WFC', 'TXN', 'NKE', 'PM', 'NEE', 'UNP', 'BMY',
            'ORCL', 'RTX', 'HON', 'QCOM', 'LOW', 'INTC', 'IBM', 'AMD', 'CAT', 'GE',
            'INTU', 'GS', 'AMAT', 'BLK', 'DE', 'MDT', 'GILD', 'ADP', 'ISRG', 'TGT',
            # 纳指100主要成分股
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'AMD', 'INTC',
            'NFLX', 'ADBE', 'CRM', 'PYPL', 'SQ', 'SHOP', 'UBER', 'SNAP', 'TWTR', 'ZM',
            'COIN', 'RBLX', 'DDOG', 'CRWD', 'SNOW', 'NET', 'MDB', 'OKTA', 'SPLK', 'TEAM'
        ]
        return list(set(us_stocks))

    def fetch_us_stock_daily(self, ticker: str, start_date: str = None,
                             end_date: str = None) -> pd.DataFrame:
        """
        获取美股日线数据

        Args:
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含OHLCV的DataFrame
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)

        if not YFINANCE_AVAILABLE:
            return pd.DataFrame()

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)

            if df is not None and not df.empty:
                df = df.reset_index()
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'dividend', 'stock_splits']
                df['ticker'] = ticker
                df['market'] = 'US'
                return df
        except Exception as e:
            print(f"获取{ticker}数据失败: {e}")

        return pd.DataFrame()

    def fetch_us_stock_financial(self, ticker: str) -> Dict:
        """
        获取美股财务数据

        Args:
            ticker: 股票代码

        Returns:
            财务数据字典
        """
        if not YFINANCE_AVAILABLE:
            return {'pe': None, 'pb': None, 'roe': None}

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'pe': info.get('forwardPE') or info.get('trailingPE'),
                'pb': info.get('priceToBook'),
                'roe': info.get('returnOnEquity')
            }
        except Exception as e:
            print(f"获取{ticker}财务数据失败: {e}")
            return {'pe': None, 'pb': None, 'roe': None}

    # ==================== 数据清洗 ====================

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗函数
        - 处理缺失值（前值填充）
        - 复权计算
        - 剔除ST/停牌标的

        Args:
            df: 原始数据DataFrame

        Returns:
            清洗后的DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        # 1. 处理缺失值 - 前值填充
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'pe', 'pb', 'roe']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')

        # 2. 复权计算（这里简化处理，实际需要获取复权因子）
        if 'adjusted_close' not in df.columns and 'close' in df.columns:
            df['adjusted_close'] = df['close']

        # 3. 标记ST股票（A股）
        if 'is_st' not in df.columns:
            df['is_st'] = 0

        # 4. 标记停牌（成交量为0视为停牌）
        if 'volume' in df.columns:
            df['is_halted'] = (df['volume'] == 0).astype(int)

        return df

    def remove_st_halted(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        剔除ST/停牌标的

        Args:
            df: 清洗后的数据

        Returns:
            过滤后的数据
        """
        if df.empty:
            return df

        df = df.copy()
        # 剔除停牌
        if 'is_halted' in df.columns:
            df = df[df['is_halted'] == 0]

        # 剔除ST（A股）
        if 'is_st' in df.columns:
            df = df[df['is_st'] == 0]

        return df

    # ==================== 数据存储 ====================

    def save_to_db(self, df: pd.DataFrame, market: str = 'A'):
        """
        保存数据到SQLite

        Args:
            df: 数据DataFrame
            market: 市场类型 ('A' 或 'US')
        """
        if df.empty:
            return

        conn = self._get_connection()

        # 准备插入数据
        records = []
        for _, row in df.iterrows():
            date_str = row['date']
            if isinstance(date_str, pd.Timestamp):
                date_str = date_str.strftime('%Y-%m-%d')

            record = (
                row.get('ticker', ''),
                market,
                date_str,
                row.get('open'),
                row.get('high'),
                row.get('low'),
                row.get('close'),
                row.get('volume'),
                row.get('turnover'),
                row.get('pe'),
                row.get('pb'),
                row.get('roe'),
                row.get('is_st', 0),
                row.get('is_halted', 0),
                row.get('adjusted_close', row.get('close'))
            )
            records.append(record)

        # 批量插入
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR REPLACE INTO stock_daily
            (ticker, market, date, open, high, low, close, volume,
             turnover_rate, pe, pb, roe, is_st, is_halted, adjusted_close)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)

        conn.commit()
        conn.close()
        print(f"已保存 {len(records)} 条数据到数据库")

    def load_from_db(self, ticker: str = None, market: str = None,
                    start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        从SQLite加载数据

        Args:
            ticker: 股票代码过滤
            market: 市场过滤 ('A' 或 'US')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame
        """
        conn = self._get_connection()

        query = "SELECT * FROM stock_daily WHERE 1=1"
        params = []

        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)

        if market:
            query += " AND market = ?"
            params.append(market)

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY ticker, date"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    # ==================== 批量数据拉取 ====================

    def fetch_all_a_stocks(self, limit: int = 50):
        """
        批量拉取A股数据

        Args:
            limit: 拉取数量限制
        """
        stocks = self.fetch_a_stock_list()[:limit]

        for i, ticker in enumerate(stocks):
            print(f"正在拉取A股 {ticker} ({i+1}/{len(stocks)})")
            try:
                df = self.fetch_a_stock_daily(ticker)
                df = self.clean_data(df)
                df = self.remove_st_halted(df)
                self.save_to_db(df, market='A')
            except Exception as e:
                print(f"  失败: {e}")

    def fetch_all_us_stocks(self, limit: int = 30):
        """
        批量拉取美股数据

        Args:
            limit: 拉取数量限制
        """
        stocks = self.fetch_us_stock_list()[:limit]

        for i, ticker in enumerate(stocks):
            print(f"正在拉取美股 {ticker} ({i+1}/{len(stocks)})")
            try:
                df = self.fetch_us_stock_daily(ticker)
                df = self.clean_data(df)
                self.save_to_db(df, market='US')
            except Exception as e:
                print(f"  失败: {e}")

    def get_representative_stocks(self, market: str = 'A', n: int = 20) -> List[str]:
        """
        获取代表性股票列表

        Args:
            market: 市场类型
            n: 数量

        Returns:
            股票代码列表
        """
        if market == 'A':
            # A股主要蓝筹股
            return [
                '600519.SH', '000858.SZ', '601318.SH', '600036.SH', '000333.SZ',
                '600900.SH', '601888.SH', '600276.SH', '601166.SH', '600030.SH',
                '600887.SH', '601857.SH', '600028.SH', '601012.SH', '600690.SH',
                '601398.SH', '601939.SH', '601288.SH', '601088.SH', '600030.SH'
            ][:n]
        else:
            # 美股主要科技股
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
                'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'HD', 'DIS',
                'NFLX', 'ADBE', 'CRM', 'PYPL', 'INTC'
            ][:n]


# 测试代码
if __name__ == "__main__":
    # 初始化数据加载器
    loader = DataLoader("stock_data.db")

    # 测试拉取数据
    print("=" * 50)
    print("测试A股数据拉取")
    print("=" * 50)
    df = loader.fetch_a_stock_daily("600519.SH")
    print(f"茅台数据: {len(df)} 条")
    print(df.tail())

    print("\n" + "=" * 50)
    print("测试美股数据拉取")
    print("=" * 50)
    df_us = loader.fetch_us_stock_daily("AAPL")
    print(f"苹果数据: {len(df_us)} 条")
    print(df_us.tail())
