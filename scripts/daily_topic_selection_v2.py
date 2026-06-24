#!/usr/bin/env python3
"""
公众号每日选题提议 V2.0
多源搜索：东方财富MX → 东方财富新闻 → 东方财富公告 → 新浪财经7x24
降级链：MX额度耗尽时自动跳过，逐级降级到备用源
"""

import os
import sys
import json
import requests
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", str(Path.home() / ".openclaw" / "workspace")))
MEMORY_DIR = WORKSPACE_DIR / 'memory'
ARTICLES_DIR = WORKSPACE_DIR / 'articles'
MX_APIKEY = os.getenv('MX_APIKEY')
SKILL_DIR = Path(os.getenv("SKILL_DIR", str(Path.home() / ".qclaw" / "skills" / "investment-knowledge")))
QUERY_SCRIPT = SKILL_DIR / 'scripts' / 'query.py'

# 9大领域（用户指定）
FIELDS = ['OLED显示', '机器人', '存储', '半导体', '封装', '先进封装', 'CPO', 'Agent AI', '物理AI']

# 领域关键词映射
FIELD_KEYWORDS = {
    'OLED显示': ['OLED', '显示', '面板', '柔性屏', 'MicroLED', 'AMOLED', 'LCD'],
    '机器人': ['人形机器人', '机器人', '减速器', '伺服', '丝杠', '灵巧手', '具身智能'],
    '存储': ['DRAM', 'NAND', 'HBM', '存储', '内存', 'SSD'],
    '半导体': ['半导体', '芯片', '晶圆', 'EDA', '设备', '材料'],
    '封装': ['封装', '封测', '键合', '引线框架', '基板'],
    '先进封装': ['先进封装', 'CoWoS', 'Chiplet', 'HBM封装', '玻璃基板', 'TSV', 'RDL'],
    'CPO': ['CPO', '光模块', '光通信', '硅光子', '光电共封装', '光互连'],
    'Agent AI': ['Agent', 'AI应用', '大模型', '多模态', 'AI Agent'],
    '物理AI': ['物理AI', '具身智能', '机器人AI', '端侧AI', '边缘AI']
}

# MX API状态标记
mx_api_available = True


def mx_search(query: str) -> list:
    """调用东方财富MX搜索接口"""
    global mx_api_available
    
    if not mx_api_available:
        return []
    
    url = "https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search"
    headers = {
        "Content-Type": "application/json",
        "apikey": MX_APIKEY
    }
    data = {"query": query, "apikey": MX_APIKEY}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if result.get('status') == 113:
            print(f"  ⚠️ MX API调用次数已达上限，切换到其他搜索源")
            mx_api_available = False
            return []
        
        if result.get("data", {}).get("data", {}).get("llmSearchResponse", {}).get("data"):
            return result["data"]["data"]["llmSearchResponse"]["data"]
        return []
    except Exception as e:
        print(f"  ⚠️ MX搜索失败: {e}")
        mx_api_available = False
        return []


def eastmoney_news_search(query: str) -> list:
    """东方财富新闻搜索（使用搜索API）"""
    try:
        import urllib.parse
        keyword = query.split()[0] if query.split() else query
        param = json.dumps({
            'uid': '',
            'keyword': keyword,
            'type': ['cmsArticleWebOld'],
            'client': 'web',
            'clientType': 'web',
            'clientVersion': 'curr',
            'param': {
                'cmsArticleWebOld': {
                    'searchScope': 'default',
                    'sort': 'default',
                    'pageIndex': 1,
                    'pageSize': 10,
                    'preTag': '',
                    'postTag': ''
                }
            }
        })
        url = f"https://search-api-web.eastmoney.com/search/jsonp?cb=callback&param={urllib.parse.quote(param)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        # 解析JSONP响应
        text = response.text
        json_str = text[text.index('(') + 1:text.rindex(')')]
        data = json.loads(json_str)
        
        if data.get('result', {}).get('cmsArticleWebOld'):
            return [{'title': item.get('title', ''), 'content': item.get('content', ''), 'date': item.get('date', '')}
                    for item in data['result']['cmsArticleWebOld'][:5]]
        return []
    except Exception as e:
        print(f"  ⚠️ 东方财富新闻搜索失败: {e}")
        return []


def eastmoney_ann_search(query: str) -> list:
    """东方财富公告搜索（使用公告API）- 只返回与关键词相关的公告"""
    try:
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
        params = {
            'cb': 'callback',
            'sr': '-1',
            'page_size': '50',
            'page_index': '1',
            'ann_type': 'A',
            'client_source': 'web',
            'f_node': '0',
            's_node': '0'
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        text = response.text
        json_str = text[text.index('(') + 1:text.rindex(')')]
        data = json.loads(json_str)
        
        if data.get('data', {}).get('list'):
            # 过滤与关键词相关的公告
            keyword = query.split()[0] if query.split() else query
            filtered = [item for item in data['data']['list'] if keyword in item.get('title', '')]
            return [{'title': item.get('title', ''), 'content': '', 'date': item.get('display_time', '')}
                    for item in filtered[:5]]
        return []
    except Exception as e:
        print(f"  ⚠️ 东方财富公告搜索失败: {e}")
        return []


def sina_news_search(query: str) -> list:
    """新浪财经7x24小时新闻搜索（通用新闻）"""
    try:
        # 获取多页新闻
        all_items = []
        for page in range(1, 4):  # 获取前3页
            url = f"https://zhibo.sina.com.cn/api/zhibo/feed?page={page}&page_size=20&zhibo_id=152&tag_id=0"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()
            
            if data.get('result', {}).get('data', {}).get('feed', {}).get('list'):
                all_items.extend(data['result']['data']['feed']['list'])
        
        if all_items:
            # 过滤与关键词相关的新闻（更宽松的匹配）
            keyword = query.split()[0] if query.split() else query
            # 扩展关键词匹配（中文关键词可能被拆分）
            keywords_to_match = [keyword]
            if len(keyword) > 1:
                keywords_to_match.extend([keyword[:2], keyword[2:]])
            
            filtered = []
            for item in all_items:
                text = item.get('rich_text', '')
                if any(kw in text for kw in keywords_to_match if kw):
                    filtered.append(item)
            
            return [{'title': item.get('rich_text', '')[:100], 'content': '', 'date': item.get('create_time', '')}
                    for item in filtered[:5]]
        return []
    except Exception as e:
        print(f"  ⚠️ 新浪财经搜索失败: {e}")
        return []





def get_recent_topics_and_keywords():
    """获取近7天已写角度和关键词（去重检查用）"""
    topics = []
    keywords = []
    companies = []
    today = datetime.now()
    
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        memory_file = MEMORY_DIR / f"{date_str}.md"
        
        if memory_file.exists():
            content = memory_file.read_text(encoding='utf-8')
            title_matches = re.findall(r'### .+', content)
            topics.extend([t.replace('### ', '') for t in title_matches])
            kw_matches = re.findall(r'【(.+?)】', content)
            keywords.extend(kw_matches)
    
    if ARTICLES_DIR.exists():
        for f in ARTICLES_DIR.glob('*.html'):
            if f.stat().st_mtime > (datetime.now() - timedelta(days=7)).timestamp():
                content = f.read_text(encoding='utf-8')
                company_matches = re.findall(r'color:#2D5A8A;font-weight:700;">(.+?)</span>', content)
                companies.extend(company_matches)
    
    return {
        'topics': topics[:20],
        'keywords': list(set(keywords))[:30],
        'companies': list(set(companies))[:30]
    }


def search_field_hotspots(field: str) -> list:
    """搜索某个领域的热点资讯（多源搜索）"""
    keywords = FIELD_KEYWORDS.get(field, [field])
    all_news = []
    
    for keyword in keywords[:2]:
        query = f"{keyword} 最新动态 2026年"
        
        # 多源搜索：优先级从高到低（已移除搜狗/百度，触发验证码无法使用）
        news = mx_search(query)  # 1. 东方财富MX（最权威，有每日调用上限）
        if not news:
            news = eastmoney_news_search(query)  # 2. 东方财富新闻搜索API（稳定）
        if not news:
            news = eastmoney_ann_search(query)  # 3. 东方财富公告（稳定）
        if not news:
            news = sina_news_search(query)  # 4. 新浪财经7x24小时新闻（稳定）
        
        all_news.extend(news[:3])
    
    return all_news[:5]


def dedup_check(candidate_title: str, candidate_content: str, recent_data: dict) -> dict:
    """去重检查"""
    result = {
        'passed': True,
        'reason': '',
        'score_penalty': 0
    }
    
    for company in recent_data['companies']:
        if company in candidate_title:
            result['passed'] = False
            result['reason'] = f'公司名{company}近7天已出现'
            return result
    
    for kw in recent_data['keywords']:
        if kw in candidate_title and kw in str(recent_data['topics']):
            result['score_penalty'] += 1
            result['reason'] = f'关键词{kw}近7天已出现'
    
    for topic in recent_data['topics']:
        common_chars = set(candidate_title) & set(topic)
        if len(common_chars) > len(candidate_title) * 0.5:
            result['score_penalty'] += 1
            result['reason'] = f'与"{topic[:20]}..."逻辑相似'
    
    return result


def score_topic(news: dict, recent_data: dict) -> dict:
    """五维度评分"""
    title = news.get('title', '')
    content = news.get('content', '')
    date = news.get('date', '')
    
    if '今天' in date or datetime.now().strftime('%Y-%m-%d') in date:
        timeliness = 5
    elif '昨天' in date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') in date:
        timeliness = 4
    elif any((datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') in date for i in range(2, 4)):
        timeliness = 3
    elif any((datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') in date for i in range(4, 8)):
        timeliness = 2
    else:
        timeliness = 1
    
    investment_keywords = ['受益', '龙头', '订单', '业绩', '增长', '涨停', '机构', '突破', '量产', '涨价']
    investment_score = sum(1 for kw in investment_keywords if kw in title + content)
    investment_clarity = min(5, max(1, 2 + investment_score))
    
    reader_keywords = ['散户', '投资', '机会', '风险', '涨价', '缺货', '概念股', '龙头股']
    reader_score = sum(1 for kw in reader_keywords if kw in title + content)
    reader_resonance = min(5, max(1, 2 + reader_score))
    
    novelty = 5
    for topic in recent_data['topics'][:10]:
        common_words = set(title.split()) & set(topic.split())
        if len(common_words) > 2:
            novelty = max(1, novelty - 2)
    
    dedup = dedup_check(title, content, recent_data)
    if not dedup['passed']:
        return None
    novelty = max(1, novelty - dedup['score_penalty'])
    
    total = (
        timeliness * 0.3 +
        investment_clarity * 0.3 +
        reader_resonance * 0.2 +
        novelty * 0.2
    )
    
    return {
        'timeliness': timeliness,
        'investment_clarity': investment_clarity,
        'reader_resonance': reader_resonance,
        'novelty': novelty,
        'total': round(total, 1)
    }



def generate_article_title(news: dict) -> str:
    """根据新闻生成公众号文章标题（爆款公式 V3 - 学习高阅读量标题）
    
    高阅读量标题特征：
    1. 必须有具体公司名或产品名（不能只有"龙头""板块"）
    2. 必须有具体数字（涨幅/金额/数量/倍数）
    3. 事件要具体（"20%涨停"比"爆发"有力，"量产交付"比"突破"具体）
    4. 制造冲突/悬念/颠覆认知（逗号转折、问号、感叹号）
    
    好标题示例：
    - 中船特气20%涨停！半导体板块集体拉升
    - 人形机器人龙头宇树科技的商业化硬仗
    - 三星旗舰屏，首次用中国造
    - 订单排到2027年！中国光模块厂商闷声发大财
    - HBM订单爆了！这两家公司躺着数钱
    """
    title = news.get('title', '')
    content = news.get('content', '')
    text = title + ' ' + content

    # ====== 提取关键信息 ======

    # 1. 提取公司名（优先匹配具体公司，排除泛称）
    company = ''
    NON_COMPANY = ['机构', '据', '今日', '截至', '盘中', '收盘', '盘面', '板块', '大盘', '市场', '行业', '全球', '国内', '海外', '龙头', '概念股', 'ETF']
    company_patterns = [
        r'([\u4e00-\u9fa5]{2,8})(?:股份|科技|发展|集团|电子|光电|材料|设备|精密|控股|实业|新材|半导体|集成)',
        r'([\u4e00-\u9fa5]{2,6})(?:：|:|发布|公告|涨停|暴跌|大涨|大跌|涨超|跌超|年内|盘中|收涨|收跌)',
    ]
    for pattern in company_patterns:
        m = re.search(pattern, title)
        if m:
            candidate = m.group(1)
            if candidate not in NON_COMPANY and len(candidate) >= 2:
                company = candidate
                break

    # 2. 提取具体数字（优先从标题提取，排除ETF/基金等无关数字）
    numbers_in_title = re.findall(r'\d+\.?\d*[万亿%倍]', title)
    numbers_in_text = re.findall(r'\d+\.?\d*[万亿%倍]', text)
    # 排除ETF相关的百分比（如"下跌1.87%"这种无关数据）
    all_numbers = numbers_in_title  # 优先用标题中的数字
    if not all_numbers:
        # 从正文中提取，但排除小百分比（<5%的通常是ETF涨跌，不是核心事件）
        all_numbers = [n for n in numbers_in_text if not (n.endswith('%') and float(n.replace('%','')) < 5)]
    number = all_numbers[0] if all_numbers else ''

    # 3. 提取领域关键词
    field = ''
    field_priority = ['CPO', 'OLED', 'HBM', 'DRAM', '半导体', '机器人', '存储', '封装', '光模块', '面板', '芯片', 'AI']
    for f in field_priority:
        if f in text:
            field = f
            break

    # 4. 提取事件 + 判断正负面
    event = ''
    is_negative = False
    event_rules = [
        ('暴跌', ['暴跌', '大跌', '下挫', '收跌', '走低', '闪崩'], True),
        ('回调', ['回调', '调整', '回落'], True),
        ('涨停', ['涨停', '一字涨停', '20cm涨停'], False),
        ('量产', ['量产', '投产', '批量交付', '出货', '量产交付'], False),
        ('涨价', ['涨价', '价格上涨', '涨价潮', '涨价预期'], False),
        ('突破', ['突破', '创新高', '新纪录', '首次', '首次实现'], False),
        ('订单', ['订单', '爆单', '中标', '签约', '签订'], False),
        ('业绩', ['营收', '业绩', '利润', '增长', '盈利', '净利'], False),
        ('入局', ['入局', '布局', '进军', '切入', '加码'], False),
        ('调研', ['调研', '机构调研', '被调研'], False),
        ('过会', ['过会', 'IPO', '上市', '获批'], False),
    ]
    for event_name, keywords, negative in event_rules:
        if any(kw in text for kw in keywords):
            event = event_name
            is_negative = negative
            break

    # 5. 提取"谁受益"信息
    beneficiary = ''
    benefit_patterns = [r'受益[标的方股]?(?:为|是|：)?([^，。,.\\s]+)', r'([^，。,.\\s]+)(?:受益|有望受益)']
    for bp in benefit_patterns:
        bm = re.search(bp, text)
        if bm:
            beneficiary = bm.group(1).strip()[:15]
            break

    # ====== 标题公式（学习高阅读量公众号标题风格 V4.0） ======
    # 高阅读量标题特征：
    # 1. 重复强调："涨停!涨停!涨停!" - 通过重复增强冲击力
    # 2. 数字+事件："3.5万亿板块突然爆了!"
    # 3. 转折+悬念："创历史新高" + "却有股崩60%"
    # 4. 情绪词："突然爆了"、"大喊活不下去了"
    # 5. 问号引发思考："你信吗?"、"还能抄底吗?"
    # 6. 叹号增强语气："突然!"、"刚刚!"
    formulas = []

    if is_negative:
        # ❌ 负面事件标题（悬念+痛点）
        if company and number:
            formulas.append(f"{company}{number}！{field or '板块'}还能抄底吗")
            formulas.append(f"{company}暴跌{number}！{field or '板块'}大跳水")
        if company and event:
            formulas.append(f"{company}{event}！{field or '板块'}怎么了")
            formulas.append(f"突发！{company}{event}，{field or '板块'}承压")
        if number and field:
            formulas.append(f"{number}！{field}板块集体回调，这次不一样？")
            formulas.append(f"刚刚！{field}暴跌{number}，发生了什么")
        if company:
            formulas.append(f"{company}崩了！{field or '板块'}大变局")
            formulas.append(f"太罕见！{company}大跌，{field or '板块'}何去何从")
        formulas.extend([
            f"突然！{field or '板块'}集体回调，{company or '龙头'}领跌",
            f"{company or '龙头'}暴跌！{field or '板块'}还能抄底吗",
            f"深夜利空！{field or '板块'}大跳水，{company or '龙头'}崩了",
        ])
    else:
        # ✅ 正面事件标题（重复+数字+情绪）
        if company and number and event:
            formulas.append(f"{company}{event}！{number}，{field or '板块'}爆发")
            formulas.append(f"刚刚！{company}{event}{number}，{field or '板块'}炸了")
        if company and event:
            formulas.append(f"{company}{event}！{field or '板块'}龙头爆发")
            formulas.append(f"突然！{company}{event}，{field or '板块'}大变局")
            formulas.append(f"太猛了！{company}{event}，{field or '板块'}炸锅")
        if number and field and event:
            formulas.append(f"{number}！{field}{event}，这次真的爆发了")
            formulas.append(f"{field}{event}{number}！板块集体涨停？")
        if company and field:
            formulas.append(f"{company}入局{field}！{field or '板块'}变天了")
            formulas.append(f"刚刚！{company}加码{field}，产业链要爆发")
        if beneficiary and event:
            formulas.append(f"{event}！{beneficiary}躺着数钱")
            formulas.append(f"{event}！{beneficiary}闷声发大财")
        if company:
            formulas.append(f"太猛了！{company}{event or '突破'}，{field or '板块'}炸锅")
            formulas.append(f"{company}大动作！{field or '行业'}变天了")
        formulas.extend([
            f"{field or '板块'}集体爆发！{company or '龙头'}涨停",
            f"{field or '板块'}订单爆了！{company or '龙头'}闷声发大财",
            f"刚刚！{field or '板块'}大爆发，{company or '龙头'}领涨",
            f"{company or '龙头'}打破垄断！{field or '板块'}国产替代成功",
            f"突发！{field or '板块'}炸了，{company or '龙头'}20cm涨停",
        ])

    # ====== 最终标题选择策略 ======
    # 策略1：优先用"清洗后的原标题"（原标题是专业编辑写的，通常最好）
    cleaned = title.strip()
    # 去掉来源前缀（如"财联社："、"证券时报："等）
    cleaned = re.sub(r'^[^：:]{1,8}[：:]\s*', '', cleaned)
    # 去掉"｜"后面的来源/板块标注
    cleaned = re.sub(r'｜[^｜]*$', '', cleaned)
    # 如果标题太长（>25字），智能截取（微信非头条标题显示约31字节）
    if len(cleaned) > 25:
        # 优先在逗号/分号/冒号处截断
        best_cut = -1
        for sep in ['，', '；', '、']:
            pos = cleaned.rfind(sep, 0, 25)
            if pos > 8:  # 至少保留8个字
                best_cut = pos
                break
        if best_cut > 0:
            cleaned = cleaned[:best_cut]
        else:
            # 没有标点，在25字处截断
            cleaned = cleaned[:25]
    
    # 策略2：如果提取到了公司名，尝试用V4.0情绪词公式
    if company and event:
        if is_negative:
            formula_title = f"{company}{event}！{field or '板块'}怎么了"
        else:
            formula_title = f"太猛了！{company}{event}，{field or '板块'}炸锅"
    else:
        formula_title = ''
    
    # 策略3：如果提取到了数字，尝试用V4.0情绪词公式
    if number and field and event:
        if is_negative:
            number_title = f"刚刚！{field}暴跌{number}，发生了什么"
        else:
            number_title = f"{number}！{field}{event}，这次真的爆发了"
    else:
        number_title = ''
    
    # 决策：优先用清洗后的原标题（更自然），其次用公式标题
    # 但清洗后的标题必须包含公司名或领域关键词才有价值
    has_value = company or field in cleaned
    
    if has_value and len(cleaned) >= 8:
        return cleaned
    elif formula_title and company in formula_title:
        return formula_title
    elif number_title:
        return number_title
    elif formulas:
        # 过滤不通顺的
        bad = ['股集体', '股板块', '板块板块', '龙头龙头', '回调回调']
        valid = [t for t in formulas if not any(bp in t for bp in bad)]
        return valid[0] if valid else formulas[0]
    else:
        return cleaned[:25] if cleaned else title[:25]


def query_knowledge_base(keyword: str) -> dict:
    """查询投资知识库，获取相关概念和逻辑链"""
    try:
        # Search concepts
        result = subprocess.run(
            ['python3', str(QUERY_SCRIPT), 'search', keyword],
            capture_output=True, text=True, timeout=10
        )
        search_output = result.stdout
        
        # Get related concepts
        related_result = subprocess.run(
            ['python3', str(QUERY_SCRIPT), 'related', keyword],
            capture_output=True, text=True, timeout=10
        )
        related_output = related_result.stdout
        
        return {
            'search': search_output,
            'related': related_output,
            'available': True
        }
    except Exception as e:
        return {'available': False, 'error': str(e)}


def generate_topic_suggestions():
    """生成选题建议（使用以前的格式）"""
    print('📰 公众号每日选题提议 V2.0')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('数据源: 东方财富MX → 东方财富新闻 → 东方财富公告 → 新浪财经7x24（降级链）')
    print('')
    
    print('📋 获取近7天已写角度（去重检查）...')
    recent_data = get_recent_topics_and_keywords()
    print(f'  已写文章: {len(recent_data["topics"])}篇')
    print(f'  已用关键词: {len(recent_data["keywords"])}个')
    print(f'  已提公司: {len(recent_data["companies"])}家')
    print('')
    
    all_candidates = []
    
    print('🔍 搜索各领域热点资讯（多源搜索）...')
    for field in FIELDS:
        print(f'  搜索 {field}...')
        news_list = search_field_hotspots(field)
        
        for news in news_list:
            score = score_topic(news, recent_data)
            if score:
                article_title = generate_article_title(news)
                all_candidates.append({
                    'field': field,
                    'original_title': news.get('title', ''),
                    'article_title': article_title,
                    'content': news.get('content', '')[:100],
                    'date': news.get('date', ''),
                    'score': score
                })
    
    all_candidates.sort(key=lambda x: x['score']['total'], reverse=True)
    
    # 内容去重（基于关键词和公司名）
    unique_candidates = []
    seen_companies = set()
    seen_keywords = set()
    
    for candidate in all_candidates:
        original_title = candidate['original_title']
        content = candidate['content']
        
        # 提取原始标题中的关键词
        # 公司名（中文2-6字+后缀）
        company_matches = re.findall(r'([一-龥]{2,6})(?:A|B|：|:|接受|发布|公告|龙头|午后|盘中|收盘)', original_title)
        # 行业关键词
        industry_keywords = ['CPO', 'OLED', '机器人', '存储', '半导体', '封装', '光模块', '面板', '芯片']
        found_keywords = [kw for kw in industry_keywords if kw in original_title or kw in content]
        # 提取中际旭创等光模块公司
        cpo_companies = ['中际旭创', '光模块', '光通信', 'CPO']
        for company in cpo_companies:
            if company in original_title or company in content:
                company_matches.append(company)
        
        # 检查是否与已有选题重复
        is_duplicate = False
        for company in company_matches:
            if company in seen_companies:
                is_duplicate = True
                break
        
        if not is_duplicate:
            for kw in found_keywords:
                if kw in seen_keywords:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_candidates.append(candidate)
            seen_companies.update(company_matches)
            seen_keywords.update(found_keywords)
    
    all_candidates = unique_candidates
    
    def safe_truncate(text, max_len):
        """安全截断中文文本，不会切断多字节字符"""
        if not text:
            return ''
        text = text.replace('\n', ' ').replace('\r', '').strip()
        if len(text) <= max_len:
            return text
        return text[:max_len] + '...'
    
    # 五维度分析格式输出
    output_file = WORKSPACE_DIR / f'选题提议_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'📰 公众号每日选题提议 V2.0\n')
        f.write(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
        f.write(f'数据源: 东方财富MX → 东方财富新闻 → 东方财富公告 → 新浪财经7x24（降级链）\n\n')
        
        f.write('🎯 今日选题候选（TOP5）：\n\n')
        
        medals = ['🥇', '🥈', '🥉', '📌', '📌']
        for i, candidate in enumerate(all_candidates[:5], 1):
            medal = medals[i-1]
            score = candidate['score']
            content_summary = safe_truncate(candidate['content'], 120)
            
            if i > 1:
                f.write(f'\n---\n\n')
            
            f.write(f'{medal} 选题{i}：{candidate["article_title"]}\n')
            f.write(f'   领域：{candidate["field"]} | 来源：国内 | 评分：{score["total"]}/5.0\n')
            f.write(f'   核心摘要：{content_summary}\n')
            f.write(f'   五维度评分：')
            f.write(f'时效性{score["timeliness"]}/5')
            f.write(f' | 投资线索{score["investment_clarity"]}/5')
            f.write(f' | 读者共鸣{score["reader_resonance"]}/5')
            if 'international_perspective' in score:
                f.write(f' | 国际视角{score["international_perspective"]}/5')
            if 'angle_freshness' in score:
                f.write(f' | 角度新鲜度{score["angle_freshness"]}/5')
            f.write(f'\n')
            
            # 投资线索摘要
            if candidate.get('investment_keywords'):
                kws = ', '.join(candidate['investment_keywords'][:3])
                f.write(f'   投资线索：{kws}\n')
            
            # 知识库查询（V3.0新增）
            field = candidate['field']
            kb_result = query_knowledge_base(field)
            if kb_result['available'] and kb_result['search']:
                f.write(f'   📚 知识库关联：\n')
                # Extract concept names from search output
                for line in kb_result['search'].split('\n')[:5]:
                    if line.strip().startswith('-') or line.strip().startswith('['):
                        f.write(f'      {line.strip()}\n')
        
        f.write(f'\n---\n\n')
        f.write(f'📚 知识库查询命令（用于写文章时参考）：\n')
        f.write(f'```bash\n')
        f.write(f'# 查询领域相关概念\n')
        f.write(f'python3 ~/.qclaw/skills/investment-knowledge/scripts/query.py search <关键词>\n')
        f.write(f'# 获取概念详情\n')
        f.write(f'python3 ~/.qclaw/skills/investment-knowledge/scripts/query.py get <概念名>\n')
        f.write(f'# 获取相关概念\n')
        f.write(f'python3 ~/.qclaw/skills/investment-knowledge/scripts/query.py related <概念名>\n')
        f.write(f'```\n\n')
        
        f.write(f'选题建议已保存到：`{output_file.name}`\n')
    
    print(f'✅ 选题建议已保存到: {output_file}')
    print('')
    print('✅ 选题生成完成')


if __name__ == '__main__':
    generate_topic_suggestions()
