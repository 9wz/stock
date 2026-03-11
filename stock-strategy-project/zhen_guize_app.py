#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真规则推荐 - 基于《股市真规则》的股票分析系统
晨星公司投资哲学实践
"""

from flask import Flask, render_template_string, request, jsonify
import sys
import os
import random
import requests


# ========== 股票搜索函数 ==========
def get_a_stock_list_eastmoney():
    """从东方财富获取A股全部股票列表"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        # 沪市股票列表
        params_sh = {
            'pn': 1, 'pz': 5000, 'po': 1, 'np': 1,
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': 2, 'invt': 2, 'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:80',
            'fields': 'f12,f14'
        }
        # 深市股票列表
        params_sz = {
            'pn': 1, 'pz': 5000, 'po': 1, 'np': 1,
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': 2, 'invt': 2, 'fid': 'f3',
            'fs': 'm:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f12,f14'
        }

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        stocks = []

        try:
            response = requests.get(url, params=params_sh, headers=headers, timeout=10)
            data = response.json()
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    code = str(item.get('f12', ''))
                    name = item.get('f14', '')
                    if code and name:
                        stocks.append({'code': code + '.SH', 'name': name, 'market': 'A'})
        except:
            pass

        try:
            response = requests.get(url, params=params_sz, headers=headers, timeout=10)
            data = response.json()
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    code = str(item.get('f12', ''))
                    name = item.get('f14', '')
                    if code and name:
                        stocks.append({'code': code + '.SZ', 'name': name, 'market': 'A'})
        except:
            pass

        return stocks
    except Exception as e:
        return []


def get_us_stock_list():
    """获取美股主要股票列表"""
    us_stocks = [
        ('AAPL', '苹果'), ('MSFT', '微软'), ('GOOGL', '谷歌'), ('AMZN', '亚马逊'),
        ('META', 'Meta'), ('NVDA', '英伟达'), ('TSLA', '特斯拉'), ('BRK.B', '伯克希尔'),
        ('JPM', '摩根大通'), ('V', 'Visa'), ('JNJ', '强生'), ('WMT', '沃尔玛'),
        ('PG', '宝洁'), ('MA', '万事达'), ('UNH', '联合健康'), ('HD', '家得宝'),
        ('DIS', '迪士尼'), ('PYPL', 'PayPal'), ('BAC', '美国银行'), ('ADBE', 'Adobe'),
        ('CRM', 'Salesforce'), ('NFLX', 'Netflix'), ('INTC', '英特尔'), ('AMD', 'AMD'),
        ('CSCO', '思科'), ('PEP', '百事'), ('KO', '可口可乐'), ('NKE', '耐克'),
        ('T', 'AT&T'), ('VZ', '威瑞森'), ('MRK', '默克'), ('ABT', '雅培'),
        ('ORCL', '甲骨文'), ('ACN', '埃森哲'), ('TXN', '德州仪器'), ('QCOM', '高通'),
    ]
    return [{'code': code, 'name': name, 'market': 'US'} for code, name in us_stocks]


def fuzzy_search_stocks(keyword):
    """模糊搜索股票 - 东方财富实时API + Yahoo Finance"""
    if not keyword:
        return []

    keyword = keyword.strip()
    if len(keyword) < 1:
        return []

    results = []
    seen = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    # 1. 东方财富搜索API
    try:
        import urllib.parse
        url = f"https://searchapi.eastmoney.com/api/suggest/get?input={urllib.parse.quote(keyword)}&type=14,12,6&count=50"
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        for table_name in ['QuotationCodeTable', 'Blog']:
            if data.get(table_name) and data[table_name].get('Data'):
                for item in data[table_name]['Data']:
                    code = item.get('Code', '')
                    name = item.get('Name', '')
                    classify = item.get('Classify', '')

                    if classify == 'AStock':
                        if code.startswith('6') or code.startswith('5'):
                            code = code + '.SH'
                        elif code.startswith('0') or code.startswith('3'):
                            code = code + '.SZ'
                        else:
                            continue
                        if code not in seen:
                            seen.add(code)
                            results.append({'code': code, 'name': name, 'market': 'A'})

                    elif classify == 'HK':
                        code = code + '.HK'
                        if code not in seen:
                            seen.add(code)
                            results.append({'code': code, 'name': name, 'market': 'HK'})
    except:
        pass

    # 2. Yahoo Finance 美股
    try:
        import urllib.parse
        yurl = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(keyword)}&quotes_count=20"
        yresp = requests.get(yurl, headers=headers, timeout=5)
        ydata = yresp.json()

        if ydata.get('quotes'):
            for q in ydata['quotes']:
                if q.get('quoteType') in ['EQUITY', 'ETF']:
                    sym = q.get('symbol', '')
                    shortname = q.get('shortname', '') or q.get('longname', '')
                    if shortname and sym not in seen:
                        seen.add(sym)
                        results.append({'code': sym, 'name': shortname, 'market': 'US'})
    except:
        pass

    return results[:30]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'zhen-guize-recommend'

# ========== 书中核心投资原则 ==========
INVESTMENT_PRINCIPLES = {
    "1": {
        "title": "做好你的功课",
        "content": "在购买股票之前，必须彻底了解公司的里里外外。需要发挥会计学知识，理解公司的财务状况，阅读年度报告，从封面读到封底，浏览过去的财务报表，检验行业内的竞争者。",
        "key_points": [
            "理解公司财务报表",
            "了解行业竞争环境",
            "分析公司管理团队",
            "实地调查研究"
        ]
    },
    "2": {
        "title": "寻找具有强大竞争优势的公司",
        "content": "竞争优势可以保护企业的利益免受侵害。识别竞争优势是关键，需要回答：公司是怎样设法使竞争者无路可走，从而获得丰厚利润的？",
        "key_points": [
            "品牌护城河",
            "专利技术",
            "转换成本",
            "网络效应",
            "低成本优势"
        ]
    },
    "3": {
        "title": "拥有安全边际",
        "content": "股票的市价与我们对股价估值的差值就是安全边际。应当在价格低于股票价值时买入，即使你过后意识到估计过于乐观，安全边际也能减轻损失。",
        "key_points": [
            "价格低于价值买入",
            "为不确定性预留空间",
            "稳定企业安全边际小",
            "高风险企业安全边际大"
        ]
    },
    "4": {
        "title": "长期持有",
        "content": "成功的投资是简单的，但实现起来并不容易。短期价格运动是完全不可预测的，应当关注公司的长期表现。",
        "key_points": [
            "忽略短期波动",
            "减少交易成本",
            "让复利发挥作用",
            "避免频繁交易"
        ]
    },
    "5": {
        "title": "知道何时卖出",
        "content": "不要仅仅因为股价下跌就抛售，但当公司基本面变差、估值过高或找到更好的投资机会时，应该考虑卖出。",
        "key_points": [
            "公司基本面恶化",
            "估值达到极端水平",
            "发现更好的机会",
            "投资逻辑改变"
        ]
    }
}

# ========== 竞争优势来源 ==========
COMPETITIVE_ADVANTAGES = {
    "brand": {
        "name": "品牌优势",
        "description": "强大的品牌能让消费者愿意为产品付更多钱",
        "examples": ["苹果", "可口可乐", "茅台"],
        "indicators": ["毛利率高于行业平均", "品牌溢价能力", "消费者忠诚度"]
    },
    "patent": {
        "name": "专利技术",
        "description": "专利可以阻止竞争对手进入市场",
        "examples": ["高通", "微软", "台积电"],
        "indicators": ["专利数量", "研发投入占比", "技术领先程度"]
    },
    "switching_cost": {
        "name": "转换成本",
        "description": "消费者更换产品的成本越高，竞争优势越强",
        "examples": ["Oracle", "SAP", "银行软件"],
        "indicators": ["客户留存率", "年均客户流失率", "客户依赖度"]
    },
    "network": {
        "name": "网络效应",
        "description": "用户越多，价值越高",
        "examples": ["Facebook", "微信", "Visa"],
        "indicators": ["用户增长率", "活跃用户占比", "网络密度"]
    },
    "cost": {
        "name": "低成本优势",
        "description": "规模经济和运营效率带来的低成本",
        "examples": ["沃尔玛", "亚马逊", "拼多多"],
        "indicators": ["成本控制能力", "规模效应", "运营效率"]
    },
    "monopoly": {
        "name": "特许经营",
        "description": "政府管制形成的垄断地位",
        "examples": ["电网", "铁路", "烟草"],
        "indicators": ["进入壁垒", "政策保护程度", "定价权"]
    }
}

# ========== 行业分析方法 ==========
INDUSTRY_ANALYSIS = {
    "tech": {
        "name": "科技行业",
        "moat": "网络效应、转换成本",
        "risks": "技术变革快",
        "key_metrics": ["研发费用占比", "用户增长", "毛利率"],
        "famous_stocks": ["苹果", "微软", "谷歌", "英伟达"]
    },
    "finance": {
        "name": "金融行业",
        "moat": "规模经济、许可证",
        "risks": "监管风险",
        "key_metrics": ["ROE", "不良贷款率", "资本充足率"],
        "famous_stocks": ["摩根大通", "招商银行", "中国平安"]
    },
    "consumer": {
        "name": "消费行业",
        "moat": "品牌、渠道",
        "risks": "消费偏好变化",
        "key_metrics": ["毛利率", "品牌力", "渠道力"],
        "famous_stocks": ["茅台", "可口可乐", "沃尔玛"]
    },
    "medical": {
        "name": "医疗健康",
        "moat": "专利、研发",
        "risks": "政策风险",
        "key_metrics": ["研发投入", "药品管线", "毛利率"],
        "famous_stocks": ["强生", "恒瑞医药", "辉瑞"]
    },
    "energy": {
        "name": "能源行业",
        "moat": "资源禀赋、规模",
        "risks": "价格波动",
        "key_metrics": ["储量", "生产成本", "现金流"],
        "famous_stocks": ["埃克森美孚", "中国石油", "长江电力"]
    },
    "industrial": {
        "name": "工业制造",
        "moat": "成本优势、规模",
        "risks": "周期性",
        "key_metrics": ["产能利用率", "毛利率", "ROE"],
        "famous_stocks": ["卡特彼勒", "中国中车", "宁德时代"]
    }
}

# ========== 估值指标标准 ==========
VALUATION_METRICS = {
    "pe": {
        "name": "市盈率 (P/E)",
        "description": "股票价格与每股收益的比率",
        "low": "低于15倍 - 可能被低估",
        "fair": "15-25倍 - 合理区间",
        "high": "高于25倍 - 可能被高估",
        "note": "适合稳定增长的企业"
    },
    "pb": {
        "name": "市净率 (P/B)",
        "description": "股票价格与每股净资产的比率",
        "low": "低于1.5倍 - 可能被低估",
        "fair": "1.5-3倍 - 合理区间",
        "high": "高于3倍 - 可能被高估",
        "note": "适合金融、资产重企业"
    },
    "ps": {
        "name": "市销率 (P/S)",
        "description": "股票价格与每股销售额的比率",
        "low": "低于1倍 - 可能被低估",
        "fair": "1-3倍 - 合理区间",
        "high": "高于3倍 - 可能被高估",
        "note": "适合高速成长企业"
    },
    "dcf": {
        "name": "DCF估值",
        "description": "现金流折现估值",
        "margin": "安全边际",
        "buy_discount": "折扣20%以上",
        "hold": "折扣0-20%",
        "overvalued": "溢价"
    }
}

# ========== 股票数据（模拟） ==========
STOCK_DATABASE = {
    # A股
    "600519.SH": {
        "name": "贵州茅台",
        "industry": "consumer",
        "price": 1650.0,
        "pe": 28.5,
        "pb": 8.2,
        "roe": 32.5,
        "gross_margin": 91.5,
        "revenue_growth": 15.2,
        "competitive_advantage": ["brand", "monopoly"],
        "dividend_yield": 1.8,
        "debt_ratio": 25.0,
        "description": "中国高端白酒龙头，拥有强大的品牌优势和定价权"
    },
    "000858.SZ": {
        "name": "五粮液",
        "industry": "consumer",
        "price": 145.0,
        "pe": 22.0,
        "pb": 5.5,
        "roe": 25.0,
        "gross_margin": 75.0,
        "revenue_growth": 12.0,
        "competitive_advantage": ["brand"],
        "dividend_yield": 2.5,
        "debt_ratio": 30.0,
        "description": "中国第二大白酒企业，品牌优势明显"
    },
    "601318.SH": {
        "name": "中国平安",
        "industry": "finance",
        "price": 48.5,
        "pe": 10.5,
        "pb": 1.2,
        "roe": 15.0,
        "gross_margin": 28.0,
        "revenue_growth": 8.0,
        "competitive_advantage": ["network", "cost"],
        "dividend_yield": 4.5,
        "debt_ratio": 85.0,
        "description": "中国最大的保险公司，拥有庞大的客户网络"
    },
    "600036.SH": {
        "name": "招商银行",
        "industry": "finance",
        "price": 38.0,
        "pe": 8.5,
        "pb": 1.3,
        "roe": 16.5,
        "gross_margin": 45.0,
        "revenue_growth": 10.0,
        "competitive_advantage": ["brand", "switching_cost"],
        "dividend_yield": 3.2,
        "debt_ratio": 92.0,
        "description": "中国最佳零售银行，客户服务质量领先"
    },
    "000333.SZ": {
        "name": "美的集团",
        "industry": "industrial",
        "price": 65.0,
        "pe": 12.0,
        "pb": 3.5,
        "roe": 28.0,
        "gross_margin": 27.0,
        "revenue_growth": 8.5,
        "competitive_advantage": ["cost", "network"],
        "dividend_yield": 4.0,
        "debt_ratio": 65.0,
        "description": "全球家电龙头，智能制造领先"
    },
    "600900.SH": {
        "name": "长江电力",
        "industry": "energy",
        "price": 28.0,
        "pe": 18.0,
        "pb": 2.8,
        "roe": 15.5,
        "gross_margin": 55.0,
        "revenue_growth": 5.0,
        "competitive_advantage": ["monopoly", "cost"],
        "dividend_yield": 3.8,
        "debt_ratio": 55.0,
        "description": "全球最大水电公司，现金流稳定"
    },
    "601888.SH": {
        "name": "中国中免",
        "industry": "consumer",
        "price": 75.0,
        "pe": 35.0,
        "pb": 12.0,
        "roe": 35.0,
        "gross_margin": 40.0,
        "revenue_growth": 25.0,
        "competitive_advantage": ["monopoly", "network"],
        "dividend_yield": 1.5,
        "debt_ratio": 45.0,
        "description": "中国免税店龙头，具有垄断优势"
    },
    "600276.SH": {
        "name": "恒瑞医药",
        "industry": "medical",
        "price": 55.0,
        "pe": 65.0,
        "pb": 10.0,
        "roe": 18.0,
        "gross_margin": 85.0,
        "revenue_growth": 15.0,
        "competitive_advantage": ["patent", "brand"],
        "dividend_yield": 0.8,
        "debt_ratio": 35.0,
        "description": "中国创新药龙头，研发实力强劲"
    },
    # 美股
    "AAPL": {
        "name": "苹果",
        "industry": "tech",
        "price": 175.0,
        "pe": 28.0,
        "pb": 45.0,
        "roe": 160.0,
        "gross_margin": 45.0,
        "revenue_growth": 8.0,
        "competitive_advantage": ["brand", "network", "switching_cost"],
        "dividend_yield": 0.5,
        "debt_ratio": 80.0,
        "description": "全球科技巨头，品牌生态强大"
    },
    "MSFT": {
        "name": "微软",
        "industry": "tech",
        "price": 380.0,
        "pe": 32.0,
        "pb": 12.0,
        "roe": 38.0,
        "gross_margin": 70.0,
        "revenue_growth": 15.0,
        "competitive_advantage": ["network", "switching_cost"],
        "dividend_yield": 0.8,
        "debt_ratio": 45.0,
        "description": "云计算龙头，企业软件垄断"
    },
    "GOOGL": {
        "name": "谷歌",
        "industry": "tech",
        "price": 140.0,
        "pe": 25.0,
        "pb": 6.0,
        "roe": 25.0,
        "gross_margin": 57.0,
        "revenue_growth": 12.0,
        "competitive_advantage": ["network", "monopoly"],
        "dividend_yield": 0.0,
        "debt_ratio": 25.0,
        "description": "全球搜索引擎霸主，广告业务强劲"
    },
    "AMZN": {
        "name": "亚马逊",
        "industry": "tech",
        "price": 180.0,
        "pe": 55.0,
        "pb": 8.0,
        "roe": 15.0,
        "gross_margin": 47.0,
        "revenue_growth": 12.0,
        "competitive_advantage": ["network", "cost"],
        "dividend_yield": 0.0,
        "debt_ratio": 65.0,
        "description": "电商云计算双巨头，网络效应极强"
    },
    "NVDA": {
        "name": "英伟达",
        "industry": "tech",
        "price": 800.0,
        "pe": 65.0,
        "pb": 45.0,
        "roe": 70.0,
        "gross_margin": 75.0,
        "revenue_growth": 120.0,
        "competitive_advantage": ["patent", "cost"],
        "dividend_yield": 0.0,
        "debt_ratio": 40.0,
        "description": "AI芯片龙头，GPU垄断地位"
    },
    "TSLA": {
        "name": "特斯拉",
        "industry": "tech",
        "price": 250.0,
        "pe": 80.0,
        "pb": 15.0,
        "roe": 20.0,
        "gross_margin": 18.0,
        "revenue_growth": 40.0,
        "competitive_advantage": ["brand", "patent"],
        "dividend_yield": 0.0,
        "debt_ratio": 45.0,
        "description": "电动汽车龙头，创新能力领先"
    },
    "JPM": {
        "name": "摩根大通",
        "industry": "finance",
        "price": 185.0,
        "pe": 11.0,
        "pb": 1.6,
        "roe": 15.0,
        "gross_margin": 55.0,
        "revenue_growth": 10.0,
        "competitive_advantage": ["network", "monopoly"],
        "dividend_yield": 2.5,
        "debt_ratio": 90.0,
        "description": "全球最大投行，护城河深厚"
    },
    "V": {
        "name": "Visa",
        "industry": "finance",
        "price": 280.0,
        "pe": 30.0,
        "pb": 15.0,
        "roe": 50.0,
        "gross_margin": 80.0,
        "revenue_growth": 12.0,
        "competitive_advantage": ["network", "switching_cost"],
        "dividend_yield": 0.7,
        "debt_ratio": 55.0,
        "description": "支付清算垄断，网络效应极强"
    }
}


def get_realtime_stock_data(stock_code):
    """获取实时股票数据"""
    import urllib.parse
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    # 判断市场
    is_us = not ('.SH' in stock_code or '.SZ' in stock_code)

    if is_us:
        # 美股 - Yahoo Finance
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}"
            resp = requests.get(url, headers=headers, timeout=5)
            data = resp.json()
            if data.get('chart') and data['chart'].get('result'):
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                return {
                    'name': meta.get('shortName', stock_code),
                    'price': meta.get('regularMarketPrice', 0),
                    'pe': meta.get('trailingPE', 0),
                    'pb': 0,
                    'roe': 0,
                    'gross_margin': 0,
                    'revenue_growth': 0,
                    'dividend_yield': meta.get('dividendYield', 0) * 100 if meta.get('dividendYield') else 0,
                    'debt_ratio': 0,
                    'competitive_advantage': [],
                    'market': 'US'
                }
        except:
            pass
    else:
        # A股 - 东方财富
        try:
            code = stock_code.replace('.SH', '').replace('.SZ', '')
            url = f"https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'invt': '2',
                'fltt': '2',
                'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f116,f117,f162,f167,f168,f169,f170,f171,f173,f177',
                'secid': f"1.{code}" if code.startswith('6') else f"0.{code}"
            }
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            data = resp.json()
            if data.get('data'):
                d = data['data']
                return {
                    'name': d.get('f58', stock_code),
                    'price': d.get('f43', 0) / 1000 if d.get('f43') else 0,
                    'change': d.get('f44', 0) / 1000 if d.get('f44') else 0,
                    'pe': d.get('f162', 0) / 1000 if d.get('f162') else 0,
                    'pb': d.get('f167', 0) / 1000 if d.get('f167') else 0,
                    'roe': d.get('f173', 0) / 100 if d.get('f173') else 0,
                    'gross_margin': d.get('f169', 0) / 100 if d.get('f169') else 0,
                    'revenue_growth': d.get('f116', 0) / 100 if d.get('f116') else 0,
                    'dividend_yield': d.get('f171', 0) / 100 if d.get('f171') else 0,
                    'debt_ratio': d.get('f177', 0) / 100 if d.get('f177') else 0,
                    'competitive_advantage': [],
                    'market': 'A'
                }
        except:
            pass

    return None


def calculate_stock_score(stock_code):
    """根据书中原则计算股票评分"""
    # 优先使用实时数据
    stock = get_realtime_stock_data(stock_code)

    # 如果没有实时数据，尝试内置数据库
    if not stock:
        stock = STOCK_DATABASE.get(stock_code)

    if not stock:
        # 尝试查找
        for key, val in STOCK_DATABASE.items():
            if key.upper() == stock_code.upper() or key.replace('.SH','').replace('.SZ','') == stock_code.replace('.SH','').replace('.SZ',''):
                stock = val
                stock_code = key
                break

    if not stock:
        return None

    scores = {
        "competitive_advantage_score": 0,
        "financial_health_score": 0,
        "valuation_score": 0,
        "growth_score": 0,
        "dividend_score": 0
    }

    # 1. 竞争优势评分 (权重30%)
    advantage_count = len(stock.get("competitive_advantage", []))
    scores["competitive_advantage_score"] = min(100, advantage_count * 25 + 25)

    # 2. 财务健康评分 (权重25%)
    # ROE评分
    roe_score = min(100, stock.get("roe", 0) * 3)
    # 毛利率评分
    margin_score = min(100, stock.get("gross_margin", 0))
    # 负债率评分（越低越好）
    debt_score = max(0, 100 - stock.get("debt_ratio", 50) * 1.2)
    scores["financial_health_score"] = (roe_score * 0.4 + margin_score * 0.3 + debt_score * 0.3)

    # 3. 估值评分 (权重20%)
    pe = stock.get("pe", 0)
    if pe < 15:
        val_score = 100
    elif pe < 25:
        val_score = 80
    elif pe < 40:
        val_score = 50
    else:
        val_score = 20
    scores["valuation_score"] = val_score

    # 4. 成长性评分 (权重15%)
    growth = stock.get("revenue_growth", 0)
    if growth > 30:
        growth_score = 100
    elif growth > 15:
        growth_score = 80
    elif growth > 5:
        growth_score = 60
    else:
        growth_score = 40
    scores["growth_score"] = growth_score

    # 5. 分红评分 (权重10%)
    div_yield = stock.get("dividend_yield", 0)
    if div_yield > 4:
        dividend_score = 100
    elif div_yield > 2:
        div_yield = 70
    elif div_yield > 0:
        dividend_score = 40
    else:
        dividend_score = 20
    scores["dividend_score"] = dividend_score

    # 综合评分
    total_score = (
        scores["competitive_advantage_score"] * 0.30 +
        scores["financial_health_score"] * 0.25 +
        scores["valuation_score"] * 0.20 +
        scores["growth_score"] * 0.15 +
        scores["dividend_score"] * 0.10
    )

    # 确定评级
    if total_score >= 80:
        rating = "★★★★★ 强烈推荐"
    elif total_score >= 65:
        rating = "★★★★☆ 值得持有"
    elif total_score >= 50:
        rating = "★★★☆☆ 中性观望"
    elif total_score >= 35:
        rating = "★★☆☆☆ 建议回避"
    else:
        rating = "★☆☆☆☆ 不推荐"

    return {
        "total_score": round(total_score, 1),
        "rating": rating,
        "component_scores": scores,
        "stock": stock
    }


def generate_recommendation_reason(stock_code):
    """根据书中原则生成推荐理由"""
    stock = STOCK_DATABASE.get(stock_code, {})
    reasons = []

    # 竞争优势
    advantages = stock.get("competitive_advantage", [])
    if "brand" in advantages:
        reasons.append("具有强大的品牌优势")
    if "patent" in advantages:
        reasons.append("拥有专利技术护城河")
    if "network" in advantages:
        reasons.append("网络效应显著")
    if "switching_cost" in advantages:
        reasons.append("客户转换成本高")
    if "cost" in advantages:
        reasons.append("低成本竞争优势")
    if "monopoly" in advantages:
        reasons.append("具有垄断地位")

    # 财务指标
    roe = stock.get("roe", 0)
    if roe > 20:
        reasons.append(f"ROE高达{roe}%（优秀）")

    gross_margin = stock.get("gross_margin", 0)
    if gross_margin > 50:
        reasons.append(f"毛利率{gross_margin}%（强劲）")

    # 估值
    pe = stock.get("pe", 0)
    if pe < 20:
        reasons.append(f"P/E={pe}（估值合理）")
    elif pe > 40:
        reasons.append(f"P/E={pe}（估值偏高）")

    # 成长性
    growth = stock.get("revenue_growth", 0)
    if growth > 20:
        reasons.append(f"营收增长{growth}%（高速成长）")

    # 分红
    div_yield = stock.get("dividend_yield", 0)
    if div_yield > 3:
        reasons.append(f"股息率{div_yield}%（分红优厚）")

    return reasons


def get_investment_strategy(stock_code):
    """根据书中原则给出投资策略"""
    stock = STOCK_DATABASE.get(stock_code, {})
    analysis = calculate_stock_score(stock_code)

    if not analysis:
        return None

    strategies = []

    # 基于竞争优势
    advantages = stock.get("competitive_advantage", [])
    if "brand" in advantages or "monopoly" in advantages:
        strategies.append({
            "type": "长期持有",
            "reason": "强大的品牌/垄断优势适合长期投资",
            "principle": "竞争优势原则 - 护城河保护利润"
        })

    # 基于估值
    pe = stock.get("pe", 0)
    if pe < 15:
        strategies.append({
            "type": "价值买入",
            "reason": "市盈率低于15倍，存在价值回归空间",
            "principle": "安全边际原则 - 寻找被低估的股票"
        })
    elif pe > 50:
        strategies.append({
            "type": "等待时机",
            "reason": "估值较高，建议等待回调",
            "principle": "安全边际原则 - 不买太贵的股票"
        })

    # 基于成长性
    growth = stock.get("revenue_growth", 0)
    if growth > 30:
        strategies.append({
            "type": "成长配置",
            "reason": "高成长性可享受估值溢价",
            "principle": "成长性分析 - 寻找高增长公司"
        })

    # 基于分红
    div_yield = stock.get("dividend_yield", 0)
    if div_yield > 3:
        strategies.append({
            "type": "稳健收益",
            "reason": "高股息提供安全垫",
            "principle": "现金流原则 - 关注真实盈利能力"
        })

    # 基于财务健康
    roe = stock.get("roe", 0)
    debt_ratio = stock.get("debt_ratio", 0)
    if roe > 15 and debt_ratio < 60:
        strategies.append({
            "type": "财务健康",
            "reason": "ROE优秀且负债率适中",
            "principle": "财务健康原则 - 稳健的资产负债表"
        })

    return strategies


# ========== HTML模板 ==========
HOME_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>真规则推荐 - 股市真规则实践</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #f39c12, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #888; font-size: 1.1em; }
        .principles {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }
        .principle-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .principle-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .principle-number {
            display: inline-block;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #f39c12, #e74c3c);
            border-radius: 50%;
            line-height: 40px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .principle-title { font-size: 1.3em; margin-bottom: 15px; color: #f39c12; }
        .principle-content { color: #ccc; line-height: 1.6; margin-bottom: 15px; font-size: 0.95em; }
        .key-points { list-style: none; }
        .key-points li {
            padding: 5px 0;
            color: #888;
            font-size: 0.9em;
        }
        .key-points li:before {
            content: "✓ ";
            color: #2ecc71;
        }
        .search-box {
            text-align: center;
            margin: 40px 0;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
        }
        .search-box h2 { margin-bottom: 20px; color: #f39c12; }
        .search-input {
            width: 100%;
            max-width: 500px;
            padding: 15px 25px;
            font-size: 16px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 30px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-input:focus { border-color: #f39c12; }
        .search-input::placeholder { color: #666; }
        .stock-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
        }
        .stock-tag {
            padding: 8px 16px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        .stock-tag:hover {
            background: #f39c12;
            color: #000;
        }
        .featured-stocks {
            margin: 40px 0;
        }
        .featured-stocks h2 { text-align: center; margin-bottom: 30px; color: #f39c12; }
        .stock-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        .stock-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
            transition: all 0.3s;
        }
        .stock-card:hover {
            transform: scale(1.02);
            border-color: #f39c12;
        }
        .stock-name { font-size: 1.3em; color: #fff; margin-bottom: 5px; }
        .stock-code { color: #666; font-size: 0.9em; }
        .stock-score {
            font-size: 2em;
            font-weight: bold;
            color: #f39c12;
            margin: 15px 0;
        }
        .stock-rating { color: #2ecc71; font-size: 1.1em; }
        .stock-tags {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .stock-tag-small {
            padding: 4px 10px;
            background: rgba(243, 156, 18, 0.2);
            border-radius: 10px;
            font-size: 0.8em;
            color: #f39c12;
        }
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>真规则推荐</h1>
            <p class="subtitle">基于《股市真规则》- 晨星公司投资哲学实践</p>
        </header>

        <div class="principles">
            {% for key, principle in principles.items() %}
            <div class="principle-card">
                <div class="principle-number">{{ key }}</div>
                <h3 class="principle-title">{{ principle.title }}</h3>
                <p class="principle-content">{{ principle.content }}</p>
                <ul class="key-points">
                    {% for point in principle.key_points %}
                    <li>{{ point }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </div>

        <div class="search-box">
            <h2>🔍 搜索股票</h2>
            <input type="text" class="search-input" id="searchInput" placeholder="输入股票代码或名称..." onkeyup="searchStock(this.value)">
            <div class="stock-list" id="searchResults"></div>
        </div>

        <div class="featured-stocks">
            <h2>⭐ 重点关注</h2>
            <div class="stock-grid" id="stockGrid">
                {% for code, stock in stocks.items() %}
                <div class="stock-card" onclick="showStock('{{ code }}')">
                    <div class="stock-name">{{ stock.name }}</div>
                    <div class="stock-code">{{ code }}</div>
                    <div class="stock-tags">
                        {% for adv in stock.competitive_advantage %}
                        <span class="stock-tag-small">{{ adv }}</span>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <footer>
            <p>本书基于帕特·多尔西《股市真规则》- 晨星公司股票研究</p>
            <p>投资有风险，入市需谨慎。本系统仅供参考，不构成投资建议。</p>
        </footer>
    </div>

    <script>
        function showStock(code) {
            window.location.href = '/stock/' + code;
        }

        function searchStock(keyword) {
            const results = document.getElementById('searchResults');
            if (!keyword) {
                results.innerHTML = '';
                return;
            }

            const stocks = {{ stock_list | tojson }};
            const filtered = stocks.filter(s =>
                s.code.toLowerCase().includes(keyword.toLowerCase()) ||
                s.name.includes(keyword)
            );

            results.innerHTML = filtered.map(s =>
                `<span class="stock-tag" onclick="showStock('${s.code}')">${s.name} (${s.code})</span>`
            ).join('');
        }
    </script>
</body>
</html>
"""

STOCK_DETAIL_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ stock.name }} - 真规则分析</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .back-btn {
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #fff;
            text-decoration: none;
            transition: background 0.3s;
        }
        .back-btn:hover { background: rgba(255,255,255,0.2); }
        .stock-header {
            text-align: center;
            padding: 40px 0;
        }
        .stock-name { font-size: 2.5em; margin-bottom: 10px; }
        .stock-code { color: #888; font-size: 1.2em; }
        .stock-price { font-size: 3em; color: #f39c12; margin: 20px 0; }
        .score-section {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }
        .total-score { font-size: 4em; font-weight: bold; color: #f39c12; }
        .rating { font-size: 1.5em; color: #2ecc71; margin: 10px 0; }
        .score-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }
        .score-item {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
        }
        .score-label { color: #888; font-size: 0.9em; }
        .score-value { font-size: 1.5em; color: #f39c12; margin-top: 5px; }
        .section {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
        }
        .section h2 {
            color: #f39c12;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .metric {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .metric-value { font-size: 1.5em; color: #fff; }
        .metric-label { color: #888; font-size: 0.85em; margin-top: 5px; }
        .advantage-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .advantage-tag {
            padding: 8px 16px;
            background: rgba(46, 204, 113, 0.2);
            color: #2ecc71;
            border-radius: 20px;
        }
        .strategy-item {
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #f39c12;
        }
        .strategy-type { font-size: 1.3em; color: #f39c12; margin-bottom: 10px; }
        .strategy-reason { color: #ccc; margin-bottom: 10px; }
        .strategy-principle { color: #888; font-size: 0.9em; }
        .principle-ref {
            background: rgba(243, 156, 18, 0.1);
            border-left: 3px solid #f39c12;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 10px 10px 0;
        }
        .principle-ref h4 { color: #f39c12; margin-bottom: 10px; }
        .reasons-list { list-style: none; }
        .reasons-list li {
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .reasons-list li:before {
            content: "✓ ";
            color: #2ecc71;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="/" class="back-btn">← 返回首页</a>
            <span>真规则推荐</span>
            <a href="/" class="back-btn">首页</a>
        </header>

        <div class="stock-header">
            <h1 class="stock-name">{{ stock.name }}</h1>
            <p class="stock-code">{{ code }}</p>
            <p class="stock-price">¥{{ stock.price }}</p>
        </div>

        <div class="score-section">
            <div class="total-score">{{ analysis.total_score }}</div>
            <div class="rating">{{ analysis.rating }}</div>
            <div class="score-details">
                <div class="score-item">
                    <div class="score-label">竞争优势</div>
                    <div class="score-value">{{ analysis.component_scores.competitive_advantage_score }}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">财务健康</div>
                    <div class="score-value">{{ analysis.component_scores.financial_health_score }}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">估值水平</div>
                    <div class="score-value">{{ analysis.component_scores.valuation_score }}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">成长性</div>
                    <div class="score-value">{{ analysis.component_scores.growth_score }}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">分红回报</div>
                    <div class="score-value">{{ analysis.component_scores.dividend_score }}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📊 公司概况</h2>
            <p>{{ stock.description }}</p>
            <div class="advantage-tags">
                {% for adv in stock.competitive_advantage %}
                <span class="advantage-tag">{{ advantage_names.get(adv, adv) }}</span>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>📈 关键财务指标</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-value">{{ stock.pe }}x</div>
                    <div class="metric-label">市盈率 (P/E)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ stock.pb }}x</div>
                    <div class="metric-label">市净率 (P/B)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ stock.roe }}%</div>
                    <div class="metric-label">ROE</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ stock.gross_margin }}%</div>
                    <div class="metric-label">毛利率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ stock.revenue_growth }}%</div>
                    <div class="metric-label">营收增长</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ stock.dividend_yield }}%</div>
                    <div class="metric-label">股息率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ stock.debt_ratio }}%</div>
                    <div class="metric-label">负债率</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>💡 推荐理由</h2>
            <ul class="reasons-list">
                {% for reason in reasons %}
                <li>{{ reason }}</li>
                {% endfor %}
            </ul>
        </div>

        <div class="section">
            <h2>🎯 投资策略建议</h2>
            {% for strategy in strategies %}
            <div class="strategy-item">
                <div class="strategy-type">{{ strategy.type }}</div>
                <div class="strategy-reason">{{ strategy.reason }}</div>
                <div class="strategy-principle">📖 依据: {{ strategy.principle }}</div>
            </div>
            {% endfor %}
        </div>

        <div class="section">
            <h2>📚 相关投资原则</h2>
            <div class="principle-ref">
                <h4>五大投资原则</h4>
                <p>本书倡导的五项核心投资原则：做好你的功课、寻找具有强大竞争优势的公司、拥有安全边际、长期持有、知道何时卖出。</p>
            </div>
            <div class="principle-ref">
                <h4>竞争优势分析</h4>
                <p>护城河类型：品牌优势、专利技术、转换成本、网络效应、低成本优势、特许经营</p>
            </div>
            <div class="principle-ref">
                <h4>安全边际</h4>
                <p>始终在股票价格低于其内在价值时买入，为不确定性预留缓冲空间。</p>
            </div>
        </div>
    </div>
</body>
</html>
"""


# ========== 路由 ==========
@app.route('/')
def home():
    """首页"""
    # 准备股票列表
    stock_list = [
        {"code": code, "name": data["name"]}
        for code, data in STOCK_DATABASE.items()
    ]

    return render_template_string(
        HOME_HTML,
        principles=INVESTMENT_PRINCIPLES,
        stocks=STOCK_DATABASE,
        stock_list=stock_list,
        advantage_names={k: v["name"] for k, v in COMPETITIVE_ADVANTAGES.items()}
    )


@app.route('/stock/<code>')
def stock_detail(code):
    """股票详情页"""
    # 尝试添加后缀
    code_with_suffix = code if "." in code else code + ".SH"

    # 优先使用实时数据
    stock = get_realtime_stock_data(code_with_suffix)
    if not stock:
        stock = get_realtime_stock_data(code)

    # 如果没有实时数据，使用内置数据库
    if not stock:
        stock_code = code_with_suffix if code_with_suffix in STOCK_DATABASE else code
        if stock_code in STOCK_DATABASE:
            stock = STOCK_DATABASE[stock_code]
        else:
            for key, val in STOCK_DATABASE.items():
                if key.upper() == code.upper():
                    stock = val
                    stock_code = key
                    break

    if not stock:
        return "股票未找到", 404

    analysis = calculate_stock_score(code_with_suffix if '.' in code_with_suffix else code)
    if not analysis:
        analysis = calculate_stock_score(code)

    if not analysis:
        return "股票未找到", 404

    reasons = generate_recommendation_reason(code)
    strategies = get_investment_strategy(code)

    return render_template_string(
        STOCK_DETAIL_HTML,
        code=code,
        stock=stock,
        analysis=analysis,
        reasons=reasons,
        strategies=strategies,
        advantage_names={k: v["name"] for k, v in COMPETITIVE_ADVANTAGES.items()}
    )


@app.route('/api/stock/<code>')
def api_stock(code):
    """API接口 - 获取股票分析"""
    # 优先使用实时数据
    stock = get_realtime_stock_data(code)
    if not stock:
        if code in STOCK_DATABASE:
            stock = STOCK_DATABASE[code]
        else:
            for key, val in STOCK_DATABASE.items():
                if key.upper() == code.upper():
                    stock = val
                    code = key
                    break

    if not stock:
        return jsonify({"error": "股票未找到"}), 404

    analysis = calculate_stock_score(code)
    if not analysis:
        return jsonify({"error": "股票未找到"}), 404

    reasons = generate_recommendation_reason(code)
    strategies = get_investment_strategy(code)

    return jsonify({
        "code": code,
        "stock": stock,
        "analysis": analysis,
        "reasons": reasons,
        "strategies": strategies
    })


@app.route('/api/search')
def api_search():
    """API接口 - 搜索股票"""
    keyword = request.args.get('q', '')

    # 使用模糊搜索获取实时股票数据
    stocks = fuzzy_search_stocks(keyword)
    results = [{"code": s["code"], "name": s["name"]} for s in stocks]

    return jsonify(results)


if __name__ == '__main__':
    print("=" * 60)
    print("真规则推荐系统 - 启动中...")
    print("=" * 60)
    print("访问地址: http://localhost:5001")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
