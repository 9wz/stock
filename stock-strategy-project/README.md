# 量化策略推荐系统

A股+美股智能策略匹配系统

## 项目架构

本系统采用6层架构设计：

```
├── 数据层 (data/)
│   └── data_loader.py     # A股/美股数据拉取、清洗、存储
│
├── 因子层 (factors/)
│   └── factor_engine.py   # 10个核心因子计算、因子有效性验证
│
├── 策略层 (strategies/)
│   └── strategy_pool.py  # 5个经典策略、回测框架
│
├── 用户画像层 (user_profile/)
│   └── profile_manager.py # 用户标签录入、量化规则
│
├── 推荐引擎层 (recommendation/)
│   └── recommender.py     # 策略筛选、匹配度计算、推荐排序
│
└── 输出层 (output/)
    └── visualization.py   # 可视化、报告生成、交互功能
```

## 功能特性

### 1. 数据层
- 自动拉取A股（全市场）、美股（标普500+纳指100）的日线数据
- 数据清洗：缺失值处理、复权计算、剔除ST/停牌标的
- SQLite本地存储

### 2. 因子层
- 18个核心因子：MA5/MA20/MA60、RSI、MACD、换手率、PE、PB、ROE、波动率、最大回撤、动量、布林带、威廉指标、ATR、OBV、KDJ、CCI、ADX
- 因子有效性验证：IC值、Rank IC计算、分层回测
- 因子有效性排名输出

### 3. 策略层
- 8个内置策略：
  1. 均线交叉策略（MA5上穿MA20买入）
  2. RSI超买超卖策略（RSI<30买入，>70卖出）
  3. 低PE高ROE选股策略（PE<20且ROE>15%）
  4. 波动率择时策略（波动率<20%持仓，>30%空仓）
  5. 美股趋势跟踪策略（站上MA60买入）
  6. 动量策略（过去20日涨幅买入）
  7. 均值回归策略（偏离均线5%反向交易）
  8. 海龟交易策略（突破20日高点买入）
- 回测框架：手续费0.05%、滑点0.1%
- 绩效指标：年化收益、夏普比率、最大回撤、胜率、盈亏比、Calmar比率、Sortino比率、VaR、Omega比率

### 4. 用户画像层
- 用户标签：市场偏好、风险等级、收益目标、持仓周期
- 量化规则：
  - 保守型：最大回撤≤10%，年化收益≥5%
  - 稳健型：最大回撤≤15%，年化收益≥10%
  - 激进型：最大回撤≤20%，年化收益≥15%

### 5. 推荐引擎层
- 策略筛选：根据用户画像过滤不符合策略
- 匹配度计算：如目标年化10%，策略11%则匹配度90%
- 推荐排序：匹配度60%权重 + 策略评分40%权重
- 输出Top3推荐策略及理由

### 6. 输出层
- 可视化：收益曲线、因子IC热力图、策略对比图
- 报告生成：Markdown格式推荐报告
- 交互功能：实时重新推荐

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 方式1: Web界面
```bash
python web_app.py
# 打开浏览器访问 http://localhost:5000
```

### 方式2: 命令行
```bash
# 基本推荐
python main.py --user root

# 指定股票分析
python main.py --user root --ticker 600519.SH --market A

# 生成报告
python main.py --user root --report

# 交互式界面
python main.py --interactive
```

### 方式3: Python API
```python
from main import QuantSystem

# 初始化系统
system = QuantSystem()

# 获取推荐
recommendations = system.get_recommendations("root")

# 因子分析
analysis = system.get_factor_analysis("600519.SH", "A")

# 生成报告
report_path = system.generate_full_report("root")
```

## 默认用户

- 用户名: root
- 密码: root (Web界面登录)
- 市场偏好: 双市场
- 风险等级: 稳健型
- 收益目标: 10%
- 持仓周期: 中期

## 示例输出

```
推荐策略（用户: root）
============================================================

推荐 1: 均线交叉策略
  年化收益: 12.0%
  夏普比率: 1.50
  最大回撤: 8.0%
  匹配度: 85.0
  核心因子: MA5, MA20

推荐 2: 波动率择时策略
  年化收益: 8.0%
  夏普比率: 1.80
  最大回撤: 6.0%
  匹配度: 90.0
  核心因子: VOLATILITY
```

## 依赖说明

| 库 | 用途 |
|---|---|
| akshare | A股数据获取 |
| yfinance | 美股数据获取 |
| pandas | 数据处理 |
| numpy | 数值计算 |
| scipy | 统计分析 |
| matplotlib | 基础可视化 |
| plotly | 交互式图表 |
| flask | Web框架 |

## 注意事项

1. 首次运行需联网下载数据
2. A股数据需要akshare库支持
3. 美股数据需要yfinance库支持
4. 建议使用虚拟环境运行
