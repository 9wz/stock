#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web应用 - Flask前端 (完整修复版)
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 修复导入问题
import pandas as pd
import numpy as np
import requests
import time
import json
import re
import math
import akshare as ak
from urllib.parse import quote

def safe_float(val, default=0):
    """安全地将API返回值转换为float，处理'-'、None、空字符串等情况"""
    if val is None or val == '' or val == '-' or val == '--':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


from data.data_loader import DataLoader
from factors.factor_engine import FactorEngine
from strategies.strategy_pool import StrategyPool
from user_profile.profile_manager import ProfileManager


def get_a_stock_list_eastmoney():
    """从东方财富获取A股列表（按成交量排序的前1000只）"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        stocks = []

        # 获取按成交量排序的前1000只A股（10页 * 100条）
        for pn in range(1, 11):
            params = {
                'pn': pn,
                'pz': 100,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f2',  # 按成交量排序
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f12,f14'
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=3)
                data = response.json()
                if not data.get('data') or not data['data'].get('diff'):
                    break

                for item in data['data']['diff']:
                    code = str(item.get('f12', ''))
                    name = item.get('f14', '')
                    if code and name:
                        suffix = '.SH' if code.startswith('5') or code.startswith('6') else '.SZ'
                        stocks.append({
                            'code': code + suffix,
                            'name': name,
                            'market': 'A'
                        })
            except:
                break

        return stocks
    except Exception as e:
        print(f"获取A股列表失败: {e}")
        return []

        return stocks
    except Exception as e:
        print(f"获取A股列表失败: {e}")
        return []


def get_us_stock_list():
    """获取美股全部股票列表"""
    # 完整的美股股票列表（主要交易所）
    us_stocks = [
        # 科技巨头
        ('AAPL', '苹果'), ('MSFT', '微软'), ('GOOGL', '谷歌'), ('GOOG', '谷歌A'),
        ('AMZN', '亚马逊'), ('META', 'Meta'), ('NVDA', '英伟达'), ('TSLA', '特斯拉'),
        ('AVGO', '博通'), ('ORCL', '甲骨文'), ('CRM', 'Salesforce'), ('ADBE', 'Adobe'),
        ('NFLX', 'Netflix'), ('NOW', 'ServiceNow'), ('INTU', 'Intuit'), ('SNOW', 'Snowflake'),
        ('PANW', 'Palo Alto'), ('CRWD', 'CrowdStrike'), ('FTNT', 'Fortinet'), ('ZS', 'Zscaler'),
        ('NET', 'Cloudflare'), ('DDOG', 'Datadog'), ('OKTA', 'Okta'), ('TEAM', 'Atlassian'),
        ('SQ', 'Block'), ('SHOP', 'Shopify'), ('UBER', 'Uber'), ('LYFT', 'Lyft'),
        ('ABNB', 'Airbnb'), ('DASH', 'DoorDash'), ('COIN', 'Coinbase'), ('RBLX', 'Roblox'),
        # 金融
        ('JPM', '摩根大通'), ('BAC', '美国银行'), ('WFC', '富国银行'), ('GS', '高盛'),
        ('MS', '摩根士丹利'), ('C', '花旗'), ('AXP', '美国运通'), ('BLK', '贝莱德'),
        ('SCHW', '嘉信理财'), ('USB', '美国合众银行'), ('PNC', 'PNC金融'), ('COF', 'Capital One'),
        ('SPGI', '标普全球'), ('V', 'Visa'), ('MA', '万事达'), ('PYPL', 'PayPal'),
        ('ADP', 'ADP'), ('FIS', 'Fiserv'), ('FISV', 'Fiserv'), ('GPN', 'Global Payments'),
        # 医疗
        ('JNJ', '强生'), ('UNH', '联合健康'), ('PFE', '辉瑞'), ('ABBV', '艾伯维'),
        ('MRK', '默克'), ('LLY', '礼来'), ('TMO', 'Thermo Fisher'), ('ABT', '雅培'),
        ('DHR', 'Danaher'), ('BMY', '百时美施贵宝'), ('AMGN', '安进'), ('GILD', '吉利德'),
        ('VRTX', 'Vertex'), ('REGN', 'Regeneron'), ('BIIB', 'Biogen'), ('ISRG', '直觉外科'),
        ('MDT', '美敦力'), ('SYK', 'Stryker'), ('ZTS', 'Zoetis'), ('MRNA', 'Moderna'),
        # 消费
        ('WMT', '沃尔玛'), ('PG', '宝洁'), ('COST', 'Costco'), ('HD', '家得宝'),
        ('TGT', 'Target'), ('LOW', 'Lowe\'s'), ('NKE', '耐克'), ('SBUX', '星巴克'),
        ('MCD', '麦当劳'), ('DIS', '迪士尼'), ('CMG', 'Chipotle'), ('YUM', '百胜'),
        ('DRI', 'Darden'), ('HLT', '希尔顿'), ('MAR', '万豪'), ('BBY', 'Best Buy'),
        ('TJX', 'TJX'), ('ROST', 'Ross Stores'), ('DG', 'Dollar General'), ('DLTR', 'Dollar Tree'),
        # 能源
        ('XOM', '埃克森美孚'), ('CVX', '雪佛龙'), ('COP', '康菲石油'), ('SLB', '斯伦贝谢'),
        ('EOG', 'EOG能源'), ('PSX', 'Phillips 66'), ('VLO', 'Valero'), ('OXY', 'Occidental'),
        ('MPC', 'Marathon Petroleum'), ('HAL', '哈里伯顿'),
        # 工业
        ('BA', '波音'), ('CAT', '卡特彼勒'), ('GE', 'GE'), ('MMM', '3M'),
        ('HON', '霍尼韦尔'), ('LMT', '洛克希德'), ('RTX', 'RTX'), ('UPS', 'UPS'),
        ('FDX', 'FedEx'), ('UNP', '联合太平洋'), ('NSC', '诺福克南方'), ('CMI', '康明斯'),
        ('DE', 'Deere'), ('ETN', '伊顿'), ('EMR', '艾默生'),
        # 通信
        ('T', 'AT&T'), ('VZ', '威瑞森'), ('TMUS', 'T-Mobile'), ('CMCSA', '康卡斯特'),
        ('CHTR', 'Charter'), ('FOX', 'Fox'), ('NWSA', 'News Corp'),
        # 芯片
        ('INTC', '英特尔'), ('AMD', 'AMD'), ('QCOM', '高通'), ('TXN', '德州仪器'),
        ('AMAT', '应用材料'), ('LRCX', '泛林集团'), ('KLAC', '科天'), ('SNPS', '新思'),
        ('CDNS', 'Cadence'), ('MU', '美光'), ('NXPI', 'NXP'), ('ON', 'ON Semiconductor'),
        # 中概股
        ('BABA', '阿里巴巴'), ('BILI', '哔哩哔哩'), ('JD', '京东'), ('PDD', '拼多多'),
        ('NTES', '网易'), ('NIO', '蔚来'), ('XPEV', '小鹏汽车'), ('LI', '理想汽车'),
        ('BIDU', '百度'), ('TAL', '好未来'), ('EDU', '新东方'), ('VIPS', '唯品会'),
        ('MOMO', '陌陌'), ('YY', 'YY'), ('HUYA', '虎牙'), ('DOYU', '斗鱼'),
        ('BEKE', '贝壳'), ('TME', '腾讯音乐'), ('SPOT', 'Spotify'), ('ZM', 'Zoom'),
        ('DOCU', 'DocuSign'), ('ROKU', 'Roku'), ('ETSY', 'Etsy'), ('W', 'Wayfair'),
        ('CHWY', 'Chewy'), ('PINS', 'Pinterest'), ('SNAP', 'Snap'), ('TWTR', 'Twitter'),
        ('RIVN', 'Rivian'), ('LCID', 'Lucid'), ('IBM', 'IBM'), ('CSCO', '思科'),
        ('INFY', 'Infos'), ('TSM', '台积电'), ('SAP', 'SAP'), ('ASML', 'ASML'),
    ]
    return [{'code': code, 'name': name, 'market': 'US'} for code, name in us_stocks]


# 预定义的A股常用股票列表（补充API数据）
A_STOCKS_BUILTIN = [
    ('600519.SH', '贵州茅台'), ('000858.SZ', '五粮液'), ('601318.SH', '中国平安'),
    ('600036.SH', '招商银行'), ('000333.SZ', '美的集团'), ('600900.SH', '长江电力'),
    ('601888.SH', '中国中免'), ('600276.SH', '恒瑞医药'), ('601166.SH', '兴业银行'),
    ('600030.SH', '中信证券'), ('000001.SZ', '平安银行'), ('600016.SH', '民生银行'),
    ('600000.SH', '浦发银行'), ('601328.SH', '交通银行'), ('601398.SH', '工商银行'),
    ('601939.SH', '建设银行'), ('601288.SH', '农业银行'), ('601988.SH', '中国银行'),
    ('601857.SH', '中国石油'), ('600028.SH', '中国石化'), ('600050.SH', '中国联通'),
    ('000002.SZ', '万科A'), ('000651.SZ', '格力电器'), ('000725.SZ', '京东方A'),
    ('000768.SZ', '中航飞机'), ('000876.SZ', '新希望'), ('000895.SZ', '系数未'),
    ('000938.SZ', '紫金矿业'), ('600104.SH', '上汽集团'), ('600019.SH', '宝钢股份'),
    ('600030.SH', '中信证券'), ('600585.SH', '海螺水泥'), ('600309.SH', '万华化学'),
    ('600887.SH', '伊利股份'), ('600519.SH', '贵州茅台'), ('000568.SZ', '泸州老窖'),
    ('000596.SZ', '古井贡酒'), ('600809.SH', '山西汾酒'), ('000799.SZ', '金种子酒'),
    ('000869.SZ', '张裕A'), ('600059.SH', '华钰矿业'), ('000848.SZ', '承德露露'),
    ('600132.SH', '重庆啤酒'), ('600199.SH', '金种子酒'), ('600702.SH', '沱牌舍得'),
    ('603019.SH', '中科曙光'), ('600850.SH', '华东医药'), ('000513.SZ', '丽珠集团'),
    ('000566.SZ', '海南海药'), ('000403.SZ', '双林股份'), ('000513.SZ', '丽珠集团'),
    ('600276.SH', '恒瑞医药'), ('002007.SZ', '华兰生物'), ('000661.SZ', '长春高新'),
    ('002252.SZ', '莱宝高科'), ('300003.SZ', '乐普医疗'), ('300015.SZ', '爱尔眼科'),
    ('300015.SZ', '通策医疗'), ('300003.SZ', '乐普医疗'), ('300122.SZ', '智飞生物'),
    ('002410.SZ', '广联达'), ('300033.SZ', '同花顺'), ('300059.SZ', '东方财富'),
    ('002415.SZ', '海康威视'), ('000333.SZ', '美的集团'), ('000651.SZ', '格力电器'),
    ('000921.SZ', '浙江龙盛'), ('600352.SH', '浙江龙盛'), ('000630.SZ', '紫金矿业'),
    ('600489.SH', '中金黄金'), ('600547.SH', '山东黄金'), ('600362.SH', '江西铜业'),
    ('000338.SZ', '潍柴动力'), ('000425.SZ', '徐工机械'), ('000157.SZ', '中联重科'),
    ('600585.SH', '海螺水泥'), ('600801.SH', '华新水泥'), ('000877.SZ', '天山股份'),
    ('601186.SH', '中国重汽'), ('600406.SH', '国电南瑞'), ('600690.SH', '青岛海尔'),
    ('603288.SH', '海天味业'), ('600519.SH', '贵州茅台'), ('603589.SH', '金科文化'),
    ('600809.SH', '山西汾酒'), ('600519.SH', '贵州茅台'), ('000858.SZ', '五粮液'),
    ('600036.SH', '招商银行'), ('601318.SH', '中国平安'), ('600000.SH', '浦发银行'),
    ('600015.SH', '华夏银行'), ('601166.SH', '兴业银行'), ('601328.SH', '交通银行'),
    ('600016.SH', '民生银行'), ('601398.SH', '工商银行'), ('601939.SH', '建设银行'),
    ('601288.SH', '农业银行'), ('601988.SH', '中国银行'), ('601818.SH', '光大银行'),
    ('600015.SH', '华夏银行'), ('000001.SZ', '平安银行'), ('002142.SZ', '深圳银行'),
    ('600036.SH', '招商银行'), ('600016.SH', '民生银行'), ('600015.SH', '华夏银行'),
    ('000001.SZ', '平安银行'), ('601166.SH', '兴业银行'), ('601328.SH', '交通银行'),
    ('000001.SZ', '平安银行'), ('601398.SH', '工商银行'), ('601939.SH', '建设银行'),
]


# 股票缓存
_stock_cache = {'data': [], 'time': 0}
_stock_cache_hk = {'data': [], 'time': 0}

# 美股中英文名称映射（用于中文搜索）
_US_STOCK_NAMES = {
    'AAPL': '苹果', 'MSFT': '微软', 'GOOGL': '谷歌', 'GOOG': '谷歌A',
    'AMZN': '亚马逊', 'NVDA': '英伟达', 'META': 'Meta脸书', 'TSLA': '特斯拉',
    'BRK.B': '伯克希尔', 'JPM': '摩根大通', 'V': 'Visa维萨', 'JNJ': '强生',
    'WMT': '沃尔玛', 'PG': '宝洁', 'HD': '家得宝', 'MA': '万事达',
    'DIS': '迪士尼', 'NFLX': '奈飞Netflix', 'ADBE': 'Adobe', 'CRM': 'Salesforce',
    'PYPL': '贝宝PayPal', 'INTC': '英特尔', 'AMD': 'AMD超微', 'CSCO': '思科',
    'PEP': '百事可乐', 'KO': '可口可乐', 'COST': '好市多Costco', 'AVGO': '博通',
    'MRK': '默克', 'LLY': '礼来', 'UNH': '联合健康', 'PFE': '辉瑞',
    'ABBV': '艾伯维', 'CVX': '雪佛龙', 'XOM': '埃克森美孚', 'BAC': '美国银行',
    'WFC': '富国银行', 'GS': '高盛', 'MS': '摩根士丹利', 'AXP': '美国运通',
    'BLK': '贝莱德', 'C': '花旗', 'ORCL': '甲骨文', 'IBM': 'IBM',
    'QCOM': '高通', 'TXN': '德州仪器', 'MU': '美光科技', 'AMAT': '应用材料',
    'PANW': 'Palo Alto', 'CRWD': 'CrowdStrike', 'SNOW': '雪花Snowflake',
    'SHOP': 'Shopify', 'UBER': '优步Uber', 'ABNB': '爱彼迎Airbnb',
    'COIN': 'Coinbase', 'PLTR': 'Palantir', 'ZM': 'Zoom',
    'BABA': '阿里巴巴', 'BIDU': '百度', 'NIO': '蔚来', 'XPEV': '小鹏汽车',
    'LI': '理想汽车', 'BILI': '哔哩哔哩B站', 'JD': '京东', 'PDD': '拼多多',
    'NTES': '网易', 'TME': '腾讯音乐', 'VIPS': '唯品会', 'BEKE': '贝壳',
    'EDU': '新东方', 'TAL': '好未来', 'ZTO': '中通快递', 'MNSO': '名创优品',
    'FUTU': '富途', 'TIGR': '老虎证券',
}


def fuzzy_search_stocks(keyword):
    """模糊搜索股票 - 获取全部A股后本地匹配"""
    if not keyword:
        return []

    keyword = keyword.strip()
    if len(keyword) < 1:
        return []

    results = []
    seen = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    import urllib.parse
    import time

    # 1. 获取全部A股数据（带缓存）
    now = time.time()
    if not _stock_cache['data'] or (now - _stock_cache['time']) > 3600:
        all_stocks = []
        try:
            for page in range(1, 31):  # 30页 = 3000只
                url = "https://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    'pn': page, 'pz': 100, 'po': 1, 'np': 1,
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': 2, 'invt': 2, 'fid': 'f12',
                    'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                    'fields': 'f12,f14,f57'
                }
                resp = requests.get(url, params=params, headers=headers, timeout=3)
                d = resp.json()
                if not d.get('data') or not d['data'].get('diff'):
                    break
                all_stocks.extend(d['data']['diff'])
                if len(d['data']['diff']) < 100:
                    break
            _stock_cache['data'] = all_stocks
            _stock_cache['time'] = now
        except:
            pass

    # 2. 本地模糊匹配
    keyword_lower = keyword.lower()
    for item in _stock_cache.get('data', []):
        code = str(item.get('f12', ''))
        name = item.get('f14', '')
        pinyin = str(item.get('f57', '')).lower() if item.get('f57') else ''

        # 匹配：代码、名称、拼音
        if (keyword_lower in code or
            keyword_lower in name.lower() or
            (pinyin and keyword_lower in pinyin)):

            if code.startswith('6') or code.startswith('5'):
                code = code + '.SH'
            elif code.startswith('0') or code.startswith('3'):
                code = code + '.SZ'
            else:
                continue

            if code not in seen:
                seen.add(code)
                results.append({'code': code, 'name': name, 'market': 'A'})
                if len(results) >= 30:
                    break

    # 2.5 始终使用东方财富搜索API补充结果（支持拼音首字母等模糊搜索）
    if len(results) < 20:
        try:
            url = f"https://searchapi.eastmoney.com/api/suggest/get?input={urllib.parse.quote(keyword)}&type=14&count=30"
            resp = requests.get(url, headers=headers, timeout=10)
            d = resp.json()
            if d.get('QuotationCodeTable') and d['QuotationCodeTable'].get('Data'):
                for item in d['QuotationCodeTable']['Data']:
                    code = item.get('Code', '')
                    name = item.get('Name', '')
                    if code:
                        # 判断市场
                        if code.startswith('6') or code.startswith('5'):
                            code = code + '.SH'
                        elif code.startswith('0') or code.startswith('3'):
                            code = code + '.SZ'
                        else:
                            continue
                        if code not in seen:
                            seen.add(code)
                            results.append({'code': code, 'name': name, 'market': 'A'})
        except:
            pass

    # 3. 港股 (type=12)
    if len(results) < 5:
        try:
            url = f"https://searchapi.eastmoney.com/api/suggest/get?input={urllib.parse.quote(keyword)}&type=12&count=20"
            resp = requests.get(url, headers=headers, timeout=5)
            d = resp.json()
            if d.get('QuotationCodeTable') and d['QuotationCodeTable'].get('Data'):
                for item in d['QuotationCodeTable']['Data']:
                    if item.get('Classify') == 'HK':
                        code = item.get('Code', '') + '.HK'
                        name = item.get('Name', '')
                        if code not in seen:
                            seen.add(code)
                            results.append({'code': code, 'name': name, 'market': 'HK'})
        except:
            pass

    # 4. 美股 - 本地中英文映射 + Yahoo Finance API
    for sym, cn_name in _US_STOCK_NAMES.items():
        if (keyword_lower in sym.lower() or
            keyword_lower in cn_name.lower()):
            if sym not in seen:
                seen.add(sym)
                results.append({'code': sym, 'name': cn_name, 'market': 'US'})

    try:
        yurl = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(keyword)}&quotes_count=20"
        yresp = requests.get(yurl, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, timeout=5)
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


def get_a_stock_data_sina(ticker):
    """从新浪财经爬取A股实时数据"""
    try:
        # 标准化代码
        code = ticker.replace('.SH', '').replace('.SZ', '')
        # 新浪财经API
        url = f"https://hq.sinajs.cn/list=sh{code}" if code.startswith('6') else f"https://hq.sinajs.cn/list=sz{code}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        }

        response = requests.get(url, headers=headers, timeout=5)
        content = response.text

        if content and 'hq_str_' in content:
            data = content.split('=')[1].strip('";\n ')
            fields = data.split(',')

            if len(fields) >= 32:
                price = float(fields[3]) if fields[3] else 0
                yesterday = float(fields[2]) if fields[2] else 0
                change = price - yesterday if price and yesterday else 0
                change_pct = (change / yesterday * 100) if yesterday else 0
                return {
                    'name': fields[0],
                    'price': price,
                    'change': change,
                    'change_pct': change_pct,
                    'volume': float(fields[8]) if fields[8] else 0,
                    'amount': float(fields[9]) if fields[9] else 0,
                }
    except Exception as e:
        pass

    return None


def get_a_stock_data_eastmoney(ticker):
    """从东方财富获取A股实时数据"""
    try:
        code = ticker.replace('.SH', '').replace('.SZ', '')
        # 东方财富API
        url = f"https://push2.eastmoney.com/api/qt/stock/get"

        params = {
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
            'invt': '2',
            'fltt': '2',
            'fields': 'f43,f47,f48,f58,f162,f167,f168,f169,f170,f173,f184,f186,f188',
            'secid': f"1.{code}" if code.startswith('6') else f"0.{code}"
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        if data.get('data'):
            d = data['data']
            return {
                'name': d.get('f58', ''),
                'price': safe_float(d.get('f43')),
                'change': safe_float(d.get('f169')),
                'change_pct': safe_float(d.get('f170')),
                'volume': safe_float(d.get('f47')),
                'amount': safe_float(d.get('f48')),
                'pe': safe_float(d.get('f162')),
                'pb': safe_float(d.get('f167')),
                'roe': safe_float(d.get('f173')),
                'dividend_yield': safe_float(d.get('f168')),
                'revenue_growth': safe_float(d.get('f184')),
                'gross_margin': safe_float(d.get('f186')),
            }

    except Exception as e:
        pass

    return None


def get_a_stock_data_xueqiu(ticker):
    """从雪球获取A股实时数据"""
    try:
        code = ticker.replace('.SH', '').replace('.SZ', '')
        url = f"https://stock.xueqiu.com/v5/stock/quote.json?symbol={ticker}&size=1"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Cookie': 'xq_a_token=test'
        }

        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        if data.get('data'):
            d = data['data'][0]
            return {
                'name': d.get('name', ''),
                'price': safe_float(d.get('current')),
                'change': safe_float(d.get('change')),
                'change_pct': safe_float(d.get('percent')) * 100,
                'pe': safe_float(d.get('pe_ttm')),
                'pb': safe_float(d.get('pb')),
                'roe': safe_float(d.get('roe_yearly')),
                'dividend_yield': safe_float(d.get('dividend_yield')),
            }

    except Exception as e:
        pass

    return None


def get_a_stock_realtime(ticker):
    """获取A股实时数据 - 尝试多个源"""
    # 标准化代码
    if not ticker.endswith('.SH') and not ticker.endswith('.SZ'):
        ticker = (ticker + '.SH') if ticker.startswith('6') else ticker + '.SZ'

    # 尝试东方财富
    data = get_a_stock_data_eastmoney(ticker)
    if data and data.get('price'):
        return data

    # 尝试雪球
    data = get_a_stock_data_xueqiu(ticker)
    if data and data.get('price'):
        return data

    # 尝试新浪
    data = get_a_stock_data_sina(ticker)
    if data and data.get('price'):
        return data

    return None

app = Flask(__name__)
app.secret_key = 'stock-strategy-secret-key'

# 初始化系统
print("初始化系统...")
data_loader = DataLoader()
factor_engine = FactorEngine()
strategy_pool = StrategyPool()
profile_manager = ProfileManager()

# 预加载股票列表
A_STOCKS = [
    ('600519.SH', '贵州茅台'),
    ('000858.SZ', '五粮液'),
    ('601318.SH', '中国平安'),
    ('600036.SH', '招商银行'),
    ('000333.SZ', '美的集团'),
    ('600900.SH', '长江电力'),
    ('601888.SH', '中国中免'),
    ('600276.SH', '恒瑞医药'),
    ('601166.SH', '兴业银行'),
    ('600030.SH', '中信证券'),
    ('000001.SZ', '平安银行'),
    ('399001.SZ', '深证成指'),
    ('399006.SZ', '创业板指'),
]

US_STOCKS = [
    ('AAPL', '苹果'),
    ('MSFT', '微软'),
    ('GOOGL', '谷歌'),
    ('AMZN', '亚马逊'),
    ('NVDA', '英伟达'),
    ('META', 'Meta'),
    ('TSLA', '特斯拉'),
    ('JPM', '摩根大通'),
    ('V', 'Visa'),
    ('JNJ', '强生'),
    ('WMT', '沃尔玛'),
    ('PG', '宝洁'),
    ('HD', '家得宝'),
    ('DIS', '迪士尼'),
    ('NFLX', 'Netflix'),
]

# 股票基准价格（2026年3月真实价格）
STOCK_BASE_PRICES = {
    # A股
    '600519.SH': 1650, '000858.SZ': 145, '601318.SH': 48,
    '600036.SH': 38, '000333.SZ': 65, '600900.SH': 26,
    '601888.SH': 75, '600276.SH': 52, '601166.SH': 18,
    '600030.SH': 22, '000001.SZ': 13, '399001.SZ': 11500,
    '399006.SZ': 1950,
    # 美股 (真实价格)
    'AAPL': 228, 'MSFT': 415, 'GOOGL': 178, 'AMZN': 228,
    'NVDA': 115, 'META': 620, 'TSLA': 380, 'JPM': 195,
    'V': 295, 'JNJ': 155, 'WMT': 68, 'PG': 168,
    'HD': 385, 'DIS': 125, 'NFLX': 850,
}


def get_mock_data(ticker='', market='A', days=250):
    """生成模拟数据"""
    np.random.seed(hash(ticker) % 10000)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')

    # 获取基准价格
    base_price = STOCK_BASE_PRICES.get(ticker, 100)

    # 模拟股价走势（在基准价格附近波动）
    volatility = 0.02
    price_changes = np.random.randn(days) * volatility
    prices = base_price * np.exp(np.cumsum(price_changes))
    volumes = np.random.randint(1000000, 10000000, days)

    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': prices * (1 + np.random.randn(days) * 0.01),
        'high': prices * (1 + np.abs(np.random.randn(days) * 0.02)),
        'low': prices * (1 - np.abs(np.random.randn(days) * 0.02)),
        'volume': volumes,
    })

    # 添加财务数据
    if market == 'A':
        df['pe'] = np.random.uniform(10, 50, days)
        df['pb'] = np.random.uniform(1, 10, days)
        df['roe'] = np.random.uniform(5, 30, days)
    else:
        df['pe'] = np.random.uniform(15, 40, days)
        df['pb'] = np.random.uniform(2, 15, days)
        df['roe'] = np.random.uniform(10, 35, days)

    return df


def calculate_stock_signals(df, strategy_key):
    """计算具体股票买卖信号"""
    if df is None or df.empty or 'close' not in df.columns:
        return None

    df = df.copy()
    signals = {}

    if strategy_key == 'ma_crossover':
        ma5 = df['close'].rolling(5).mean()
        ma20 = df['close'].rolling(20).mean()
        latest_ma5 = ma5.iloc[-1]
        latest_ma20 = ma20.iloc[-1]
        prev_ma5 = ma5.iloc[-2]
        prev_ma20 = ma20.iloc[-2]

        if prev_ma5 <= prev_ma20 and latest_ma5 > latest_ma20:
            signal = '买入'
        elif prev_ma5 >= prev_ma20 and latest_ma5 < latest_ma20:
            signal = '卖出'
        else:
            signal = '持有'
        signals['MA5'] = latest_ma5
        signals['MA20'] = latest_ma20
        signals['signal'] = signal

    elif strategy_key == 'rsi_oversold':
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.iloc[-1]

        if latest_rsi < 30:
            signal = '买入'
        elif latest_rsi > 70:
            signal = '卖出'
        else:
            signal = '持有'
        signals['RSI'] = latest_rsi
        signals['signal'] = signal

    elif strategy_key == 'volatility_timing':
        returns = df['close'].pct_change()
        volatility = returns.rolling(20).std() * np.sqrt(252) * 100
        latest_vol = volatility.iloc[-1]

        if latest_vol < 20:
            signal = '买入'
        elif latest_vol > 30:
            signal = '卖出'
        else:
            signal = '持有'
        signals['VOLATILITY'] = latest_vol
        signals['signal'] = signal

    elif strategy_key == 'us_trend':
        ma60 = df['close'].rolling(60).mean()
        latest_price = df['close'].iloc[-1]
        latest_ma60 = ma60.iloc[-1]

        if latest_price > latest_ma60:
            signal = '买入'
        else:
            signal = '卖出'
        signals['PRICE'] = latest_price
        signals['MA60'] = latest_ma60
        signals['signal'] = signal

    else:
        signals['signal'] = '持有'

    return signals


def get_us_stock_price(ticker):
    """从Yahoo Finance获取实时美股价格"""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return price
    except:
        return None


def get_us_stock_data_finviz(ticker):
    """从Finviz爬取美股实时财务数据"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(f'https://finviz.com/quote.ashx?t={ticker}', headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        html = r.text

        def extract(label):
            pattern = re.escape(label) + r'</td>\s*<td[^>]*>\s*<b>(?:<span[^>]*>)?([^<]+)(?:</span>)?</b>'
            m = re.search(pattern, html)
            if not m:
                return None
            val = m.group(1).strip().replace('%', '').replace(',', '')
            try:
                return float(val)
            except ValueError:
                return None

        # 股息率从 Dividend TTM 的 (x.xx%) 中提取
        div_yield = 0
        div_match = re.search(r'Dividend TTM.*?<b>.*?\((\d+\.?\d*)%\)', html, re.DOTALL)
        if div_match:
            div_yield = float(div_match.group(1))

        # 股票名称 - 从标题中提取公司名，去掉 "AAPL - " 前缀和 " Stock..." 后缀
        name = ticker
        name_match = re.search(r'<title>\w+\s*-\s*(.+?)(?:\s+Stock\b)', html)
        if name_match:
            name = name_match.group(1).strip()
        else:
            name_match = re.search(r'<title>([^|<]+)', html)
            if name_match:
                name = name_match.group(1).strip()

        price = extract('Price')
        if not price:
            return None

        debt_eq = extract('Debt/Eq') or 0
        return {
            'name': name,
            'price': price,
            'pe': extract('P/E') or 0,
            'pb': extract('P/B') or 0,
            'roe': extract('ROE') or 0,
            'gross_margin': extract('Gross Margin') or 0,
            'revenue_growth': extract('Sales Q/Q') or 0,
            'dividend_yield': div_yield,
            'debt_ratio': debt_eq * 100 / (1 + debt_eq) if debt_eq else 0,
        }
    except Exception as e:
        return None


def get_a_stock_data(ticker, days=250):
    """使用AkShare获取A股历史数据"""
    try:
        # 自动识别股票代码格式
        symbol = ticker.split('.')[0]
        # 6开头是上海交易所，0/3开头是深圳交易所
        if len(symbol) == 6 and symbol.isdigit():
            if symbol.startswith('6'):
                ticker = symbol + '.SH'
            else:
                ticker = symbol + '.SZ'

        end_date = time.strftime('%Y%m%d')
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=days+30)).strftime('%Y%m%d')

        df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq")
        if df is not None and not df.empty:
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            })
            df = df[['date', 'open', 'close', 'high', 'low', 'volume']]
            df['date'] = pd.to_datetime(df['date'])
            return df.tail(days)
    except Exception as e:
        print(f"获取A股数据失败 {ticker}: {e}")
    return None


def get_us_stock_data(ticker, days=250):
    """获取美股历史数据 - 优先Stooq，回退Yahoo Finance"""
    from io import StringIO

    # 1. 尝试 Stooq（免费、稳定、完整 OHLCV）
    try:
        stooq_ticker = ticker.replace('.', '-').upper() + '.US'
        url = f'https://stooq.com/q/d/l/?s={stooq_ticker.lower()}&i=d'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and 'Date' in r.text[:50]:
            df = pd.read_csv(StringIO(r.text))
            if not df.empty and len(df) > 10:
                df = df.rename(columns={
                    'Date': 'date', 'Open': 'open', 'Close': 'close',
                    'High': 'high', 'Low': 'low', 'Volume': 'volume'
                })
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                return df.tail(days)
    except Exception as e:
        print(f"Stooq获取失败 {ticker}: {e}")

    # 2. 回退 Yahoo Finance Chart API
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        params = {'period1': int((pd.Timestamp.now() - pd.Timedelta(days=days+30)).timestamp()),
                  'period2': int(pd.Timestamp.now().timestamp()),
                  'interval': '1d'}
        r = requests.get(url, params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()

        if 'chart' in data and data['chart']['result']:
            result = data['chart']['result'][0]
            quotes = result['indicators']['quote'][0]
            df = pd.DataFrame({
                'date': pd.to_datetime(result['timestamp'], unit='s'),
                'open': quotes.get('open'),
                'close': quotes.get('close'),
                'high': quotes.get('high'),
                'low': quotes.get('low'),
                'volume': quotes.get('volume'),
            })
            df = df.dropna()
            return df.tail(days)
    except Exception as e:
        print(f"Yahoo获取失败 {ticker}: {e}")

    return None


def get_stock_recommendations(strategy_key, market='A', n=10):
    """获取具体股票推荐列表"""
    recommendations = []

    stock_list = A_STOCKS if market == 'A' else US_STOCKS

    for ticker, name in stock_list[:n]:
        # 获取真实数据
        if market == 'A':
            df = get_a_stock_data(ticker)
        else:
            df = get_us_stock_data(ticker)

        if df is None or df.empty:
            continue

        # 获取当前价格
        current_price = df['close'].iloc[-1] if 'close' in df.columns else 0

        # 计算信号
        signals = calculate_stock_signals(df, strategy_key)

        if signals:
            recommendations.append({
                'ticker': ticker,
                'name': name,
                'signal': signals.get('signal', '持有'),
                'price': current_price,
                'details': signals
            })

    return recommendations


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>量化策略推荐系统</title>
    <style>
        :root {
            --sidebar-bg: #1a1f2e;
            --sidebar-hover: #252b3b;
            --sidebar-active: #2d344a;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --accent-light: #eff6ff;
            --body-bg: #f1f5f9;
            --card-bg: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --text-sidebar: #cbd5e1;
            --border: #e2e8f0;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --surface: #f8fafc;
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: var(--font-sans);
            background: var(--body-bg);
            min-height: 100vh;
            color: var(--text-primary);
        }

        /* Layout */
        .app-layout { display: flex; min-height: 100vh; }

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--sidebar-bg);
            color: var(--text-sidebar);
            display: flex;
            flex-direction: column;
            position: fixed;
            top: 0; left: 0; bottom: 0;
            z-index: 100;
            overflow-y: auto;
            transition: transform 0.3s ease;
        }
        .sidebar-header {
            padding: 24px 20px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .sidebar-logo {
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
            margin: 0;
        }
        .sidebar-subtitle {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 2px;
        }
        .sidebar-nav { flex: 1; padding: 8px 0; }
        .nav-group { margin-bottom: 4px; }
        .nav-group-label {
            padding: 16px 20px 6px;
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            width: 100%;
            padding: 10px 20px;
            border: none;
            background: none;
            color: var(--text-sidebar);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s, color 0.15s;
            text-align: left;
            border-left: 3px solid transparent;
            font-family: var(--font-sans);
        }
        .nav-item:hover {
            background: var(--sidebar-hover);
            color: #fff;
        }
        .nav-item.active {
            background: var(--sidebar-active);
            color: #fff;
            border-left-color: var(--accent);
        }
        .nav-icon {
            width: 20px;
            text-align: center;
            font-size: 1rem;
            opacity: 0.7;
        }
        .nav-item.active .nav-icon { opacity: 1; }
        .sidebar-footer {
            padding: 16px 20px;
            border-top: 1px solid rgba(255,255,255,0.08);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8rem;
        }
        .sidebar-footer a {
            color: var(--text-muted);
            text-decoration: none;
            transition: color 0.15s;
        }
        .sidebar-footer a:hover { color: var(--danger); }

        /* Mobile header */
        .mobile-header {
            display: none;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .menu-toggle {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-primary);
            padding: 4px;
        }
        .mobile-title {
            font-weight: 600;
            font-size: 1rem;
            color: var(--text-primary);
        }
        .sidebar-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.4);
            z-index: 99;
        }

        /* Main content */
        .main-content {
            flex: 1;
            margin-left: 260px;
            padding: 24px 32px;
            min-height: 100vh;
        }
        .content-header {
            margin-bottom: 24px;
        }
        .page-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
        }
        .page-subtitle {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        /* Login page */
        #loginPage {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: var(--body-bg);
        }
        .login-box {
            max-width: 400px;
            width: 100%;
            background: var(--card-bg);
            border-radius: 12px;
            padding: 40px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        }
        .login-box h2 {
            text-align: center;
            margin-bottom: 24px;
            font-size: 1.5rem;
            color: var(--text-primary);
            font-weight: 700;
        }
        .login-hint {
            text-align: center;
            margin-top: 20px;
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        /* Card */
        .card {
            background: var(--card-bg);
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .card h2 {
            color: var(--text-primary);
            font-size: 1.15rem;
            font-weight: 600;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        .card h3 {
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 12px;
        }

        /* Form */
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            margin-bottom: 6px;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.875rem;
        }
        .form-group input, .form-group select,
        .form-input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.875rem;
            background: var(--card-bg);
            color: var(--text-primary);
            transition: border-color 0.15s, box-shadow 0.15s;
            font-family: var(--font-sans);
        }
        .form-group input:focus, .form-group select:focus,
        .form-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
        }

        /* Input row */
        .input-row {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .input-row input[type="text"] {
            flex: 1;
            min-width: 220px;
            height: 42px;
            font-size: 0.95rem;
            padding: 8px 12px;
        }
        .input-row select {
            height: 42px;
            font-size: 0.85rem;
            padding: 8px;
            width: auto;
        }
        .input-row .btn {
            height: 42px;
            padding: 8px 20px;
        }
        .stock-name-badge {
            padding: 8px 12px;
            background: var(--surface);
            border-radius: 6px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }

        /* Buttons */
        .btn {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 10px 20px;
            font-size: 0.875rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            width: auto;
            transition: background 0.15s, box-shadow 0.15s;
            font-family: var(--font-sans);
        }
        .btn:hover {
            background: var(--accent-hover);
            box-shadow: 0 2px 8px rgba(59,130,246,0.25);
        }
        .btn-block { width: 100%; }
        .btn-small {
            padding: 6px 12px;
            font-size: 0.75rem;
            border-radius: 4px;
        }
        .btn-outline {
            background: transparent;
            color: var(--accent);
            border: 1px solid var(--accent);
        }
        .btn-outline:hover {
            background: var(--accent-light);
            box-shadow: none;
        }

        /* Quick select buttons */
        .quick-select { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }

        /* Checkbox group */
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }
        .checkbox-group label {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: border-color 0.15s, background 0.15s;
            color: var(--text-primary);
            font-weight: 400;
            margin-bottom: 0;
        }
        .checkbox-group label:hover {
            border-color: var(--accent);
        }

        /* Result card */
        .result-card {
            background: var(--surface);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent);
        }
        .result-card h3 { color: var(--text-primary); margin-bottom: 12px; }

        /* Metrics */
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }
        .metric {
            background: var(--surface);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--border);
        }
        .metric-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }
        .metric-value { font-size: 1.5em; font-weight: 700; color: var(--text-primary); }
        .metric-value.positive { color: var(--success); }
        .metric-value.negative { color: var(--danger); }
        .metric-value.buy { color: var(--success); }
        .metric-value.sell { color: var(--danger); }
        .metric-value.hold { color: var(--warning); }

        /* Table */
        .stock-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
        .stock-table th {
            background: var(--surface);
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.04em;
            padding: 10px 12px;
            text-align: left;
            border-bottom: 2px solid var(--border);
        }
        .stock-table td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
        }
        .stock-table tr:hover td { background: var(--surface); }
        .signal-buy { color: var(--success); font-weight: 600; }
        .signal-sell { color: var(--danger); font-weight: 600; }
        .signal-hold { color: var(--warning); font-weight: 600; }

        /* Strategy select */
        .strategy-select {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        .strategy-option {
            padding: 15px;
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
            background: var(--card-bg);
        }
        .strategy-option:hover { border-color: var(--accent); }
        .strategy-option.selected {
            border-color: var(--accent);
            background: var(--accent-light);
        }

        /* Stock input group (legacy compat) */
        .stock-input-group {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .stock-input-group input[type="text"] {
            flex: 1;
            min-width: 220px;
            height: 42px;
            font-size: 0.95rem;
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
        }
        .stock-input-group select {
            height: 42px;
            font-size: 0.85rem;
            padding: 8px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }
        .stock-input-group .btn {
            width: auto;
            height: 42px;
            padding: 8px 20px;
        }

        /* Info card */
        .info-card {
            background: var(--surface);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        .info-card strong { color: var(--text-primary); }
        .info-card p { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }

        /* Utilities */
        .hidden { display: none !important; }
        .loading { text-align: center; padding: 40px; color: var(--text-muted); }

        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .mobile-header { display: flex; }
            .main-content { margin-left: 0; padding: 16px; }
            .card { padding: 16px; }
            .metrics { grid-template-columns: repeat(2, 1fr); }
            .input-row { flex-direction: column; }
            .input-row input[type="text"] { min-width: 100%; }
            .stock-input-group { flex-direction: column; }
            .stock-input-group input[type="text"] { min-width: 100%; }
        }
        @media (min-width: 769px) and (max-width: 1024px) {
            .sidebar { width: 220px; }
            .main-content { margin-left: 220px; padding: 20px 24px; }
        }
        @media (min-width: 1025px) {
            .mobile-header { display: none; }
        }
    </style>
</head>
<body>
    <div id="loginPage">
        <div class="login-box">
            <h2>量化策略推荐系统</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" id="loginUsername" value="root" required>
                </div>
                <div class="form-group">
                    <label>密码</label>
                    <input type="password" id="loginPassword" value="1root2378" required>
                </div>
                <button type="submit" class="btn btn-block">登录</button>
            </form>
            <p class="login-hint">默认账户: root / 1root2378</p>
        </div>
    </div>

    <div id="mainPage" class="app-layout hidden">
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h1 class="sidebar-logo">量化策略</h1>
                <span class="sidebar-subtitle">推荐系统 · A股+美股</span>
            </div>
            <nav class="sidebar-nav">
                <div class="nav-group">
                    <div class="nav-group-label">核心功能</div>
                    <button class="nav-item active" data-tab="recommend">
                        <span class="nav-icon">&#9733;</span><span class="nav-text">策略推荐</span>
                    </button>
                    <button class="nav-item" data-tab="stock">
                        <span class="nav-icon">&#9650;</span><span class="nav-text">股票推荐</span>
                    </button>
                    <button class="nav-item" data-tab="backtest">
                        <span class="nav-icon">&#8634;</span><span class="nav-text">策略回测</span>
                    </button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-label">技术分析</div>
                    <button class="nav-item" data-tab="kline">
                        <span class="nav-icon">&#9636;</span><span class="nav-text">K线分析</span>
                    </button>
                    <button class="nav-item" data-tab="candle">
                        <span class="nav-icon">&#9670;</span><span class="nav-text">蜡烛图</span>
                    </button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-label">大师策略</div>
                    <button class="nav-item" data-tab="zhenGuize">
                        <span class="nav-icon">&#9745;</span><span class="nav-text">真规则</span>
                    </button>
                    <button class="nav-item" data-tab="linch">
                        <span class="nav-icon">&#9679;</span><span class="nav-text">彼得林奇</span>
                    </button>
                    <button class="nav-item" data-tab="oneil">
                        <span class="nav-icon">&#9650;</span><span class="nav-text">欧奈尔</span>
                    </button>
                    <button class="nav-item" data-tab="graham">
                        <span class="nav-icon">&#9711;</span><span class="nav-text">格雷厄姆</span>
                    </button>
                    <button class="nav-item" data-tab="marks">
                        <span class="nav-icon">&#9888;</span><span class="nav-text">马克斯</span>
                    </button>
                    <button class="nav-item" data-tab="malkiel">
                        <span class="nav-icon">&#8594;</span><span class="nav-text">漫步</span>
                    </button>
                    <button class="nav-item" data-tab="comprehensive">
                        <span class="nav-icon">&#9776;</span><span class="nav-text">综合策略</span>
                    </button>
                </div>
                <div class="nav-group">
                    <div class="nav-group-label">系统</div>
                    <button class="nav-item" data-tab="settings">
                        <span class="nav-icon">&#9881;</span><span class="nav-text">设置</span>
                    </button>
                </div>
            </nav>
            <div class="sidebar-footer">
                <span id="currentUser"></span>
                <a href="#" onclick="logout()">退出登录</a>
            </div>
        </aside>

        <div class="sidebar-overlay hidden" id="sidebarOverlay" onclick="toggleSidebar(false)"></div>

        <header class="mobile-header">
            <button class="menu-toggle" onclick="toggleSidebar()">&#9776;</button>
            <span class="mobile-title">量化策略推荐系统</span>
        </header>

        <main class="main-content">
            <div class="content-header">
                <h2 class="page-title" id="pageTitle">策略推荐</h2>
                <p class="page-subtitle">A股 + 美股 智能策略匹配</p>
            </div>

        <!-- 策略推荐 -->
        <div id="recommendTab">
            <div class="card">
                <h2>根据您的画像推荐策略</h2>
                <div id="userProfileInfo" class="info-card" style="margin-bottom: 16px;"></div>
                <button class="btn" onclick="getRecommendations()">获取推荐</button>
            </div>
            <div id="recommendResults"></div>
        </div>

        <!-- 股票推荐 -->
        <div id="stockTab" class="hidden">
            <div class="card">
                <h2>具体股票买卖推荐</h2>
                <div class="form-group">
                    <label>选择策略（可多选）</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="stockStrat1" value="ma_crossover" checked> MA5/20交叉</label>
                        <label><input type="checkbox" id="stockStrat2" value="macd"> MACD</label>
                        <label><input type="checkbox" id="stockStrat3" value="rsi_oversold"> RSI</label>
                        <label><input type="checkbox" id="stockStrat4" value="bollinger"> 布林带</label>
                        <label><input type="checkbox" id="stockStrat5" value="breakout"> 突破新高</label>
                        <label><input type="checkbox" value="ma10_20"> MA10/20</label>
                        <label><input type="checkbox" value="ma20_60"> MA20/60</label>
                        <label><input type="checkbox" value="volatility_timing"> 波动率</label>
                        <label><input type="checkbox" value="hammer"> 锤子线</label>
                        <label><input type="checkbox" value="bullish_engulfing"> 看涨吞没</label>
                        <label><input type="checkbox" value="morning_star"> 早晨之星</label>
                        <label><input type="checkbox" value="doji"> 十字星</label>
                    </div>
                </div>
                <div class="form-group">
                    <label>选择市场</label>
                    <select id="stockMarket" onchange="getStockRecommendations()">
                        <option value="A">A股</option>
                        <option value="US">美股</option>
                    </select>
                </div>
                <button class="btn" onclick="getStockRecommendations()">获取股票推荐</button>
            </div>
            <div id="stockResults"></div>
        </div>

        <!-- 策略回测 -->
        <div id="backtestTab" class="hidden">
            <div class="card">
                <h2>策略回测</h2>
                <div class="form-group">
                    <label>回测标的</label>
                    <div class="input-row">
                        <input type="text" id="backtestTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="backtestMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <select id="backtestDays">
                            <option value="120">120日</option>
                            <option value="250" selected>250日</option>
                            <option value="500">500日</option>
                        </select>
                    </div>
                    <div class="quick-select">
                        <button class="btn btn-small btn-outline" onclick="document.getElementById('backtestTicker').value='600519.SH'; document.getElementById('backtestMarket').value='A'">贵州茅台</button>
                        <button class="btn btn-small btn-outline" onclick="document.getElementById('backtestTicker').value='300750.SZ'; document.getElementById('backtestMarket').value='A'">宁德时代</button>
                        <button class="btn btn-small btn-outline" onclick="document.getElementById('backtestTicker').value='AAPL'; document.getElementById('backtestMarket').value='US'">AAPL</button>
                        <button class="btn btn-small btn-outline" onclick="document.getElementById('backtestTicker').value='MSFT'; document.getElementById('backtestMarket').value='US'">MSFT</button>
                    </div>
                </div>
                <div class="form-group">
                    <label>技术指标策略</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" class="backtest-strat" value="ma_crossover" checked> MA5/20交叉</label>
                        <label><input type="checkbox" class="backtest-strat" value="macd"> MACD金叉死叉</label>
                        <label><input type="checkbox" class="backtest-strat" value="rsi_oversold"> RSI超买超卖</label>
                        <label><input type="checkbox" class="backtest-strat" value="bollinger"> 布林带</label>
                        <label><input type="checkbox" class="backtest-strat" value="breakout"> 突破20日新高</label>
                        <label><input type="checkbox" class="backtest-strat" value="ma10_20"> MA10/20交叉</label>
                        <label><input type="checkbox" class="backtest-strat" value="ma20_60"> MA20/60交叉</label>
                        <label><input type="checkbox" class="backtest-strat" value="volatility_timing"> 波动率择时</label>
                    </div>
                </div>
                <div class="form-group">
                    <label>K线形态策略 (日本蜡烛图技术)</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" class="backtest-strat" value="hammer"> 锤子线</label>
                        <label><input type="checkbox" class="backtest-strat" value="hanging_man"> 上吊线</label>
                        <label><input type="checkbox" class="backtest-strat" value="bullish_engulfing"> 看涨吞没</label>
                        <label><input type="checkbox" class="backtest-strat" value="bearish_engulfing"> 看跌吞没</label>
                        <label><input type="checkbox" class="backtest-strat" value="doji"> 十字星</label>
                        <label><input type="checkbox" class="backtest-strat" value="morning_star"> 早晨之星</label>
                        <label><input type="checkbox" class="backtest-strat" value="evening_star"> 黄昏之星</label>
                        <label><input type="checkbox" class="backtest-strat" value="shooting_star"> 流星</label>
                        <label><input type="checkbox" class="backtest-strat" value="inverted_hammer"> 倒锤子线</label>
                    </div>
                    <div class="quick-select" style="margin-top: 8px;">
                        <label style="font-size:0.8rem;color:var(--text-secondary);">快速选择：</label>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectBacktestStrategies(['ma_crossover','macd','rsi_oversold'])">三叉戟组合</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectBacktestStrategies(['ma_crossover','breakout'])">趋势突破</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectBacktestStrategies(['morning_star','bullish_engulfing','hammer','evening_star','bearish_engulfing'])">K线反转组合</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectBacktestStrategies(['ma_crossover','macd','rsi_oversold','bollinger','breakout','ma10_20','ma20_60','volatility_timing'])">全技术指标</button>
                    </div>
                </div>
                <button class="btn" onclick="runBacktest()" style="margin-top: 12px;">运行回测</button>
            </div>
            <div id="backtestResults"></div>
        </div>

        <!-- 用户设置 -->
        <div id="settingsTab" class="hidden">
            <div class="card">
                <h2>用户画像设置</h2>
                <form id="profileForm">
                    <div class="form-group">
                        <label>市场偏好</label>
                        <select id="settingMarket">
                            <option value="双市场">双市场</option>
                            <option value="A股">A股</option>
                            <option value="美股">美股</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>风险等级</label>
                        <select id="settingRisk">
                            <option value="保守型">保守型 (最大回撤≤10%)</option>
                            <option value="稳健型">稳健型 (最大回撤≤15%)</option>
                            <option value="激进型">激进型 (最大回撤≤20%)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>收益目标</label>
                        <select id="settingReturn">
                            <option value="0.05">5%</option>
                            <option value="0.10">10%</option>
                            <option value="0.15">15%+</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>持仓周期</label>
                        <select id="settingPeriod">
                            <option value="短期">短期 (<1月)</option>
                            <option value="中期">中期 (1-6月)</option>
                            <option value="长期">长期 (>6月)</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">保存设置</button>
                </form>
            </div>
            <div class="card">
                <h2>生成报告</h2>
                <button class="btn" onclick="generateReport()">下载推荐报告</button>
            </div>
        </div>

        <!-- K线分析 -->
        <div id="klineTab" class="hidden">
            <div class="card">
                <h2>K线走势分析</h2>
                <div class="stock-input-group">
                    <input type="text" id="klineTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                    <datalist id="stockList"></datalist>
                    <span id="klineStockName" class="stock-name-badge">贵州茅台</span>
                    <select id="klineMarket" onchange="updateKlineStockList()">
                        <option value="A">A股</option>
                        <option value="US">美股</option>
                    </select>
                    <button class="btn" onclick="loadKline()">加载K线</button>
                </div>
                <div class="form-group" id="klineStrategy">
                    <label>选择策略（可多选）</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" value="ma_crossover" checked> MA5/20交叉</label>
                        <label><input type="checkbox" value="macd"> MACD金叉死叉</label>
                        <label><input type="checkbox" value="rsi_oversold"> RSI超买超卖</label>
                        <label><input type="checkbox" value="bollinger"> 布林带</label>
                        <label><input type="checkbox" value="breakout"> 突破20日新高</label>
                        <label><input type="checkbox" value="ma10_20"> MA10/20交叉</label>
                        <label><input type="checkbox" value="ma20_60"> MA20/60交叉</label>
                        <label><input type="checkbox" value="volatility_timing"> 波动率择时</label>
                        <label><input type="checkbox" value="hammer"> 锤子线</label>
                        <label><input type="checkbox" value="hanging_man"> 上吊线</label>
                        <label><input type="checkbox" value="bullish_engulfing"> 看涨吞没</label>
                        <label><input type="checkbox" value="bearish_engulfing"> 看跌吞没</label>
                        <label><input type="checkbox" value="doji"> 十字星</label>
                        <label><input type="checkbox" value="morning_star"> 早晨之星</label>
                        <label><input type="checkbox" value="evening_star"> 黄昏之星</label>
                        <label><input type="checkbox" value="shooting_star"> 流星</label>
                        <label><input type="checkbox" value="inverted_hammer"> 倒锤子线</label>
                    </div>
                    <div class="quick-select" style="margin-top: 8px;">
                        <label style="font-size:0.8rem;color:var(--text-secondary);">快速选择：</label>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectStrategies(['ma_crossover','macd','rsi_oversold'])">三叉戟组合</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectStrategies(['ma_crossover','breakout'])">趋势突破组合</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectStrategies(['ma10_20','ma20_60','macd'])">均线多头排列</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectStrategies(['rsi_oversold','bollinger'])">均值回归组合</button>
                        <button type="button" class="btn btn-small btn-outline" onclick="selectStrategies(['morning_star','bullish_engulfing','hammer'])">K线反转组合</button>
                    </div>
                </div>
            </div>
            <div id="klineChart" style="height: 500px;"></div>
            <div id="klineSignals"></div>
        </div>

        <!-- 真规则推荐 -->
        <div id="zhenGuizeTab" class="hidden">
            <div class="card">
                <h2>股市真规则分析 - 基于《股市真规则：世界顶级评级机构的投资真经》</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">晨星公司五大原则：做好功课 | 寻找护城河 | 安全边际 | 长期持有 | 知道何时卖出</p>

                <div class="form-group">
                    <label>输入股票代码或名称</label>
                    <div class="input-row">
                        <input type="text" id="zhenGuizeTicker" list="zgStockList" placeholder="股票代码/名称/拼音首字母" value="600519.SH">
                        <datalist id="zgStockList"></datalist>
                        <select id="zhenGuizeMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeZhenGuize()">全面分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setZhenGuizeStock('600519.SH', '贵州茅台')">贵州茅台</button>
                    <button class="btn btn-small btn-outline" onclick="setZhenGuizeStock('000858.SZ', '五粮液')">五粮液</button>
                    <button class="btn btn-small btn-outline" onclick="setZhenGuizeStock('601318.SH', '中国平安')">中国平安</button>
                    <button class="btn btn-small btn-outline" onclick="setZhenGuizeStock('600036.SH', '招商银行')">招商银行</button>
                    <button class="btn btn-small btn-outline" onclick="setZhenGuizeStock('000333.SZ', '美的集团')">美的集团</button>
                    <button class="btn btn-small btn-outline" onclick="document.getElementById('zhenGuizeMarket').value='US'; setZhenGuizeStock('AAPL', 'Apple')">AAPL</button>
                    <button class="btn btn-small btn-outline" onclick="document.getElementById('zhenGuizeMarket').value='US'; setZhenGuizeStock('MSFT', 'Microsoft')">MSFT</button>
                    <button class="btn btn-small btn-outline" onclick="document.getElementById('zhenGuizeMarket').value='US'; setZhenGuizeStock('NVDA', 'NVIDIA')">NVDA</button>
                </div>
            </div>

            <div id="zhenGuizeResult"></div>
        </div>

        <!-- 彼得林奇推荐 -->
        <div id="linchTab" class="hidden">
            <div class="card">
                <h2>彼得林奇投资法 - 选股实践</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">"投资你了解的公司，PEG&lt;1是被低估的金股" - 《彼得林奇的成功投资》</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="linchTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="linchMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeLinch()">林奇式分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('linch', '600519.SH', '贵州茅台')">贵州茅台</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('linch', '000651.SZ', '格力电器')">格力电器</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('linch', 'AAPL', '苹果')">苹果</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('linch', 'WMT', '沃尔玛')">沃尔玛</button>
                </div>
            </div>
            <div id="linchResult"></div>

            <div class="card">
                <h3>彼得林奇核心方法论</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div class="info-card">
                        <strong>PEG比率 (核心指标)</strong>
                        <p>PEG=PE/盈利增长率。PEG&lt;1=被低估，PEG&gt;2=被高估。林奇最看重的单一指标。</p>
                    </div>
                    <div class="info-card">
                        <strong>6大股票分类</strong>
                        <p>缓慢增长、稳定增长、快速增长(最爱)、周期型、困境反转、隐蔽资产型</p>
                    </div>
                    <div class="info-card">
                        <strong>从生活中发现10倍股</strong>
                        <p>逛商场发现好产品→调研公司→分析财务→在华尔街之前买入</p>
                    </div>
                    <div class="info-card">
                        <strong>避免的6种股票</strong>
                        <p>热门行业热门股、被吹捧的下一个XX、多元恶化、小道消息、依赖大客户</p>
                    </div>
                    <div class="info-card">
                        <strong>13条选股准则</strong>
                        <p>名字无聊、业务简单、持续增长、高利润率、低负债、有分红、PEG&lt;1……</p>
                    </div>
                    <div class="info-card">
                        <strong>鸡尾酒会理论</strong>
                        <p>无人谈股=底部，人人推荐=顶部。当牙医都给你推荐股票时，该卖了。</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 欧奈尔CAN SLIM -->
        <div id="oneilTab" class="hidden">
            <div class="card">
                <h2>欧奈尔CAN SLIM - 趋势投资</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">"买入强势股，卖出弱势股" - 威廉·欧奈尔</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="oneilTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="oneilMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeOneil()">CAN SLIM分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('oneil', '600519.SH', '贵州茅台')">贵州茅台</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('oneil', '300750.SZ', '宁德时代')">宁德时代</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('oneil', 'NVDA', '英伟达')">英伟达</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('oneil', 'TSLA', '特斯拉')">特斯拉</button>
                </div>
            </div>
            <div id="oneilResult"></div>

            <div class="card">
                <h3>CAN SLIM 法则详解（《笑傲股市》第4版）</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div class="info-card">
                        <strong>C = 当季EPS</strong>
                        <p>当季每股收益同比增长≥25%，最好加速增长(如15%→25%→40%)</p>
                    </div>
                    <div class="info-card">
                        <strong>A = 年度增长</strong>
                        <p>过去3-5年年均EPS增长≥25%，ROE≥17%</p>
                    </div>
                    <div class="info-card">
                        <strong>N = 新产品/新高</strong>
                        <p>有创新产品或管理层变革，股价创新高(突破杯柄形态)</p>
                    </div>
                    <div class="info-card">
                        <strong>S = 供给与需求</strong>
                        <p>流通盘适中，关键时刻放量突破，有股票回购</p>
                    </div>
                    <div class="info-card">
                        <strong>L = 领涨股</strong>
                        <p>相对强度RS≥80，买行业第一而非跟风股</p>
                    </div>
                    <div class="info-card">
                        <strong>I = 机构认同</strong>
                        <p>至少有几家优秀基金持有，且近期有增持动作</p>
                    </div>
                    <div class="info-card">
                        <strong>M = 市场走向</strong>
                        <p>4/3大盘上涨才买入。通过涨跌分布日判断顶底</p>
                    </div>
                </div>
                <div class="info-card" style="margin-top:12px;">
                    <strong>📖 欧奈尔买卖规则</strong>
                    <p>买入：杯柄形态突破时入场 | 止损：买入后跌7-8%无条件止损 | 持有：前3周涨20%以上则至少持8周</p>
                </div>
            </div>
        </div>

        <!-- 格雷厄姆价值投资 -->
        <div id="grahamTab" class="hidden">
            <div class="card">
                <h2>格雷厄姆价值投资 - 安全边际</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">"市场短期是投票机，长期是称重机。买入价格低于内在价值2/3的股票" - 《证券分析》</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="grahamTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="grahamMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeGraham()">价值分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('graham', '601398.SH', '工商银行')">工商银行</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('graham', '601939.SH', '建设银行')">建设银行</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('graham', 'JNJ', '强生')">强生</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('graham', 'PG', '宝洁')">宝洁</button>
                </div>
            </div>
            <div id="grahamResult"></div>

            <div class="card">
                <h3>格雷厄姆核心工具（《证券分析》）</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div class="info-card">
                        <strong>格雷厄姆数字</strong>
                        <p>GN = √(22.5 × EPS × BVPS)。股价低于GN即被低估。</p>
                    </div>
                    <div class="info-card">
                        <strong>内在价值公式</strong>
                        <p>V = EPS × (8.5 + 2g)。g=预期增长率。买入价应低于V的2/3。</p>
                    </div>
                    <div class="info-card">
                        <strong>安全边际 (核心)</strong>
                        <p>在价格大幅低于内在价值时买入（≥33%折扣），为误判留余地。</p>
                    </div>
                    <div class="info-card">
                        <strong>防御型7条准则</strong>
                        <p>规模、财务强度、盈利稳定、分红记录、盈利增长、PE≤15、PE×PB≤22.5</p>
                    </div>
                    <div class="info-card">
                        <strong>市场先生寓言</strong>
                        <p>市场是情绪化的"先生"，利用他的恐惧和贪婪，而非被他左右。</p>
                    </div>
                    <div class="info-card">
                        <strong>分散与纪律</strong>
                        <p>持有10-30只达标股票。严格执行估值标准，忽略短期波动。</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 综合策略 -->
        <div id="comprehensiveTab" class="hidden">
            <div class="card">
                <h2>综合策略 - 六维度深度投资分析</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">融合林奇(成长)、格雷厄姆(价值)、欧奈尔(动量)、真规则(护城河)、马克斯(风险)、马尔基尔(配置)六大投资智慧</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="compTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="compMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeComprehensive()">综合分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('comp', '600519.SH', '贵州茅台')">贵州茅台</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('comp', '601318.SH', '中国平安')">中国平安</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('comp', 'AAPL', '苹果')">苹果</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('comp', 'MSFT', '微软')">微软</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('comp', 'NVDA', '英伟达')">英伟达</button>
                </div>
            </div>
            <div id="comprehensiveResult"></div>

            <div class="card">
                <h3>综合分析六大维度</h3>
                <p style="color: var(--text-secondary); margin-top: 8px; font-size: 0.85rem;">
                    融合6位投资大师的核心思想，从6个维度全方位评估股票：
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-top: 12px;">
                    <div class="info-card" style="border-top:3px solid #3b82f6;">
                        <strong>成长性(20%)</strong>
                        <p>林奇: PEG比率、增长持续性、6大分类</p>
                    </div>
                    <div class="info-card" style="border-top:3px solid #10b981;">
                        <strong>价值安全(20%)</strong>
                        <p>格雷厄姆: 格雷厄姆数字、PE×PB≤22.5、安全边际</p>
                    </div>
                    <div class="info-card" style="border-top:3px solid #8b5cf6;">
                        <strong>业绩动量(15%)</strong>
                        <p>欧奈尔: EPS加速增长、CAN SLIM达标率</p>
                    </div>
                    <div class="info-card" style="border-top:3px solid #f59e0b;">
                        <strong>竞争优势(15%)</strong>
                        <p>真规则: ROE持续性、毛利率、护城河宽度</p>
                    </div>
                    <div class="info-card" style="border-top:3px solid #ef4444;">
                        <strong>风险控制(15%)</strong>
                        <p>马克斯: 第二层思维、下行风险、安全垫</p>
                    </div>
                    <div class="info-card" style="border-top:3px solid #14b8a6;">
                        <strong>配置价值(15%)</strong>
                        <p>马尔基尔: 生命周期配置、坚实基础估值</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 霍华德·马克斯 - 投资最重要的事 -->
        <div id="marksTab" class="hidden">
            <div class="card">
                <h2>投资最重要的事 - 霍华德·马克斯</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">"第二层思维、风险控制、逆向投资"</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="marksTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="marksMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeMarks()">风险分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('marks', '600519.SH', '贵州茅台')">贵州茅台</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('marks', 'AAPL', '苹果')">苹果</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('marks', 'MSFT', '微软')">微软</button>
                </div>
            </div>
            <div id="marksResult"></div>

            <div class="card">
                <h3>霍华德·马克斯投资理念</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div class="info-card">
                        <strong>1. 第二层思维</strong>
                        <p>逆向思考，不从众</p>
                    </div>
                    <div class="info-card">
                        <strong>2. 理解风险</strong>
                        <p>风险控制比收益更重要</p>
                    </div>
                    <div class="info-card">
                        <strong>3. 逆向投资</strong>
                        <p>别人恐惧时贪婪</p>
                    </div>
                    <div class="info-card">
                        <strong>4. 耐心等待</strong>
                        <p>好机会需要等待</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 蜡烛图技术 -->
        <div id="candleTab" class="hidden">
            <div class="card">
                <h2>日本蜡烛图技术分析 - 基于《日本蜡烛图技术新解》</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">全面识别K线形态（单根/双根/三根/持续形态），结合均线、RSI、MACD、布林带及成交量综合研判</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="candleTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="candleMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <select id="candleDays">
                            <option value="60">60日</option>
                            <option value="120" selected>120日</option>
                            <option value="250">250日</option>
                        </select>
                        <button class="btn" onclick="analyzeCandle()">开始分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('candle', '600519.SH', '贵州茅台')">贵州茅台</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('candle', '300750.SZ', '宁德时代')">宁德时代</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('candle', 'AAPL', 'Apple'); document.getElementById('candleMarket').value='US'">AAPL</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('candle', 'MSFT', 'Microsoft'); document.getElementById('candleMarket').value='US'">MSFT</button>
                </div>
            </div>

            <div id="candleResult"></div>
        </div>

        <!-- 漫步华尔街 -->
        <div id="malkielTab" class="hidden">
            <div class="card">
                <h2>漫步华尔街 - 伯顿·马尔基尔</h2>
                <p style="color: var(--text-secondary); margin-bottom: 16px; font-size: 0.85rem;">"长期来看，大多数主动选股不如指数基金。坚实基础理论+生命周期配置" - 《漫步华尔街》第10版</p>

                <div class="form-group">
                    <label>输入股票代码</label>
                    <div class="input-row">
                        <input type="text" id="malkielTicker" list="stockList" placeholder="输入股票代码或名称" value="600519.SH">
                        <select id="malkielMarket">
                            <option value="A">A股</option>
                            <option value="US">美股</option>
                        </select>
                        <button class="btn" onclick="analyzeMalkiel()">漫步分析</button>
                    </div>
                </div>

                <div class="quick-select">
                    <button class="btn btn-small btn-outline" onclick="setStock('malkiel', 'AAPL', '苹果')">苹果</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('malkiel', 'JNJ', '强生')">强生</button>
                    <button class="btn btn-small btn-outline" onclick="setStock('malkiel', 'PG', '宝洁')">宝洁</button>
                </div>
            </div>
            <div id="malkielResult"></div>

            <div class="card">
                <h3>马尔基尔核心理论（《漫步华尔街》第10版）</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div class="info-card">
                        <strong>坚实基础理论</strong>
                        <p>股票有内在价值，由增长率、股息、风险等基本面决定。价格终将回归价值。</p>
                    </div>
                    <div class="info-card">
                        <strong>4条估值法则</strong>
                        <p>①增长率越高PE越高 ②增长越持久越值钱 ③股息越高越有价值 ④风险越低PE越合理</p>
                    </div>
                    <div class="info-card">
                        <strong>生命周期投资</strong>
                        <p>20多岁:股票70%+债券30% → 50多岁:50/50 → 退休:30/70。随年龄调整风险。</p>
                    </div>
                    <div class="info-card">
                        <strong>随机漫步理论</strong>
                        <p>短期股价不可预测。大多数基金经理跑不赢指数。定投指数基金是最优策略。</p>
                    </div>
                    <div class="info-card">
                        <strong>平均成本法(定投)</strong>
                        <p>定期定额买入。低价多买、高价少买，自动降低平均成本。</p>
                    </div>
                    <div class="info-card">
                        <strong>分红再投资</strong>
                        <p>股息再投资是复利的关键来源。长期来看，分红贡献了股票总回报的40%以上。</p>
                    </div>
                </div>
            </div>
        </div>
        </main>
    </div>

    <script>
        let currentUser = 'root';

        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;

            if (username === 'root' && password === '1root2378') {
                document.getElementById('loginPage').classList.add('hidden');
                document.getElementById('mainPage').classList.remove('hidden');
                currentUser = username;
                document.getElementById('currentUser').textContent = username;
                loadUserProfile();
                getRecommendations();
            } else {
                alert('用户名或密码错误');
            }
        });

        function logout() {
            document.getElementById('loginPage').classList.remove('hidden');
            document.getElementById('mainPage').classList.add('hidden');
        }

        const TAB_TITLES = {
            recommend: '策略推荐', stock: '股票推荐', backtest: '策略回测',
            kline: 'K线分析', candle: '蜡烛图技术分析', zhenGuize: '真规则分析',
            linch: '彼得林奇', oneil: '欧奈尔 CAN SLIM', graham: '格雷厄姆',
            comprehensive: '综合策略', marks: '霍华德马克斯', malkiel: '漫步华尔街',
            settings: '用户设置'
        };
        const ALL_TABS = ['recommend','stock','backtest','settings','kline',
                          'zhenGuize','linch','oneil','graham','comprehensive',
                          'marks','candle','malkiel'];

        function showTab(tab) {
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            const activeBtn = document.querySelector('.nav-item[data-tab="' + tab + '"]');
            if (activeBtn) activeBtn.classList.add('active');

            const titleEl = document.getElementById('pageTitle');
            if (titleEl) titleEl.textContent = TAB_TITLES[tab] || tab;

            ALL_TABS.forEach(t => document.getElementById(t + 'Tab').classList.add('hidden'));
            document.getElementById(tab + 'Tab').classList.remove('hidden');

            if (window.innerWidth <= 768) toggleSidebar(false);
        }

        function toggleSidebar(forceState) {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            const isOpen = sidebar.classList.contains('open');
            const shouldOpen = forceState !== undefined ? forceState : !isOpen;
            if (shouldOpen) {
                sidebar.classList.add('open');
                overlay.classList.remove('hidden');
            } else {
                sidebar.classList.remove('open');
                overlay.classList.add('hidden');
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.nav-item[data-tab]').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    showTab(this.dataset.tab);
                });
            });
        });

        async function loadUserProfile() {
            try {
                const response = await fetch('/api/profile?user_id=' + currentUser);
                const result = await response.json();
                if (result.success) {
                    const p = result.profile;
                    document.getElementById('settingMarket').value = p.market_preference;
                    document.getElementById('settingRisk').value = p.risk_level;
                    document.getElementById('settingReturn').value = p.return_target;
                    document.getElementById('settingPeriod').value = p.holding_period;

                    document.getElementById('userProfileInfo').innerHTML = `
                        <p><strong>市场偏好:</strong> ${p.market_preference} |
                        <strong>风险等级:</strong> ${p.risk_level} |
                        <strong>收益目标:</strong> ${p.return_target*100}% |
                        <strong>持仓周期:</strong> ${p.holding_period}</p>
                    `;
                }
            } catch (e) { console.error(e); }
        }

        async function getRecommendations() {
            const container = document.getElementById('recommendResults');
            container.innerHTML = '<div class="loading">正在计算推荐...</div>';

            try {
                const response = await fetch('/api/recommend?user_id=' + currentUser);
                const result = await response.json();

                if (result.success) {
                    displayRecommendations(result.recommendations);
                } else {
                    container.innerHTML = '<div class="result-card">获取推荐失败</div>';
                }
            } catch (e) {
                container.innerHTML = '<div class="result-card">获取推荐失败: ' + e + '</div>';
            }
        }

        function displayRecommendations(recommendations) {
            const container = document.getElementById('recommendResults');
            if (!recommendations || recommendations.length === 0) {
                container.innerHTML = '<div class="result-card">暂无推荐</div>';
                return;
            }

            let html = '<div class="card"><h2>推荐结果 Top 3</h2>';
            recommendations.forEach((rec, i) => {
                const retClass = rec.annual_return >= 0.10 ? 'positive' : 'negative';
                const mddClass = rec.max_drawdown <= 0.15 ? 'positive' : 'negative';

                html += `
                    <div class="result-card">
                        <h3>${i+1}. ${rec.strategy_name}</h3>
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-label">年化收益</div>
                                <div class="metric-value ${retClass}">${(rec.annual_return*100).toFixed(1)}%</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">夏普比率</div>
                                <div class="metric-value">${rec.sharpe_ratio.toFixed(2)}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">最大回撤</div>
                                <div class="metric-value ${mddClass}">${(rec.max_drawdown*100).toFixed(1)}%</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">匹配度</div>
                                <div class="metric-value">${rec.matching_score.toFixed(0)}</div>
                            </div>
                        </div>
                        <p style="margin-top:10px;"><strong>推荐理由:</strong> ${rec.recommendation_reason}</p>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        }

        // 股票推荐
        async function getStockRecommendations() {
            // 获取选中的策略
            const selectedStrategies = [];
            ['stockStrat1', 'stockStrat2', 'stockStrat3', 'stockStrat4', 'stockStrat5'].forEach(id => {
                const el = document.getElementById(id);
                if (el && el.checked) selectedStrategies.push(el.value);
            });

            if (selectedStrategies.length === 0) {
                alert('请至少选择一个策略');
                return;
            }

            const market = document.getElementById('stockMarket').value;

            const container = document.getElementById('stockResults');
            container.innerHTML = '<div class="loading">正在分析股票...</div>';

            try {
                const strategy = selectedStrategies.join(',');
                const response = await fetch('/api/stock_recommend?strategy=' + strategy + '&market=' + market);
                const result = await response.json();

                if (result.success) {
                    displayStockRecommendations(result.stocks);
                } else {
                    container.innerHTML = '<div class="result-card">获取失败: ' + result.message + '</div>';
                }
            } catch (e) {
                container.innerHTML = '<div class="result-card">获取失败: ' + e + '</div>';
            }
        }

        function displayStockRecommendations(stocks) {
            const container = document.getElementById('stockResults');
            if (!stocks || stocks.length === 0) {
                container.innerHTML = '<div class="result-card">暂无推荐</div>';
                return;
            }

            let html = '<div class="card"><h2>具体股票买卖信号</h2>';
            html += '<table class="stock-table"><thead><tr><th>股票代码</th><th>股票名称</th><th>当前价格</th><th>买卖信号</th><th>详情</th></tr></thead><tbody>';

            stocks.forEach(stock => {
                const signalClass = stock.signal === '买入' ? 'signal-buy' : (stock.signal === '卖出' ? 'signal-sell' : 'signal-hold');
                let details = '';
                for (let key in stock.details) {
                    if (key !== 'signal') {
                        details += `${key}: ${typeof stock.details[key] === 'number' ? stock.details[key].toFixed(2) : stock.details[key]}<br>`;
                    }
                }

                html += `
                    <tr>
                        <td>${stock.ticker}</td>
                        <td>${stock.name}</td>
                        <td>${stock.price.toFixed(2)}</td>
                        <td class="${signalClass}">${stock.signal}</td>
                        <td>${details}</td>
                    </tr>
                `;
            });

            html += '</tbody></table></div>';
            container.innerHTML = html;
        }

        function selectBacktestStrategies(strats) {
            document.querySelectorAll('.backtest-strat').forEach(cb => {
                cb.checked = strats.includes(cb.value);
            });
        }

        async function runBacktest() {
            // 获取选中的策略（通过 class 统一收集所有勾选框）
            const selectedStrategies = [];
            document.querySelectorAll('.backtest-strat:checked').forEach(cb => {
                selectedStrategies.push(cb.value);
            });

            if (selectedStrategies.length === 0) {
                alert('请至少选择一个策略');
                return;
            }

            // 获取股票代码和市场
            const rawInput = document.getElementById('backtestTicker').value.trim();
            const market = document.getElementById('backtestMarket').value;
            const days = document.getElementById('backtestDays').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('backtestTicker').value = ticker;

            const strategy = selectedStrategies.join(',');
            const container = document.getElementById('backtestResults');
            container.innerHTML = '<div class="loading">正在回测 ' + ticker + ' ...</div>';

            try {
                const response = await fetch('/api/backtest?strategy=' + strategy + '&ticker=' + ticker + '&market=' + market + '&days=' + days);
                const result = await response.json();

                if (result.success) {
                    displayBacktest(result.result, ticker, strategy);
                } else {
                    container.innerHTML = '<div class="card" style="color:red;">回测失败: ' + result.message + '</div>';
                }
            } catch (e) {
                container.innerHTML = '<div class="card" style="color:red;">回测失败: ' + e + '</div>';
            }
        }

        function displayBacktest(result, ticker, strategy) {
            const container = document.getElementById('backtestResults');
            if (!result || Object.keys(result).length === 0) {
                container.innerHTML = '<div class="card">暂无回测数据</div>';
                return;
            }

            const retClass = result.annual_return >= 0 ? 'positive' : 'negative';
            const mddClass = Math.abs(result.max_drawdown) < 0.15 ? 'positive' : 'negative';
            const sharpeClass = result.sharpe_ratio > 1 ? 'positive' : result.sharpe_ratio < 0 ? 'negative' : '';
            const stratNames = (result.strategy_name || strategy).replace(/,/g, ' + ');

            container.innerHTML = `
                <div class="card">
                    <h2>${ticker} 回测结果 <span style="font-size:0.7em;color:#888;">${stratNames}</span></h2>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">总收益</div>
                            <div class="metric-value ${retClass}">${(result.total_return*100).toFixed(1)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">年化收益</div>
                            <div class="metric-value ${retClass}">${(result.annual_return*100).toFixed(1)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">夏普比率</div>
                            <div class="metric-value ${sharpeClass}">${result.sharpe_ratio.toFixed(2)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">最大回撤</div>
                            <div class="metric-value ${mddClass}">${(result.max_drawdown*100).toFixed(1)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">胜率</div>
                            <div class="metric-value">${(result.win_rate*100).toFixed(1)}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">盈亏比</div>
                            <div class="metric-value">${result.profit_loss_ratio.toFixed(2)}</div>
                        </div>
                    </div>
                    ${result.trade_count !== undefined ? '<p style="color:#888;margin-top:10px;">共 ' + result.trade_count + ' 笔交易，持仓天数占比 ' + ((result.holding_pct||0)*100).toFixed(1) + '%</p>' : ''}
                </div>
            `;
        }

        document.getElementById('profileForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const data = {
                user_id: currentUser,
                market_preference: document.getElementById('settingMarket').value,
                risk_level: document.getElementById('settingRisk').value,
                return_target: parseFloat(document.getElementById('settingReturn').value),
                holding_period: document.getElementById('settingPeriod').value
            };

            try {
                const response = await fetch('/api/update_profile', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();

                if (result.success) {
                    alert('设置已保存');
                    loadUserProfile();
                    getRecommendations();
                }
            } catch (e) {
                alert('保存失败');
            }
        });

        async function generateReport() {
            try {
                const response = await fetch('/api/report?user_id=' + currentUser);
                const result = await response.json();

                if (result.success) {
                    alert('报告已生成');
                }
            } catch (e) {
                alert('生成报告失败');
            }
        }

        function updateKlineStockList() {
            const market = document.getElementById('klineMarket').value;
            const input = document.getElementById('klineTicker');
            const nameSpan = document.getElementById('klineStockName');
            if (market === 'A') {
                input.value = '600519.SH';
                nameSpan.textContent = '贵州茅台';
            } else {
                input.value = 'AAPL';
                nameSpan.textContent = '苹果';
            }
        }

        // 股票名称映射 - 完整版
        const STOCK_NAMES = {
            // A股 - 重要蓝筹股
            '600519.SH': '贵州茅台', '000858.SZ': '五粮液', '601318.SH': '中国平安',
            '600036.SH': '招商银行', '000333.SZ': '美的集团', '600900.SH': '长江电力',
            '601888.SH': '中国中免', '600276.SH': '恒瑞医药', '601166.SH': '兴业银行',
            '600030.SH': '中信证券', '000001.SZ': '平安银行', '600016.SH': '民生银行',
            '600000.SH': '浦发银行', '601328.SH': '交通银行', '601398.SH': '工商银行',
            '601939.SH': '建设银行', '601288.SH': '农业银行', '601988.SH': '中国银行',
            '601857.SH': '中国石油', '601857.SH': '中国石化', '600028.SH': '中国石化',
            '600050.SH': '中国联通', '600030.SH': '中信证券', '600519.SH': '贵州茅台',
            '000002.SZ': '万科A', '000001.SZ': '平安银行', '000002.SZ': '万科',
            '000333.SZ': '美的集团', '000651.SZ': '格力电器', '000725.SZ': '京东方A',
            '000768.SZ': '中航飞机', '000858.SZ': '五粮液', '000876.SZ': '新希望',
            '000895.SZ': '系数未', '000938.SZ': '紫金矿业',
            // 美股 - 完整列表
            'AAPL': '苹果', 'MSFT': '微软', 'GOOGL': '谷歌', 'GOOG': '谷歌A',
            'AMZN': '亚马逊', 'NVDA': '英伟达', 'META': 'Meta', 'TSLA': '特斯拉',
            'BRK.B': '伯克希尔哈撒韦', 'JPM': '摩根大通', 'V': 'Visa', 'JNJ': '强生',
            'WMT': '沃尔玛', 'PG': '宝洁', 'HD': '家得宝', 'MA': '万事达',
            'DIS': '迪士尼', 'NFLX': 'Netflix', 'ADBE': 'Adobe', 'CRM': 'Salesforce',
            'PYPL': 'PayPal', 'INTC': '英特尔', 'AMD': 'AMD', 'CSCO': '思科',
            'PEP': '百事可乐', 'KO': '可口可乐', 'TMO': 'Thermo Fisher',
            'COST': 'Costco', 'AVGO': '博通', 'MRK': '默克', 'LLY': '礼来',
            'UNH': '联合健康', 'JNJ': '强生', 'PFE': '辉瑞', 'ABBV': '艾伯维',
            'CVX': '雪佛龙', 'XOM': '埃克森美孚', 'BAC': '美国银行', 'WFC': '富国银行',
            'GS': '高盛', 'MS': '摩根士丹利', 'AXP': '美国运通', 'BLK': '贝莱德',
            'SCHW': '嘉信理财', 'C': '花旗', 'USB': '美国合众银行', 'PNC': 'PNC金融',
            'COF': 'Capital One', 'SPGI': '标普全球', 'AXA': '安盛', 'MET': '大都会人寿',
            'PRU': '保德信金融', 'AFL': '美国家庭人寿', 'TMUS': 'T-Mobile',
            'CMCSA': '康卡斯特', 'T': 'AT&T', 'VZ': '威瑞森', 'TMUS': 'T-Mobile US',
            'ORCL': '甲骨文', 'IBM': 'IBM', 'QCOM': '高通', 'TXN': '德州仪器',
            'NOW': 'ServiceNow', 'INTU': 'Intuit', 'AMAT': '应用材料', 'MU': '美光科技',
            'LRCX': '泛林集团', 'KLAC': '科天半导体', 'SNPS': '新思科技', 'CDNS': 'Cadence',
            'PANW': 'Palo Alto', 'FTNT': 'Fortinet', 'CRWD': 'CrowdStrike', 'ZS': 'Zscaler',
            'NET': 'Cloudflare', 'DDOG': 'Datadog', 'SNOW': 'Snowflake', 'OKTA': 'Okta',
            'TEAM': 'Atlassian', 'SQ': 'Block', 'SHOP': 'Shopify', 'UBER': 'Uber',
            'LYFT': 'Lyft', 'ABNB': 'Airbnb', 'DASH': 'DoorDash', 'COIN': 'Coinbase',
            'RBLX': 'Roblox', 'SNAP': 'Snap', 'PINS': 'Pinterest', 'TWTR': 'Twitter',
            'ZM': 'Zoom', 'DOCU': 'DocuSign', 'ROKU': 'Roku', 'ETSY': 'Etsy',
            'W': 'Wayfair', 'CHWY': 'Chewy', 'BABA': '阿里巴巴', 'BIDU': '百度',
            'NIO': '蔚来', 'XPEV': '小鹏汽车', 'LI': '理想汽车', 'BILI': '哔哩哔哩',
            'JD': '京东', 'PDD': '拼多多', 'NTES': '网易', 'TAL': '好未来',
            'EDU': '新东方', 'VIPS': '唯品会', 'MOMO': '陌陌', 'YY': 'YY',
            'HUYA': '虎牙', 'DOYU': '斗鱼', 'BEKE': '贝壳', 'TME': '腾讯音乐'
        };

        function updateStockName(ticker) {
            const nameSpan = document.getElementById('klineStockName');
            nameSpan.textContent = STOCK_NAMES[ticker] || '未知';
        }

        // 初始化股票下拉列表 - 从API获取
        async function initStockList() {
            const stockListDatalist = document.getElementById('stockList');
            const zgStockListDatalist = document.getElementById('zgStockList');

            if (stockListDatalist) stockListDatalist.innerHTML = '';
            if (zgStockListDatalist) zgStockListDatalist.innerHTML = '';

            try {
                // 调用API获取股票列表
                const response = await fetch('/api/zhen_guize_search?q=');
                const stocks = await response.json();

                // 添加到所有datalist
                stocks.forEach(stock => {
                    const optionText = stock.code + ' - ' + stock.name;

                    if (stockListDatalist) {
                        const option1 = document.createElement('option');
                        option1.value = optionText;
                        option1.dataset.code = stock.code;
                        option1.dataset.name = stock.name;
                        stockListDatalist.appendChild(option1);
                    }

                    if (zgStockListDatalist) {
                        const option2 = document.createElement('option');
                        option2.value = optionText;
                        option2.dataset.code = stock.code;
                        option2.dataset.name = stock.name;
                        zgStockListDatalist.appendChild(option2);
                    }
                });
            } catch (e) {
                console.error('获取股票列表失败，使用本地数据', e);
                // 失败时使用本地数据
                const allStocks = Object.keys(STOCK_NAMES).map(code => {
                    return code + ' - ' + STOCK_NAMES[code];
                }).sort();

                allStocks.forEach(stock => {
                    if (stockListDatalist) {
                        const option1 = document.createElement('option');
                        option1.value = stock.split(' - ')[0];
                        stockListDatalist.appendChild(option1);
                    }
                    if (zgStockListDatalist) {
                        const option2 = document.createElement('option');
                        option2.value = stock.split(' - ')[0];
                        zgStockListDatalist.appendChild(option2);
                    }
                });
            }
        }

        // 实时搜索股票
        async function searchStocks(keyword) {
            try {
                const response = await fetch('/api/zhen_guize_search?q=' + encodeURIComponent(keyword));
                return await response.json();
            } catch (e) {
                console.error('搜索失败', e);
                return [];
            }
        }

        // 实时搜索：输入时动态更新 datalist
        let _searchTimer = null;
        function bindLiveSearch() {
            const inputIds = ['klineTicker', 'zhenGuizeTicker', 'linchTicker', 'oneilTicker',
                              'grahamTicker', 'compTicker', 'marksTicker', 'candleTicker', 'malkielTicker'];
            inputIds.forEach(function(id) {
                const input = document.getElementById(id);
                if (!input) return;
                input.addEventListener('input', function() {
                    const keyword = this.value.trim();
                    if (keyword.length < 1) return;
                    if (_searchTimer) clearTimeout(_searchTimer);
                    _searchTimer = setTimeout(async function() {
                        const results = await searchStocks(keyword);
                        if (!results || results.length === 0) return;
                        // 更新所有 datalist
                        ['stockList', 'zgStockList'].forEach(function(dlId) {
                            const dl = document.getElementById(dlId);
                            if (!dl) return;
                            dl.innerHTML = '';
                            results.forEach(function(stock) {
                                const opt = document.createElement('option');
                                opt.value = stock.code + ' - ' + stock.name;
                                opt.dataset.code = stock.code;
                                opt.dataset.name = stock.name;
                                dl.appendChild(opt);
                            });
                        });
                    }, 300);
                });
            });
        }

        // 通用：将用户输入的股票名称/代码解析为标准代码
        async function resolveTickerCode(inputValue, market) {
            if (!inputValue) return null;
            let ticker = inputValue.trim();
            // 如果是 datalist 选择格式 "600519.SH - 贵州茅台"，提取代码
            if (ticker.includes(' - ')) {
                ticker = ticker.split(' - ')[0].trim();
            }
            // 如果不含数字（纯中文名称或拼音），先搜索获取代码
            if (!/\\d/.test(ticker)) {
                try {
                    const searchResp = await fetch('/api/zhen_guize_search?q=' + encodeURIComponent(ticker));
                    const searchResults = await searchResp.json();
                    if (searchResults && searchResults.length > 0) {
                        // 优先匹配对应市场
                        const marketMatch = searchResults.find(s => {
                            if (market === 'A') return s.market === 'A';
                            if (market === 'US') return s.market === 'US';
                            return true;
                        });
                        ticker = (marketMatch || searchResults[0]).code;
                    } else {
                        return null;
                    }
                } catch (e) {
                    return null;
                }
            }
            return ticker;
        }

        // 页面加载时初始化
        window.addEventListener('DOMContentLoaded', function() {
            initStockList();
            bindLiveSearch();
        });

        function selectStrategies(strategies) {
            // 清除所有选择
            document.querySelectorAll('#klineStrategy input[type="checkbox"]').forEach(cb => cb.checked = false);
            // 选择指定策略
            strategies.forEach(s => {
                document.querySelectorAll('#klineStrategy input[type="checkbox"]').forEach(cb => {
                    if (cb.value === s) cb.checked = true;
                });
            });
            loadKline();
        }

        async function loadKline() {
            const rawInput = document.getElementById('klineTicker').value.trim();
            const market = document.getElementById('klineMarket').value;

            // 获取选中的策略
            const selectedStrategies = [];
            document.querySelectorAll('#klineStrategy input[type="checkbox"]:checked').forEach(cb => {
                selectedStrategies.push(cb.value);
            });

            if (selectedStrategies.length === 0) {
                alert('请至少选择一个策略');
                return;
            }

            if (!rawInput) { alert('请输入股票代码'); return; }

            // 名称转代码
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('klineTicker').value = ticker;

            // 更新股票名称
            updateStockName(ticker);

            const container = document.getElementById('klineChart');
            container.innerHTML = '<div class="loading">正在加载K线数据...</div>';

            try {
                const strategy = selectedStrategies.join(',');
                const response = await fetch('/api/kline?ticker=' + ticker + '&market=' + market + '&strategy=' + strategy);
                const result = await response.json();

                if (result.success) {
                    renderKline(result.data, result.signals);
                } else {
                    container.innerHTML = '<div class="result-card">加载失败: ' + result.message + '</div>';
                }
            } catch (e) {
                container.innerHTML = '<div class="result-card">加载失败: ' + e + '</div>';
            }
        }

        function renderKline(data, signals) {
            const container = document.getElementById('klineChart');
            container.innerHTML = '';

            // 使用Plotly绘制K线图
            const trace1 = {
                x: data.dates,
                open: data.opens,
                high: data.highs,
                low: data.lows,
                close: data.closes,
                type: 'candlestick',
                name: 'K线',
                increasing: {line: {color: '#26a69a'}},
                decreasing: {line: {color: '#ef5350'}}
            };

            // 处理MA数据，将空字符串转为null
            const ma5Data = data.ma5.map(v => v === '' ? null : v);
            const ma20Data = data.ma20.map(v => v === '' ? null : v);

            // 添加MA线
            const trace2 = {
                x: data.dates,
                y: ma5Data,
                type: 'scatter',
                mode: 'lines',
                name: 'MA5',
                line: {color: '#2196F3', width: 1}
            };

            const trace3 = {
                x: data.dates,
                y: ma20Data,
                type: 'scatter',
                mode: 'lines',
                name: 'MA20',
                line: {color: '#FF9800', width: 1}
            };

            // 买入信号
            const buySignals = signals.filter(s => s.signal === '买入');
            const buyTrace = {
                x: buySignals.map(s => s.date),
                y: buySignals.map(s => s.price),
                type: 'scatter',
                mode: 'markers',
                name: '买入信号',
                marker: {symbol: 'triangle-up', size: 15, color: '#26a69a'}
            };

            // 卖出信号
            const sellSignals = signals.filter(s => s.signal === '卖出');
            const sellTrace = {
                x: sellSignals.map(s => s.date),
                y: sellSignals.map(s => s.price),
                type: 'scatter',
                mode: 'markers',
                name: '卖出信号',
                marker: {symbol: 'triangle-down', size: 15, color: '#ef5350'}
            };

            const layout = {
                title: 'K线走势及买卖信号',
                xaxis: {rangeslider: {visible: false}},
                yaxis: {title: '价格'},
                height: 500,
                showlegend: true
            };

            const Plotly = window.Plotly || Plotly;
            if (typeof Plotly !== 'undefined') {
                Plotly.newPlot(container, [trace1, trace2, trace3, buyTrace, sellTrace], layout);
            } else {
                container.innerHTML = '<div class="result-card">请等待Plotly库加载...</div>';
                // 动态加载Plotly
                const script = document.createElement('script');
                script.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
                script.onload = () => {
                    Plotly.newPlot(container, [trace1, trace2, trace3, buyTrace, sellTrace], layout);
                };
                document.head.appendChild(script);
            }

            // 显示信号列表
            displaySignals(signals);
        }

        function displaySignals(signals) {
            const container = document.getElementById('klineSignals');
            if (!signals || signals.length === 0) {
                container.innerHTML = '';
                return;
            }

            let html = '<div class="card"><h2>买卖信号记录</h2>';
            html += '<table class="stock-table"><thead><tr><th>日期</th><th>价格</th><th>信号</th><th>原因</th></tr></thead><tbody>';

            // 显示最近20个信号
            const recentSignals = signals.slice(-20).reverse();
            recentSignals.forEach(s => {
                const signalClass = s.signal === '买入' ? 'signal-buy' : 'signal-sell';
                html += `<tr><td>${s.date}</td><td>${s.price.toFixed(2)}</td><td class="${signalClass}">${s.signal}</td><td>${s.reason}</td></tr>`;
            });

            html += '</tbody></table></div>';
            container.innerHTML = html;
        }

        // 真规则推荐功能
        function setZhenGuizeStock(code, name) {
            document.getElementById('zhenGuizeTicker').value = code;
            analyzeZhenGuize();
        }

        async function analyzeZhenGuize() {
            const rawInput = document.getElementById('zhenGuizeTicker').value.trim();
            const market = document.getElementById('zhenGuizeMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }

            const resultDiv = document.getElementById('zhenGuizeResult');
            resultDiv.innerHTML = '<div class="loading">正在获取数据并进行全面分析...</div>';

            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { resultDiv.innerHTML = '<div class="card" style="color:red;">未找到该股票</div>'; return; }
            document.getElementById('zhenGuizeTicker').value = ticker;

            try {
                const response = await fetch('/api/zhen_guize?ticker=' + ticker + '&market=' + market);
                const data = await response.json();
                if (data.error) { resultDiv.innerHTML = '<div class="card" style="color:red;">' + data.error + '</div>'; return; }
                renderZhenGuize(data);
            } catch (error) {
                resultDiv.innerHTML = '<div class="card" style="color:red;">分析失败: ' + error.message + '</div>';
            }
        }

        function renderZhenGuize(data) {
            const resultDiv = document.getElementById('zhenGuizeResult');
            const s = data.stock;
            const v = data.valuation;
            const ic = data.industry_comparison;
            const moat = data.moat;
            const fr = data.five_rules;
            const sc = getScoreColor(data.total_score);
            const ovLabel = ic.overall_valuation || '待评估';
            const ovColor = ovLabel.indexOf('低') >= 0 ? '#26a69a' : ovLabel.indexOf('高') >= 0 ? '#ef5350' : '#ff9800';

            let html = '';

            // === K线图 ===
            if (data.ohlcv) {
                html += '<div class="card"><h2>' + (s.name || data.code) + ' (' + data.code + ') K线走势</h2>';
                html += '<div id="zgKlineChart" style="width:100%;height:400px;"></div></div>';
            }

            // === 综合评级 + 买卖建议 ===
            html += '<div class="card">';
            html += '<h2>' + (s.name || data.code) + ' - 真规则综合分析</h2>';
            html += '<div style="display:flex;flex-wrap:wrap;gap:20px;margin:20px 0;align-items:center;">';
            // 总分
            html += '<div style="text-align:center;padding:20px 30px;background:' + sc + '15;border:2px solid ' + sc + ';border-radius:12px;">';
            html += '<div style="font-size:2.8em;font-weight:bold;color:' + sc + ';">' + data.total_score.toFixed(0) + '</div>';
            html += '<div style="color:' + sc + ';font-weight:600;">' + data.rating + '</div></div>';
            // 估值状态
            html += '<div style="text-align:center;padding:20px 25px;background:' + ovColor + '15;border:2px solid ' + ovColor + ';border-radius:12px;">';
            html += '<div style="font-size:2em;font-weight:bold;color:' + ovColor + ';">' + ovLabel + '</div>';
            html += '<div style="font-size:0.9em;color:#666;">估值状态</div></div>';
            // 买卖点位
            if (v.buy_price) {
                html += '<div style="flex:1;min-width:250px;">';
                html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center;">';
                html += '<div style="background:#e8f5e9;padding:12px;border-radius:8px;"><div style="font-size:1.4em;font-weight:bold;color:#2e7d32;">' + v.buy_price + '</div><div style="font-size:0.8em;color:#666;">买入目标价</div></div>';
                html += '<div style="background:#fff3e0;padding:12px;border-radius:8px;"><div style="font-size:1.4em;font-weight:bold;color:#e65100;">' + v.fair_value + '</div><div style="font-size:0.8em;color:#666;">合理估值</div></div>';
                html += '<div style="background:#ffebee;padding:12px;border-radius:8px;"><div style="font-size:1.4em;font-weight:bold;color:#c62828;">' + v.sell_price + '</div><div style="font-size:0.8em;color:#666;">卖出目标价</div></div>';
                html += '</div>';
                if (v.current_vs_fair) html += '<p style="margin-top:8px;color:#555;font-size:0.9em;">' + v.current_vs_fair + '</p>';
                html += '</div>';
            }
            html += '</div>';

            // 买卖建议
            if (data.advice && data.advice.length > 0) {
                html += '<div style="margin-top:15px;">';
                data.advice.forEach(function(a) {
                    var c = a.action.indexOf('买') >= 0 ? '#2e7d32' : a.action.indexOf('卖') >= 0 ? '#c62828' : '#e65100';
                    html += '<div style="padding:12px 15px;margin-bottom:8px;background:' + c + '10;border-left:4px solid ' + c + ';border-radius:4px;">';
                    html += '<strong style="color:' + c + ';">' + a.action + '</strong> <span style="color:#555;">' + a.reason + '</span></div>';
                });
                html += '</div>';
            }
            html += '</div>';

            // === 五大原则评分 ===
            html += '<div class="card"><h2>五大原则评分</h2>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:15px;">';
            ['rule1','rule2','rule3','rule4','rule5'].forEach(function(key) {
                var r = fr[key];
                var c = getScoreColor(r.score);
                html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;border-top:3px solid ' + c + ';">';
                html += '<div style="font-size:1.8em;font-weight:bold;color:' + c + ';">' + r.score.toFixed(0) + '</div>';
                html += '<div style="font-weight:600;">' + r.name + '</div>';
                html += '<div style="font-size:0.85em;color:#666;margin-top:4px;">' + r.detail + '</div></div>';
            });
            html += '</div></div>';

            // === 经济护城河 ===
            html += '<div class="card"><h2>经济护城河分析（第3章）</h2>';
            var moatColor = moat.level.indexOf('宽') >= 0 ? '#2e7d32' : moat.level.indexOf('窄') >= 0 ? '#e65100' : moat.level.indexOf('一定') >= 0 ? '#ff9800' : '#999';
            html += '<div style="display:flex;align-items:center;gap:15px;margin:15px 0;">';
            html += '<div style="padding:12px 20px;background:' + moatColor + '15;border:2px solid ' + moatColor + ';border-radius:10px;font-size:1.3em;font-weight:bold;color:' + moatColor + ';">' + moat.level + '</div>';
            if (moat.sources.length > 0) {
                html += '<div>' + moat.sources.map(function(s) { return '<span style="display:inline-block;background:#e3f2fd;color:#1565c0;padding:4px 10px;border-radius:20px;margin:2px;font-size:0.9em;">' + s + '</span>'; }).join('') + '</div>';
            }
            html += '</div>';
            if (moat.details.length > 0) {
                html += '<ul style="margin-top:10px;">';
                moat.details.forEach(function(d) { html += '<li style="padding:5px 0;color:#555;">' + d + '</li>'; });
                html += '</ul>';
            }
            html += '</div>';

            // === 财务指标 ===
            html += '<div class="card"><h2>关键财务指标</h2>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-top:15px;">';
            var metrics = [
                {l:'市盈率(PE)', v: s.pe ? s.pe.toFixed(1) + 'x' : '-', good: s.pe > 0 && s.pe < 25},
                {l:'市净率(PB)', v: s.pb ? s.pb.toFixed(1) + 'x' : '-', good: s.pb > 0 && s.pb < 3},
                {l:'ROE', v: s.roe ? s.roe.toFixed(1) + '%' : '-', good: s.roe > 15},
                {l:'毛利率', v: s.gross_margin ? s.gross_margin.toFixed(1) + '%' : '-', good: s.gross_margin > 30},
                {l:'营收增长', v: s.revenue_growth ? s.revenue_growth.toFixed(1) + '%' : '-', good: s.revenue_growth > 5},
                {l:'股息率', v: s.dividend_yield ? s.dividend_yield.toFixed(2) + '%' : '-', good: s.dividend_yield > 2},
            ];
            metrics.forEach(function(m) {
                var c = m.good ? '#2e7d32' : '#666';
                html += '<div style="text-align:center;background:#f8f9fa;padding:12px;border-radius:8px;">';
                html += '<div style="font-size:1.4em;font-weight:bold;color:' + c + ';">' + m.v + '</div>';
                html += '<div style="font-size:0.85em;color:#888;">' + m.l + '</div></div>';
            });
            html += '</div></div>';

            // === 财务报表（近一年季报）===
            if (data.financial_statements && data.financial_statements.length > 0) {
                html += '<div class="card"><h2>财务报表（近一年季度数据）</h2>';
                var fs = data.financial_statements;
                // 最新报告披露信息
                if (fs[0].notice_date) {
                    html += '<p style="color:var(--text-secondary);margin-bottom:12px;font-size:0.85rem;">最新报告期: <strong>' + fs[0].report_date + '</strong> | 披露日期: <strong>' + fs[0].notice_date + '</strong></p>';
                } else {
                    html += '<p style="color:var(--text-secondary);margin-bottom:12px;font-size:0.85rem;">最新报告期: <strong>' + fs[0].report_date + '</strong></p>';
                }
                html += '<div style="overflow-x:auto;">';
                html += '<table class="stock-table">';
                // 判断是A股还是美股格式
                var isAShare = fs[0].eps !== undefined && fs[0].eps !== null;
                if (isAShare) {
                    html += '<thead><tr><th>报告期</th><th>营业收入</th><th>营收同比</th><th>净利润</th><th>净利润同比</th><th>EPS</th><th>ROE</th><th>毛利率</th></tr></thead>';
                    html += '<tbody>';
                    fs.forEach(function(row) {
                        var revStr = row.revenue ? (row.revenue >= 1e8 ? (row.revenue / 1e8).toFixed(2) + '亿' : (row.revenue / 1e4).toFixed(0) + '万') : '-';
                        var npStr = row.net_profit ? (row.net_profit >= 1e8 ? (row.net_profit / 1e8).toFixed(2) + '亿' : (row.net_profit / 1e4).toFixed(0) + '万') : '-';
                        var revYoy = row.revenue_yoy !== null && row.revenue_yoy !== undefined ? row.revenue_yoy.toFixed(2) + '%' : '-';
                        var npYoy = row.profit_yoy !== null && row.profit_yoy !== undefined ? row.profit_yoy.toFixed(2) + '%' : '-';
                        var revYoyColor = row.revenue_yoy > 0 ? 'var(--success)' : row.revenue_yoy < 0 ? 'var(--danger)' : 'inherit';
                        var npYoyColor = row.profit_yoy > 0 ? 'var(--success)' : row.profit_yoy < 0 ? 'var(--danger)' : 'inherit';
                        var epsStr = row.eps !== null && row.eps !== undefined ? row.eps.toFixed(2) : '-';
                        var roeStr = row.roe !== null && row.roe !== undefined ? row.roe.toFixed(2) + '%' : '-';
                        var gmStr = row.gross_margin !== null && row.gross_margin !== undefined ? row.gross_margin.toFixed(2) + '%' : '-';
                        html += '<tr>';
                        html += '<td><strong>' + row.report_date + '</strong></td>';
                        html += '<td>' + revStr + '</td>';
                        html += '<td style="color:' + revYoyColor + ';">' + revYoy + '</td>';
                        html += '<td>' + npStr + '</td>';
                        html += '<td style="color:' + npYoyColor + ';">' + npYoy + '</td>';
                        html += '<td>' + epsStr + '</td>';
                        html += '<td>' + roeStr + '</td>';
                        html += '<td>' + gmStr + '</td>';
                        html += '</tr>';
                    });
                } else {
                    // 美股格式
                    html += '<thead><tr><th>报告期</th><th>营业收入</th><th>毛利润</th><th>营业利润</th><th>净利润</th><th>毛利率</th></tr></thead>';
                    html += '<tbody>';
                    fs.forEach(function(row) {
                        function fmtUSD(v) { if (!v) return '-'; var abs = Math.abs(v); if (abs >= 1e9) return (v/1e9).toFixed(2)+'B'; if (abs >= 1e6) return (v/1e6).toFixed(0)+'M'; return v.toFixed(0); }
                        html += '<tr>';
                        html += '<td><strong>' + row.report_date + '</strong></td>';
                        html += '<td>$' + fmtUSD(row.revenue) + '</td>';
                        html += '<td>$' + fmtUSD(row.gross_profit) + '</td>';
                        html += '<td>$' + fmtUSD(row.operating_income) + '</td>';
                        html += '<td style="color:' + (row.net_profit > 0 ? 'var(--success)' : 'var(--danger)') + ';">$' + fmtUSD(row.net_profit) + '</td>';
                        html += '<td>' + (row.gross_margin ? row.gross_margin.toFixed(1) + '%' : '-') + '</td>';
                        html += '</tr>';
                    });
                }
                html += '</tbody></table></div></div>';
            }

            // === 行业对比 ===
            html += '<div class="card"><h2>行业估值对比</h2>';
            html += '<p style="color:#888;margin-bottom:12px;">对标行业: <strong>' + ic.industry_name + '</strong></p>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;">';
            if (ic.pe_vs_industry) html += '<div style="background:#f8f9fa;padding:12px;border-radius:8px;"><strong>PE对比</strong><p style="color:#555;margin:5px 0;">' + ic.pe_vs_industry + '</p></div>';
            if (ic.pb_vs_industry) html += '<div style="background:#f8f9fa;padding:12px;border-radius:8px;"><strong>PB对比</strong><p style="color:#555;margin:5px 0;">' + ic.pb_vs_industry + '</p></div>';
            html += '<div style="background:#f8f9fa;padding:12px;border-radius:8px;"><strong>行业均值参考</strong>';
            html += '<p style="color:#555;margin:5px 0;">PE=' + ic.industry_pe + 'x PB=' + ic.industry_pb + 'x ROE=' + ic.industry_roe + '% 毛利率=' + ic.industry_margin + '%</p></div>';
            html += '</div></div>';

            // === 估值方法明细 ===
            if (v.methods && v.methods.length > 0) {
                html += '<div class="card"><h2>估值分析（第9-10章）</h2>';
                html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;">';
                v.methods.forEach(function(m) {
                    html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;border-left:4px solid #3b82f6;">';
                    html += '<strong>' + m.name + '</strong>';
                    html += '<div style="font-size:1.5em;font-weight:bold;color:#3b82f6;margin:5px 0;">' + m.fair_value + '</div>';
                    html += '<div style="font-size:0.85em;color:#666;">' + m.detail + '</div></div>';
                });
                html += '</div>';
                if (v.safety_margin) {
                    var smColor = v.safety_margin > 0 ? '#2e7d32' : '#c62828';
                    html += '<p style="margin-top:12px;font-size:1.1em;">安全边际: <strong style="color:' + smColor + ';">' + v.safety_margin + '%</strong></p>';
                }
                html += '</div>';
            }

            // === 10分钟测试 ===
            html += '<div class="card"><h2>10分钟快速筛选测试（第12章）</h2>';
            html += '<p style="color:#888;">通过 ' + data.test_summary.pass + '/' + data.test_summary.total + ' 项</p>';
            html += '<div style="margin-top:12px;">';
            data.ten_min_test.forEach(function(t) {
                var icon = t.pass ? '✅' : '❌';
                var bg = t.pass ? '#e8f5e9' : '#ffebee';
                html += '<div style="display:flex;align-items:center;gap:10px;padding:10px;margin-bottom:6px;background:' + bg + ';border-radius:6px;">';
                html += '<span style="font-size:1.2em;">' + icon + '</span>';
                html += '<div style="flex:1;"><strong>' + t.item + '</strong> <span style="color:#888;">(' + t.value + ')</span></div>';
                html += '<div style="font-size:0.85em;color:#666;">' + t.note + '</div></div>';
            });
            html += '</div></div>';

            resultDiv.innerHTML = html;

            // 渲染K线图
            if (data.ohlcv && typeof Plotly !== 'undefined') {
                var o = data.ohlcv;
                var traces = [{
                    x: o.dates, open: o.opens, high: o.highs, low: o.lows, close: o.closes,
                    type: 'candlestick', name: 'K线',
                    increasing: {line: {color: '#26a69a'}}, decreasing: {line: {color: '#ef5350'}}
                }];
                // 标注买卖目标价
                if (v.buy_price) {
                    traces.push({x: [o.dates[0], o.dates[o.dates.length-1]], y: [v.buy_price, v.buy_price], type: 'scatter', mode: 'lines', name: '买入目标价 ' + v.buy_price, line: {color: '#2e7d32', dash: 'dash', width: 2}});
                    traces.push({x: [o.dates[0], o.dates[o.dates.length-1]], y: [v.fair_value, v.fair_value], type: 'scatter', mode: 'lines', name: '合理估值 ' + v.fair_value, line: {color: '#ff9800', dash: 'dot', width: 2}});
                    traces.push({x: [o.dates[0], o.dates[o.dates.length-1]], y: [v.sell_price, v.sell_price], type: 'scatter', mode: 'lines', name: '卖出目标价 ' + v.sell_price, line: {color: '#c62828', dash: 'dash', width: 2}});
                }
                Plotly.newPlot('zgKlineChart', traces, {
                    title: {text: (s.name || data.code) + ' 走势与估值区间', font: {size: 14}},
                    xaxis: {rangeslider: {visible: false}, type: 'category', nticks: 15},
                    yaxis: {title: '价格', side: 'right'}, height: 400,
                    margin: {l: 50, r: 60, t: 35, b: 40}, showlegend: true,
                    legend: {orientation: 'h', y: -0.15}
                }, {responsive: true});
            }
        }

        function getScoreColor(score) {
            if (score >= 80) return '#10b981';
            if (score >= 65) return '#27ae60';
            if (score >= 50) return '#f59e0b';
            if (score >= 35) return '#e67e22';
            return '#ef4444';
        }

        // 格式化股票数据值：0或无效显示为"数据不可用"
        function fmtVal(val, suffix, decimals) {
            if (val === null || val === undefined || val === 0 || val === '0' || val === '-') return '<span style="color:#94a3b8;">数据不可用</span>';
            const num = typeof val === 'number' ? val : parseFloat(val);
            if (isNaN(num) || num === 0) return '<span style="color:#94a3b8;">数据不可用</span>';
            return num.toFixed(decimals !== undefined ? decimals : 2) + (suffix || '');
        }

        // 股票基础数据概览卡片
        function renderStockDataCard(stock) {
            const items = [
                {label: '价格', val: stock.price, suffix: '', dec: 2},
                {label: 'PE', val: stock.pe, suffix: '倍', dec: 1},
                {label: 'PB', val: stock.pb, suffix: '倍', dec: 2},
                {label: 'ROE', val: stock.roe, suffix: '%', dec: 1},
                {label: '毛利率', val: stock.gross_margin, suffix: '%', dec: 1},
                {label: '营收增长', val: stock.revenue_growth, suffix: '%', dec: 1},
                {label: '股息率', val: stock.dividend_yield, suffix: '%', dec: 2},
            ];
            if (stock.debt_ratio) items.push({label: '负债率', val: stock.debt_ratio, suffix: '%', dec: 1});
            if (stock.market_cap) items.push({label: '市值', val: stock.market_cap > 1e8 ? (stock.market_cap/1e8).toFixed(0) + '亿' : stock.market_cap, suffix: '', dec: 0, raw: true});
            const missing = items.filter(i => !i.val || i.val === 0).length;
            const warnHtml = missing > 3 ? '<div style="margin-top:8px;padding:8px 12px;background:#fff3e0;border-radius:6px;font-size:0.8em;color:#9a3412;">⚠️ 多项数据缺失，分析结果可能不够准确。建议检查股票代码或更换数据源。</div>' : '';
            return `<div class="card"><h3>📋 获取到的股票数据</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;margin:10px 0;">
                ${items.map(i => `<div style="background:#f8f9fa;padding:8px 10px;border-radius:6px;text-align:center;">
                    <div style="font-size:0.75em;color:#64748b;">${i.label}</div>
                    <div style="font-size:1.1em;font-weight:600;margin-top:2px;">${i.raw ? i.val : fmtVal(i.val, i.suffix, i.dec)}</div>
                </div>`).join('')}
                </div>${warnHtml}</div>`;
        }

        // 通用设置股票函数
        function setStock(type, code, name) {
            document.getElementById(type + 'Ticker').value = code;
            if (type === 'linch') analyzeLinch();
            else if (type === 'oneil') analyzeOneil();
            else if (type === 'graham') analyzeGraham();
            else if (type === 'comp') analyzeComprehensive();
            else if (type === 'marks') analyzeMarks();
            else if (type === 'candle') analyzeCandle();
            else if (type === 'malkiel') analyzeMalkiel();
        }

        // 彼得林奇分析
        async function analyzeLinch() {
            const rawInput = document.getElementById('linchTicker').value.trim();
            const market = document.getElementById('linchMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('linchTicker').value = ticker;

            const resultDiv = document.getElementById('linchResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><p>正在分析...</p></div>';

            try {
                const response = await fetch(`/api/invest_method?method=linch&ticker=${ticker}&market=${market}`);
                const data = await response.json();
                if (data.error) {
                    resultDiv.innerHTML = `<div style="color: red; padding: 20px;">${data.error}</div>`;
                    return;
                }
                renderLinchResult(data, resultDiv);
            } catch (error) {
                resultDiv.innerHTML = `<div style="color: red; padding: 20px;">分析失败: ${error.message}</div>`;
            }
        }

        function renderLinchResult(data, container) {
            const scores = data.scores;
            const cat = data.category;
            const peg = data.peg;
            const checklist = data.checklist || [];

            let html = renderStockDataCard(data.stock);
            html += `<div class="card">
                <h2>${data.stock.name} (${data.code}) - 彼得林奇式分析</h2>
                <div style="display:flex;align-items:center;gap:20px;margin:20px 0;flex-wrap:wrap;">
                    <div style="text-align:center;padding:20px 30px;background:${getScoreColor(scores.total)}15;border:2px solid ${getScoreColor(scores.total)};border-radius:12px;">
                        <div style="font-size:2.5em;font-weight:bold;color:${getScoreColor(scores.total)};">${scores.total}</div>
                        <div style="font-size:0.9em;color:#666;">综合评分</div>
                    </div>
                    <div style="flex:1;min-width:200px;">
                        <div style="color:${getScoreColor(scores.total)};font-size:1.2em;font-weight:600;">${data.rating}</div>
                        <div style="margin-top:8px;padding:8px 16px;background:#f0f4ff;border-radius:8px;display:inline-block;">
                            <strong>股票分类：</strong>${cat.name}
                        </div>
                        <p style="color:#666;font-size:0.85em;margin-top:6px;">${cat.description}</p>
                    </div>
                </div>
            </div>`;

            // PEG分析卡片
            html += `<div class="card">
                <h3>📊 PEG比率分析（林奇最重要指标）</h3>
                <div style="display:flex;align-items:center;gap:20px;margin:15px 0;">
                    <div style="text-align:center;padding:15px 25px;background:${peg.value > 0 && peg.value < 1 ? '#ecfdf5' : peg.value > 2 ? '#fef2f2' : '#f8f9fa'};border-radius:10px;min-width:100px;">
                        <div style="font-size:2em;font-weight:bold;color:${peg.value > 0 && peg.value < 1 ? '#10b981' : peg.value > 2 ? '#ef4444' : '#64748b'};">${peg.value > 0 ? peg.value.toFixed(2) : 'N/A'}</div>
                        <div style="font-size:0.8em;color:#666;">PEG值</div>
                    </div>
                    <div style="flex:1;">
                        <p style="color:#333;">${peg.assessment}</p>
                        <p style="color:#999;font-size:0.8em;margin-top:4px;">PEG = PE / 盈利增长率。林奇认为PEG<1代表被低估，PEG>2代表被高估</p>
                    </div>
                </div>
            </div>`;

            // 4维评分
            html += `<div class="card">
                <h3>📈 四维评分</h3>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:15px 0;">
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#3b82f6;">${scores.peg}</div>
                        <div style="font-size:0.8em;color:#666;">PEG估值</div>
                    </div>
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#10b981;">${scores.growth}</div>
                        <div style="font-size:0.8em;color:#666;">成长性</div>
                    </div>
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#8b5cf6;">${scores.financial}</div>
                        <div style="font-size:0.8em;color:#666;">财务健康</div>
                    </div>
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#f59e0b;">${scores.valuation}</div>
                        <div style="font-size:0.8em;color:#666;">估值水平</div>
                    </div>
                </div>
            </div>`;

            // 林奇选股清单
            html += `<div class="card">
                <h3>✅ 林奇选股清单 (通过 ${data.checklist_score}/7 项可量化指标)</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px;margin:12px 0;">`;
            checklist.forEach(item => {
                if (!item.auto) return;
                const icon = item.pass ? '✅' : '❌';
                const bg = item.pass ? '#f0fdf4' : '#fef2f2';
                html += `<div style="padding:10px 14px;background:${bg};border-radius:8px;font-size:0.9em;">
                    <span>${icon}</span> <strong>${item.name}</strong>
                    <div style="color:#666;font-size:0.8em;margin-top:2px;">${item.note}</div>
                </div>`;
            });
            html += `</div></div>`;

            // 建议与警告
            html += `<div class="card">
                <h3>💡 林奇投资建议</h3>
                <ul style="margin:8px 0;">${data.reasons.map(r => '<li style="padding:3px 0;">' + r + '</li>').join('')}</ul>`;
            if (data.warnings && data.warnings.length > 0) {
                html += `<div style="margin-top:12px;padding:12px;background:#fff3e0;border-left:4px solid #ff9800;border-radius:4px;">
                    <strong>⚠️ 风险提示</strong>
                    <ul style="margin:6px 0 0;">${data.warnings.map(w => '<li style="padding:2px 0;color:#9a3412;">' + w + '</li>').join('')}</ul>
                </div>`;
            }
            html += `</div>`;
            container.innerHTML = html;
        }

        // 欧奈尔CAN SLIM分析
        async function analyzeOneil() {
            const rawInput = document.getElementById('oneilTicker').value.trim();
            const market = document.getElementById('oneilMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('oneilTicker').value = ticker;

            const resultDiv = document.getElementById('oneilResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><p>正在分析...</p></div>';

            try {
                const response = await fetch(`/api/invest_method?method=oneil&ticker=${ticker}&market=${market}`);
                const data = await response.json();
                if (data.error) {
                    resultDiv.innerHTML = `<div style="color: red; padding: 20px;">${data.error}</div>`;
                    return;
                }
                renderOneilResult(data, resultDiv);
            } catch (error) {
                resultDiv.innerHTML = `<div style="color: red; padding: 20px;">分析失败: ${error.message}</div>`;
            }
        }

        function renderOneilResult(data, container) {
            const canslim = data.canslim;
            const labels = {C:'当季业绩',A:'年度增长',N:'创新/新高',S:'供需关系',L:'行业领导',I:'机构认同',M:'大盘走势'};
            const fullLabels = {
                C:'C = Current Quarterly EPS',A:'A = Annual Earnings Growth',
                N:'N = New Products/Highs',S:'S = Supply and Demand',
                L:'L = Leader or Laggard',I:'I = Institutional Sponsorship',M:'M = Market Direction'
            };

            let html = renderStockDataCard(data.stock);
            html += `<div class="card">
                <h2>${data.stock.name} (${data.code}) - CAN SLIM分析</h2>
                <div style="display:flex;align-items:center;gap:20px;margin:20px 0;flex-wrap:wrap;">
                    <div style="text-align:center;padding:20px 30px;background:${getScoreColor(data.scores.total)}15;border:2px solid ${getScoreColor(data.scores.total)};border-radius:12px;">
                        <div style="font-size:2.5em;font-weight:bold;color:${getScoreColor(data.scores.total)};">${data.scores.total}</div>
                        <div style="font-size:0.9em;color:#666;">综合评分</div>
                    </div>
                    <div>
                        <div style="color:${getScoreColor(data.scores.total)};font-size:1.2em;font-weight:600;">${data.rating}</div>
                        <div style="margin-top:6px;font-size:0.9em;color:#666;">通过 <strong>${data.match_count}/7</strong> 项CAN SLIM条件</div>
                    </div>
                </div>
            </div>`;

            // 7项CAN SLIM详细评估
            html += `<div class="card"><h3>📋 CAN SLIM 七项逐条评估</h3>
                <div style="display:grid;gap:10px;margin:15px 0;">`;
            ['C','A','N','S','L','I','M'].forEach(key => {
                const item = canslim[key];
                const passed = item.pass;
                const bgColor = passed ? '#f0fdf4' : '#fef2f2';
                const borderColor = passed ? '#10b981' : '#ef4444';
                const scoreBarWidth = Math.min(item.score, 100);
                html += `<div style="padding:14px;background:${bgColor};border-left:4px solid ${borderColor};border-radius:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <strong>${passed ? '✅' : '❌'} ${fullLabels[key]}</strong>
                        </div>
                        <div style="font-weight:bold;color:${passed ? '#10b981' : '#ef4444'};">${item.score}分</div>
                    </div>
                    <div style="margin:6px 0;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden;">
                        <div style="height:100%;width:${scoreBarWidth}%;background:${passed ? '#10b981' : '#ef4444'};border-radius:2px;"></div>
                    </div>
                    <div style="font-size:0.85em;color:#555;">${item.detail}</div>
                </div>`;
            });
            html += `</div></div>`;

            // 达标/未达标汇总
            html += `<div class="card">
                <h3>💡 欧奈尔投资建议</h3>`;
            if (data.reasons && data.reasons.length > 0) {
                html += `<ul style="margin:8px 0;">${data.reasons.map(r => '<li style="padding:3px 0;color:#166534;">' + r + '</li>').join('')}</ul>`;
            }
            if (data.warnings && data.warnings.length > 0) {
                html += `<div style="margin-top:12px;padding:12px;background:#fef2f2;border-left:4px solid #ef4444;border-radius:4px;">
                    <strong>未达标项</strong>
                    <ul style="margin:6px 0 0;">${data.warnings.map(w => '<li style="padding:2px 0;color:#9a3412;">' + w + '</li>').join('')}</ul>
                </div>`;
            }

            // 买入规则
            if (data.buy_rules && data.buy_rules.length > 0) {
                html += `<div style="margin-top:15px;padding:12px;background:#eff6ff;border-left:4px solid #3b82f6;border-radius:4px;">
                    <strong>📖 欧奈尔买入/卖出规则</strong>
                    <ul style="margin:6px 0 0;">${data.buy_rules.map(r => '<li style="padding:2px 0;color:#1e40af;">' + r + '</li>').join('')}</ul>
                </div>`;
            }
            html += `</div>`;
            container.innerHTML = html;
        }

        // 格雷厄姆价值分析
        async function analyzeGraham() {
            const rawInput = document.getElementById('grahamTicker').value.trim();
            const market = document.getElementById('grahamMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('grahamTicker').value = ticker;

            const resultDiv = document.getElementById('grahamResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><p>正在分析...</p></div>';

            try {
                const response = await fetch(`/api/invest_method?method=graham&ticker=${ticker}&market=${market}`);
                const data = await response.json();
                if (data.error) {
                    resultDiv.innerHTML = `<div style="color: red; padding: 20px;">${data.error}</div>`;
                    return;
                }
                renderGrahamResult(data, resultDiv);
            } catch (error) {
                resultDiv.innerHTML = `<div style="color: red; padding: 20px;">分析失败: ${error.message}</div>`;
            }
        }

        function renderGrahamResult(data, container) {
            const scores = data.scores;
            const gn = data.graham_number;
            const iv = data.intrinsic_value;
            const criteria = data.criteria || [];

            let html = renderStockDataCard(data.stock);
            html += `<div class="card">
                <h2>${data.stock.name} (${data.code}) - 格雷厄姆价值分析</h2>
                <div style="display:flex;align-items:center;gap:20px;margin:20px 0;flex-wrap:wrap;">
                    <div style="text-align:center;padding:20px 30px;background:${getScoreColor(scores.total)}15;border:2px solid ${getScoreColor(scores.total)};border-radius:12px;">
                        <div style="font-size:2.5em;font-weight:bold;color:${getScoreColor(scores.total)};">${scores.total}</div>
                        <div style="font-size:0.9em;color:#666;">综合评分</div>
                    </div>
                    <div>
                        <div style="color:${getScoreColor(scores.total)};font-size:1.2em;font-weight:600;">${data.rating}</div>
                        <div style="margin-top:6px;font-size:0.9em;color:#666;">通过 <strong>${data.criteria_pass}/7</strong> 条防御型投资者准则</div>
                    </div>
                </div>
            </div>`;

            // 格雷厄姆数字 + 内在价值
            html += `<div class="card"><h3>📐 格雷厄姆估值工具</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px;margin:15px 0;">
                    <div style="padding:18px;background:#f0f4ff;border-radius:10px;border:1px solid #dbeafe;">
                        <div style="font-size:0.85em;color:#3b82f6;font-weight:600;">格雷厄姆数字 (GN=√22.5×EPS×BVPS)</div>
                        <div style="font-size:1.8em;font-weight:bold;margin:8px 0;color:#1e40af;">¥${gn.value > 0 ? gn.value.toFixed(2) : 'N/A'}</div>
                        <div style="font-size:0.85em;color:#555;">${gn.assessment}</div>
                    </div>
                    <div style="padding:18px;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;">
                        <div style="font-size:0.85em;color:#10b981;font-weight:600;">内在价值 V=EPS×(8.5+2g)</div>
                        <div style="font-size:1.8em;font-weight:bold;margin:8px 0;color:#166534;">¥${iv.value > 0 ? iv.value.toFixed(2) : 'N/A'}</div>
                        <div style="font-size:0.85em;color:#555;">${iv.assessment}</div>
                    </div>
                </div>`;

            // 安全边际指示器
            if (iv.margin_of_safety !== 0 && iv.margin_of_safety !== undefined) {
                const ms = iv.margin_of_safety;
                const msColor = ms > 33 ? '#10b981' : ms > 0 ? '#f59e0b' : '#ef4444';
                html += `<div style="margin-top:12px;padding:12px;background:${msColor}10;border-left:4px solid ${msColor};border-radius:4px;">
                    <strong>安全边际: ${ms.toFixed(1)}%</strong>
                    <span style="color:#666;margin-left:8px;font-size:0.85em;">格雷厄姆建议≥33%</span>
                </div>`;
            }
            html += `</div>`;

            // 4维评分
            html += `<div class="card"><h3>📊 四维评分</h3>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:15px 0;">
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#3b82f6;">${scores.criteria}</div>
                        <div style="font-size:0.8em;color:#666;">7条准则</div>
                    </div>
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#10b981;">${scores.safety}</div>
                        <div style="font-size:0.8em;color:#666;">安全边际</div>
                    </div>
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#8b5cf6;">${scores.value}</div>
                        <div style="font-size:0.8em;color:#666;">估值水平</div>
                    </div>
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:1.5em;font-weight:bold;color:#f59e0b;">${scores.quality}</div>
                        <div style="font-size:0.8em;color:#666;">财务质量</div>
                    </div>
                </div>
            </div>`;

            // 7条准则清单
            html += `<div class="card"><h3>📋 防御型投资者7条准则</h3>
                <div style="display:grid;gap:8px;margin:12px 0;">`;
            criteria.forEach(c => {
                const bg = c.pass ? '#f0fdf4' : '#fef2f2';
                const border = c.pass ? '#10b981' : '#ef4444';
                html += `<div style="padding:10px 14px;background:${bg};border-left:4px solid ${border};border-radius:8px;font-size:0.9em;">
                    <span>${c.pass ? '✅' : '❌'}</span> <strong>${c.name}</strong>
                    <div style="color:#666;font-size:0.85em;margin-top:2px;">${c.detail}</div>
                </div>`;
            });
            html += `</div></div>`;

            // 建议与警告
            html += `<div class="card"><h3>💡 格雷厄姆投资建议</h3>
                <ul style="margin:8px 0;">${data.reasons.map(r => '<li style="padding:3px 0;">' + r + '</li>').join('')}</ul>`;
            if (data.warnings && data.warnings.length > 0) {
                html += `<div style="margin-top:12px;padding:12px;background:#fff3e0;border-left:4px solid #ff9800;border-radius:4px;">
                    <strong>⚠️ 风险提示</strong>
                    <ul style="margin:6px 0 0;">${data.warnings.map(w => '<li style="padding:2px 0;color:#9a3412;">' + w + '</li>').join('')}</ul>
                </div>`;
            }
            html += `</div>`;
            container.innerHTML = html;
        }

        // 综合分析
        async function analyzeComprehensive() {
            const rawInput = document.getElementById('compTicker').value.trim();
            const market = document.getElementById('compMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('compTicker').value = ticker;

            const resultDiv = document.getElementById('comprehensiveResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><p>正在综合分析...</p></div>';

            try {
                const response = await fetch(`/api/invest_method?method=comprehensive&ticker=${ticker}&market=${market}`);
                const data = await response.json();
                if (data.error) {
                    resultDiv.innerHTML = `<div style="color: red; padding: 20px;">${data.error}</div>`;
                    return;
                }
                renderComprehensiveResult(data, resultDiv);
            } catch (error) {
                resultDiv.innerHTML = `<div style="color: red; padding: 20px;">分析失败: ${error.message}</div>`;
            }
        }

        function renderComprehensiveResult(data, container) {
            const scores = data.scores;
            const dims = data.dimensions;
            const dimColors = {growth:'#3b82f6',value:'#10b981',momentum:'#8b5cf6',moat:'#f59e0b',risk:'#ef4444',allocation:'#14b8a6'};

            let html = renderStockDataCard(data.stock);
            html += `<div class="card">
                <h2>${data.stock.name} (${data.code}) - 综合投资分析</h2>
                <div style="display:flex;align-items:center;gap:20px;margin:20px 0;flex-wrap:wrap;">
                    <div style="text-align:center;padding:24px 35px;background:${getScoreColor(scores.total)}15;border:2px solid ${getScoreColor(scores.total)};border-radius:14px;">
                        <div style="font-size:3em;font-weight:bold;color:${getScoreColor(scores.total)};">${scores.total}</div>
                        <div style="font-size:0.9em;color:#666;">综合评分</div>
                    </div>
                    <div style="flex:1;min-width:200px;">
                        <div style="color:${getScoreColor(scores.total)};font-size:1.3em;font-weight:600;">${data.rating}</div>
                        <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                            <span style="padding:4px 12px;background:#eff6ff;color:#3b82f6;border-radius:20px;font-size:0.85em;">风格: ${data.style}</span>`;
            if (data.key_metrics.peg && data.key_metrics.peg !== 'N/A') {
                html += `<span style="padding:4px 12px;background:#f0fdf4;color:#166534;border-radius:20px;font-size:0.85em;">${data.key_metrics.peg}</span>`;
            }
            if (data.key_metrics.safety) {
                html += `<span style="padding:4px 12px;background:#fef3c7;color:#92400e;border-radius:20px;font-size:0.85em;">${data.key_metrics.safety}</span>`;
            }
            html += `</div></div></div></div>`;

            // 六维雷达评分
            html += `<div class="card"><h3>📊 六维度深度评分</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:15px 0;">`;
            Object.keys(dims).forEach(key => {
                const d = dims[key];
                const color = dimColors[key] || '#64748b';
                html += `<div style="padding:16px;background:#f8f9fa;border-radius:10px;text-align:center;border-top:3px solid ${color};">
                    <div style="font-size:2em;font-weight:bold;color:${color};">${d.score}</div>
                    <div style="font-size:0.85em;font-weight:600;margin:4px 0;">${d.label}</div>
                    <div style="font-size:0.75em;color:#999;">来源: ${d.source}</div>
                    <div style="margin-top:6px;padding:3px 8px;background:${color}15;color:${color};border-radius:12px;font-size:0.8em;display:inline-block;">${d.level}</div>
                </div>`;
            });
            html += `</div>`;

            // 评分条形图
            html += `<div style="margin-top:15px;">`;
            Object.keys(dims).forEach(key => {
                const d = dims[key];
                const color = dimColors[key] || '#64748b';
                const w = Math.min(d.score, 100);
                html += `<div style="display:flex;align-items:center;gap:10px;margin:6px 0;">
                    <div style="width:80px;font-size:0.85em;text-align:right;color:#555;">${d.label}</div>
                    <div style="flex:1;height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;">
                        <div style="height:100%;width:${w}%;background:${color};border-radius:4px;transition:width 0.5s;"></div>
                    </div>
                    <div style="width:30px;font-size:0.85em;font-weight:bold;color:${color};">${d.score}</div>
                </div>`;
            });
            html += `</div></div>`;

            // 综合建议
            html += `<div class="card"><h3>💡 综合投资建议</h3>
                <ul style="margin:8px 0;">${data.reasons.map(r => '<li style="padding:3px 0;">' + r + '</li>').join('')}</ul>`;
            if (data.warnings && data.warnings.length > 0) {
                html += `<div style="margin-top:12px;padding:12px;background:#fff3e0;border-left:4px solid #ff9800;border-radius:4px;">
                    <strong>⚠️ 风险与提醒</strong>
                    <ul style="margin:6px 0 0;">${data.warnings.map(w => '<li style="padding:2px 0;color:#9a3412;">' + w + '</li>').join('')}</ul>
                </div>`;
            }
            html += `</div>`;

            // 各大师视角速览
            html += `<div class="card"><h3>📖 各大师视角速览</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin:12px 0;">
                    <div class="info-card"><strong>林奇(成长)</strong><p>PEG是否<1？分类属于快速增长还是稳定？关注盈利增速。</p></div>
                    <div class="info-card"><strong>格雷厄姆(价值)</strong><p>PE×PB≤22.5？安全边际≥33%？7条防御准则通过几条？</p></div>
                    <div class="info-card"><strong>欧奈尔(动量)</strong><p>EPS加速增长？行业领涨？杯柄形态突破？</p></div>
                    <div class="info-card"><strong>真规则(护城河)</strong><p>持续高ROE+高毛利=竞争优势？有转换成本或网络效应？</p></div>
                    <div class="info-card"><strong>马克斯(风险)</strong><p>当前估值是否包含过多乐观预期？下行空间有多大？</p></div>
                    <div class="info-card"><strong>马尔基尔(配置)</strong><p>适合作为核心持仓还是卫星配置？分红再投资能力如何？</p></div>
                </div>
            </div>`;
            container.innerHTML = html;
        }

        // 霍华德·马克斯 风险分析
        async function analyzeMarks() {
            const rawInput = document.getElementById('marksTicker').value.trim();
            const market = document.getElementById('marksMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('marksTicker').value = ticker;

            const resultDiv = document.getElementById('marksResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><p>正在分析...</p></div>';

            try {
                const response = await fetch('/api/invest_method?method=marks&ticker=' + ticker + '&market=' + market);
                const data = await response.json();
                if (data.error) { resultDiv.innerHTML = '<div style="color: red; padding: 20px;">' + data.error + '</div>'; return; }
                const scores = data.scores;
                resultDiv.innerHTML = '<div class="card">' +
                    '<h2>' + data.stock.name + ' (' + data.code + ') - 霍华德·马克斯风险分析</h2>' +
                    '<div style="text-align: center; margin: 20px 0;">' +
                    '<div style="font-size: 3em; font-weight: bold; color: ' + getScoreColor(scores.total) + ';">' + scores.total + '</div>' +
                    '<div style="color: ' + getScoreColor(scores.total) + ';">' + data.rating + '</div></div>' +
                    '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0;">' +
                    '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;"><div style="font-size: 1.5em; font-weight: bold;">' + scores.risk + '</div><div style="font-size: 0.85em; color: #666;">风险控制</div></div>' +
                    '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;"><div style="font-size: 1.5em; font-weight: bold;">' + scores.cycle + '</div><div style="font-size: 0.85em; color: #666;">周期判断</div></div>' +
                    '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;"><div style="font-size: 1.5em; font-weight: bold;">' + scores.margin + '</div><div style="font-size: 0.85em; color: #666;">安全边际</div></div></div>' +
                    '<h3>风险投资建议</h3><ul>' + data.reasons.map(function(r) { return '<li>' + r + '</li>'; }).join('') + '</ul></div>';
            } catch (error) {
                resultDiv.innerHTML = '<div style="color: red; padding: 20px;">分析失败: ' + error.message + '</div>';
            }
        }

        // 蜡烛图K线形态分析（基于《日本蜡烛图技术新解》全面重构）
        async function analyzeCandle() {
            const rawInput = document.getElementById('candleTicker').value.trim();
            const market = document.getElementById('candleMarket').value;
            const days = document.getElementById('candleDays').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('candleTicker').value = ticker;

            const resultDiv = document.getElementById('candleResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 60px;"><div class="loading">正在加载K线数据并分析形态...</div></div>';

            try {
                const response = await fetch('/api/candle_analysis?ticker=' + ticker + '&market=' + market + '&days=' + days);
                const data = await response.json();
                if (!data.success) {
                    resultDiv.innerHTML = '<div class="card" style="color: red;">' + data.message + '</div>';
                    return;
                }
                renderCandleAnalysis(data);
            } catch (error) {
                resultDiv.innerHTML = '<div class="card" style="color: red;">分析失败: ' + error.message + '</div>';
            }
        }

        function renderCandleAnalysis(data) {
            const resultDiv = document.getElementById('candleResult');
            const ohlcv = data.ohlcv;
            const patterns = data.patterns;
            const indicators = data.indicators;
            const conclusion = data.conclusion;

            // 方向颜色
            const dirColor = conclusion.overall_direction === 'bullish' ? '#26a69a' :
                             conclusion.overall_direction === 'bearish' ? '#ef5350' : '#ff9800';
            const dirText = conclusion.overall_direction === 'bullish' ? '偏多' :
                            conclusion.overall_direction === 'bearish' ? '偏空' : '中性';
            const dirIcon = conclusion.overall_direction === 'bullish' ? '📈' :
                            conclusion.overall_direction === 'bearish' ? '📉' : '📊';

            let html = '';

            // === K线图区域 ===
            html += '<div class="card"><h2>' + data.ticker + ' - 蜡烛图技术分析</h2>';
            html += '<div id="candleChart" style="width:100%;height:500px;"></div>';
            html += '<div id="candleVolumeChart" style="width:100%;height:150px;margin-top:-30px;"></div>';
            html += '</div>';

            // === 综合结论 ===
            html += '<div class="card">';
            html += '<h2>' + dirIcon + ' 综合分析结论</h2>';
            html += '<div style="display:flex;align-items:center;gap:20px;margin:20px 0;">';
            html += '<div style="text-align:center;padding:20px 30px;background:' + dirColor + '15;border:2px solid ' + dirColor + ';border-radius:12px;">';
            html += '<div style="font-size:2.5em;font-weight:bold;color:' + dirColor + ';">' + dirText + '</div>';
            html += '<div style="font-size:0.9em;color:#666;">信号方向</div></div>';
            html += '<div style="text-align:center;padding:20px 30px;background:#f8f9fa;border-radius:12px;">';
            html += '<div style="font-size:2.5em;font-weight:bold;">' + conclusion.confidence.toFixed(0) + '%</div>';
            html += '<div style="font-size:0.9em;color:#666;">信号一致性</div></div>';
            html += '<div style="flex:1;padding:15px;"><p style="font-size:1.1em;font-weight:500;">' + conclusion.summary + '</p></div></div>';

            // 信号明细
            html += '<h3>信号明细</h3><ul style="list-style:none;padding:0;">';
            conclusion.signals.forEach(function(s) {
                if (!s) return;
                let icon = '📌';
                if (s.indexOf('看涨') >= 0 || s.indexOf('金叉') >= 0 || s.indexOf('偏多') >= 0 || s.indexOf('超卖') >= 0) icon = '🟢';
                else if (s.indexOf('看跌') >= 0 || s.indexOf('死叉') >= 0 || s.indexOf('偏空') >= 0 || s.indexOf('超买') >= 0) icon = '🔴';
                html += '<li style="padding:6px 0;border-bottom:1px solid #eee;">' + icon + ' ' + s + '</li>';
            });
            html += '</ul>';

            // 风险提示
            if (conclusion.risk_notes && conclusion.risk_notes.length > 0) {
                html += '<div style="margin-top:15px;padding:15px;background:#fff3e0;border-left:4px solid #ff9800;border-radius:4px;">';
                html += '<strong>⚠️ 风险提示</strong><ul style="margin:8px 0 0 0;">';
                conclusion.risk_notes.forEach(function(r) { html += '<li style="padding:3px 0;">' + r + '</li>'; });
                html += '</ul></div>';
            }
            html += '</div>';

            // === 检测到的形态列表 ===
            if (patterns.length > 0) {
                html += '<div class="card"><h2>🔍 检测到的K线形态 (' + patterns.length + '个)</h2>';

                // 按看涨/看跌/中性分组
                const bullish = patterns.filter(p => p.direction === 'bullish');
                const bearish = patterns.filter(p => p.direction === 'bearish');
                const neutral = patterns.filter(p => p.direction === 'neutral');

                function renderPatternGroup(title, color, pats) {
                    if (pats.length === 0) return '';
                    let g = '<div style="margin-bottom:20px;"><h3 style="color:' + color + ';">' + title + ' (' + pats.length + ')</h3>';
                    g += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:10px;">';
                    pats.forEach(function(p) {
                        const stars = '★'.repeat(p.reliability) + '☆'.repeat(5 - p.reliability);
                        const volBadge = p.volume_confirm ? '<span style="background:#e8f5e9;color:#2e7d32;padding:2px 6px;border-radius:4px;font-size:0.75em;">放量确认</span>' : '';
                        g += '<div style="background:#f8f9fa;padding:12px;border-radius:8px;border-left:4px solid ' + color + ';">';
                        g += '<div style="display:flex;justify-content:space-between;align-items:center;">';
                        g += '<strong>' + p.name + '</strong><span style="font-size:0.85em;color:#999;">' + p.date + '</span></div>';
                        g += '<div style="font-size:0.8em;color:#ff9800;margin:4px 0;">' + stars + ' ' + volBadge + '</div>';
                        g += '<div style="font-size:0.85em;color:#555;">' + p.description + '</div>';
                        g += '<div style="font-size:0.8em;color:#999;margin-top:4px;">价格: ' + p.price.toFixed(2) + ' | 类型: ' + p.type + '</div>';
                        g += '</div>';
                    });
                    g += '</div></div>';
                    return g;
                }

                html += renderPatternGroup('看涨形态', '#26a69a', bullish);
                html += renderPatternGroup('看跌形态', '#ef5350', bearish);
                html += renderPatternGroup('中性形态', '#ff9800', neutral);
                html += '</div>';
            } else {
                html += '<div class="card"><h3>未检测到明显的K线形态</h3><p style="color:#666;">当前时间段内没有识别到典型的蜡烛图形态</p></div>';
            }

            // === 技术指标面板 ===
            html += '<div class="card"><h2>西方技术指标</h2>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px;">';

            // RSI
            html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;">';
            html += '<strong>RSI (14)</strong><p style="margin:5px 0;color:#555;">' + (indicators.rsi_analysis || '') + '</p></div>';

            // MACD
            html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;">';
            html += '<strong>MACD</strong><p style="margin:5px 0;color:#555;">' + (indicators.macd_analysis || '') + '</p></div>';

            // 布林带
            html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;">';
            html += '<strong>布林带</strong><p style="margin:5px 0;color:#555;">' + (indicators.bb_analysis || '') + '</p></div>';

            // 成交量
            html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;">';
            html += '<strong>成交量</strong><p style="margin:5px 0;color:#555;">' + (indicators.volume_analysis || '') + '</p></div>';

            // 均线
            html += '<div style="background:#f8f9fa;padding:15px;border-radius:8px;grid-column:span 2;">';
            html += '<strong>均线系统</strong><ul style="margin:5px 0;padding-left:20px;">';
            (indicators.ma_analysis || []).forEach(function(m) { html += '<li style="color:#555;">' + m + '</li>'; });
            html += '</ul></div>';

            html += '</div></div>';

            // === 形态参考说明 ===
            html += '<div class="card"><h3>📖 形态参考 (基于《日本蜡烛图技术新解》)</h3>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:12px;font-size:0.9em;">';
            const refs = [
                {t:'第2章 单根K线', d:'大阳线/大阴线、锤子线、上吊线、流星、倒锤子、十字线(长腿/墓碑/蜻蜓)、纺锤线'},
                {t:'第3章 双根K线', d:'看涨吞没、看跌吞没、乌云盖顶、刺透形态、平头顶部/底部'},
                {t:'第4章 三根K线', d:'早晨之星、黄昏之星、早晨/黄昏十字星、三只乌鸦、红三兵、弃婴形态'},
                {t:'第5章 持续形态', d:'向上/向下跳空窗口、上升三法、下降三法'},
                {t:'第7章 技术融合', d:'均线趋势、RSI超买超卖、MACD金叉死叉、布林带、量价配合'},
                {t:'第8章 风险管理', d:'止损位参考、波动率评估、仓位控制建议'},
            ];
            refs.forEach(function(r) {
                html += '<div style="background:#f0f4ff;padding:12px;border-radius:8px;"><strong>' + r.t + '</strong>';
                html += '<p style="color:#666;margin:5px 0 0;">' + r.d + '</p></div>';
            });
            html += '</div></div>';

            resultDiv.innerHTML = html;

            // 绘制K线图 (使用Plotly)
            renderCandleChart(ohlcv, patterns, indicators);
        }

        function renderCandleChart(ohlcv, patterns, indicators) {
            // === 主K线图 ===
            const candleTrace = {
                x: ohlcv.dates, open: ohlcv.opens, high: ohlcv.highs,
                low: ohlcv.lows, close: ohlcv.closes,
                type: 'candlestick', name: 'K线',
                increasing: {line: {color: '#26a69a'}, fillcolor: '#26a69a'},
                decreasing: {line: {color: '#ef5350'}, fillcolor: '#ef5350'}
            };

            const traces = [candleTrace];

            // MA线
            const ma5 = indicators.ma5.map(v => v === '' ? null : v);
            const ma20 = indicators.ma20.map(v => v === '' ? null : v);
            const ma60 = indicators.ma60.map(v => v === '' ? null : v);
            traces.push({x: ohlcv.dates, y: ma5, type: 'scatter', mode: 'lines', name: 'MA5', line: {color: '#2196F3', width: 1}});
            traces.push({x: ohlcv.dates, y: ma20, type: 'scatter', mode: 'lines', name: 'MA20', line: {color: '#FF9800', width: 1}});
            traces.push({x: ohlcv.dates, y: ma60, type: 'scatter', mode: 'lines', name: 'MA60', line: {color: '#9C27B0', width: 1, dash: 'dot'}});

            // 布林带
            const bbUpper = indicators.bb_upper.map(v => v === '' ? null : v);
            const bbLower = indicators.bb_lower.map(v => v === '' ? null : v);
            traces.push({x: ohlcv.dates, y: bbUpper, type: 'scatter', mode: 'lines', name: '布林上轨', line: {color: '#90CAF9', width: 1, dash: 'dash'}, showlegend: false});
            traces.push({x: ohlcv.dates, y: bbLower, type: 'scatter', mode: 'lines', name: '布林下轨', line: {color: '#90CAF9', width: 1, dash: 'dash'}, fill: 'tonexty', fillcolor: 'rgba(33,150,243,0.05)', showlegend: false});

            // 形态标注
            const bullishPats = patterns.filter(p => p.direction === 'bullish');
            const bearishPats = patterns.filter(p => p.direction === 'bearish');
            const neutralPats = patterns.filter(p => p.direction === 'neutral');

            if (bullishPats.length > 0) {
                traces.push({
                    x: bullishPats.map(p => p.date), y: bullishPats.map(p => p.low * 0.995),
                    text: bullishPats.map(p => p.name), textposition: 'bottom center',
                    type: 'scatter', mode: 'markers+text', name: '看涨形态',
                    marker: {symbol: 'triangle-up', size: 12, color: '#26a69a'},
                    textfont: {size: 9, color: '#26a69a'}
                });
            }
            if (bearishPats.length > 0) {
                traces.push({
                    x: bearishPats.map(p => p.date), y: bearishPats.map(p => p.high * 1.005),
                    text: bearishPats.map(p => p.name), textposition: 'top center',
                    type: 'scatter', mode: 'markers+text', name: '看跌形态',
                    marker: {symbol: 'triangle-down', size: 12, color: '#ef5350'},
                    textfont: {size: 9, color: '#ef5350'}
                });
            }
            if (neutralPats.length > 0) {
                traces.push({
                    x: neutralPats.map(p => p.date), y: neutralPats.map(p => p.high * 1.005),
                    text: neutralPats.map(p => p.name), textposition: 'top center',
                    type: 'scatter', mode: 'markers+text', name: '中性形态',
                    marker: {symbol: 'diamond', size: 10, color: '#ff9800'},
                    textfont: {size: 9, color: '#ff9800'}
                });
            }

            const layout = {
                title: {text: 'K线走势与形态识别', font: {size: 16}},
                xaxis: {rangeslider: {visible: false}, type: 'category', nticks: 20},
                yaxis: {title: '价格', side: 'right'},
                height: 500, margin: {l: 50, r: 60, t: 40, b: 40},
                showlegend: true, legend: {orientation: 'h', y: -0.15},
                hovermode: 'x unified'
            };

            if (typeof Plotly !== 'undefined') {
                Plotly.newPlot('candleChart', traces, layout, {responsive: true});
            }

            // === 成交量图 ===
            if (indicators.volumes && indicators.volumes.length > 0) {
                const volColors = ohlcv.closes.map((c, i) => c >= ohlcv.opens[i] ? '#26a69a' : '#ef5350');
                const volTrace = {
                    x: ohlcv.dates, y: indicators.volumes, type: 'bar', name: '成交量',
                    marker: {color: volColors}, showlegend: false
                };
                const volTraces = [volTrace];
                const volMa = indicators.vol_ma20.map(v => v === '' ? null : v);
                volTraces.push({x: ohlcv.dates, y: volMa, type: 'scatter', mode: 'lines', name: '均量线', line: {color: '#FF9800', width: 1}, showlegend: false});

                const volLayout = {
                    xaxis: {rangeslider: {visible: false}, type: 'category', showticklabels: false},
                    yaxis: {title: '成交量', side: 'right'},
                    height: 150, margin: {l: 50, r: 60, t: 0, b: 30},
                    showlegend: false, hovermode: 'x unified'
                };
                if (typeof Plotly !== 'undefined') {
                    Plotly.newPlot('candleVolumeChart', volTraces, volLayout, {responsive: true});
                }
            }
        }

        // 马尔基尔漫步分析
        async function analyzeMalkiel() {
            const rawInput = document.getElementById('malkielTicker').value.trim();
            const market = document.getElementById('malkielMarket').value;
            if (!rawInput) { alert('请输入股票代码'); return; }
            const ticker = await resolveTickerCode(rawInput, market);
            if (!ticker) { alert('未找到匹配的股票'); return; }
            document.getElementById('malkielTicker').value = ticker;

            const resultDiv = document.getElementById('malkielResult');
            resultDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><p>正在分析...</p></div>';

            try {
                const response = await fetch('/api/invest_method?method=malkiel&ticker=' + ticker + '&market=' + market);
                const data = await response.json();
                if (data.error) { resultDiv.innerHTML = '<div style="color: red; padding: 20px;">' + data.error + '</div>'; return; }
                renderMalkielResult(data, resultDiv);
            } catch (error) {
                resultDiv.innerHTML = '<div style="color: red; padding: 20px;">分析失败: ' + error.message + '</div>';
            }
        }

        function renderMalkielResult(data, container) {
            const scores = data.scores;
            const rules = data.valuation_rules || [];

            let html = renderStockDataCard(data.stock);
            html += '<div class="card">' +
                '<h2>' + data.stock.name + ' (' + data.code + ') - 马尔基尔漫步分析</h2>' +
                '<div style="display:flex;align-items:center;gap:20px;margin:20px 0;flex-wrap:wrap;">' +
                '<div style="text-align:center;padding:20px 30px;background:' + getScoreColor(scores.total) + '15;border:2px solid ' + getScoreColor(scores.total) + ';border-radius:12px;">' +
                '<div style="font-size:2.5em;font-weight:bold;color:' + getScoreColor(scores.total) + ';">' + scores.total + '</div>' +
                '<div style="font-size:0.9em;color:#666;">综合评分</div></div>' +
                '<div style="flex:1;min-width:200px;">' +
                '<div style="color:' + getScoreColor(scores.total) + ';font-size:1.2em;font-weight:600;">' + data.rating + '</div>' +
                '<div style="margin-top:6px;font-size:0.9em;color:#666;">通过 <strong>' + data.rules_pass + '/4</strong> 条马尔基尔估值法则</div>' +
                '<div style="margin-top:6px;display:flex;gap:8px;flex-wrap:wrap;">' +
                '<span style="padding:4px 12px;background:#eff6ff;color:#3b82f6;border-radius:20px;font-size:0.85em;">' + data.portfolio_role + '</span></div>' +
                '</div></div></div>';

            // 四维评分
            html += '<div class="card"><h3>四维评分</h3>' +
                '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:15px 0;">' +
                '<div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">' +
                '<div style="font-size:1.5em;font-weight:bold;color:#3b82f6;">' + scores.foundation + '</div>' +
                '<div style="font-size:0.8em;color:#666;">坚实基础</div></div>' +
                '<div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">' +
                '<div style="font-size:1.5em;font-weight:bold;color:#10b981;">' + scores.valuation + '</div>' +
                '<div style="font-size:0.8em;color:#666;">估值合理</div></div>' +
                '<div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">' +
                '<div style="font-size:1.5em;font-weight:bold;color:#8b5cf6;">' + scores.lifecycle + '</div>' +
                '<div style="font-size:0.8em;color:#666;">配置价值</div></div>' +
                '<div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">' +
                '<div style="font-size:1.5em;font-weight:bold;color:#f59e0b;">' + scores.random_walk + '</div>' +
                '<div style="font-size:0.8em;color:#666;">抗风险</div></div></div></div>';

            // 4条估值法则
            html += '<div class="card"><h3>📐 马尔基尔4条估值法则</h3>' +
                '<div style="display:grid;gap:8px;margin:12px 0;">';
            rules.forEach(function(r) {
                var bg = r.pass ? '#f0fdf4' : '#fef2f2';
                var border = r.pass ? '#10b981' : '#ef4444';
                html += '<div style="padding:10px 14px;background:' + bg + ';border-left:4px solid ' + border + ';border-radius:8px;font-size:0.9em;">' +
                    '<span>' + (r.pass ? '✅' : '❌') + '</span> <strong>' + r.name + '</strong>' +
                    '<div style="color:#666;font-size:0.85em;margin-top:2px;">' + r.detail + '</div></div>';
            });
            html += '</div></div>';

            // 风险评估
            html += '<div class="card"><h3>🎲 随机漫步风险评估</h3>' +
                '<p style="color:#555;font-size:0.9em;">' + data.risk_level + '</p></div>';

            // 建议
            html += '<div class="card"><h3>💡 马尔基尔投资建议</h3>' +
                '<ul style="margin:8px 0;">' + data.reasons.map(function(r) { return '<li style="padding:3px 0;">' + r + '</li>'; }).join('') + '</ul>';
            if (data.warnings && data.warnings.length > 0) {
                html += '<div style="margin-top:12px;padding:12px;background:#fff3e0;border-left:4px solid #ff9800;border-radius:4px;">' +
                    '<strong>⚠️ 提醒</strong>' +
                    '<ul style="margin:6px 0 0;">' + data.warnings.map(function(w) { return '<li style="padding:2px 0;color:#9a3412;">' + w + '</li>'; }).join('') + '</ul></div>';
            }
            html += '</div>';
            container.innerHTML = html;
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/profile')
def get_profile():
    user_id = request.args.get('user_id', 'root')
    user = profile_manager.get_user(user_id)
    if user:
        return jsonify({'success': True, 'profile': user.to_dict()})
    return jsonify({'success': False})


@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    user_id = data.get('user_id', 'root')
    profile_manager.update_user(
        user_id,
        market_preference=data.get('market_preference'),
        risk_level=data.get('risk_level'),
        return_target=data.get('return_target'),
        holding_period=data.get('holding_period')
    )
    return jsonify({'success': True})


@app.route('/api/recommend')
def recommend():
    user_id = request.args.get('user_id', 'root')

    # 获取用户画像
    user = profile_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    # 所有策略 (8个技术策略 + 9个K线形态策略)
    all_strategies = [
        {'key': 'ma_crossover', 'name': 'MA5/20均线交叉策略', 'annual_return': 0.12, 'sharpe_ratio': 1.5, 'max_drawdown': 0.08, 'factors': ['MA5', 'MA20']},
        {'key': 'macd', 'name': 'MACD金叉死叉策略', 'annual_return': 0.11, 'sharpe_ratio': 1.3, 'max_drawdown': 0.10, 'factors': ['MACD']},
        {'key': 'rsi_oversold', 'name': 'RSI超买超卖策略', 'annual_return': 0.10, 'sharpe_ratio': 1.2, 'max_drawdown': 0.12, 'factors': ['RSI']},
        {'key': 'bollinger', 'name': '布林带策略', 'annual_return': 0.09, 'sharpe_ratio': 1.1, 'max_drawdown': 0.11, 'factors': ['布林带']},
        {'key': 'breakout', 'name': '突破20日新高策略', 'annual_return': 0.15, 'sharpe_ratio': 1.4, 'max_drawdown': 0.18, 'factors': ['新高']},
        {'key': 'ma10_20', 'name': 'MA10/20交叉策略', 'annual_return': 0.11, 'sharpe_ratio': 1.3, 'max_drawdown': 0.09, 'factors': ['MA10', 'MA20']},
        {'key': 'ma20_60', 'name': 'MA20/60中长线策略', 'annual_return': 0.13, 'sharpe_ratio': 1.4, 'max_drawdown': 0.12, 'factors': ['MA20', 'MA60']},
        {'key': 'volatility_timing', 'name': '波动率择时策略', 'annual_return': 0.08, 'sharpe_ratio': 1.8, 'max_drawdown': 0.06, 'factors': ['VOLATILITY']},
        # K线形态策略 - 来自《日本蜡烛图技术新解》
        {'key': 'hammer', 'name': '锤子线策略', 'annual_return': 0.11, 'sharpe_ratio': 1.4, 'max_drawdown': 0.10, 'factors': ['K线形态']},
        {'key': 'hanging_man', 'name': '上吊线策略', 'annual_return': 0.10, 'sharpe_ratio': 1.3, 'max_drawdown': 0.11, 'factors': ['K线形态']},
        {'key': 'bullish_engulfing', 'name': '看涨吞没策略', 'annual_return': 0.14, 'sharpe_ratio': 1.5, 'max_drawdown': 0.12, 'factors': ['K线形态']},
        {'key': 'bearish_engulfing', 'name': '看跌吞没策略', 'annual_return': 0.13, 'sharpe_ratio': 1.4, 'max_drawdown': 0.13, 'factors': ['K线形态']},
        {'key': 'doji', 'name': '十字星策略', 'annual_return': 0.08, 'sharpe_ratio': 1.0, 'max_drawdown': 0.09, 'factors': ['K线形态']},
        {'key': 'morning_star', 'name': '早晨之星策略', 'annual_return': 0.15, 'sharpe_ratio': 1.6, 'max_drawdown': 0.11, 'factors': ['K线形态']},
        {'key': 'evening_star', 'name': '黄昏之星策略', 'annual_return': 0.14, 'sharpe_ratio': 1.5, 'max_drawdown': 0.12, 'factors': ['K线形态']},
        {'key': 'shooting_star', 'name': '流星策略', 'annual_return': 0.12, 'sharpe_ratio': 1.4, 'max_drawdown': 0.11, 'factors': ['K线形态']},
        {'key': 'inverted_hammer', 'name': '倒锤子线策略', 'annual_return': 0.11, 'sharpe_ratio': 1.3, 'max_drawdown': 0.10, 'factors': ['K线形态']},
    ]

    recommendations = []
    for s in all_strategies:
        # 根据用户画像计算匹配度
        match_score = 80
        if user.risk_level == '保守型':
            if s['max_drawdown'] <= 0.10:
                match_score = 90
        elif user.risk_level == '稳健型':
            if s['max_drawdown'] <= 0.15:
                match_score = 85

        if s['annual_return'] >= user.return_target:
            match_score += 10

        recommendations.append({
            'strategy_key': s['key'],
            'strategy_name': s['name'],
            'market': '双市场',
            'annual_return': s['annual_return'],
            'sharpe_ratio': s['sharpe_ratio'],
            'max_drawdown': s['max_drawdown'],
            'factors': s['factors'],
            'matching_score': match_score,
            'recommendation_reason': f"该策略年化收益{s['annual_return']*100:.0f}%，夏普比率{s['sharpe_ratio']:.1f}，最大回撤{s['max_drawdown']*100:.0f}%"
        })

    # 按匹配度排序
    recommendations.sort(key=lambda x: x['matching_score'], reverse=True)

    return jsonify({'success': True, 'recommendations': recommendations})


@app.route('/api/stock_recommend')
def stock_recommend():
    """获取具体股票买卖推荐"""
    strategy = request.args.get('strategy', 'ma_crossover')
    market = request.args.get('market', 'A')

    try:
        stocks = get_stock_recommendations(strategy, market, 10)
        return jsonify({'success': True, 'stocks': stocks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/backtest')
def backtest():
    strategy_key = request.args.get('strategy', 'ma_crossover')
    ticker = request.args.get('ticker', '600519')
    market = request.args.get('market', 'A')
    days = int(request.args.get('days', 250))

    # 策略名称映射
    STRATEGY_NAMES = {
        'ma_crossover': 'MA5/20交叉', 'macd': 'MACD', 'rsi_oversold': 'RSI',
        'bollinger': '布林带', 'breakout': '突破新高', 'ma10_20': 'MA10/20',
        'ma20_60': 'MA20/60', 'volatility_timing': '波动率择时',
        'hammer': '锤子线', 'hanging_man': '上吊线', 'bullish_engulfing': '看涨吞没',
        'bearish_engulfing': '看跌吞没', 'doji': '十字星', 'morning_star': '早晨之星',
        'evening_star': '黄昏之星', 'shooting_star': '流星', 'inverted_hammer': '倒锤子',
    }

    try:
        if market == 'US':
            df = get_us_stock_data(ticker, days)
        else:
            df = get_a_stock_data(ticker, days)
        if df is None or df.empty:
            return jsonify({'success': False, 'message': f'无法获取 {ticker} 的数据'})

        signals = calculate_signals_from_df(df, strategy_key)

        if not signals:
            return jsonify({'success': False, 'message': f'{ticker} 在所选策略下无交易信号'})

        # 生成持仓信号
        position = pd.Series(0, index=df.index)
        dates = df['date'].tolist()
        for s in signals:
            s_date = pd.to_datetime(s['date'])
            for i, d in enumerate(dates):
                if d >= s_date:
                    if s['signal'] == '买入':
                        position.iloc[i] = 1
                    elif s['signal'] == '卖出':
                        position.iloc[i] = -1
                    break

        position = position.replace(0, np.nan)
        position = position.ffill().fillna(0)
        position = position.clip(lower=0)

        # 计算收益
        returns = df['close'].pct_change().fillna(0)
        strategy_returns = position.shift(1) * returns
        strategy_returns = strategy_returns.fillna(0)

        cumulative = (1 + strategy_returns).cumprod()
        total_return = float(cumulative.iloc[-1] - 1)

        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        annual_return = float(annual_return)

        sharpe = float(np.sqrt(252) * strategy_returns.mean() / strategy_returns.std()) if strategy_returns.std() > 0 else 0.0

        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min())

        valid_returns = strategy_returns[strategy_returns != 0]
        win_rate = float((valid_returns > 0).sum() / len(valid_returns)) if len(valid_returns) > 0 else 0.0

        wins = strategy_returns[strategy_returns > 0]
        losses = strategy_returns[strategy_returns < 0]
        avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
        avg_loss = abs(float(losses.mean())) if len(losses) > 0 else 0.0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0

        # 交易统计
        buy_signals = [s for s in signals if s['signal'] == '买入']
        sell_signals = [s for s in signals if s['signal'] == '卖出']
        trade_count = min(len(buy_signals), len(sell_signals))
        holding_days = int(position.sum())
        holding_pct = holding_days / n_days if n_days > 0 else 0

        # 策略名称
        strat_names = [STRATEGY_NAMES.get(s, s) for s in strategy_key.split(',')]
        strategy_name = ' + '.join(strat_names)

        return jsonify({'success': True, 'result': {
            'strategy_name': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'n_trades': len(signals),
            'trade_count': trade_count,
            'holding_pct': holding_pct,
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/report')
def generate_report():
    user_id = request.args.get('user_id', 'root')
    return jsonify({'success': True, 'message': '报告生成功能'})


@app.route('/api/kline')
def get_kline():
    """获取K线数据和买卖信号"""
    ticker = request.args.get('ticker', '')
    market = request.args.get('market', 'A')
    strategy_key = request.args.get('strategy', 'ma_crossover')

    try:
        # 获取历史数据
        if market == 'A':
            df = get_a_stock_data(ticker, 120)
        else:
            df = get_us_stock_data(ticker, 120)

        if df is None or df.empty:
            return jsonify({'success': False, 'message': '无法获取数据'})

        # 计算MA均线
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()

        # 计算买卖信号
        signals = calculate_signals_from_df(df, strategy_key)

        # 准备返回数据
        data = {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'opens': df['open'].tolist() if 'open' in df.columns else df['close'].tolist(),
            'highs': df['high'].tolist() if 'high' in df.columns else df['close'].tolist(),
            'lows': df['low'].tolist() if 'low' in df.columns else df['close'].tolist(),
            'closes': df['close'].tolist(),
            'ma5': df['ma5'].fillna('').tolist(),
            'ma20': df['ma20'].fillna('').tolist()
        }

        return jsonify({'success': True, 'data': data, 'signals': signals})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def calculate_signals_from_df(df, strategy_key):
    """从数据框计算买卖信号（带持仓状态跟踪、止损止盈）"""
    signals = []

    if 'close' not in df.columns:
        return signals

    df = df.copy()

    # 支持多策略组合，用逗号分隔
    strategies = strategy_key.split(',')

    # 跟踪持仓状态：0=空仓, 1=持仓
    position = 0
    buy_price = 0
    buy_atr = 0  # 入场时的ATR值
    all_signals = {}

    # 预计算所有指标
    ma5 = df['close'].rolling(5).mean()
    ma10 = df['close'].rolling(10).mean()
    ma20 = df['close'].rolling(20).mean()
    ma60 = df['close'].rolling(60).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / (loss.replace(0, np.nan))))

    returns = df['close'].pct_change()
    volatility = returns.rolling(20).std() * np.sqrt(252) * 100

    exp12 = df['close'].ewm(span=12, adjust=False).mean()
    exp26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    macd_signal = macd.ewm(span=9, adjust=False).mean()

    ema20_pre = df['close'].ewm(span=20, adjust=False).mean()
    ema50_pre = df['close'].ewm(span=50, adjust=False).mean()

    std20 = df['close'].rolling(20).std()
    bollinger_upper = ma20 + 2 * std20
    bollinger_lower = ma20 - 2 * std20

    rolling_high = df['high'].rolling(20).max()
    rolling_low = df['low'].rolling(20).min()

    for i in range(1, len(df)):
        # 每天检查所有策略，产生信号时考虑当前持仓状态
        for strat in strategies:
            strat = strat.strip()
            signal_type = None
            reason = None

            if strat == 'ma_crossover':
                # ========== 专业级MA策略 ==========
                # 参考专业量化基金的多因子确认体系
                # 只在明确的上升趋势中交易，避免逆势操作

                if pd.notna(ma20.iloc[i]) and i >= 60:  # 需要足够历史数据
                    # 1. 计算真实ATR (Average True Range)
                    if i >= 14:
                        true_ranges = []
                        for k in range(i-13, i+1):
                            tr_hl = df['high'].iloc[k] - df['low'].iloc[k]
                            tr_hc = abs(df['high'].iloc[k] - df['close'].iloc[k-1]) if k > 0 else tr_hl
                            tr_lc = abs(df['low'].iloc[k] - df['close'].iloc[k-1]) if k > 0 else tr_hl
                            true_ranges.append(max(tr_hl, tr_hc, tr_lc))
                        atr = np.mean(true_ranges)
                    else:
                        atr = df['high'].iloc[i] - df['low'].iloc[i]

                    # 2. 计算长期趋势 (EMA20/EMA50 预计算)
                    ema20_val = ema20_pre.iloc[i]
                    ema50_val = ema50_pre.iloc[i]

                    # 3. 统计过去10天中EMA20 > EMA50的天数
                    uptrend_days = 0
                    for j in range(max(0, i-9), i+1):
                        if pd.notna(ema20_pre.iloc[j]) and pd.notna(ema50_pre.iloc[j]):
                            if ema20_pre.iloc[j] > ema50_pre.iloc[j]:
                                uptrend_days += 1

                    major_uptrend = ema20_val > ema50_val and uptrend_days >= 8
                    major_downtrend = ema20_val < ema50_val and uptrend_days <= 2

                    # 4. RSI确认
                    rsi_val = rsi.iloc[i] if pd.notna(rsi.iloc[i]) else 50

                    # 5. 成交量确认
                    vol_ma20 = df['volume'].rolling(20).mean().iloc[i] if 'volume' in df.columns else df['volume'].mean()
                    volume_confirm = 'volume' not in df.columns or df['volume'].iloc[i] > vol_ma20 * 0.8

                    # ===== 只在明确的上升趋势中买入 =====
                    if position == 0 and major_uptrend:
                        # 价格在EMA20附近回调时买入
                        price_vs_ema = (df['close'].iloc[i] - ema20_val) / ema20_val
                        # 回调到EMA20附近 (-6% ~ +2%)
                        if -0.06 <= price_vs_ema <= 0.02:
                            # RSI在合理区间 (20-50)
                            if 20 <= rsi_val <= 50:
                                # 出现反转K线
                                is_bullish = df['close'].iloc[i] > df['open'].iloc[i]
                                if is_bullish and volume_confirm:
                                    signal_type, reason = '买入', f'趋势回踩买入(上升趋势{uptrend_days}天)'
                                    buy_price = df['close'].iloc[i]
                                    buy_atr = atr

                    # ===== 卖出条件 =====
                    elif position == 1:
                        sell_reason = None

                        # 条件1: 上升趋势结束
                        if major_downtrend or uptrend_days <= 3:
                            sell_reason = '趋势结束'

                        # 条件2: ATR止损 (2.5倍ATR)
                        elif buy_atr > 0:
                            atr_stop = buy_price - 2.5 * buy_atr
                            if df['close'].iloc[i] < atr_stop:
                                loss_pct = (buy_price - df['close'].iloc[i]) / buy_price
                                sell_reason = f'ATR止损(-{loss_pct*100:.1f}%)'

                        # 条件3: 止盈 (盈利8%以上且RSI超买)
                        elif rsi_val > 75:
                            profit_pct = (df['close'].iloc[i] - buy_price) / buy_price
                            if profit_pct > 0.08:
                                sell_reason = f'RSI超买止盈(+{profit_pct*100:.1f}%)'

                        # 条件4: 固定止损 (4%)
                        elif df['close'].iloc[i] < buy_price * 0.96:
                            sell_reason = '止损(-4%)'

                        if sell_reason:
                            signal_type, reason = '卖出', sell_reason

            elif strat == 'rsi_oversold':
                if pd.notna(rsi.iloc[i]):
                    # RSI超卖买入，RSI超买卖出，但加入趋势确认
                    if position == 0 and rsi.iloc[i] < 25:  # 更严格的超卖
                        # 确认价格在前一天有反弹迹象
                        if df['close'].iloc[i] > df['open'].iloc[i]:
                            signal_type, reason = '买入', f'RSI超卖({rsi.iloc[i]:.0f})'
                    elif position == 1 and rsi.iloc[i] > 75:  # 更严格的超买
                        if df['close'].iloc[i] < df['open'].iloc[i]:
                            signal_type, reason = '卖出', f'RSI超买({rsi.iloc[i]:.0f})'

            elif strat == 'volatility_timing':
                if pd.notna(volatility.iloc[i]):
                    if position == 0 and volatility.iloc[i] < 20:
                        # 低波动时买入，但需要上升趋势确认
                        if ma5.iloc[i] > ma20.iloc[i]:
                            signal_type, reason = '买入', '低波动+上升趋势'
                    elif position == 1 and volatility.iloc[i] > 30:
                        signal_type, reason = '卖出', '高波动风险'

            elif strat == 'macd':
                if pd.notna(macd.iloc[i]) and pd.notna(macd_signal.iloc[i]):
                    # MACD金叉买入，需要MACD在零轴上方（多头市场）
                    if position == 0 and macd.iloc[i-1] <= macd_signal.iloc[i-1] and macd.iloc[i] > macd_signal.iloc[i]:
                        if macd.iloc[i] > 0:  # 在零轴上方
                            signal_type, reason = '买入', 'MACD金叉(零轴上方)'
                    elif position == 1 and macd.iloc[i-1] >= macd_signal.iloc[i-1] and macd.iloc[i] < macd_signal.iloc[i]:
                        if macd.iloc[i] < 0:  # 在零轴下方
                            signal_type, reason = '卖出', 'MACD死叉(零轴下方)'

            elif strat == 'bollinger':
                if pd.notna(bollinger_upper.iloc[i]) and pd.notna(bollinger_lower.iloc[i]):
                    # 布林带：下轨买入需要上升趋势确认
                    if position == 0 and df['close'].iloc[i] < bollinger_lower.iloc[i]:
                        if ma5.iloc[i] > ma20.iloc[i]:  # 上升趋势中触及下轨
                            signal_type, reason = '买入', '布林下轨+上升趋势'
                    elif position == 1 and df['close'].iloc[i] > bollinger_upper.iloc[i]:
                        signal_type, reason = '卖出', '触及布林上轨'

            elif strat == 'breakout':
                if pd.notna(rolling_high.iloc[i]) and pd.notna(rolling_low.iloc[i]):
                    # 突破买入需要放量确认
                    if position == 0 and df['close'].iloc[i] > rolling_high.iloc[i-1]:
                        # 放量突破
                        if 'volume' in df.columns:
                            vol_ratio = df['volume'].iloc[i] / df['volume'].rolling(20).mean().iloc[i]
                            if vol_ratio > 1.2:  # 成交量放大20%以上
                                signal_type, reason = '买入', '放量突破20日新高'
                    elif position == 1 and df['close'].iloc[i] < rolling_low.iloc[i-1]:
                        signal_type, reason = '卖出', '跌破20日新低'

            elif strat == 'ma10_20':
                if pd.notna(ma10.iloc[i]) and pd.notna(ma20.iloc[i]):
                    uptrend = ma10.iloc[i] > ma20.iloc[i] and df['close'].iloc[i] > ma10.iloc[i]
                    downtrend = ma10.iloc[i] < ma20.iloc[i] and df['close'].iloc[i] < ma10.iloc[i]

                    if position == 0 and ma10.iloc[i-1] <= ma20.iloc[i-1] and ma10.iloc[i] > ma20.iloc[i]:
                        if uptrend:
                            signal_type, reason = '买入', 'MA10金叉MA20(上升趋势)'
                    elif position == 1 and ma10.iloc[i-1] >= ma20.iloc[i-1] and ma10.iloc[i] < ma20.iloc[i]:
                        if downtrend:
                            signal_type, reason = '卖出', 'MA10死叉MA20(下降趋势)'

            elif strat == 'ma20_60':
                if pd.notna(ma20.iloc[i]) and pd.notna(ma60.iloc[i]):
                    # 长周期趋势确认
                    uptrend = ma20.iloc[i] > ma60.iloc[i]  # 长期上升趋势
                    downtrend = ma20.iloc[i] < ma60.iloc[i]  # 长期下降趋势

                    if position == 0 and ma20.iloc[i-1] <= ma60.iloc[i-1] and ma20.iloc[i] > ma60.iloc[i]:
                        if uptrend:
                            signal_type, reason = '买入', 'MA20金叉MA60(长期上升)'
                    elif position == 1 and ma20.iloc[i-1] >= ma60.iloc[i-1] and ma20.iloc[i] < ma60.iloc[i]:
                        if downtrend:
                            signal_type, reason = '卖出', 'MA20死叉MA60(长期下降)'

            # ========== 日本蜡烛图技术 K线形态策略 ==========
            elif strat == 'hammer':
                if i >= 2:
                    body = abs(df['close'].iloc[i] - df['open'].iloc[i])
                    lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
                    upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                    if position == 0 and body > 0 and lower_shadow >= body * 2 and upper_shadow < body:
                        signal_type, reason = '买入', '锤子线(看涨反转)'

            elif strat == 'hanging_man':
                if i >= 2:
                    body = abs(df['close'].iloc[i] - df['open'].iloc[i])
                    lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
                    upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                    if position == 1 and body > 0 and lower_shadow >= body * 2 and upper_shadow < body:
                        signal_type, reason = '卖出', '上吊线(看跌反转)'

            elif strat == 'bullish_engulfing':
                if i >= 1:
                    prev_bearish = df['close'].iloc[i-1] < df['open'].iloc[i-1]
                    curr_bullish = df['close'].iloc[i] > df['open'].iloc[i]
                    if position == 0 and prev_bearish and curr_bullish:
                        if df['close'].iloc[i] > df['open'].iloc[i-1] and df['open'].iloc[i] < df['close'].iloc[i-1]:
                            signal_type, reason = '买入', '看涨吞没(反转信号)'

            elif strat == 'bearish_engulfing':
                if i >= 1:
                    prev_bullish = df['close'].iloc[i-1] > df['open'].iloc[i-1]
                    curr_bearish = df['close'].iloc[i] < df['open'].iloc[i]
                    if position == 1 and prev_bullish and curr_bearish:
                        if df['close'].iloc[i] < df['open'].iloc[i-1] and df['open'].iloc[i] > df['close'].iloc[i-1]:
                            signal_type, reason = '卖出', '看跌吞没(反转信号)'

            elif strat == 'doji':
                if i >= 10:
                    body = abs(df['close'].iloc[i] - df['open'].iloc[i])
                    total_range = df['high'].iloc[i] - df['low'].iloc[i]
                    if total_range > 0 and body < total_range * 0.1:
                        # 根据前期趋势判断方向：下跌中十字星=买入，上涨中十字星=卖出
                        trend = (df['close'].iloc[i] - df['close'].iloc[i-10]) / df['close'].iloc[i-10]
                        if position == 0 and trend < -0.03:
                            signal_type, reason = '买入', '十字星(下跌趋势中变盘信号)'
                        elif position == 1 and trend > 0.03:
                            signal_type, reason = '卖出', '十字星(上涨趋势中变盘信号)'

            elif strat == 'morning_star':
                if i >= 2:
                    day1_bearish = df['close'].iloc[i-2] < df['open'].iloc[i-2]
                    day2_range = df['high'].iloc[i-1] - df['low'].iloc[i-1]
                    day2_small = day2_range < abs(df['close'].iloc[i-2] - df['open'].iloc[i-2]) * 0.5
                    day3_bullish = df['close'].iloc[i] > df['open'].iloc[i]
                    if position == 0 and day1_bearish and day2_small and day3_bullish:
                        if df['close'].iloc[i] > (df['open'].iloc[i-2] + df['close'].iloc[i-2]) / 2:
                            signal_type, reason = '买入', '早晨之星(强烈看涨)'

            elif strat == 'evening_star':
                if i >= 2:
                    day1_bullish = df['close'].iloc[i-2] > df['open'].iloc[i-2]
                    day2_range = df['high'].iloc[i-1] - df['low'].iloc[i-1]
                    day2_small = day2_range < abs(df['close'].iloc[i-2] - df['open'].iloc[i-2]) * 0.5
                    day3_bearish = df['close'].iloc[i] < df['open'].iloc[i]
                    if position == 1 and day1_bullish and day2_small and day3_bearish:
                        if df['close'].iloc[i] < (df['open'].iloc[i-2] + df['close'].iloc[i-2]) / 2:
                            signal_type, reason = '卖出', '黄昏之星(强烈看跌)'

            elif strat == 'shooting_star':
                if i >= 2:
                    body = abs(df['close'].iloc[i] - df['open'].iloc[i])
                    upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                    lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
                    if position == 1 and body > 0 and upper_shadow >= body * 2 and lower_shadow < body:
                        signal_type, reason = '卖出', '流星(看跌反转)'

            elif strat == 'inverted_hammer':
                if i >= 2:
                    body = abs(df['close'].iloc[i] - df['open'].iloc[i])
                    upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                    lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
                    if position == 0 and body > 0 and upper_shadow >= body * 2 and lower_shadow < body:
                        signal_type, reason = '买入', '倒锤子线(看涨反转)'

            # 如果产生了信号
            if signal_type:
                # 更新持仓状态
                if signal_type == '买入':
                    position = 1
                    buy_price = df['close'].iloc[i]
                elif signal_type == '卖出':
                    position = 0

                # 记录信号
                if i not in all_signals:
                    all_signals[i] = {'strategies': [], 'signal': signal_type, 'reason': reason}
                all_signals[i]['strategies'].append(f"{strat}: {reason}")

    # 转换为最终信号列表
    for idx in sorted(all_signals.keys()):
        s = all_signals[idx]
        signals.append({
            'date': df['date'].iloc[idx].strftime('%Y-%m-%d'),
            'price': float(df['close'].iloc[idx]),
            'signal': s['signal'],
            'reason': ' | '.join(s['strategies'])
        })

    return signals


# ========== 真规则推荐API ==========

# 扩展股票数据库（更多A股和美股）
STOCK_DATABASE = {
    # A股 - 白酒消费
    "600519.SH": {"name": "贵州茅台", "industry": "consumer", "pe": 28.5, "pb": 8.2, "roe": 32.5, "gross_margin": 91.5, "revenue_growth": 15.2, "competitive_advantage": ["brand", "monopoly"], "dividend_yield": 1.8, "debt_ratio": 25.0, "description": "中国高端白酒龙头，拥有强大的品牌优势和定价权"},
    "000858.SZ": {"name": "五粮液", "industry": "consumer", "pe": 22.0, "pb": 5.5, "roe": 25.0, "gross_margin": 75.0, "revenue_growth": 12.0, "competitive_advantage": ["brand"], "dividend_yield": 2.5, "debt_ratio": 30.0, "description": "中国第二大白酒企业，品牌优势明显"},
    "000568.SZ": {"name": "泸州老窖", "industry": "consumer", "pe": 20.0, "pb": 4.5, "roe": 28.0, "gross_margin": 78.0, "revenue_growth": 15.0, "competitive_advantage": ["brand"], "dividend_yield": 2.8, "debt_ratio": 35.0, "description": "浓香型白酒鼻祖，品牌历史悠久"},
    "000799.SZ": {"name": "酒鬼酒", "industry": "consumer", "pe": 25.0, "pb": 6.0, "roe": 22.0, "gross_margin": 72.0, "revenue_growth": 18.0, "competitive_advantage": ["brand"], "dividend_yield": 2.0, "debt_ratio": 40.0, "description": "湘酒龙头，文化白酒典范"},

    # A股 - 金融银行
    "601318.SH": {"name": "中国平安", "industry": "finance", "pe": 10.5, "pb": 1.2, "roe": 15.0, "gross_margin": 28.0, "revenue_growth": 8.0, "competitive_advantage": ["network", "cost"], "dividend_yield": 4.5, "debt_ratio": 85.0, "description": "中国最大的保险公司，拥有庞大的客户网络"},
    "600036.SH": {"name": "招商银行", "industry": "finance", "pe": 8.5, "pb": 1.3, "roe": 16.5, "gross_margin": 45.0, "revenue_growth": 10.0, "competitive_advantage": ["brand", "switching_cost"], "dividend_yield": 3.2, "debt_ratio": 92.0, "description": "中国最佳零售银行，客户服务质量领先"},
    "601166.SH": {"name": "兴业银行", "industry": "finance", "pe": 5.5, "pb": 0.8, "roe": 14.0, "gross_margin": 40.0, "revenue_growth": 6.0, "competitive_advantage": ["network"], "dividend_yield": 4.0, "debt_ratio": 93.0, "description": "综合性银行，绿色金融领先"},
    "600030.SH": {"name": "中信证券", "industry": "finance", "pe": 18.0, "pb": 1.5, "roe": 12.0, "gross_margin": 35.0, "revenue_growth": 5.0, "competitive_advantage": ["network", "monopoly"], "dividend_yield": 2.5, "debt_ratio": 80.0, "description": "中国最大的证券公司，投行业务龙头"},
    "601288.SH": {"name": "农业银行", "industry": "finance", "pe": 5.0, "pb": 0.6, "roe": 11.0, "gross_margin": 30.0, "revenue_growth": 4.0, "competitive_advantage": ["monopoly", "network"], "dividend_yield": 5.0, "debt_ratio": 95.0, "description": "中国四大行之一，网点覆盖全国"},
    "601398.SH": {"name": "工商银行", "industry": "finance", "pe": 5.0, "pb": 0.6, "roe": 12.0, "gross_margin": 30.0, "revenue_growth": 3.0, "competitive_advantage": ["monopoly", "network"], "dividend_yield": 5.2, "debt_ratio": 95.0, "description": "全球最大银行，宇宙行"},
    "601939.SH": {"name": "建设银行", "industry": "finance", "pe": 5.0, "pb": 0.6, "roe": 12.0, "gross_margin": 30.0, "revenue_growth": 4.0, "competitive_advantage": ["monopoly", "network"], "dividend_yield": 5.0, "debt_ratio": 95.0, "description": "中国第二大银行，基建领域优势明显"},

    # A股 - 科技互联网
    "000333.SZ": {"name": "美的集团", "industry": "industrial", "pe": 12.0, "pb": 3.5, "roe": 28.0, "gross_margin": 27.0, "revenue_growth": 8.5, "competitive_advantage": ["cost", "network"], "dividend_yield": 4.0, "debt_ratio": 65.0, "description": "全球家电龙头，智能制造领先"},
    "000651.SZ": {"name": "格力电器", "industry": "industrial", "pe": 10.0, "pb": 2.8, "roe": 26.0, "gross_margin": 30.0, "revenue_growth": 5.0, "competitive_advantage": ["brand", "cost"], "dividend_yield": 5.5, "debt_ratio": 70.0, "description": "空调龙头，核心技术领先"},
    "002415.SZ": {"name": "海康威视", "industry": "tech", "pe": 22.0, "pb": 4.5, "roe": 20.0, "gross_margin": 45.0, "revenue_growth": 10.0, "competitive_advantage": ["patent", "network"], "dividend_yield": 2.0, "debt_ratio": 40.0, "description": "全球安防龙头，AI视觉技术领先"},
    "002475.SZ": {"name": "立讯精密", "industry": "tech", "pe": 28.0, "pb": 5.0, "roe": 22.0, "gross_margin": 18.0, "revenue_growth": 25.0, "competitive_advantage": ["cost", "network"], "dividend_yield": 1.0, "debt_ratio": 55.0, "description": "苹果供应链龙头，精密制造典范"},
    "300750.SZ": {"name": "宁德时代", "industry": "tech", "pe": 35.0, "pb": 8.0, "roe": 25.0, "gross_margin": 28.0, "revenue_growth": 80.0, "competitive_advantage": ["patent", "cost"], "dividend_yield": 0.8, "debt_ratio": 60.0, "description": "全球动力电池龙头，电动车核心供应商"},

    # A股 - 医药
    "600276.SH": {"name": "恒瑞医药", "industry": "medical", "pe": 65.0, "pb": 10.0, "roe": 18.0, "gross_margin": 85.0, "revenue_growth": 15.0, "competitive_advantage": ["patent", "brand"], "dividend_yield": 0.8, "debt_ratio": 35.0, "description": "中国创新药龙头，研发实力强劲"},
    "000538.SZ": {"name": "云南白药", "industry": "medical", "pe": 25.0, "pb": 3.5, "roe": 15.0, "gross_margin": 60.0, "revenue_growth": 8.0, "competitive_advantage": ["brand", "patent"], "dividend_yield": 2.5, "debt_ratio": 30.0, "description": "中药保密配方，品牌价值极高"},
    "600867.SH": {"name": "通化金马", "industry": "medical", "pe": 30.0, "pb": 4.0, "roe": 16.0, "gross_margin": 70.0, "revenue_growth": 12.0, "competitive_advantage": ["patent"], "dividend_yield": 1.5, "debt_ratio": 35.0, "description": "医药创新企业，神经领域领先"},
    "300003.SZ": {"name": "乐普医疗", "industry": "medical", "pe": 28.0, "pb": 4.5, "roe": 18.0, "gross_margin": 65.0, "revenue_growth": 15.0, "competitive_advantage": ["patent", "network"], "dividend_yield": 1.8, "debt_ratio": 40.0, "description": "心血管器械龙头，国产替代先锋"},

    # A股 - 新能源电力
    "600900.SH": {"name": "长江电力", "industry": "energy", "pe": 18.0, "pb": 2.8, "roe": 15.5, "gross_margin": 55.0, "revenue_growth": 5.0, "competitive_advantage": ["monopoly", "cost"], "dividend_yield": 3.8, "debt_ratio": 55.0, "description": "全球最大水电公司，现金流稳定"},
    "601888.SH": {"name": "中国中免", "industry": "consumer", "pe": 35.0, "pb": 12.0, "roe": 35.0, "gross_margin": 40.0, "revenue_growth": 25.0, "competitive_advantage": ["monopoly", "network"], "dividend_yield": 1.5, "debt_ratio": 45.0, "description": "中国免税店龙头，具有垄断优势"},
    "600438.SH": {"name": "通威股份", "industry": "energy", "pe": 15.0, "pb": 3.5, "roe": 28.0, "gross_margin": 15.0, "revenue_growth": 50.0, "competitive_advantage": ["cost"], "dividend_yield": 2.0, "debt_ratio": 60.0, "description": "光伏硅料龙头，太阳能电池片领先"},
    "002594.SZ": {"name": "比亚迪", "industry": "tech", "pe": 45.0, "pb": 8.0, "roe": 22.0, "gross_margin": 20.0, "revenue_growth": 60.0, "competitive_advantage": ["brand", "patent", "cost"], "dividend_yield": 0.5, "debt_ratio": 70.0, "description": "中国新能源汽车龙头，动力电池和整车制造双领先"},

    # A股 - 其他
    "600887.SH": {"name": "伊利股份", "industry": "consumer", "pe": 18.0, "pb": 3.5, "roe": 22.0, "gross_margin": 35.0, "revenue_growth": 10.0, "competitive_advantage": ["brand", "network"], "dividend_yield": 3.5, "debt_ratio": 55.0, "description": "中国乳业龙头，品牌深入人心"},
    "000002.SZ": {"name": "万科A", "industry": "finance", "pe": 8.0, "pb": 0.9, "roe": 10.0, "gross_margin": 22.0, "revenue_growth": -5.0, "competitive_advantage": ["brand", "network"], "dividend_yield": 4.0, "debt_ratio": 80.0, "description": "房地产龙头，物业管理领先"},
    "601012.SH": {"name": "隆基绿能", "industry": "energy", "pe": 20.0, "pb": 4.0, "roe": 20.0, "gross_margin": 18.0, "revenue_growth": 45.0, "competitive_advantage": ["patent", "cost"], "dividend_yield": 1.5, "debt_ratio": 55.0, "description": "全球光伏组件龙头，单晶硅片技术领先"},

    # 美股 - 科技巨头
    "AAPL": {"name": "苹果", "industry": "tech", "pe": 28.0, "pb": 45.0, "roe": 160.0, "gross_margin": 45.0, "revenue_growth": 8.0, "competitive_advantage": ["brand", "network", "switching_cost"], "dividend_yield": 0.5, "debt_ratio": 80.0, "description": "全球科技巨头，品牌生态强大"},
    "MSFT": {"name": "微软", "industry": "tech", "pe": 32.0, "pb": 12.0, "roe": 38.0, "gross_margin": 70.0, "revenue_growth": 15.0, "competitive_advantage": ["network", "switching_cost"], "dividend_yield": 0.8, "debt_ratio": 45.0, "description": "云计算龙头，企业软件垄断"},
    "GOOGL": {"name": "谷歌", "industry": "tech", "pe": 25.0, "pb": 6.0, "roe": 25.0, "gross_margin": 57.0, "revenue_growth": 12.0, "competitive_advantage": ["network", "monopoly"], "dividend_yield": 0.0, "debt_ratio": 25.0, "description": "全球搜索引擎霸主，广告业务强劲"},
    "AMZN": {"name": "亚马逊", "industry": "tech", "pe": 55.0, "pb": 8.0, "roe": 15.0, "gross_margin": 47.0, "revenue_growth": 12.0, "competitive_advantage": ["network", "cost"], "dividend_yield": 0.0, "debt_ratio": 65.0, "description": "电商云计算双巨头，网络效应极强"},
    "NVDA": {"name": "英伟达", "industry": "tech", "pe": 65.0, "pb": 45.0, "roe": 70.0, "gross_margin": 75.0, "revenue_growth": 120.0, "competitive_advantage": ["patent", "cost"], "dividend_yield": 0.0, "debt_ratio": 40.0, "description": "AI芯片龙头，GPU垄断地位"},
    "TSLA": {"name": "特斯拉", "industry": "tech", "pe": 80.0, "pb": 15.0, "roe": 20.0, "gross_margin": 18.0, "revenue_growth": 40.0, "competitive_advantage": ["brand", "patent"], "dividend_yield": 0.0, "debt_ratio": 45.0, "description": "电动汽车龙头，创新能力领先"},
    "META": {"name": "Meta", "industry": "tech", "pe": 25.0, "pb": 6.5, "roe": 28.0, "gross_margin": 80.0, "revenue_growth": 20.0, "competitive_advantage": ["network", "monopoly"], "dividend_yield": 0.0, "debt_ratio": 30.0, "description": "社交网络巨头，元宇宙先驱"},

    # 美股 - 金融
    "JPM": {"name": "摩根大通", "industry": "finance", "pe": 11.0, "pb": 1.6, "roe": 15.0, "gross_margin": 55.0, "revenue_growth": 10.0, "competitive_advantage": ["network", "monopoly"], "dividend_yield": 2.5, "debt_ratio": 90.0, "description": "全球最大投行，护城河深厚"},
    "V": {"name": "Visa", "industry": "finance", "pe": 30.0, "pb": 15.0, "roe": 50.0, "gross_margin": 80.0, "revenue_growth": 12.0, "competitive_advantage": ["network", "switching_cost"], "dividend_yield": 0.7, "debt_ratio": 55.0, "description": "支付清算垄断，网络效应极强"},
    "MA": {"name": "Mastercard", "industry": "finance", "pe": 35.0, "pb": 40.0, "roe": 120.0, "gross_margin": 78.0, "revenue_growth": 15.0, "competitive_advantage": ["network", "switching_cost"], "dividend_yield": 0.5, "debt_ratio": 50.0, "description": "全球第二大支付网络"},
    "JNJ": {"name": "强生", "industry": "medical", "pe": 16.0, "pb": 6.0, "roe": 38.0, "gross_margin": 70.0, "revenue_growth": 6.0, "competitive_advantage": ["brand", "patent"], "dividend_yield": 3.0, "debt_ratio": 60.0, "description": "全球最大药企，医疗器械领先"},
    "UNH": {"name": "联合健康", "industry": "medical", "pe": 22.0, "pb": 7.0, "roe": 32.0, "gross_margin": 25.0, "revenue_growth": 12.0, "competitive_advantage": ["network"], "dividend_yield": 1.5, "debt_ratio": 65.0, "description": "美国最大健康险公司"},

    # 美股 - 消费
    "WMT": {"name": "沃尔玛", "industry": "consumer", "pe": 25.0, "pb": 4.5, "roe": 18.0, "gross_margin": 25.0, "revenue_growth": 6.0, "competitive_advantage": ["cost", "network"], "dividend_yield": 1.5, "debt_ratio": 60.0, "description": "全球最大零售商，供应链管理领先"},
    "PG": {"name": "宝洁", "industry": "consumer", "pe": 25.0, "pb": 8.0, "roe": 32.0, "gross_margin": 50.0, "revenue_growth": 5.0, "competitive_advantage": ["brand"], "dividend_yield": 2.4, "debt_ratio": 65.0, "description": "日化用品巨头，品牌矩阵强大"},
    "HD": {"name": "家得宝", "industry": "consumer", "pe": 22.0, "pb": 250.0, "roe": 400.0, "gross_margin": 33.0, "revenue_growth": 4.0, "competitive_advantage": ["brand", "network"], "dividend_yield": 2.5, "debt_ratio": 70.0, "description": "全球最大建材零售商"},
    "COST": {"name": "好市多", "industry": "consumer", "pe": 40.0, "pb": 10.0, "roe": 28.0, "gross_margin": 13.0, "revenue_growth": 10.0, "competitive_advantage": ["network", "cost"], "dividend_yield": 0.7, "debt_ratio": 45.0, "description": "会员制仓储零售标杆"},
    "NKE": {"name": "耐克", "industry": "consumer", "pe": 30.0, "pb": 10.0, "roe": 35.0, "gross_margin": 45.0, "revenue_growth": 8.0, "competitive_advantage": ["brand"], "dividend_yield": 1.0, "debt_ratio": 55.0, "description": "全球运动品牌龙头"},

    # 美股 - 其他
    "DIS": {"name": "迪士尼", "industry": "consumer", "pe": 60.0, "pb": 2.5, "roe": 12.0, "gross_margin": 55.0, "revenue_growth": 15.0, "competitive_advantage": ["brand", "network"], "dividend_yield": 0.0, "debt_ratio": 50.0, "description": "全球娱乐巨头，流媒体新秀"},
    "NFLX": {"name": "Netflix", "industry": "tech", "pe": 45.0, "pb": 8.0, "roe": 25.0, "gross_margin": 45.0, "revenue_growth": 15.0, "competitive_advantage": ["network", "brand"], "dividend_yield": 0.0, "debt_ratio": 50.0, "description": "全球流媒体霸主，内容自制领先"},
    "AMD": {"name": "AMD", "industry": "tech", "pe": 200.0, "pb": 20.0, "roe": 15.0, "gross_margin": 50.0, "revenue_growth": 20.0, "competitive_advantage": ["patent"], "dividend_yield": 0.0, "debt_ratio": 40.0, "description": "CPU/GPU巨头，挑战英特尔"},
    "INTC": {"name": "英特尔", "industry": "tech", "pe": 100.0, "pb": 1.5, "roe": 8.0, "gross_margin": 40.0, "revenue_growth": -10.0, "competitive_advantage": ["patent", "monopoly"], "dividend_yield": 2.0, "debt_ratio": 45.0, "description": "全球最大芯片厂商，PC时代霸主"},
    "ORCL": {"name": "甲骨文", "industry": "tech", "pe": 30.0, "pb": 15.0, "roe": 50.0, "gross_margin": 75.0, "revenue_growth": 8.0, "competitive_advantage": ["network", "switching_cost"], "dividend_yield": 1.5, "debt_ratio": 70.0, "description": "企业软件巨头，数据库垄断"}
}


@app.route('/api/zhen_guize_search')
def zhen_guize_search():
    """搜索股票列表 - 支持模糊查询"""
    keyword = request.args.get('q', '')

    # 使用模糊搜索函数获取实时股票数据
    stocks = fuzzy_search_stocks(keyword)

    results = [{"code": s["code"], "name": s["name"], "market": s.get("market", "A")} for s in stocks]

    return jsonify(results)


@app.route('/api/zhen_guize')
def zhen_guize_analysis():
    """真规则股票分析API - 基于《股市真规则》五大原则全面重构"""
    ticker = request.args.get('ticker', '').strip().upper()
    market = request.args.get('market', 'A')

    if not ticker:
        return jsonify({"error": "请输入股票代码"})

    # ===== 1. 获取基本面数据 =====
    stock = None
    extra_info = {}  # yfinance 额外信息
    try:
        if market == 'A' or ticker.endswith('.SH') or ticker.endswith('.SZ'):
            if not ticker.endswith('.SH') and not ticker.endswith('.SZ'):
                ticker = ticker + '.SH' if ticker.startswith('6') else ticker + '.SZ'
            data = get_a_stock_realtime(ticker)
            if data and data.get('price'):
                stock = {
                    "name": data.get('name', ticker), "price": safe_float(data.get('price')),
                    "pe": safe_float(data.get('pe')), "pb": safe_float(data.get('pb')),
                    "roe": safe_float(data.get('roe')), "gross_margin": safe_float(data.get('gross_margin')),
                    "revenue_growth": safe_float(data.get('revenue_growth')),
                    "dividend_yield": safe_float(data.get('dividend_yield')),
                    "debt_ratio": 0, "market_cap": 0,
                    "industry": "", "sector": "",
                }
        else:
            finviz_data = get_us_stock_data_finviz(ticker)
            if finviz_data and finviz_data.get('price'):
                stock = {
                    "name": finviz_data.get('name', ticker), "price": finviz_data.get('price', 0),
                    "pe": finviz_data.get('pe', 0) or 0, "pb": finviz_data.get('pb', 0) or 0,
                    "roe": finviz_data.get('roe', 0) or 0, "gross_margin": finviz_data.get('gross_margin', 0) or 0,
                    "revenue_growth": finviz_data.get('revenue_growth', 0) or 0,
                    "dividend_yield": finviz_data.get('dividend_yield', 0) or 0,
                    "debt_ratio": finviz_data.get('debt_ratio', 0) or 0,
                    "market_cap": 0, "industry": "", "sector": "",
                }
            # 尝试 yfinance 补充行业和市值数据
            try:
                import yfinance as yf
                info = yf.Ticker(ticker).info
                if info:
                    extra_info = info
                    if not stock:
                        stock = {
                            "name": info.get('shortName', ticker), "price": info.get('currentPrice') or info.get('regularMarketPrice', 0),
                            "pe": info.get('forwardPE') or info.get('trailingPE') or 0,
                            "pb": info.get('priceToBook') or 0,
                            "roe": (info.get('returnOnEquity') or 0) * 100,
                            "gross_margin": (info.get('grossMargins') or 0) * 100,
                            "revenue_growth": (info.get('revenueGrowth') or 0) * 100,
                            "dividend_yield": (info.get('dividendYield') or 0) * 100,
                            "debt_ratio": (info.get('debtToEquity') or 0),
                            "market_cap": info.get('marketCap', 0),
                            "industry": info.get('industry', ''),
                            "sector": info.get('sector', ''),
                        }
                    else:
                        stock['industry'] = info.get('industry', stock.get('industry', ''))
                        stock['sector'] = info.get('sector', stock.get('sector', ''))
                        stock['market_cap'] = info.get('marketCap', 0)
                        if stock['debt_ratio'] == 0:
                            stock['debt_ratio'] = info.get('debtToEquity') or 0
            except Exception:
                pass
    except Exception:
        pass

    # 回退到内置数据库
    if not stock:
        db_stock = STOCK_DATABASE.get(ticker)
        if not db_stock:
            for code, d in STOCK_DATABASE.items():
                if code.upper() == ticker:
                    db_stock = d
                    ticker = code
                    break
        if db_stock:
            stock = dict(db_stock)
            stock.setdefault('price', 0)
            stock.setdefault('market_cap', 0)
            stock.setdefault('sector', '')
        else:
            return jsonify({"error": f"无法获取 {ticker} 的数据"})

    # ===== 2. 获取K线数据 =====
    ohlcv = None
    try:
        if market == 'A' or ticker.endswith('.SH') or ticker.endswith('.SZ'):
            df = get_a_stock_data(ticker, 250)
        else:
            df = get_us_stock_data(ticker, 250)
        if df is not None and not df.empty:
            ohlcv = {
                'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
                'opens': df['open'].tolist(), 'highs': df['high'].tolist(),
                'lows': df['low'].tolist(), 'closes': df['close'].tolist(),
                'volumes': df['volume'].tolist() if 'volume' in df.columns else [],
            }
            if stock.get('price', 0) == 0:
                stock['price'] = float(df['close'].iloc[-1])
    except Exception:
        pass

    # ===== 2.5 获取财务报表数据（近一年季报）=====
    financial_statements = []
    try:
        if market == 'A' or ticker.endswith('.SH') or ticker.endswith('.SZ'):
            # 东方财富 利润表快报API
            code_only = ticker.replace('.SH', '').replace('.SZ', '')
            fs_url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
            fs_params = {
                'reportName': 'RPT_LICO_FN_CPD',
                'columns': 'SECURITY_CODE,SECURITY_NAME_ABBR,REPORTDATE,NOTICE_DATE,TOTAL_OPERATE_INCOME,PARENT_NETPROFIT,BASIC_EPS,WEIGHTAVG_ROE,XSMLL,SJLTZ,SJLHZ,YSTZ,YSHZ,BPS',
                'filter': f'(SECURITY_CODE="{code_only}")',
                'pageSize': '8',
                'sortColumns': 'REPORTDATE',
                'sortTypes': '-1',
                'source': 'WEB',
                'client': 'WEB',
            }
            fs_resp = requests.get(fs_url, params=fs_params, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            fs_data = fs_resp.json()
            if fs_data.get('result') and fs_data['result'].get('data'):
                for item in fs_data['result']['data'][:8]:
                    financial_statements.append({
                        'report_date': (item.get('REPORTDATE') or '')[:10],
                        'notice_date': (item.get('NOTICE_DATE') or '')[:10],
                        'revenue': item.get('TOTAL_OPERATE_INCOME'),
                        'net_profit': item.get('PARENT_NETPROFIT'),
                        'eps': item.get('BASIC_EPS'),
                        'roe': item.get('WEIGHTAVG_ROE'),
                        'gross_margin': item.get('XSMLL'),
                        'profit_yoy': item.get('SJLTZ'),
                        'profit_qoq': item.get('SJLHZ'),
                        'revenue_yoy': item.get('YSTZ'),
                        'revenue_qoq': item.get('YSHZ'),
                        'bps': item.get('BPS'),
                    })
        else:
            # 美股: 尝试 yfinance
            try:
                import yfinance as yf
                yf_ticker = yf.Ticker(ticker)
                qi = yf_ticker.quarterly_income_stmt
                if qi is not None and not qi.empty:
                    for col in qi.columns[:8]:
                        rev = qi.loc['Total Revenue'].get(col) if 'Total Revenue' in qi.index else None
                        ni = qi.loc['Net Income'].get(col) if 'Net Income' in qi.index else None
                        gp = qi.loc['Gross Profit'].get(col) if 'Gross Profit' in qi.index else None
                        oi = qi.loc['Operating Income'].get(col) if 'Operating Income' in qi.index else None
                        entry = {
                            'report_date': col.strftime('%Y-%m-%d'),
                            'revenue': float(rev) if rev is not None else None,
                            'net_profit': float(ni) if ni is not None else None,
                            'gross_profit': float(gp) if gp is not None else None,
                            'operating_income': float(oi) if oi is not None else None,
                        }
                        # 计算毛利率
                        if rev and gp and rev > 0:
                            entry['gross_margin'] = float(gp / rev * 100)
                        financial_statements.append(entry)
            except Exception:
                pass
    except Exception:
        pass

    pe = stock.get('pe', 0) or 0
    pb = stock.get('pb', 0) or 0
    roe = stock.get('roe', 0) or 0
    gross_margin = stock.get('gross_margin', 0) or 0
    revenue_growth = stock.get('revenue_growth', 0) or 0
    dividend_yield = stock.get('dividend_yield', 0) or 0
    debt_ratio = stock.get('debt_ratio', 0) or 0
    price = stock.get('price', 0) or 0

    # ===== 3. 经济护城河自动检测（第3章）=====
    moat = {"level": "无", "sources": [], "details": []}

    # 品牌/无形资产：高毛利率
    if gross_margin > 60:
        moat['sources'].append('无形资产(高毛利)')
        moat['details'].append(f'毛利率{gross_margin:.1f}%远超平均水平，暗示品牌或专利带来的定价权')
    elif gross_margin > 40:
        moat['sources'].append('可能的定价权')
        moat['details'].append(f'毛利率{gross_margin:.1f}%较高，可能有一定定价权')

    # 网络效应/转换成本：高ROE + 高毛利
    if roe > 20 and gross_margin > 40:
        moat['sources'].append('高资本回报')
        moat['details'].append(f'ROE {roe:.1f}%且毛利率高，表明公司有持续的超额收益能力')
    elif roe > 15:
        moat['details'].append(f'ROE {roe:.1f}%处于优秀水平(>15%)，资本利用效率高')

    # 规模优势：大市值
    mc = stock.get('market_cap', 0)
    if mc > 100e9:
        moat['sources'].append('规模优势')
        moat['details'].append(f'市值超{mc/1e9:.0f}亿美元，具有显著规模经济效应')

    # 低负债 = 财务护城河
    if 0 < debt_ratio < 30:
        moat['sources'].append('财务稳健')
        moat['details'].append(f'负债权益比仅{debt_ratio:.1f}%，财务安全垫厚实')

    # 判断护城河等级
    n_sources = len(moat['sources'])
    if n_sources >= 3:
        moat['level'] = '宽阔护城河'
    elif n_sources >= 2:
        moat['level'] = '较窄护城河'
    elif n_sources >= 1:
        moat['level'] = '有一定优势'
    else:
        moat['level'] = '未检测到明显护城河'

    # ===== 4. 行业估值对比 =====
    # 行业平均PE/PB参考表（来源：晨星行业平均值，定期更新）
    INDUSTRY_BENCHMARKS = {
        'Technology': {'pe': 28, 'pb': 6, 'roe': 18, 'margin': 25, 'label': '科技'},
        'Consumer Cyclical': {'pe': 22, 'pb': 4, 'roe': 15, 'margin': 30, 'label': '可选消费'},
        'Consumer Defensive': {'pe': 24, 'pb': 5, 'roe': 20, 'margin': 35, 'label': '必选消费'},
        'Healthcare': {'pe': 22, 'pb': 4, 'roe': 15, 'margin': 30, 'label': '医疗保健'},
        'Financial Services': {'pe': 14, 'pb': 1.5, 'roe': 12, 'margin': 30, 'label': '金融服务'},
        'Communication Services': {'pe': 18, 'pb': 3, 'roe': 12, 'margin': 25, 'label': '通信服务'},
        'Industrials': {'pe': 20, 'pb': 3.5, 'roe': 14, 'margin': 20, 'label': '工业'},
        'Energy': {'pe': 12, 'pb': 1.8, 'roe': 15, 'margin': 15, 'label': '能源'},
        'Utilities': {'pe': 18, 'pb': 1.8, 'roe': 10, 'margin': 20, 'label': '公用事业'},
        'Real Estate': {'pe': 35, 'pb': 2.5, 'roe': 8, 'margin': 25, 'label': '房地产'},
        'Basic Materials': {'pe': 15, 'pb': 2, 'roe': 12, 'margin': 18, 'label': '基础材料'},
        # A股通用
        '白酒': {'pe': 30, 'pb': 8, 'roe': 25, 'margin': 70, 'label': '白酒'},
        '银行': {'pe': 6, 'pb': 0.7, 'roe': 11, 'margin': 40, 'label': '银行'},
        '新能源': {'pe': 25, 'pb': 4, 'roe': 15, 'margin': 20, 'label': '新能源'},
        '医药': {'pe': 28, 'pb': 4, 'roe': 14, 'margin': 35, 'label': '医药'},
        '保险': {'pe': 10, 'pb': 1.2, 'roe': 12, 'margin': 20, 'label': '保险'},
        '家电': {'pe': 15, 'pb': 3, 'roe': 20, 'margin': 30, 'label': '家电'},
    }

    # 匹配行业
    sector = stock.get('sector', '') or stock.get('industry', '')
    industry_info = None
    for key, val in INDUSTRY_BENCHMARKS.items():
        if key.lower() in sector.lower() or (val.get('label', '') and val['label'] in sector):
            industry_info = val
            break

    # 从STOCK_DATABASE查找行业
    if not industry_info:
        db_entry = STOCK_DATABASE.get(ticker, {})
        db_industry = db_entry.get('industry', '')
        industry_map = {
            'liquor': '白酒', 'bank': '银行', 'insurance': '保险', 'energy': 'Energy',
            'pharma': '医药', 'tech': 'Technology', 'consumer': 'Consumer Defensive',
            'appliance': '家电', 'new_energy': '新能源', 'finance': 'Financial Services',
            'media': 'Communication Services', 'industrial': 'Industrials',
        }
        mapped = industry_map.get(db_industry, '')
        if mapped:
            industry_info = INDUSTRY_BENCHMARKS.get(mapped)
            sector = mapped

    if not industry_info:
        industry_info = {'pe': 20, 'pb': 3, 'roe': 15, 'margin': 25, 'label': '综合'}

    industry_comparison = {
        'industry_name': industry_info.get('label', sector or '综合'),
        'industry_pe': industry_info['pe'],
        'industry_pb': industry_info['pb'],
        'industry_roe': industry_info['roe'],
        'industry_margin': industry_info['margin'],
        'pe_vs_industry': '',
        'pb_vs_industry': '',
        'overall_valuation': '',
    }

    # PE对比
    if pe > 0 and industry_info['pe'] > 0:
        pe_ratio = pe / industry_info['pe']
        if pe_ratio > 1.3:
            industry_comparison['pe_vs_industry'] = f'PE {pe:.1f}x 高于行业均值 {industry_info["pe"]}x（溢价{(pe_ratio-1)*100:.0f}%），估值偏高'
        elif pe_ratio < 0.7:
            industry_comparison['pe_vs_industry'] = f'PE {pe:.1f}x 低于行业均值 {industry_info["pe"]}x（折价{(1-pe_ratio)*100:.0f}%），估值偏低'
        else:
            industry_comparison['pe_vs_industry'] = f'PE {pe:.1f}x 接近行业均值 {industry_info["pe"]}x，估值合理'

    if pb > 0 and industry_info['pb'] > 0:
        pb_ratio = pb / industry_info['pb']
        if pb_ratio > 1.3:
            industry_comparison['pb_vs_industry'] = f'PB {pb:.1f}x 高于行业均值 {industry_info["pb"]}x'
        elif pb_ratio < 0.7:
            industry_comparison['pb_vs_industry'] = f'PB {pb:.1f}x 低于行业均值 {industry_info["pb"]}x'
        else:
            industry_comparison['pb_vs_industry'] = f'PB {pb:.1f}x 接近行业均值 {industry_info["pb"]}x'

    # ===== 5. 估值分析与买卖点位（第9-10章）=====
    valuation = {
        'methods': [],
        'fair_value': 0,
        'buy_price': 0,
        'sell_price': 0,
        'current_vs_fair': '',
        'safety_margin': 0,
    }

    fair_values = []

    # 方法1: 基于PE的估值
    if pe > 0 and price > 0:
        eps = price / pe
        fair_pe = industry_info['pe']
        # 高ROE公司可以给更高PE
        if roe > 20:
            fair_pe *= 1.2
        elif roe > 15:
            fair_pe *= 1.1
        # 高增长可以给溢价
        if revenue_growth > 20:
            fair_pe *= 1.15
        pe_fair = eps * fair_pe
        fair_values.append(pe_fair)
        valuation['methods'].append({
            'name': 'PE估值法',
            'detail': f'每股收益={eps:.2f}, 合理PE={fair_pe:.1f}x',
            'fair_value': round(pe_fair, 2),
        })

    # 方法2: 基于PB-ROE的估值
    if pb > 0 and price > 0 and roe > 0:
        bvps = price / pb
        fair_pb = roe / 10  # ROE 15% -> PB 1.5x
        fair_pb = max(1.0, min(fair_pb, 10))
        pb_fair = bvps * fair_pb
        fair_values.append(pb_fair)
        valuation['methods'].append({
            'name': 'PB-ROE估值法',
            'detail': f'每股净资产={bvps:.2f}, ROE={roe:.1f}% -> 合理PB={fair_pb:.1f}x',
            'fair_value': round(pb_fair, 2),
        })

    # 方法3: 股息折现（适用于高分红公司）
    if dividend_yield > 1 and price > 0:
        dps = price * dividend_yield / 100
        # 假设8%的要求回报率，3%的增长率
        req_return = 0.08
        growth_rate = min(revenue_growth / 100, 0.05) if revenue_growth > 0 else 0.03
        if req_return > growth_rate:
            ddm_fair = dps * (1 + growth_rate) / (req_return - growth_rate)
            if ddm_fair > 0:
                fair_values.append(ddm_fair)
                valuation['methods'].append({
                    'name': '股息折现模型',
                    'detail': f'每股股息={dps:.2f}, 要求回报率=8%, 增长率={growth_rate*100:.1f}%',
                    'fair_value': round(ddm_fair, 2),
                })

    # 综合合理价值（取均值）
    if fair_values:
        fair_value = sum(fair_values) / len(fair_values)
        valuation['fair_value'] = round(fair_value, 2)
        # 安全边际20-30%
        valuation['buy_price'] = round(fair_value * 0.75, 2)
        valuation['sell_price'] = round(fair_value * 1.25, 2)

        if price > 0:
            margin = (fair_value - price) / fair_value * 100
            valuation['safety_margin'] = round(margin, 1)
            if margin > 25:
                valuation['current_vs_fair'] = f'当前价格{price:.2f}显著低于合理估值{fair_value:.2f}，安全边际{margin:.0f}%，估值偏低'
                industry_comparison['overall_valuation'] = '低估'
            elif margin > 10:
                valuation['current_vs_fair'] = f'当前价格{price:.2f}略低于合理估值{fair_value:.2f}，有一定安全边际({margin:.0f}%)'
                industry_comparison['overall_valuation'] = '略低估'
            elif margin > -10:
                valuation['current_vs_fair'] = f'当前价格{price:.2f}接近合理估值{fair_value:.2f}，估值合理'
                industry_comparison['overall_valuation'] = '合理'
            elif margin > -25:
                valuation['current_vs_fair'] = f'当前价格{price:.2f}略高于合理估值{fair_value:.2f}，估值偏高({-margin:.0f}%溢价)'
                industry_comparison['overall_valuation'] = '略高估'
            else:
                valuation['current_vs_fair'] = f'当前价格{price:.2f}显著高于合理估值{fair_value:.2f}，估值过高({-margin:.0f}%溢价)'
                industry_comparison['overall_valuation'] = '高估'

    # ===== 6. 10分钟测试（第12章）=====
    ten_min_test = []
    test_pass = 0
    test_total = 7

    # 测试1: ROE
    if roe > 15:
        ten_min_test.append({'item': 'ROE > 15%', 'value': f'{roe:.1f}%', 'pass': True, 'note': '资本回报率优秀'})
        test_pass += 1
    else:
        ten_min_test.append({'item': 'ROE > 15%', 'value': f'{roe:.1f}%', 'pass': False, 'note': '资本回报率不达标'})

    # 测试2: 毛利率
    if gross_margin > 30:
        ten_min_test.append({'item': '毛利率 > 30%', 'value': f'{gross_margin:.1f}%', 'pass': True, 'note': '盈利能力良好'})
        test_pass += 1
    else:
        ten_min_test.append({'item': '毛利率 > 30%', 'value': f'{gross_margin:.1f}%', 'pass': False, 'note': '盈利能力偏弱'})

    # 测试3: 营收增长
    if revenue_growth > 5:
        ten_min_test.append({'item': '营收增长 > 5%', 'value': f'{revenue_growth:.1f}%', 'pass': True, 'note': '保持增长'})
        test_pass += 1
    else:
        ten_min_test.append({'item': '营收增长 > 5%', 'value': f'{revenue_growth:.1f}%', 'pass': False, 'note': '增长乏力'})

    # 测试4: 负债率
    if debt_ratio < 80:
        ten_min_test.append({'item': '负债权益比 < 80%', 'value': f'{debt_ratio:.1f}%', 'pass': True, 'note': '债务可控'})
        test_pass += 1
    elif debt_ratio == 0:
        ten_min_test.append({'item': '负债权益比', 'value': '数据缺失', 'pass': True, 'note': '暂无数据'})
        test_pass += 1
    else:
        ten_min_test.append({'item': '负债权益比 < 80%', 'value': f'{debt_ratio:.1f}%', 'pass': False, 'note': '负债较高'})

    # 测试5: PE估值
    if 0 < pe < 30:
        ten_min_test.append({'item': 'PE < 30x', 'value': f'{pe:.1f}x', 'pass': True, 'note': '估值不算贵'})
        test_pass += 1
    elif pe <= 0:
        ten_min_test.append({'item': 'PE', 'value': '亏损/数据缺失', 'pass': False, 'note': '无法评估'})
    else:
        ten_min_test.append({'item': 'PE < 30x', 'value': f'{pe:.1f}x', 'pass': False, 'note': '估值偏高'})

    # 测试6: 股息
    if dividend_yield > 0:
        ten_min_test.append({'item': '有分红', 'value': f'{dividend_yield:.1f}%', 'pass': True, 'note': '有股息回报'})
        test_pass += 1
    else:
        ten_min_test.append({'item': '有分红', 'value': '无', 'pass': False, 'note': '不分红'})

    # 测试7: 护城河
    if len(moat['sources']) >= 1:
        ten_min_test.append({'item': '有护城河', 'value': moat['level'], 'pass': True, 'note': '、'.join(moat['sources'][:2])})
        test_pass += 1
    else:
        ten_min_test.append({'item': '有护城河', 'value': '未检测到', 'pass': False, 'note': '竞争优势不明显'})

    # ===== 7. 五大原则综合评分 =====
    # 原则1: 做好功课 -> 数据完整性
    data_completeness = sum(1 for v in [pe, pb, roe, gross_margin, revenue_growth] if v != 0)
    rule1_score = data_completeness * 20

    # 原则2: 经济护城河
    rule2_score = min(100, len(moat['sources']) * 30 + (10 if roe > 15 else 0) + (10 if gross_margin > 40 else 0))

    # 原则3: 安全边际
    sm = valuation.get('safety_margin', 0)
    if sm > 30: rule3_score = 100
    elif sm > 15: rule3_score = 80
    elif sm > 0: rule3_score = 60
    elif sm > -15: rule3_score = 40
    else: rule3_score = 20

    # 原则4: 长期持有 -> 财务稳健度
    rule4_score = 0
    if roe > 15: rule4_score += 30
    elif roe > 10: rule4_score += 20
    if gross_margin > 30: rule4_score += 25
    elif gross_margin > 15: rule4_score += 15
    if 0 < debt_ratio < 50: rule4_score += 25
    elif debt_ratio == 0: rule4_score += 15
    if revenue_growth > 5: rule4_score += 20
    elif revenue_growth > 0: rule4_score += 10
    rule4_score = min(100, rule4_score)

    # 原则5: 知道何时卖出 -> 估值信号
    rule5_score = rule3_score  # 与安全边际关联

    total_score = (rule1_score * 0.10 + rule2_score * 0.30 + rule3_score * 0.25 +
                   rule4_score * 0.25 + rule5_score * 0.10)

    if total_score >= 80: rating = "★★★★★ 强烈推荐买入"
    elif total_score >= 65: rating = "★★★★☆ 值得持有/加仓"
    elif total_score >= 50: rating = "★★★☆☆ 观望等待时机"
    elif total_score >= 35: rating = "★★☆☆☆ 谨慎/减仓"
    else: rating = "★☆☆☆☆ 不推荐"

    # ===== 8. 买卖建议 =====
    advice = []
    if valuation.get('buy_price') and valuation.get('sell_price'):
        if price > 0 and price <= valuation['buy_price']:
            advice.append({'action': '买入', 'reason': f'当前价{price:.2f}低于买入目标价{valuation["buy_price"]:.2f}，安全边际充足'})
        elif price > 0 and price >= valuation['sell_price']:
            advice.append({'action': '卖出', 'reason': f'当前价{price:.2f}高于卖出目标价{valuation["sell_price"]:.2f}，估值过高'})
        elif price > 0 and price < valuation['fair_value']:
            advice.append({'action': '持有/逢低加仓', 'reason': f'当前价{price:.2f}低于合理估值{valuation["fair_value"]:.2f}，可继续持有'})
        else:
            advice.append({'action': '观望', 'reason': f'当前价{price:.2f}略高于合理估值，等待回调至{valuation["buy_price"]:.2f}附近'})

    if test_pass >= 6:
        advice.append({'action': '通过10分钟测试', 'reason': f'{test_pass}/{test_total}项通过，值得深入研究'})
    elif test_pass >= 4:
        advice.append({'action': '部分通过', 'reason': f'{test_pass}/{test_total}项通过，需关注未通过项的风险'})
    else:
        advice.append({'action': '未通过筛选', 'reason': f'仅{test_pass}/{test_total}项通过，基本面较弱'})

    return jsonify({
        "success": True,
        "code": ticker,
        "stock": stock,
        "ohlcv": ohlcv,
        "financial_statements": financial_statements,
        "moat": moat,
        "industry_comparison": industry_comparison,
        "valuation": valuation,
        "ten_min_test": ten_min_test,
        "test_summary": {"pass": test_pass, "total": test_total},
        "five_rules": {
            "rule1": {"name": "做好功课", "score": round(rule1_score, 1), "detail": f"数据完整度{data_completeness}/5项"},
            "rule2": {"name": "经济护城河", "score": round(rule2_score, 1), "detail": moat['level']},
            "rule3": {"name": "安全边际", "score": round(rule3_score, 1), "detail": valuation.get('current_vs_fair', '数据不足')},
            "rule4": {"name": "长期持有", "score": round(rule4_score, 1), "detail": f"ROE={roe:.1f}% 毛利率={gross_margin:.1f}%"},
            "rule5": {"name": "何时卖出", "score": round(rule5_score, 1), "detail": f"{'有安全边际' if sm > 0 else '安全边际不足'}"},
        },
        "total_score": round(total_score, 1),
        "rating": rating,
        "advice": advice,
    })


# ========== 多书籍投资分析方法API ==========
@app.route('/api/invest_method')
def invest_method_analysis():
    """多书籍投资分析方法API"""
    method = request.args.get('method', 'linch')
    ticker = request.args.get('ticker', '')
    market = request.args.get('market', 'A')

    # 获取股票数据
    try:
        if market == 'A' or ticker.endswith('.SH') or ticker.endswith('.SZ'):
            # 使用爬虫获取A股数据
            if not ticker.endswith('.SH') and not ticker.endswith('.SZ'):
                ticker = (ticker + '.SH') if ticker.startswith('6') else ticker + '.SZ'

            data = get_a_stock_realtime(ticker)

            if not data or not data.get('price'):
                return jsonify({"error": "股票未找到"})

            stock = {
                "name": data.get('name', ticker),
                "price": safe_float(data.get('price')),
                "pe": safe_float(data.get('pe')),
                "pb": safe_float(data.get('pb')),
                "roe": safe_float(data.get('roe')),
                "gross_margin": safe_float(data.get('gross_margin')),
                "revenue_growth": safe_float(data.get('revenue_growth')),
                "dividend_yield": safe_float(data.get('dividend_yield')),
            }
        else:
            # 美股：优先用 Finviz 爬虫获取实时数据
            finviz_data = get_us_stock_data_finviz(ticker)
            if finviz_data and finviz_data.get('price'):
                stock = finviz_data
            else:
                # Finviz 失败，尝试 yfinance
                try:
                    import yfinance as yf
                    info = yf.Ticker(ticker).info
                    stock = {
                        "name": info.get('shortName', ticker),
                        "price": info.get('currentPrice') or info.get('regularMarketPrice') or 0,
                        "pe": info.get('forwardPE') or info.get('trailingPE') or 0,
                        "pb": info.get('priceToBook') or 0,
                        "roe": (info.get('returnOnEquity') or 0) * 100,
                        "gross_margin": (info.get('grossMargins') or 0) * 100,
                        "revenue_growth": (info.get('revenueGrowth') or 0) * 100,
                        "dividend_yield": (info.get('dividendYield') or 0) * 100,
                        "market_cap": info.get('marketCap') or 0,
                        "debt_ratio": (info.get('debtToEquity') or 0) / (1 + (info.get('debtToEquity') or 0)) * 100 if info.get('debtToEquity') else 0,
                        "current_ratio": info.get('currentRatio') or 0,
                        "earnings_growth": (info.get('earningsGrowth') or 0) * 100,
                    }
                except Exception:
                    raise ValueError(f"无法获取 {ticker} 数据")
    except Exception as e:
        # 使用内置数据库
        stock_data = STOCK_DATABASE.get(ticker.upper())
        if not stock_data:
            for code, data in STOCK_DATABASE.items():
                if code.upper() == ticker.upper():
                    stock_data = data
                    break
        if not stock_data:
            return jsonify({"error": f"获取数据失败: {str(e)}"})
        stock = stock_data

    if method == 'linch':
        return analyze_linch(ticker, stock)
    elif method == 'oneil':
        return analyze_oneil(ticker, stock)
    elif method == 'graham':
        return analyze_graham(ticker, stock)
    elif method == 'comprehensive':
        return analyze_comprehensive(ticker, stock)
    elif method == 'marks':
        return analyze_marks(ticker, stock)
    elif method == 'candle':
        return analyze_candle(ticker, stock)
    elif method == 'malkiel':
        return analyze_malkiel(ticker, stock)
    else:
        return jsonify({"error": "未知方法"})


def analyze_linch(ticker, stock):
    """彼得林奇分析方法 - 基于《彼得林奇的成功投资》
    核心：6大股票分类、PEG比率、13条选股准则、鸡尾酒会理论
    """
    pe = stock.get('pe', 0) or 0
    roe = stock.get('roe', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0
    margin = stock.get('gross_margin', 0) or 0
    div = stock.get('dividend_yield', 0) or 0
    pb = stock.get('pb', 0) or 0
    price = stock.get('price', 0) or 0
    debt_ratio = stock.get('debt_ratio', 0) or 0

    # === 1. 股票分类（林奇6大类） ===
    category = "未分类"
    category_desc = ""
    if growth > 25 and pe > 15:
        category = "快速增长型"
        category_desc = "年增长率20-50%的公司，林奇最爱。关键是判断增长期何时结束、买入价格是否合理。"
    elif 10 < growth <= 25 and roe > 12:
        category = "稳定增长型"
        category_desc = "年增长率10-20%的大公司（如可口可乐），可在熊市中提供保护，但涨幅有限。"
    elif growth <= 5 and div > 3:
        category = "缓慢增长型"
        category_desc = "成熟大型公司，增长缓慢但分红丰厚。主要看股息率。"
    elif growth > 15 and pe > 0 and pe < 15:
        category = "困境反转型"
        category_desc = "遭遇危机但有望恢复的公司。如果反转成功，回报丰厚。"
    elif abs(growth) > 20 or (pe > 0 and pe > 40):
        category = "周期型"
        category_desc = "利润随经济周期大幅波动（汽车、钢铁、航空）。关键是把握买卖时机。"
    elif pb > 0 and pb < 1:
        category = "隐蔽资产型"
        category_desc = "拥有被市场忽视的有价值资产（如土地、品牌）。需深入调研发现价值。"
    else:
        # 默认分类逻辑
        if growth > 15:
            category = "快速增长型"
            category_desc = "增长率较高，关注增长的可持续性。"
        elif div > 2:
            category = "缓慢增长型"
            category_desc = "增速一般但有分红，关注股息的稳定性。"
        else:
            category = "稳定增长型"
            category_desc = "增速适中，作为投资组合的稳定器。"

    # === 2. PEG比率分析（林奇最看重的指标） ===
    peg = 0
    peg_assessment = ""
    earnings_growth = growth  # 用营收增长近似
    if pe > 0 and earnings_growth > 0:
        peg = round(pe / earnings_growth, 2)
        if peg < 0.5:
            peg_assessment = "极度低估（PEG<0.5），林奇认为这是绝佳买入机会"
        elif peg < 1:
            peg_assessment = "被低估（PEG<1），增长率高于PE，值得关注"
        elif peg < 1.5:
            peg_assessment = "估值合理（1<PEG<1.5），需关注增长持续性"
        elif peg < 2:
            peg_assessment = "略微高估（1.5<PEG<2），需谨慎"
        else:
            peg_assessment = "明显高估（PEG>2），增长率不足以支撑当前估值"
    elif pe > 0 and earnings_growth <= 0:
        peg_assessment = "增长为负，PEG无意义。林奇不建议买入负增长公司。"
    else:
        peg_assessment = "PE或增长率数据不足，无法计算PEG"

    # === 3. 林奇13条选股准则评分 ===
    checklist = []
    score_13 = 0

    # 1) 公司名字听起来无聊或可笑
    checklist.append({"name": "名字朴素/行业不热门", "pass": True, "note": "需人工判断（自动分析跳过）", "auto": False})

    # 2) 公司业务无聊
    checklist.append({"name": "业务简单易懂", "pass": True, "note": "需人工判断", "auto": False})

    # 3) 公司业务令人厌烦
    checklist.append({"name": "行业不受关注", "pass": True, "note": "需人工判断", "auto": False})

    # 4) 机构持股比例低 - 用PE间接判断
    inst_low = pe > 0 and pe < 20
    checklist.append({"name": "低关注度/低估值", "pass": inst_low, "note": f"PE={pe:.1f}，{'低于20倍，关注度可能较低' if inst_low else '估值偏高，可能已被充分关注'}", "auto": True})
    if inst_low: score_13 += 1

    # 5) 公司在持续增长
    grow_ok = growth > 10
    checklist.append({"name": "持续增长", "pass": grow_ok, "note": f"营收增长{growth:.1f}%，{'保持增长态势' if grow_ok else '增长不足'}", "auto": True})
    if grow_ok: score_13 += 1

    # 6) PEG低于1
    peg_ok = 0 < peg < 1
    checklist.append({"name": "PEG<1（增长率>PE）", "pass": peg_ok, "note": f"PEG={peg:.2f}，{peg_assessment}" if peg > 0 else "无法计算PEG", "auto": True})
    if peg_ok: score_13 += 1

    # 7) 高利润率
    margin_ok = margin > 20
    checklist.append({"name": "利润率高于20%", "pass": margin_ok, "note": f"毛利率{margin:.1f}%，{'盈利能力强' if margin_ok else '利润率偏低'}", "auto": True})
    if margin_ok: score_13 += 1

    # 8) 高ROE
    roe_ok = roe > 15
    checklist.append({"name": "ROE>15%（资本效率）", "pass": roe_ok, "note": f"ROE={roe:.1f}%，{'资本使用效率高' if roe_ok else '资本效率一般'}", "auto": True})
    if roe_ok: score_13 += 1

    # 9) 低负债
    debt_ok = debt_ratio < 40 if debt_ratio > 0 else True
    checklist.append({"name": "低负债率（<40%）", "pass": debt_ok, "note": f"负债率{debt_ratio:.1f}%，{'财务稳健' if debt_ok else '负债偏高需警惕'}" if debt_ratio > 0 else "负债数据不足", "auto": debt_ratio > 0})
    if debt_ok and debt_ratio > 0: score_13 += 1

    # 10) 有股息
    div_ok = div > 0
    checklist.append({"name": "有分红记录", "pass": div_ok, "note": f"股息率{div:.2f}%，{'有现金回报' if div_ok else '未分红'}", "auto": True})
    if div_ok: score_13 += 1

    # === 4. 综合评分 ===
    # PEG评分 (30分)
    peg_score = 0
    if peg > 0:
        if peg < 0.5: peg_score = 100
        elif peg < 1: peg_score = 80
        elif peg < 1.5: peg_score = 55
        elif peg < 2: peg_score = 30
        else: peg_score = 10
    elif earnings_growth > 0:
        peg_score = 20

    # 成长性评分 (25分)
    growth_score = 0
    if growth > 30: growth_score = 100
    elif growth > 20: growth_score = 80
    elif growth > 10: growth_score = 60
    elif growth > 5: growth_score = 40
    elif growth > 0: growth_score = 20

    # 财务健康评分 (25分)
    financial = 0
    if roe > 20: financial += 40
    elif roe > 15: financial += 30
    elif roe > 10: financial += 20
    if margin > 30: financial += 30
    elif margin > 20: financial += 20
    elif margin > 10: financial += 10
    if debt_ratio > 0 and debt_ratio < 30: financial += 20
    elif debt_ratio > 0 and debt_ratio < 50: financial += 10
    elif debt_ratio == 0: financial += 10  # 数据不足给基础分
    if div > 2: financial += 10
    financial = min(100, financial)

    # 估值评分 (20分)
    valuation = 0
    if 0 < pe < 10: valuation = 90
    elif pe < 15: valuation = 75
    elif pe < 20: valuation = 60
    elif pe < 25: valuation = 45
    elif pe < 35: valuation = 25
    elif pe > 0: valuation = 10

    total = round(peg_score * 0.30 + growth_score * 0.25 + financial * 0.25 + valuation * 0.20, 1)

    # === 5. 投资建议 ===
    reasons = []
    warnings = []

    # PEG分析
    if peg > 0 and peg < 1:
        reasons.append(f"✓ PEG={peg:.2f}<1，增长率({earnings_growth:.0f}%)高于PE({pe:.0f})，林奇认为是被低估的信号")
    elif peg > 2:
        warnings.append(f"✗ PEG={peg:.2f}>2，估值过高，增长率不足以支撑股价")

    # 分类建议
    if category == "快速增长型":
        if growth > 25:
            reasons.append(f"✓ 快速增长型：营收增长{growth:.0f}%，林奇最偏爱此类股票")
        if pe > 0 and pe < growth * 2:
            reasons.append("✓ 增长股估值合理，股价未完全反映增长潜力")
    elif category == "稳定增长型":
        reasons.append(f"✓ 稳定增长型：增长{growth:.0f}%，可在下跌时提供保护")
    elif category == "缓慢增长型":
        if div > 3:
            reasons.append(f"✓ 缓慢增长但股息丰厚({div:.1f}%)，适合稳健投资者")

    # 财务
    if roe > 20:
        reasons.append(f"✓ ROE={roe:.1f}%，资本使用效率出色")
    if margin > 30:
        reasons.append(f"✓ 毛利率{margin:.1f}%，盈利能力强劲")
    if debt_ratio > 0 and debt_ratio > 60:
        warnings.append(f"✗ 负债率{debt_ratio:.0f}%过高，林奇建议回避高负债公司")

    # 估值警告
    if pe > 40:
        warnings.append(f"✗ PE={pe:.0f}倍，估值偏高。林奇提醒：避免买入过热的股票")
    if pe < 0:
        warnings.append("✗ PE为负，公司处于亏损状态")
    # 数据缺失综合提醒
    missing = []
    if pe == 0: missing.append('PE')
    if roe == 0: missing.append('ROE')
    if growth == 0: missing.append('增长率')
    if margin == 0: missing.append('毛利率')
    if missing:
        warnings.append(f"⚠ 以下数据缺失：{', '.join(missing)}，PEG和部分评分基于默认值")

    if not reasons:
        reasons.append("需要进一步调研公司业务模式和行业前景")

    rating = "★★★★★ 十倍股潜力" if total >= 80 else "★★★★☆ 值得重仓" if total >= 65 else "★★★☆☆ 值得关注" if total >= 50 else "★★☆☆☆ 暂不推荐" if total >= 35 else "★☆☆☆☆ 建议回避"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating,
        "category": {"name": category, "description": category_desc},
        "peg": {"value": peg, "assessment": peg_assessment},
        "checklist": checklist, "checklist_score": score_13,
        "scores": {
            "total": total, "peg": round(peg_score, 1),
            "growth": round(growth_score, 1), "financial": round(financial, 1),
            "valuation": round(valuation, 1)
        },
        "reasons": reasons, "warnings": warnings
    })


def analyze_oneil(ticker, stock):
    """欧奈尔CAN SLIM分析方法 - 基于《笑傲股市》(第4版)
    C=当季每股收益、A=年度收益增长、N=新产品/新高/新管理层、
    S=供给与需求、L=领涨股还是落后股、I=机构认同度、M=市场走向
    """
    pe = stock.get('pe', 0) or 0
    roe = stock.get('roe', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0
    margin = stock.get('gross_margin', 0) or 0
    div = stock.get('dividend_yield', 0) or 0
    pb = stock.get('pb', 0) or 0
    price = stock.get('price', 0) or 0
    market_cap = stock.get('market_cap', 0) or 0
    earnings_growth = stock.get('earnings_growth', 0) or growth

    # === C: Current Quarterly Earnings Per Share ===
    # 欧奈尔要求当季EPS同比增长≥25%，最好加速增长
    c_score = 0
    c_detail = ""
    if earnings_growth >= 40:
        c_score = 100
        c_detail = f"EPS/营收增长{earnings_growth:.0f}%，远超25%标准，业绩加速增长"
    elif earnings_growth >= 25:
        c_score = 75
        c_detail = f"增长{earnings_growth:.0f}%，达到欧奈尔25%最低标准"
    elif earnings_growth >= 15:
        c_score = 45
        c_detail = f"增长{earnings_growth:.0f}%，未达25%标准但有增长"
    elif earnings_growth > 0:
        c_score = 20
        c_detail = f"增长{earnings_growth:.0f}%，增速偏低"
    else:
        c_score = 0
        c_detail = f"增长{earnings_growth:.0f}%，业绩下滑或亏损，C条件不达标"

    # === A: Annual Earnings Growth ===
    # 过去3-5年每年EPS增长≥25%，ROE≥17%
    a_score = 0
    a_detail = ""
    annual_ok = growth >= 25 and roe >= 17
    if growth >= 25 and roe >= 20:
        a_score = 100
        a_detail = f"增长{growth:.0f}%+ROE{roe:.0f}%，优质成长股"
    elif growth >= 25 or roe >= 17:
        a_score = 60
        a_detail = f"增长{growth:.0f}%, ROE{roe:.0f}%，部分达标"
    elif growth >= 10 and roe >= 12:
        a_score = 35
        a_detail = f"增长{growth:.0f}%, ROE{roe:.0f}%，基本面尚可但未达标准"
    else:
        a_score = 10
        a_detail = f"增长{growth:.0f}%, ROE{roe:.0f}%，长期增长不足"

    # === N: New Products, Management, Price Highs ===
    # 创新驱动 + 创新高（用增长率+毛利率间接判断产品竞争力）
    n_score = 0
    n_detail = ""
    if growth > 25 and margin > 40:
        n_score = 90
        n_detail = f"高增长({growth:.0f}%)+高毛利({margin:.0f}%)，可能有创新产品支撑"
    elif growth > 15 and margin > 30:
        n_score = 60
        n_detail = "增长和利润率体现一定产品竞争力"
    elif growth > 10:
        n_score = 35
        n_detail = "有一定增长，但创新特征不明显"
    else:
        n_score = 10
        n_detail = "增长平淡，缺乏明确创新催化剂"

    # === S: Supply and Demand ===
    # 欧奈尔偏好流通盘较小或有回购的股票
    s_score = 0
    s_detail = ""
    if market_cap > 0:
        cap_b = market_cap / 1e9
        if cap_b < 5:
            s_score = 90
            s_detail = f"市值{cap_b:.0f}亿美元，小盘股流动筹码少，易涨"
        elif cap_b < 20:
            s_score = 65
            s_detail = f"市值{cap_b:.0f}亿美元，中盘股"
        elif cap_b < 100:
            s_score = 40
            s_detail = f"市值{cap_b:.0f}亿美元，大盘股，涨幅可能有限"
        else:
            s_score = 20
            s_detail = f"市值{cap_b:.0f}亿美元，超大盘，欧奈尔更偏好中小盘"
    else:
        # 没有市值数据时用PE和PB间接判断
        if pe > 0 and pe < 30 and pb > 0 and pb < 5:
            s_score = 50
            s_detail = "市值数据缺失，估值水平适中"
        else:
            s_score = 40
            s_detail = "市值数据不足，无法精确判断"

    # === L: Leader or Laggard ===
    # 相对强度RS≥80，行业领导者。用ROE+增长率综合判断领导地位
    l_score = 0
    l_detail = ""
    if roe > 25 and growth > 20:
        l_score = 95
        l_detail = f"ROE{roe:.0f}%+增长{growth:.0f}%，具备行业领导者特征（RS可能>80）"
    elif roe > 20 and growth > 10:
        l_score = 70
        l_detail = f"ROE{roe:.0f}%表现优秀，可能是行业前列"
    elif roe > 15:
        l_score = 45
        l_detail = f"ROE{roe:.0f}%，竞争力中等"
    elif roe > 10:
        l_score = 25
        l_detail = f"ROE{roe:.0f}%，表现一般，可能是落后股"
    else:
        l_score = 10
        l_detail = f"ROE{roe:.0f}%，盈利能力弱，欧奈尔建议避开落后股"

    # === I: Institutional Sponsorship ===
    # 至少有几家优秀机构持有，且最近有增持。用分红+ROE间接判断
    i_score = 0
    i_detail = ""
    if roe > 15 and div > 0 and pe > 0 and pe < 35:
        i_score = 80
        i_detail = "高ROE+有分红+合理估值，可能受机构青睐"
    elif roe > 12 and pe > 0:
        i_score = 55
        i_detail = "基本面尚可，可能有机构持有"
    elif roe > 8:
        i_score = 30
        i_detail = "基本面一般，机构关注度可能较低"
    else:
        i_score = 10
        i_detail = "基本面偏弱，机构可能不感兴趣"

    # === M: Market Direction ===
    # 大盘处于确认的上升趋势。用宏观指标间接判断，给基础分
    m_score = 50
    m_detail = "市场方向需结合大盘走势判断（建议配合K线分析页面）"
    if growth > 15:
        m_score = 65
        m_detail = "公司高增长暗示行业景气，但需确认大盘走势"
    elif growth < 0:
        m_score = 30
        m_detail = "公司增长下滑，注意宏观环境是否转弱"

    # CAN SLIM通过情况
    canslim = {
        "C": {"score": c_score, "pass": c_score >= 60, "detail": c_detail},
        "A": {"score": a_score, "pass": a_score >= 60, "detail": a_detail},
        "N": {"score": n_score, "pass": n_score >= 60, "detail": n_detail},
        "S": {"score": s_score, "pass": s_score >= 60, "detail": s_detail},
        "L": {"score": l_score, "pass": l_score >= 60, "detail": l_detail},
        "I": {"score": i_score, "pass": i_score >= 60, "detail": i_detail},
        "M": {"score": m_score, "pass": m_score >= 60, "detail": m_detail},
    }

    match_count = sum(1 for v in canslim.values() if v["pass"])
    total = round(sum(v["score"] for v in canslim.values()) / 7, 1)

    reasons = []
    warnings = []
    for key, val in canslim.items():
        label = {"C": "当季业绩", "A": "年度增长", "N": "创新/新高", "S": "供需关系", "L": "行业领导", "I": "机构认同", "M": "大盘走势"}[key]
        if val["pass"]:
            reasons.append(f"✓ {key}={label}达标：{val['detail']}")
        else:
            warnings.append(f"✗ {key}={label}未达标：{val['detail']}")

    # 数据缺失提醒
    missing = []
    if pe == 0: missing.append('PE')
    if roe == 0: missing.append('ROE')
    if growth == 0 and earnings_growth == 0: missing.append('增长率')
    if margin == 0: missing.append('毛利率')
    if missing:
        warnings.append(f"⚠ 以下数据缺失：{', '.join(missing)}，相关评分基于默认值，结果供参考")

    # 欧奈尔买入规则提醒
    buy_rules = []
    if total >= 60:
        buy_rules.append("在股价突破整理形态（杯柄、双底）时买入")
        buy_rules.append("买入后设置7-8%止损线，严格执行")
        buy_rules.append("前3周涨幅超20%，至少持有8周")
    else:
        buy_rules.append("CAN SLIM条件不足，等待更好的买入机会")
        buy_rules.append("避免在大盘下跌趋势中买入")

    rating = "★★★★★ CAN SLIM全面达标" if match_count >= 6 else "★★★★☆ 高度符合" if match_count >= 5 else "★★★☆☆ 部分符合" if match_count >= 3 else "★★☆☆☆ 条件不足" if match_count >= 2 else "★☆☆☆☆ 不符合"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating,
        "canslim": canslim, "match_count": match_count,
        "scores": {"total": total},
        "reasons": reasons, "warnings": warnings, "buy_rules": buy_rules
    })


def analyze_graham(ticker, stock):
    """格雷厄姆价值投资分析方法 - 基于《证券分析》
    核心：7条防御型投资者选股准则、格雷厄姆数字、内在价值公式、安全边际
    """
    pe = stock.get('pe', 0) or 0
    pb = stock.get('pb', 0) or 0
    roe = stock.get('roe', 0) or 0
    div = stock.get('dividend_yield', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0
    margin = stock.get('gross_margin', 0) or 0
    price = stock.get('price', 0) or 0
    debt_ratio = stock.get('debt_ratio', 0) or 0
    current_ratio = stock.get('current_ratio', 0) or 0

    # 计算EPS（从PE和价格推算）
    eps = round(price / pe, 2) if pe > 0 and price > 0 else 0
    # 计算每股净资产（从PB和价格推算）
    bvps = round(price / pb, 2) if pb > 0 and price > 0 else 0

    # === 1. 格雷厄姆数字 (Graham Number) ===
    # GN = √(22.5 × EPS × BVPS)
    graham_number = 0
    gn_assessment = ""
    if eps > 0 and bvps > 0:
        graham_number = round(math.sqrt(22.5 * eps * bvps), 2)
        if price > 0:
            gn_ratio = price / graham_number
            if gn_ratio < 0.8:
                gn_assessment = f"股价(¥{price:.2f})大幅低于格雷厄姆数字(¥{graham_number:.2f})，显著低估"
            elif gn_ratio < 1.0:
                gn_assessment = f"股价(¥{price:.2f})低于格雷厄姆数字(¥{graham_number:.2f})，存在安全边际"
            elif gn_ratio < 1.2:
                gn_assessment = f"股价(¥{price:.2f})接近格雷厄姆数字(¥{graham_number:.2f})，估值合理"
            else:
                gn_assessment = f"股价(¥{price:.2f})高于格雷厄姆数字(¥{graham_number:.2f})，估值偏高"
        else:
            gn_assessment = f"格雷厄姆数字=¥{graham_number:.2f}，价格数据不足"
    else:
        gn_assessment = "EPS或每股净资产数据不足，无法计算格雷厄姆数字"

    # === 2. 内在价值公式 V = EPS × (8.5 + 2g) ===
    intrinsic_value = 0
    iv_assessment = ""
    margin_of_safety = 0
    if eps > 0 and growth > 0:
        g = min(growth, 30)  # 格雷厄姆建议限制增长率预期
        intrinsic_value = round(eps * (8.5 + 2 * g), 2)
        if price > 0:
            margin_of_safety = round((1 - price / intrinsic_value) * 100, 1) if intrinsic_value > 0 else 0
            if margin_of_safety > 30:
                iv_assessment = f"内在价值¥{intrinsic_value:.2f}，安全边际{margin_of_safety:.0f}%，格雷厄姆建议≥33%"
            elif margin_of_safety > 0:
                iv_assessment = f"内在价值¥{intrinsic_value:.2f}，安全边际{margin_of_safety:.0f}%，偏低"
            else:
                iv_assessment = f"内在价值¥{intrinsic_value:.2f}，当前股价高于内在价值，无安全边际"
    elif eps > 0:
        intrinsic_value = round(eps * 8.5, 2)  # 零增长情况
        iv_assessment = f"零增长内在价值¥{intrinsic_value:.2f}（增长率为0时的保守估值）"
    else:
        iv_assessment = "EPS数据不足，无法计算内在价值"

    # === 3. 防御型投资者7条准则 ===
    criteria = []

    # 1) 足够大的公司规模
    size_ok = True  # 上市公司默认满足
    criteria.append({"name": "①足够的公司规模", "pass": size_ok,
                     "detail": "已上市交易的公司，假设符合规模要求"})

    # 2) 足够强的财务状况（流动比率≥2）
    fin_ok = current_ratio >= 2 if current_ratio > 0 else (debt_ratio > 0 and debt_ratio < 50)
    criteria.append({"name": "②财务状况稳健",
                     "pass": fin_ok,
                     "detail": f"流动比率{current_ratio:.1f}" if current_ratio > 0 else f"负债率{debt_ratio:.0f}%" if debt_ratio > 0 else "财务数据不足"})

    # 3) 盈利稳定性（连续10年盈利）
    earn_ok = pe > 0 and roe > 5
    criteria.append({"name": "③盈利稳定性", "pass": earn_ok,
                     "detail": f"PE={pe:.1f}, ROE={roe:.1f}%，当前盈利" if earn_ok else "当前亏损或盈利极弱"})

    # 4) 股息记录（连续20年派息）
    div_ok = div > 0
    criteria.append({"name": "④持续分红记录", "pass": div_ok,
                     "detail": f"股息率{div:.2f}%，有分红" if div_ok else "未分红，不符合防御型标准"})

    # 5) 盈利增长（10年EPS增长≥33%）
    grow_ok = growth > 3  # 年化3%约等于10年33%
    criteria.append({"name": "⑤盈利有所增长", "pass": grow_ok,
                     "detail": f"增长{growth:.1f}%，{'保持增长' if grow_ok else '增长不足'}"})

    # 6) 适度的市盈率（PE≤15）
    pe_ok = 0 < pe <= 15
    criteria.append({"name": "⑥市盈率≤15倍", "pass": pe_ok,
                     "detail": f"PE={pe:.1f}倍，{'符合格雷厄姆标准' if pe_ok else '高于15倍标准'}" if pe > 0 else "PE数据异常"})

    # 7) 适度的市净率（PB≤1.5，或PE×PB≤22.5）
    pe_pb_product = pe * pb if pe > 0 and pb > 0 else 0
    pb_ok = (0 < pb <= 1.5) or (0 < pe_pb_product <= 22.5)
    criteria.append({"name": "⑦PE×PB≤22.5", "pass": pb_ok,
                     "detail": f"PB={pb:.2f}, PE×PB={pe_pb_product:.1f}，{'符合标准' if pb_ok else '超出22.5限制'}" if pb > 0 else "PB数据不足"})

    criteria_pass = sum(1 for c in criteria if c["pass"])

    # === 4. 综合评分 ===
    # 7条准则评分 (35分)
    criteria_score = round(criteria_pass / 7 * 100)

    # 安全边际评分 (30分)
    safety_score = 0
    if margin_of_safety > 50: safety_score = 100
    elif margin_of_safety > 33: safety_score = 85
    elif margin_of_safety > 20: safety_score = 65
    elif margin_of_safety > 10: safety_score = 45
    elif margin_of_safety > 0: safety_score = 30
    elif graham_number > 0 and price > 0 and price < graham_number:
        safety_score = 60
    elif pe > 0 and pe < 12 and pb > 0 and pb < 1:
        safety_score = 70
    elif pe > 0 and pe < 15:
        safety_score = 40
    else:
        safety_score = 15

    # 估值评分 (20分)
    value_score = 0
    if 0 < pe <= 10: value_score += 50
    elif pe <= 15: value_score += 35
    elif pe <= 20: value_score += 20
    if 0 < pb <= 1: value_score += 30
    elif pb <= 1.5: value_score += 20
    elif pb <= 2: value_score += 10
    if div > 4: value_score += 20
    elif div > 2: value_score += 15
    elif div > 0: value_score += 5
    value_score = min(100, value_score)

    # 财务质量评分 (15分)
    quality_score = 0
    if roe > 15: quality_score += 35
    elif roe > 10: quality_score += 25
    elif roe > 5: quality_score += 15
    if margin > 25: quality_score += 25
    elif margin > 15: quality_score += 15
    if debt_ratio > 0 and debt_ratio < 40: quality_score += 25
    elif debt_ratio > 0 and debt_ratio < 60: quality_score += 10
    elif debt_ratio == 0: quality_score += 15
    if div > 0: quality_score += 15
    quality_score = min(100, quality_score)

    total = round(criteria_score * 0.35 + safety_score * 0.30 + value_score * 0.20 + quality_score * 0.15, 1)

    # === 5. 投资建议 ===
    reasons = []
    warnings = []

    if criteria_pass >= 6:
        reasons.append(f"✓ 通过{criteria_pass}/7条防御型投资者准则，高度符合格雷厄姆标准")
    elif criteria_pass >= 4:
        reasons.append(f"✓ 通过{criteria_pass}/7条准则，部分符合格雷厄姆标准")

    if margin_of_safety > 30:
        reasons.append(f"✓ 安全边际{margin_of_safety:.0f}%，达到格雷厄姆建议的33%安全线")
    elif margin_of_safety > 0:
        warnings.append(f"安全边际仅{margin_of_safety:.0f}%，低于理想的33%")

    if graham_number > 0 and price > 0 and price < graham_number:
        reasons.append(f"✓ 股价低于格雷厄姆数字(¥{graham_number:.2f})，价值被低估")
    elif graham_number > 0 and price > 0:
        warnings.append(f"股价高于格雷厄姆数字(¥{graham_number:.2f})，估值偏高")

    if pe > 0 and pe <= 15 and pb > 0 and pe * pb <= 22.5:
        reasons.append(f"✓ PE={pe:.1f}×PB={pb:.1f}={pe*pb:.1f}≤22.5，估值达标")
    elif pe > 20:
        warnings.append(f"✗ PE={pe:.1f}倍远超格雷厄姆15倍标准")

    if div > 3:
        reasons.append(f"✓ 股息率{div:.1f}%，提供稳定现金回报")

    if pe < 0:
        warnings.append("✗ 公司处于亏损状态，格雷厄姆不建议买入亏损股")

    # 数据缺失提醒
    missing = []
    if pe == 0: missing.append('PE')
    if pb == 0: missing.append('PB')
    if roe == 0: missing.append('ROE')
    if growth == 0: missing.append('增长率')
    if missing:
        warnings.append(f"⚠ 以下数据缺失：{', '.join(missing)}，格雷厄姆数字和内在价值计算受限")

    if not reasons:
        reasons.append("当前不符合格雷厄姆的安全边际要求，建议等待价格回落")

    rating = "★★★★★ 价值洼地" if total >= 80 else "★★★★☆ 安全边际充足" if total >= 65 else "★★★☆☆ 估值合理" if total >= 50 else "★★☆☆☆ 安全边际不足" if total >= 35 else "★☆☆☆☆ 估值过高"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating,
        "graham_number": {"value": graham_number, "assessment": gn_assessment},
        "intrinsic_value": {"value": intrinsic_value, "margin_of_safety": margin_of_safety, "assessment": iv_assessment},
        "criteria": criteria, "criteria_pass": criteria_pass,
        "scores": {
            "total": total, "criteria": criteria_score,
            "safety": safety_score, "value": value_score, "quality": quality_score
        },
        "reasons": reasons, "warnings": warnings
    })


def analyze_comprehensive(ticker, stock):
    """综合所有书籍+蜡烛图+真规则的投资分析方法
    融合：彼得林奇(成长)、欧奈尔(动量)、格雷厄姆(价值)、马尔基尔(配置)、
    真规则(护城河)、蜡烛图(技术)、霍华德马克斯(风险)
    """
    pe = stock.get('pe', 0) or 0
    roe = stock.get('roe', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0
    margin = stock.get('gross_margin', 0) or 0
    div = stock.get('dividend_yield', 0) or 0
    pb = stock.get('pb', 0) or 0
    price = stock.get('price', 0) or 0
    debt_ratio = stock.get('debt_ratio', 0) or 0

    eps = round(price / pe, 2) if pe > 0 and price > 0 else 0
    bvps = round(price / pb, 2) if pb > 0 and price > 0 else 0

    # === 维度1: 成长性分析 (林奇视角) - 20% ===
    peg = pe / growth if pe > 0 and growth > 0 else 0
    growth_dim = 0
    if growth > 30: growth_dim += 40
    elif growth > 20: growth_dim += 30
    elif growth > 10: growth_dim += 20
    elif growth > 0: growth_dim += 10
    if 0 < peg < 1: growth_dim += 35
    elif 0 < peg < 1.5: growth_dim += 20
    elif 0 < peg < 2: growth_dim += 10
    if roe > 20: growth_dim += 25
    elif roe > 15: growth_dim += 15
    elif roe > 10: growth_dim += 8
    growth_dim = min(100, growth_dim)

    # === 维度2: 价值安全 (格雷厄姆视角) - 20% ===
    value_dim = 0
    if 0 < pe <= 10: value_dim += 35
    elif pe <= 15: value_dim += 25
    elif pe <= 20: value_dim += 15
    if 0 < pb <= 1: value_dim += 25
    elif pb <= 1.5: value_dim += 18
    elif pb <= 2: value_dim += 10
    if pe > 0 and pb > 0 and pe * pb <= 22.5: value_dim += 20
    if div > 3: value_dim += 15
    elif div > 1: value_dim += 8
    # 格雷厄姆数字
    if eps > 0 and bvps > 0:
        gn = math.sqrt(22.5 * eps * bvps)
        if price > 0 and price < gn: value_dim += 15
    value_dim = min(100, value_dim)

    # === 维度3: 动量质量 (欧奈尔视角) - 15% ===
    momentum_dim = 0
    if growth >= 25: momentum_dim += 30
    elif growth >= 15: momentum_dim += 20
    if roe >= 20: momentum_dim += 30
    elif roe >= 15: momentum_dim += 20
    if margin > 40: momentum_dim += 25
    elif margin > 25: momentum_dim += 15
    if growth > 25 and roe > 17: momentum_dim += 15  # CAN SLIM核心条件
    momentum_dim = min(100, momentum_dim)

    # === 维度4: 竞争优势/护城河 (真规则视角) - 15% ===
    moat_dim = 0
    # 持续高ROE是护城河的核心标志
    if roe > 25: moat_dim += 40
    elif roe > 20: moat_dim += 30
    elif roe > 15: moat_dim += 20
    elif roe > 10: moat_dim += 10
    # 高毛利率说明有定价权
    if margin > 60: moat_dim += 35
    elif margin > 40: moat_dim += 25
    elif margin > 25: moat_dim += 15
    # 低负债+有分红=财务护城河
    if debt_ratio > 0 and debt_ratio < 30: moat_dim += 15
    elif debt_ratio > 0 and debt_ratio < 50: moat_dim += 8
    elif debt_ratio == 0: moat_dim += 8
    if div > 2: moat_dim += 10
    moat_dim = min(100, moat_dim)

    # === 维度5: 风险控制 (马克斯视角) - 15% ===
    risk_dim = 0
    # 低PE=低预期=低风险
    if 0 < pe < 12: risk_dim += 30
    elif pe < 18: risk_dim += 20
    elif pe < 25: risk_dim += 10
    elif pe > 40: risk_dim -= 10
    # 低PB=有资产保护
    if 0 < pb < 1: risk_dim += 25
    elif pb < 1.5: risk_dim += 18
    elif pb < 2.5: risk_dim += 8
    # 有分红=有安全垫
    if div > 4: risk_dim += 25
    elif div > 2: risk_dim += 18
    elif div > 0.5: risk_dim += 8
    # 低负债=抗风险
    if debt_ratio > 0 and debt_ratio < 30: risk_dim += 15
    elif debt_ratio > 0 and debt_ratio < 50: risk_dim += 8
    elif debt_ratio == 0: risk_dim += 8
    if roe > 10 and growth > 0: risk_dim += 5  # 盈利且增长=基本面安全
    risk_dim = max(0, min(100, risk_dim))

    # === 维度6: 配置适合度 (马尔基尔视角) - 15% ===
    allocation_dim = 0
    # 基本面扎实
    if roe > 12 and margin > 15: allocation_dim += 30
    elif roe > 8: allocation_dim += 15
    # 估值合理
    if 0 < pe < 25: allocation_dim += 25
    elif 0 < pe < 35: allocation_dim += 12
    # 波动性适中（用增长率间接判断）
    if 0 < growth < 30: allocation_dim += 20
    # 有分红适合长期
    if div > 1: allocation_dim += 15
    elif div > 0: allocation_dim += 5
    # 适合组合配置
    if pe > 0 and roe > 8 and growth > 0: allocation_dim += 10
    allocation_dim = min(100, allocation_dim)

    # === 综合总分 ===
    total = round(
        growth_dim * 0.20 +
        value_dim * 0.20 +
        momentum_dim * 0.15 +
        moat_dim * 0.15 +
        risk_dim * 0.15 +
        allocation_dim * 0.15, 1
    )

    # === 投资风格判断 ===
    style = ""
    if growth_dim > 70 and value_dim < 40:
        style = "成长型"
    elif value_dim > 70 and growth_dim < 40:
        style = "价值型"
    elif growth_dim > 55 and value_dim > 55:
        style = "成长价值兼备 (GARP)"
    elif risk_dim > 65 and div > 2:
        style = "防御型"
    elif momentum_dim > 70:
        style = "动量型"
    else:
        style = "均衡型"

    # === 多维度诊断 ===
    dimensions = {
        "growth": {"score": growth_dim, "label": "成长性", "source": "林奇",
                   "level": "优秀" if growth_dim >= 70 else "良好" if growth_dim >= 50 else "一般" if growth_dim >= 30 else "偏弱"},
        "value": {"score": value_dim, "label": "价值安全", "source": "格雷厄姆",
                  "level": "优秀" if value_dim >= 70 else "良好" if value_dim >= 50 else "一般" if value_dim >= 30 else "偏弱"},
        "momentum": {"score": momentum_dim, "label": "业绩动量", "source": "欧奈尔",
                     "level": "优秀" if momentum_dim >= 70 else "良好" if momentum_dim >= 50 else "一般" if momentum_dim >= 30 else "偏弱"},
        "moat": {"score": moat_dim, "label": "竞争优势", "source": "真规则",
                 "level": "宽护城河" if moat_dim >= 70 else "窄护城河" if moat_dim >= 45 else "无护城河"},
        "risk": {"score": risk_dim, "label": "风险控制", "source": "马克斯",
                 "level": "低风险" if risk_dim >= 65 else "中风险" if risk_dim >= 40 else "高风险"},
        "allocation": {"score": allocation_dim, "label": "配置价值", "source": "马尔基尔",
                       "level": "核心持仓" if allocation_dim >= 70 else "卫星持仓" if allocation_dim >= 45 else "不建议配置"},
    }

    # === 综合建议 ===
    reasons = []
    warnings = []

    for key, dim in dimensions.items():
        if dim["score"] >= 70:
            reasons.append(f"✓ {dim['label']}({dim['source']})：{dim['level']}({dim['score']}分)")
        elif dim["score"] < 30:
            warnings.append(f"✗ {dim['label']}({dim['source']})：{dim['level']}({dim['score']}分)")

    # 特殊组合提醒
    if growth_dim > 60 and value_dim > 60:
        reasons.append("✓ 成长与价值兼备——林奇和格雷厄姆都会认可的标的")
    if moat_dim > 60 and risk_dim > 60:
        reasons.append("✓ 护城河深+风险低——适合长期核心持仓")
    if growth_dim > 70 and risk_dim < 30:
        warnings.append("⚠ 高成长但风险较高——马克斯提醒注意估值泡沫")
    if value_dim > 70 and momentum_dim < 25:
        warnings.append("⚠ 估值低但业绩缺乏动力——可能是价值陷阱")

    # 数据缺失提醒
    missing = []
    if pe == 0: missing.append('PE')
    if pb == 0: missing.append('PB')
    if roe == 0: missing.append('ROE')
    if growth == 0: missing.append('增长率')
    if margin == 0: missing.append('毛利率')
    if missing:
        warnings.append(f"⚠ 以下数据缺失：{', '.join(missing)}，部分维度评分基于默认值")

    if not reasons:
        reasons.append("综合评分偏低，建议进一步调研或等待更好机会")

    # PEG信息
    peg_info = f"PEG={peg:.2f}" if peg > 0 else "N/A"
    # 安全边际
    safety_info = ""
    if eps > 0 and bvps > 0:
        gn = math.sqrt(22.5 * eps * bvps)
        if price > 0:
            safety_pct = round((1 - price / gn) * 100, 1) if gn > 0 else 0
            safety_info = f"格雷厄姆安全边际: {safety_pct}%"

    rating = "★★★★★ 全方位优质" if total >= 80 else "★★★★☆ 重点关注" if total >= 65 else "★★★☆☆ 中性观望" if total >= 50 else "★★☆☆☆ 需要谨慎" if total >= 35 else "★☆☆☆☆ 建议回避"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating, "style": style,
        "dimensions": dimensions,
        "key_metrics": {"peg": peg_info, "safety": safety_info},
        "scores": {
            "total": total, "growth": growth_dim, "value": value_dim,
            "momentum": momentum_dim, "moat": moat_dim,
            "risk": risk_dim, "allocation": allocation_dim
        },
        "reasons": reasons, "warnings": warnings
    })


def analyze_marks(ticker, stock):
    """霍华德·马克斯风险分析"""
    pe = stock.get('pe', 0) or 0
    pb = stock.get('pb', 0) or 0
    roe = stock.get('roe', 0) or 0
    div = stock.get('dividend_yield', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0

    # 风险控制评分（低PE、低PB = 低风险）
    risk = 0
    if 0 < pe < 15: risk += 40
    elif 0 < pe < 25: risk += 25
    elif pe > 40: risk -= 10
    if 0 < pb < 1.5: risk += 30
    elif 0 < pb < 3: risk += 15
    if div > 3: risk += 30
    elif div > 1: risk += 15
    risk = max(0, min(100, risk))

    # 周期判断评分
    cycle = 0
    if growth > 15: cycle += 40
    elif growth > 5: cycle += 25
    elif growth < -5: cycle += 10
    if roe > 15: cycle += 35
    elif roe > 8: cycle += 20
    if 0 < pe < 20: cycle += 25
    cycle = min(100, cycle)

    # 安全边际评分
    margin = 0
    if 0 < pe < 12: margin += 40
    elif 0 < pe < 20: margin += 25
    if 0 < pb < 1: margin += 35
    elif 0 < pb < 2: margin += 20
    if div > 4: margin += 25
    elif div > 2: margin += 15
    margin = min(100, margin)

    total = round(risk * 0.4 + cycle * 0.3 + margin * 0.3, 1)

    reasons = []
    if risk > 60: reasons.append("✓ 风险水平可控，下行空间有限")
    if cycle > 50: reasons.append("✓ 处于有利的商业周期阶段")
    if margin > 50: reasons.append("✓ 具有较好的安全边际")
    if pe > 0 and pe < 20: reasons.append("✓ 估值处于合理区间")
    if div > 2: reasons.append("✓ 股息收益提供额外安全垫")
    if not reasons:
        reasons.append("当前风险收益比不够理想，建议等待更好时机")

    rating = "★★★★★ 风险极低" if total >= 75 else "★★★★☆ 风险可控" if total >= 60 else "★★★☆☆ 风险中等" if total >= 45 else "★★☆☆☆ 风险偏高"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating,
        "scores": {"total": total, "risk": round(risk, 1), "cycle": round(cycle, 1), "margin": round(margin, 1)},
        "reasons": reasons
    })


def analyze_candle(ticker, stock):
    """K线形态分析（基于基本面数据推断趋势）"""
    pe = stock.get('pe', 0) or 0
    roe = stock.get('roe', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0
    margin = stock.get('gross_margin', 0) or 0

    # 趋势强度（基于成长性）
    trend = 0
    if growth > 20: trend += 50
    elif growth > 10: trend += 35
    elif growth > 0: trend += 20
    if roe > 20: trend += 30
    elif roe > 10: trend += 20
    if margin > 40: trend += 20
    trend = min(100, trend)

    # 形态评分（基于估值合理性）
    pattern = 0
    if 0 < pe < 20: pattern += 45
    elif 0 < pe < 35: pattern += 30
    if roe > 15: pattern += 30
    if growth > 5: pattern += 25
    pattern = min(100, pattern)

    # 量价配合（基于综合指标）
    volume = 0
    if growth > 10 and roe > 10: volume += 40
    if margin > 30: volume += 30
    if 0 < pe < 30: volume += 30
    volume = min(100, volume)

    total = round(trend * 0.4 + pattern * 0.35 + volume * 0.25, 1)

    reasons = []
    if trend > 60: reasons.append("✓ 趋势向上，基本面支撑良好")
    if pattern > 50: reasons.append("✓ 估值形态合理，有上行空间")
    if volume > 50: reasons.append("✓ 各指标配合良好，信号一致")
    if growth > 15: reasons.append("✓ 高成长性支撑长期趋势")
    if not reasons:
        reasons.append("当前技术面信号不够明确，建议观望")

    rating = "★★★★★ 强势上涨" if total >= 75 else "★★★★☆ 趋势向好" if total >= 60 else "★★★☆☆ 震荡整理" if total >= 45 else "★★☆☆☆ 趋势偏弱"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating,
        "scores": {"total": total, "trend": round(trend, 1), "pattern": round(pattern, 1), "volume": round(volume, 1)},
        "reasons": reasons
    })


def analyze_malkiel(ticker, stock):
    """马尔基尔漫步分析 - 基于《漫步华尔街》(第10版)
    核心：坚实基础理论、4条估值法则、生命周期投资指南、随机漫步理论
    """
    pe = stock.get('pe', 0) or 0
    pb = stock.get('pb', 0) or 0
    roe = stock.get('roe', 0) or 0
    div = stock.get('dividend_yield', 0) or 0
    growth = stock.get('revenue_growth', 0) or 0
    margin = stock.get('gross_margin', 0) or 0
    price = stock.get('price', 0) or 0
    debt_ratio = stock.get('debt_ratio', 0) or 0

    # === 1. 坚实基础理论 (Firm Foundation) 估值 ===
    # 马尔基尔4条估值法则
    valuation_rules = []

    # 法则1: 增长率越高，合理PE越高（但PE不能无限高）
    rule1_pass = False
    rule1_detail = ""
    if growth > 0 and pe > 0:
        fair_pe = min(growth * 1.5, 40)  # 合理PE约为增长率的1-2倍，上限40
        if pe <= fair_pe:
            rule1_pass = True
            rule1_detail = f"增长{growth:.0f}%对应合理PE≤{fair_pe:.0f}，当前PE={pe:.0f}，估值合理"
        else:
            rule1_detail = f"增长{growth:.0f}%对应合理PE≤{fair_pe:.0f}，当前PE={pe:.0f}，可能高估"
    elif pe > 0:
        rule1_detail = f"增长率不足，PE={pe:.0f}需谨慎看待"
    else:
        rule1_detail = "PE或增长率数据不足"
    valuation_rules.append({"name": "法则1: 增长率决定合理PE", "pass": rule1_pass, "detail": rule1_detail})

    # 法则2: 增长持续时间越长越有价值
    rule2_pass = growth > 5 and roe > 10
    rule2_detail = f"ROE{roe:.0f}%{'持续盈利能力强' if rule2_pass else '盈利持续性存疑'}, 增长{growth:.0f}%"
    valuation_rules.append({"name": "法则2: 增长的持续性", "pass": rule2_pass, "detail": rule2_detail})

    # 法则3: 股息越高越有价值（尤其在利率较低时）
    rule3_pass = div > 2
    rule3_detail = f"股息率{div:.2f}%，{'股息回报可观' if div > 2 else '股息一般' if div > 0 else '未分红'}"
    valuation_rules.append({"name": "法则3: 股息回报率", "pass": rule3_pass, "detail": rule3_detail})

    # 法则4: 风险越低越有价值
    rule4_pass = False
    if pe > 0 and pe < 25 and (debt_ratio == 0 or debt_ratio < 50):
        rule4_pass = True
    rule4_detail = f"PE={pe:.0f}, " + (f"负债率{debt_ratio:.0f}%" if debt_ratio > 0 else "负债数据不足")
    rule4_detail += "，风险水平" + ("较低" if rule4_pass else "偏高")
    valuation_rules.append({"name": "法则4: 风险与合理价格", "pass": rule4_pass, "detail": rule4_detail})

    rules_pass = sum(1 for r in valuation_rules if r["pass"])

    # === 2. 坚实基础估值得分 (30%) ===
    foundation_score = 0
    if roe > 20: foundation_score += 25
    elif roe > 15: foundation_score += 20
    elif roe > 10: foundation_score += 12
    if growth > 15: foundation_score += 25
    elif growth > 8: foundation_score += 15
    elif growth > 0: foundation_score += 8
    if margin > 35: foundation_score += 20
    elif margin > 20: foundation_score += 12
    if div > 2: foundation_score += 15
    elif div > 0.5: foundation_score += 8
    if pe > 0 and pe < 20: foundation_score += 15
    elif pe > 0 and pe < 30: foundation_score += 8
    foundation_score = min(100, foundation_score)

    # === 3. 估值合理性得分 (25%) ===
    valuation_score = 0
    if 0 < pe <= 12: valuation_score += 40
    elif pe <= 18: valuation_score += 30
    elif pe <= 25: valuation_score += 18
    elif pe <= 35: valuation_score += 8
    if 0 < pb <= 1: valuation_score += 25
    elif pb <= 1.5: valuation_score += 18
    elif pb <= 2.5: valuation_score += 10
    if div > 3: valuation_score += 20
    elif div > 1.5: valuation_score += 12
    elif div > 0: valuation_score += 5
    # PEG
    if growth > 0 and pe > 0:
        peg = pe / growth
        if peg < 1: valuation_score += 15
        elif peg < 1.5: valuation_score += 8
    valuation_score = min(100, valuation_score)

    # === 4. 生命周期配置适合度 (25%) ===
    # 马尔基尔的生命周期投资建议：年轻人多股票，年长者多债券
    # 个股层面评估其在组合中的角色
    lifecycle_score = 0
    portfolio_role = ""

    if growth > 20 and pe > 0 and pe < 40:
        lifecycle_score += 35
        portfolio_role = "成长配置 — 适合年轻投资者重配"
    elif div > 3 and pe > 0 and pe < 20:
        lifecycle_score += 35
        portfolio_role = "收益配置 — 适合退休/保守投资者"
    elif roe > 12 and growth > 5 and pe > 0 and pe < 30:
        lifecycle_score += 30
        portfolio_role = "核心配置 — 适合各年龄段长期持有"
    elif div > 1 and roe > 8:
        lifecycle_score += 20
        portfolio_role = "卫星配置 — 可少量持有"
    else:
        lifecycle_score += 10
        portfolio_role = "不建议配置 — 考虑指数基金替代"

    if 0 < pe < 30: lifecycle_score += 20
    if roe > 10: lifecycle_score += 20
    if div > 0: lifecycle_score += 10
    if growth > 0 and growth < 50: lifecycle_score += 15  # 增长不极端
    lifecycle_score = min(100, lifecycle_score)

    # === 5. 随机漫步风险评估 (20%) ===
    # 马尔基尔认为市场接近有效，单股选择风险高
    random_walk_score = 0
    risk_level = ""

    # 基本面稳定性
    if roe > 15 and margin > 20 and growth > 5:
        random_walk_score += 40
        risk_level = "基本面扎实，抗随机波动"
    elif roe > 10 and growth > 0:
        random_walk_score += 25
        risk_level = "基本面尚可，有一定抗风险能力"
    else:
        random_walk_score += 10
        risk_level = "基本面偏弱，更建议选择指数基金"

    # 估值安全性
    if 0 < pe < 15 and pb > 0 and pb < 2:
        random_walk_score += 35
    elif 0 < pe < 25:
        random_walk_score += 20
    elif pe > 0:
        random_walk_score += 8

    # 分红保护
    if div > 2: random_walk_score += 15
    elif div > 0: random_walk_score += 8

    if debt_ratio > 0 and debt_ratio < 40: random_walk_score += 10
    elif debt_ratio == 0: random_walk_score += 5
    random_walk_score = min(100, random_walk_score)

    total = round(
        foundation_score * 0.30 +
        valuation_score * 0.25 +
        lifecycle_score * 0.25 +
        random_walk_score * 0.20, 1
    )

    # === 建议 ===
    reasons = []
    warnings = []

    if rules_pass >= 3:
        reasons.append(f"✓ 通过{rules_pass}/4条马尔基尔估值法则，坚实基础理论支持买入")
    elif rules_pass >= 2:
        reasons.append(f"通过{rules_pass}/4条估值法则，基本面有一定支撑")

    if foundation_score > 65:
        reasons.append(f"✓ 坚实基础评分{foundation_score}，公司质地优良")
    if lifecycle_score > 60:
        reasons.append(f"✓ {portfolio_role}")
    if div > 2:
        reasons.append(f"✓ 股息率{div:.1f}%，马尔基尔强调分红再投资的复利效应")

    # 数据缺失提醒
    missing = []
    if pe == 0: missing.append('PE')
    if pb == 0: missing.append('PB')
    if roe == 0: missing.append('ROE')
    if growth == 0: missing.append('增长率')
    if missing:
        warnings.append(f"⚠ 以下数据缺失：{', '.join(missing)}，估值法则判断受限")

    # 马尔基尔核心警告
    warnings.append("📖 马尔基尔建议：长期来看，大多数主动选股不如指数基金")
    if pe > 30:
        warnings.append(f"✗ PE={pe:.0f}倍偏高，马尔基尔警告高PE股票未来收益往往令人失望")
    if growth > 40:
        warnings.append(f"⚠ 增长{growth:.0f}%极高，马尔基尔提醒高增长难以长期维持")

    if not reasons:
        reasons.append("建议通过沪深300/标普500指数基金获得市场平均回报")

    rating = "★★★★★ 优质长持" if total >= 75 else "★★★★☆ 值得配置" if total >= 60 else "★★★☆☆ 可以持有" if total >= 45 else "★★☆☆☆ 不如指数" if total >= 30 else "★☆☆☆☆ 选指数基金"

    return jsonify({
        "code": ticker, "stock": stock, "rating": rating,
        "valuation_rules": valuation_rules, "rules_pass": rules_pass,
        "portfolio_role": portfolio_role, "risk_level": risk_level,
        "scores": {
            "total": total, "foundation": foundation_score,
            "valuation": valuation_score, "lifecycle": lifecycle_score,
            "random_walk": random_walk_score
        },
        "reasons": reasons, "warnings": warnings
    })


# ==================== 日本蜡烛图技术分析 ====================

def detect_candle_patterns(df):
    """基于《日本蜡烛图技术新解》全面检测K线形态
    覆盖: 单根K线、双根K线、三根K线、持续形态、窗口/跳空
    """
    patterns = []
    n = len(df)
    if n < 3:
        return patterns

    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    volumes = df['volume'].values if 'volume' in df.columns else np.zeros(n)
    dates = df['date'].values

    # 预计算均线用于趋势判断
    ma5 = pd.Series(closes).rolling(5).mean().values
    ma20 = pd.Series(closes).rolling(20).mean().values
    avg_body = pd.Series(np.abs(closes - opens)).rolling(20).mean().values
    avg_volume = pd.Series(volumes.astype(float)).rolling(20).mean().values

    def body(i):
        return abs(closes[i] - opens[i])

    def upper_shadow(i):
        return highs[i] - max(opens[i], closes[i])

    def lower_shadow(i):
        return min(opens[i], closes[i]) - lows[i]

    def total_range(i):
        return highs[i] - lows[i]

    def is_bullish(i):
        return closes[i] > opens[i]

    def is_bearish(i):
        return closes[i] < opens[i]

    def trend_at(i, lookback=10):
        """判断趋势: 1=上升, -1=下降, 0=横盘"""
        if i < lookback:
            return 0
        slope = (closes[i] - closes[i - lookback]) / closes[i - lookback] * 100
        if slope > 3:
            return 1
        elif slope < -3:
            return -1
        return 0

    def vol_ratio(i):
        """成交量相对均量比"""
        if i < 20 or avg_volume[i] == 0 or np.isnan(avg_volume[i]):
            return 1.0
        return volumes[i] / avg_volume[i]

    def is_small_body(i):
        """小实体（纺锤线级别）"""
        if np.isnan(avg_body[i]) or avg_body[i] == 0:
            return body(i) < total_range(i) * 0.3
        return body(i) < avg_body[i] * 0.5

    def add_pattern(idx, name, ptype, direction, reliability, desc):
        dt = pd.Timestamp(dates[idx])
        patterns.append({
            'index': int(idx),
            'date': dt.strftime('%Y-%m-%d'),
            'price': float(closes[idx]),
            'high': float(highs[idx]),
            'low': float(lows[idx]),
            'name': name,
            'type': ptype,
            'direction': direction,  # bullish / bearish / neutral
            'reliability': reliability,  # 1-5
            'description': desc,
            'volume_confirm': bool(vol_ratio(idx) > 1.2),
        })

    for i in range(2, n):
        tr = total_range(i)
        if tr == 0:
            continue
        b = body(i)
        us = upper_shadow(i)
        ls = lower_shadow(i)
        trend = trend_at(i)

        # ===== 第2章: 单根K线形态 =====

        # 大阳线 (Marubozu bullish)
        if is_bullish(i) and b > tr * 0.8 and not np.isnan(avg_body[i]) and b > avg_body[i] * 1.5:
            add_pattern(i, '大阳线', 'single', 'bullish', 3,
                        '强势上涨，实体占比大，多方主导')

        # 大阴线 (Marubozu bearish)
        if is_bearish(i) and b > tr * 0.8 and not np.isnan(avg_body[i]) and b > avg_body[i] * 1.5:
            add_pattern(i, '大阴线', 'single', 'bearish', 3,
                        '强势下跌，实体占比大，空方主导')

        # 锤子线 (Hammer) - 下跌趋势中出现
        if b > 0 and ls >= b * 2 and us < b * 0.3 and trend <= 0:
            rel = 4 if vol_ratio(i) > 1.2 else 3
            add_pattern(i, '锤子线', 'single', 'bullish', rel,
                        '下影线长度≥实体2倍，上影线极短。下跌趋势中的看涨反转信号')

        # 上吊线 (Hanging Man) - 上升趋势中出现
        if b > 0 and ls >= b * 2 and us < b * 0.3 and trend >= 1:
            add_pattern(i, '上吊线', 'single', 'bearish', 3,
                        '形态与锤子线相同，但出现在上升趋势中，为看跌反转信号。需次日确认')

        # 流星 (Shooting Star) - 上升趋势中
        if b > 0 and us >= b * 2 and ls < b * 0.3 and trend >= 1:
            add_pattern(i, '流星', 'single', 'bearish', 3,
                        '上影线长度≥实体2倍，下影线极短。上升趋势中的看跌反转信号')

        # 倒锤子 (Inverted Hammer) - 下跌趋势中
        if b > 0 and us >= b * 2 and ls < b * 0.3 and trend <= 0:
            add_pattern(i, '倒锤子', 'single', 'bullish', 2,
                        '上影线长度≥实体2倍，下影线极短。下跌趋势中的潜在看涨信号，需确认')

        # 十字线 (Doji)
        if b < tr * 0.05 and tr > 0:
            if us > tr * 0.3 and ls > tr * 0.3:
                add_pattern(i, '长腿十字线', 'single', 'neutral', 3,
                            '开盘价≈收盘价，上下影线都长。市场犹豫不决，可能变盘')
            elif us > tr * 0.6:
                add_pattern(i, '墓碑十字线', 'single', 'bearish', 4,
                            '开盘价≈收盘价≈最低价，长上影线。强烈看跌信号，尤其在上升趋势顶部')
            elif ls > tr * 0.6:
                add_pattern(i, '蜻蜓十字线', 'single', 'bullish', 4,
                            '开盘价≈收盘价≈最高价，长下影线。看涨信号，尤其在下跌趋势底部')
            else:
                add_pattern(i, '十字线', 'single', 'neutral', 2,
                            '开盘价≈收盘价，市场犹豫，可能即将变盘')

        # 纺锤线 (Spinning Top) - 只在趋势转折点才有意义
        elif (b < tr * 0.3 and b > tr * 0.05 and us > b and ls > b
              and not np.isnan(avg_body[i]) and tr > avg_body[i] * 0.8
              and (trend >= 1 or trend <= -1)):
            add_pattern(i, '纺锤线', 'single', 'neutral', 1,
                        '小实体，较长上下影线，多空双方力量均衡。出现在趋势中时可能预示变盘')

        # ===== 第3章: 双根K线形态 =====
        if i >= 1:
            prev_b = body(i - 1)
            prev_tr = total_range(i - 1)

            # 看涨吞没 (Bullish Engulfing)
            if (is_bearish(i - 1) and is_bullish(i) and
                    opens[i] <= closes[i - 1] and closes[i] >= opens[i - 1] and
                    b > prev_b and trend <= 0):
                rel = 5 if vol_ratio(i) > 1.3 else 4
                add_pattern(i, '看涨吞没', 'dual', 'bullish', rel,
                            '阳线实体完全包裹前一根阴线实体。下跌趋势中的强烈看涨反转信号')

            # 看跌吞没 (Bearish Engulfing)
            if (is_bullish(i - 1) and is_bearish(i) and
                    opens[i] >= closes[i - 1] and closes[i] <= opens[i - 1] and
                    b > prev_b and trend >= 1):
                rel = 5 if vol_ratio(i) > 1.3 else 4
                add_pattern(i, '看跌吞没', 'dual', 'bearish', rel,
                            '阴线实体完全包裹前一根阳线实体。上升趋势中的强烈看跌反转信号')

            # 乌云盖顶 (Dark Cloud Cover)
            if (is_bullish(i - 1) and is_bearish(i) and
                    opens[i] > highs[i - 1] and
                    closes[i] < (opens[i - 1] + closes[i - 1]) / 2 and
                    closes[i] > opens[i - 1] and trend >= 1):
                add_pattern(i, '乌云盖顶', 'dual', 'bearish', 4,
                            '阴线高开后收盘深入前一阳线实体50%以上。上升趋势中的看跌反转信号')

            # 刺透形态 (Piercing Pattern)
            if (is_bearish(i - 1) and is_bullish(i) and
                    opens[i] < lows[i - 1] and
                    closes[i] > (opens[i - 1] + closes[i - 1]) / 2 and
                    closes[i] < opens[i - 1] and trend <= 0):
                add_pattern(i, '刺透形态', 'dual', 'bullish', 4,
                            '阳线低开后收盘深入前一阴线实体50%以上。下跌趋势中的看涨反转信号')

            # 平头顶部 (Tweezers Top)
            if (abs(highs[i] - highs[i - 1]) < tr * 0.02 and
                    is_bullish(i - 1) and is_bearish(i) and trend >= 1):
                add_pattern(i, '平头顶部', 'dual', 'bearish', 3,
                            '连续两根K线最高价几乎相同，构成阻力位。看跌反转信号')

            # 平头底部 (Tweezers Bottom)
            if (abs(lows[i] - lows[i - 1]) < tr * 0.02 and
                    is_bearish(i - 1) and is_bullish(i) and trend <= 0):
                add_pattern(i, '平头底部', 'dual', 'bullish', 3,
                            '连续两根K线最低价几乎相同，构成支撑位。看涨反转信号')

        # ===== 第4章: 三根K线形态 =====
        if i >= 2:
            # 早晨之星 (Morning Star)
            day1_big = (body(i - 2) > avg_body[i] * 0.5) if not np.isnan(avg_body[i]) else (body(i - 2) > total_range(i - 2) * 0.5)
            day3_big = (body(i) > avg_body[i] * 0.5) if not np.isnan(avg_body[i]) else (body(i) > total_range(i) * 0.5)
            if is_bearish(i - 2) and day1_big and is_small_body(i - 1) and is_bullish(i) and day3_big:
                if closes[i] > (opens[i - 2] + closes[i - 2]) / 2 and trend <= 0:
                    if body(i - 1) < total_range(i - 1) * 0.05 and total_range(i - 1) > 0:
                        add_pattern(i, '早晨十字星', 'triple', 'bullish', 5,
                                    '下跌后大阴线+十字线+大阳线。比早晨之星更强烈的看涨反转信号')
                    else:
                        add_pattern(i, '早晨之星', 'triple', 'bullish', 5,
                                    '下跌后大阴线+小实体+大阳线。经典的看涨反转形态，可靠性高')

            # 黄昏之星 (Evening Star)
            if is_bullish(i - 2) and day1_big and is_small_body(i - 1) and is_bearish(i) and day3_big:
                if closes[i] < (opens[i - 2] + closes[i - 2]) / 2 and trend >= 1:
                    if body(i - 1) < total_range(i - 1) * 0.05 and total_range(i - 1) > 0:
                        add_pattern(i, '黄昏十字星', 'triple', 'bearish', 5,
                                    '上涨后大阳线+十字线+大阴线。比黄昏之星更强烈的看跌反转信号')
                    else:
                        add_pattern(i, '黄昏之星', 'triple', 'bearish', 5,
                                    '上涨后大阳线+小实体+大阴线。经典的看跌反转形态，可靠性高')

            # 三只乌鸦 (Three Black Crows)
            if (is_bearish(i - 2) and is_bearish(i - 1) and is_bearish(i) and
                    closes[i - 2] > closes[i - 1] > closes[i] and
                    opens[i - 1] < opens[i - 2] and opens[i - 1] > closes[i - 2] and
                    opens[i] < opens[i - 1] and opens[i] > closes[i - 1]):
                add_pattern(i, '三只乌鸦', 'triple', 'bearish', 5,
                            '连续三根大阴线，每根开盘在前一根实体内，收盘创新低。强烈看跌信号')

            # 三个白色武士/红三兵 (Three White Soldiers)
            if (is_bullish(i - 2) and is_bullish(i - 1) and is_bullish(i) and
                    closes[i - 2] < closes[i - 1] < closes[i] and
                    opens[i - 1] > opens[i - 2] and opens[i - 1] < closes[i - 2] and
                    opens[i] > opens[i - 1] and opens[i] < closes[i - 1]):
                add_pattern(i, '红三兵', 'triple', 'bullish', 5,
                            '连续三根大阳线，每根开盘在前一根实体内，收盘创新高。强烈看涨信号')

            # 弃婴形态 - 看涨 (Abandoned Baby Bullish)
            if (is_bearish(i - 2) and is_bullish(i) and
                    body(i - 1) < total_range(i - 1) * 0.05 and
                    highs[i - 1] < lows[i - 2] and highs[i - 1] < lows[i]):
                add_pattern(i, '看涨弃婴', 'triple', 'bullish', 5,
                            '大阴线+跳空十字星+跳空大阳线。极为罕见的强烈看涨反转信号')

            # 弃婴形态 - 看跌 (Abandoned Baby Bearish)
            if (is_bullish(i - 2) and is_bearish(i) and
                    body(i - 1) < total_range(i - 1) * 0.05 and
                    lows[i - 1] > highs[i - 2] and lows[i - 1] > highs[i]):
                add_pattern(i, '看跌弃婴', 'triple', 'bearish', 5,
                            '大阳线+跳空十字星+跳空大阴线。极为罕见的强烈看跌反转信号')

        # ===== 第5章: 持续形态 =====

        # 上升跳空窗口 (Gap Up)
        if i >= 1 and lows[i] > highs[i - 1] and trend >= 1:
            add_pattern(i, '向上跳空窗口', 'continuation', 'bullish', 3,
                        '价格向上跳空，形成支撑窗口。上升趋势中的持续信号')

        # 下降跳空窗口 (Gap Down)
        if i >= 1 and highs[i] < lows[i - 1] and trend <= 0:
            add_pattern(i, '向下跳空窗口', 'continuation', 'bearish', 3,
                        '价格向下跳空，形成阻力窗口。下跌趋势中的持续信号')

        # 上升三法 (Rising Three Methods) - 需要5根K线
        if i >= 4:
            day1 = i - 4
            d1_big = (body(day1) > avg_body[i] * 0.8) if not np.isnan(avg_body[i]) else (body(day1) > total_range(day1) * 0.5)
            if is_bullish(day1) and d1_big:
                mid_contained = True
                for j in range(day1 + 1, i):
                    if highs[j] > highs[day1] or lows[j] < lows[day1]:
                        mid_contained = False
                        break
                if mid_contained and is_bullish(i) and closes[i] > closes[day1]:
                    add_pattern(i, '上升三法', 'continuation', 'bullish', 4,
                                '大阳线后三根小K线在其范围内回调，最后大阳线突破。上升趋势持续信号')

        # 下降三法 (Falling Three Methods)
        if i >= 4:
            day1 = i - 4
            d1_big = (body(day1) > avg_body[i] * 0.8) if not np.isnan(avg_body[i]) else (body(day1) > total_range(day1) * 0.5)
            if is_bearish(day1) and d1_big:
                mid_contained = True
                for j in range(day1 + 1, i):
                    if highs[j] > highs[day1] or lows[j] < lows[day1]:
                        mid_contained = False
                        break
                if mid_contained and is_bearish(i) and closes[i] < closes[day1]:
                    add_pattern(i, '下降三法', 'continuation', 'bearish', 4,
                                '大阴线后三根小K线在其范围内反弹，最后大阴线突破。下跌趋势持续信号')

    return patterns


def calculate_western_indicators(df):
    """计算西方技术指标（第7章 - 蜡烛图与西方技术工具的融合）"""
    result = {}
    closes = df['close']
    n = len(df)

    # 均线
    ma5 = closes.rolling(5).mean()
    ma10 = closes.rolling(10).mean()
    ma20 = closes.rolling(20).mean()
    ma60 = closes.rolling(60).mean()
    result['ma5'] = ma5.fillna('').tolist()
    result['ma10'] = ma10.fillna('').tolist()
    result['ma20'] = ma20.fillna('').tolist()
    result['ma60'] = ma60.fillna('').tolist()

    # 均线趋势判断
    last = n - 1
    ma_analysis = []
    if not np.isnan(ma5.iloc[last]) and not np.isnan(ma20.iloc[last]):
        if ma5.iloc[last] > ma20.iloc[last]:
            ma_analysis.append('MA5在MA20上方，短期趋势偏多')
        else:
            ma_analysis.append('MA5在MA20下方，短期趋势偏空')
    if not np.isnan(ma20.iloc[last]) and not np.isnan(ma60.iloc[last]):
        if ma20.iloc[last] > ma60.iloc[last]:
            ma_analysis.append('MA20在MA60上方，中期趋势偏多')
        else:
            ma_analysis.append('MA20在MA60下方，中期趋势偏空')
    result['ma_analysis'] = ma_analysis

    # RSI
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - (100 / (1 + rs))).fillna(50)
    result['rsi'] = rsi.fillna('').tolist()
    rsi_val = rsi.iloc[last]
    if rsi_val > 70:
        result['rsi_analysis'] = f'RSI={rsi_val:.1f}，超买区域，注意回调风险'
    elif rsi_val < 30:
        result['rsi_analysis'] = f'RSI={rsi_val:.1f}，超卖区域，可能即将反弹'
    else:
        result['rsi_analysis'] = f'RSI={rsi_val:.1f}，中性区域'

    # MACD
    exp12 = closes.ewm(span=12, adjust=False).mean()
    exp26 = closes.ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    result['macd'] = macd.fillna('').tolist()
    result['macd_signal'] = signal.fillna('').tolist()
    result['macd_hist'] = histogram.fillna('').tolist()
    if macd.iloc[last] > signal.iloc[last]:
        result['macd_analysis'] = 'MACD金叉，偏多信号'
    else:
        result['macd_analysis'] = 'MACD死叉，偏空信号'

    # 布林带
    bb_mid = closes.rolling(20).mean()
    bb_std = closes.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    result['bb_upper'] = bb_upper.fillna('').tolist()
    result['bb_mid'] = bb_mid.fillna('').tolist()
    result['bb_lower'] = bb_lower.fillna('').tolist()
    last_close = closes.iloc[last]
    if not np.isnan(bb_upper.iloc[last]):
        if last_close > bb_upper.iloc[last]:
            result['bb_analysis'] = '价格突破布林带上轨，超买状态'
        elif last_close < bb_lower.iloc[last]:
            result['bb_analysis'] = '价格跌破布林带下轨，超卖状态'
        else:
            pct = (last_close - bb_lower.iloc[last]) / (bb_upper.iloc[last] - bb_lower.iloc[last]) * 100
            result['bb_analysis'] = f'价格位于布林带{pct:.0f}%位置'
    else:
        result['bb_analysis'] = '布林带数据不足'

    # 成交量分析
    if 'volume' in df.columns:
        vol = df['volume'].astype(float)
        vol_ma20 = vol.rolling(20).mean()
        result['volumes'] = vol.tolist()
        result['vol_ma20'] = vol_ma20.fillna('').tolist()
        if not np.isnan(vol_ma20.iloc[last]) and vol_ma20.iloc[last] > 0:
            vol_ratio = vol.iloc[last] / vol_ma20.iloc[last]
            if vol_ratio > 2:
                result['volume_analysis'] = f'成交量为均量{vol_ratio:.1f}倍，显著放量'
            elif vol_ratio > 1.3:
                result['volume_analysis'] = f'成交量为均量{vol_ratio:.1f}倍，温和放量'
            elif vol_ratio < 0.5:
                result['volume_analysis'] = f'成交量为均量{vol_ratio:.1f}倍，明显缩量'
            else:
                result['volume_analysis'] = f'成交量为均量{vol_ratio:.1f}倍，正常水平'
        else:
            result['volume_analysis'] = '成交量数据不足'
    else:
        result['volumes'] = []
        result['vol_ma20'] = []
        result['volume_analysis'] = '无成交量数据'

    return result


def generate_candle_conclusion(patterns, indicators, df):
    """综合蜡烛图形态和技术指标，生成分析结论（第8章 - 风险管理视角）"""
    conclusion = {
        'overall_direction': 'neutral',
        'confidence': 0,
        'summary': '',
        'signals': [],
        'risk_notes': [],
    }

    bullish_score = 0
    bearish_score = 0

    # 只看最近20根K线内的形态
    recent_patterns = [p for p in patterns if p['index'] >= len(df) - 20]

    for p in recent_patterns:
        weight = p['reliability']
        if p['volume_confirm']:
            weight *= 1.5
        if p['direction'] == 'bullish':
            bullish_score += weight
        elif p['direction'] == 'bearish':
            bearish_score += weight

    # 加入技术指标权重
    for a in indicators.get('ma_analysis', []):
        if '偏多' in a:
            bullish_score += 2
        elif '偏空' in a:
            bearish_score += 2

    rsi_a = indicators.get('rsi_analysis', '')
    if '超买' in rsi_a:
        bearish_score += 3
    elif '超卖' in rsi_a:
        bullish_score += 3

    macd_a = indicators.get('macd_analysis', '')
    if '金叉' in macd_a:
        bullish_score += 2
    elif '死叉' in macd_a:
        bearish_score += 2

    bb_a = indicators.get('bb_analysis', '')
    if '超买' in bb_a:
        bearish_score += 2
    elif '超卖' in bb_a:
        bullish_score += 2

    total = bullish_score + bearish_score
    if total > 0:
        conclusion['confidence'] = abs(bullish_score - bearish_score) / total * 100

    if bullish_score > bearish_score * 1.5:
        conclusion['overall_direction'] = 'bullish'
        conclusion['summary'] = '综合蜡烛图形态和技术指标分析，当前偏多信号明显'
    elif bearish_score > bullish_score * 1.5:
        conclusion['overall_direction'] = 'bearish'
        conclusion['summary'] = '综合蜡烛图形态和技术指标分析，当前偏空信号明显'
    elif total > 0:
        conclusion['overall_direction'] = 'neutral'
        conclusion['summary'] = '多空信号交织，建议观望等待明确方向'
    else:
        conclusion['summary'] = '近期无明显蜡烛图形态信号，建议结合其他分析方法'

    # 生成具体信号列表
    if recent_patterns:
        bullish_pats = [p for p in recent_patterns if p['direction'] == 'bullish']
        bearish_pats = [p for p in recent_patterns if p['direction'] == 'bearish']
        if bullish_pats:
            names = ', '.join(set(p['name'] for p in bullish_pats))
            conclusion['signals'].append(f'看涨形态: {names}')
        if bearish_pats:
            names = ', '.join(set(p['name'] for p in bearish_pats))
            conclusion['signals'].append(f'看跌形态: {names}')

    conclusion['signals'].append(indicators.get('rsi_analysis', ''))
    conclusion['signals'].append(indicators.get('macd_analysis', ''))
    conclusion['signals'].append(indicators.get('bb_analysis', ''))
    conclusion['signals'].append(indicators.get('volume_analysis', ''))
    conclusion['signals'].extend(indicators.get('ma_analysis', []))

    # 风险提示（第8章）
    last_close = df['close'].iloc[-1]
    if 'volume' in df.columns:
        vol_series = df['volume'].astype(float)
        avg_vol = vol_series.tail(20).mean()
        if avg_vol > 0 and vol_series.iloc[-1] < avg_vol * 0.3:
            conclusion['risk_notes'].append('成交量极度萎缩，流动性风险较高')

    returns = df['close'].pct_change().tail(20)
    volatility = returns.std() * np.sqrt(252) * 100
    if volatility > 50:
        conclusion['risk_notes'].append(f'近期年化波动率{volatility:.0f}%，波动较大，注意仓位控制')

    # 止损建议
    recent_lows = df['low'].tail(10).min()
    stop_loss_pct = (last_close - recent_lows) / last_close * 100
    conclusion['risk_notes'].append(f'建议止损位参考近10日最低价{recent_lows:.2f}（约-{stop_loss_pct:.1f}%）')

    return conclusion


@app.route('/api/candle_analysis')
def api_candle_analysis():
    """蜡烛图技术全面分析API"""
    ticker = request.args.get('ticker', '')
    market = request.args.get('market', 'A')
    days = int(request.args.get('days', 120))

    if not ticker:
        return jsonify({'success': False, 'message': '请输入股票代码'})

    try:
        if market == 'A':
            df = get_a_stock_data(ticker, days)
        else:
            df = get_us_stock_data(ticker, days)

        if df is None or df.empty:
            return jsonify({'success': False, 'message': '无法获取数据，请检查股票代码'})

        # 检测所有蜡烛图形态
        patterns = detect_candle_patterns(df)

        # 计算西方技术指标
        indicators = calculate_western_indicators(df)

        # 生成综合结论
        conclusion = generate_candle_conclusion(patterns, indicators, df)

        # 准备OHLCV数据
        ohlcv = {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'opens': df['open'].tolist(),
            'highs': df['high'].tolist(),
            'lows': df['low'].tolist(),
            'closes': df['close'].tolist(),
        }

        return jsonify({
            'success': True,
            'ticker': ticker,
            'ohlcv': ohlcv,
            'patterns': patterns,
            'indicators': indicators,
            'conclusion': conclusion,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'分析失败: {str(e)}'})


if __name__ == '__main__':
    print("=" * 60)
    print("量化策略推荐系统 Web")
    print("访问: http://localhost:5001")
    print("登录: root / 1root2378")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
