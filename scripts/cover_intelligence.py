#!/usr/bin/env python3
"""
封面图智能规划与搜索引擎 v2.0
解决：相关性低、重复率高、来源质量不一、内容匹配缺失

v2.0 核心改进（2026-05-09）：
  1. LLM搜索词参与视觉标签匹配 — 传入search_terms列表，不再只看原始keyword
  2. 来源质量评分 — 域名优先级分层，高质量来源优先（半导体官网>权威媒体>toutiaoimg）
  3. 搜索结果内容相关性评分 — 标题+来源联合判断，匹配度高排前
  4. --entities 参数 — 传入文章关键实体，丰富搜索词

v1.2更新（2026-05-08）：
  - 视觉标签阈值从3调整为5，避免过度过滤
  - AI超时从45s调整为60s
  - LLM prompt重写：必须含专有名词、禁止泛化词

⚠️ 重要规则（2026-05-24 新增）：
  1. 禁止用PIL/Pillow自己生成封面图 — 必须搜索真实照片
  2. 推送时必须确保封面图存在 — 不能缺失
  3. 封面图分类：企业类→企业照片，行业类→技术/行业照片

用法（被wechat_draft_publisher_v2.py调用）：
  python3 cover_intelligence.py --title "SK海力士HBM4量产" --keyword "HBM4" --entities "SK海力士,HBM4" --output /tmp/_cover_bg_auto.jpg --skip-llm

⚠️ 定时任务/脚本调用必须加 --skip-llm
  python3 cover_intelligence.py "OLED面板" --output /tmp/bg.jpg --skip-llm
"""
import sys, os, json, time, random, hashlib, re, subprocess, urllib.request, argparse
from PIL import Image

# ============ 常量 ============
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
PROSEARCH_PATH = os.path.expanduser(
    '~/Library/Application Support/QClaw/openclaw/config/skills/online-search/scripts/prosearch.cjs'
)
USED_COVERS_FILE = '/tmp/_used_cover_md5.json'
VISUAL_TAGS_FILE = os.path.expanduser('~/.qclaw/workspace/config/cover_visual_tags.json')

# ===== 来源质量评分（来源优先级 × 内容相关性权重） =====
# Tier 1: 官方品牌官网 → 最高权重
# Tier 2: 权威半导体媒体/通讯社 → 高权重
# Tier 3: 一般科技媒体 → 中等权重
# Tier 4: 内容农场/低质来源 → 降权

SOURCE_WEIGHTS = {
    # Tier 1 (score=3): 官方品牌官网
    'samsung.com': 3, 'samsungdevices.com': 3,
    'nvidia.com': 3, 'developer.nvidia.com': 3,
    'intel.com': 3, 'tech.intel.com': 3,
    'tsmc.com': 3, 'news.tsmc.com': 3,
    'skhynix.com': 3, 'news.skhynix.com': 3,
    'micronsemiconductor.com': 3, 'ir.micron.com': 3,
    'broadcom.com': 3,
    'qualcomm.com': 3,
    'amd.com': 3,
    'apple.com': 3,
    'huawei.com': 3,
    'boeglobal.com': 3, 'boe.com': 3, 'boe.com.cn': 3,
    'visionox.com': 3,
    'ligitek.com': 3,
    'tianma.com': 3,
    # Tier 2 (score=2): 权威媒体/通讯社
    'reuters.com': 2, 'bloomberg.com': 2,
    'ft.com': 2, 'financialtimes.com': 2,
    'wsj.com': 2, 'wsj.net': 2,
    'theverge.com': 2, 'arstechnica.com': 2,
    'wired.com': 2,
    'techcrunch.com': 2,
    'eetimes.com': 2, 'eenewsembedded.com': 2,
    'semiconductordigest.com': 2,
    'techinsights.com': 2, 'techinsider.com': 2,
    'anandtech.com': 2,
    'tomshardware.com': 2,
    'pcwatch.com': 2,
    'sina.com.cn': 2, 'finance.sina.com': 2,
    '163.com': 2, 'money.163.com': 2,
    'qq.com': 2, 'tech.qq.com': 2,
    'sohu.com': 2, 'it.sohu.com': 2,
    'ifeng.com': 2,
    '36kr.com': 2, '36comtops.com': 2,
    'leiphone.com': 2, 'www.leiphone.com': 2,
    'jiqizhixin.com': 2, 'robotchina.com': 2,
    'ofweek.com': 2,
    'elecfans.com': 2,
    'ednchina.com': 2,
    # Tier 3 (score=1.5): 一般科技媒体/地方门户
    'icsmart.cn': 1.5,
    'cctime.com': 1.5,
    'bjx.com.cn': 1.5, 'bjpg.com.cn': 1.5, 'bjpcf.com': 1.5,
    'eeboard.com': 1.5,
    'digitimes.com': 1.5, 'digitimes.com.tw': 1.5,
    'nanometrics.com': 1.5,
    # Tier 4 (score=0.5): 低质内容农场/防盗链严苛
    'toutiaoimg.com': 0.5,
    'pstatp.com': 0.5,
    'ixigua.com': 0.5,
    'feiliao.com': 0.5,
    'snail.com': 0.5,
}

# 防盗链Referer映射
REFERER_MAP = {
    '126.net': 'https://www.163.com/',
    'ws.126.net': 'https://www.163.com/',
    'toutiaoimg.com': 'https://www.toutiao.com/',
    'itc.cn': 'https://www.sohu.com/',
    'sinaimg.cn': 'https://www.sina.com.cn/',
    'qq.com': 'https://www.qq.com/',
    'bjpcf.com': 'https://www.bjpg.com.cn/',
    'bjx.com.cn': 'https://www.bjx.com.cn/',
    'icsmart.cn': 'https://www.icsmart.cn/',
    'leiphone.com': 'https://www.leiphone.com/',
    '36kr.com': 'https://www.36kr.com/',
    'cctime.com': 'https://www.cctime.com/',
    'eeboard.com': 'https://www.eeboard.com/',
}

# Unsplash池（保留作为最终fallback，但优先使用搜索结果）
UNSPLASH_POOL = {
    'semiconductor': [
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1601132359864-c974e79890ac?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1555617981-dac3880eac6e?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1563770660941-20978e870e26?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1516321318423-06199680f38a?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=900&h=383&fit=crop&auto=format',
    ],
    'display': [
        'https://images.unsplash.com/photo-1592659762303-90081d34b277?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1585792180666-f7347c490ee2?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1609587312208-cea54be969e7?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900&h=383&fit=crop&auto=format',
    ],
    'smartphone': [
        'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1605236453806-6ff36851218e?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1580910051074-3eb694886571?w=900&h=383&fit=crop&auto=format',
    ],
    'robot': [
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1563206767-5b18f218e8de?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1546776310-eef45dd6d63c?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1531746790095-e5995aca49e0?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1581091226825-a6a2a286170c?w=900&h=383&fit=crop&auto=format',
    ],
    'datacenter': [
        'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1573164574572-cb89e39749b4?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1597852072373-7435e49eaf23?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1551708647-1be90c19ba15?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1543002588-bfa74002ed7a?w=900&h=383&fit=crop&auto=format',
    ],
    'battery': [
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=900&h=383&fit=crop&auto=format',
    ],
    'vehicle': [
        'https://images.unsplash.com/photo-1593017468775-cbb3b9e6c7a6?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1619767888026-0b1e9e6b1a6e?w=900&h=383&fit=crop&auto=format',
    ],
    'tech': [
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1518773553398-650c184e0bb3?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&h=383&fit=crop&auto=format',
    ],
    'ai_chip': [
        'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1601132359864-c974e79890ac?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1555617981-dac3880eac6e?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1563770660941-20978e870e26?w=900&h=383&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=900&h=383&fit=crop&auto=format',
    ],
}

# ============ 关键词扩展知识库 ============
# 企业名 → 相关视觉搜索词
BRAND_KEYWORDS = {
    '三星': ['Samsung semiconductor', 'Samsung chip factory', 'Samsung OLED panel'],
    'LG': ['LG Display OLED', 'LG factory production'],
    'SK海力士': ['SK hynix HBM', 'SK hynix memory chip', 'hynix wafer'],
    '英伟达': ['NVIDIA GPU datacenter', 'NVIDIA chip'],
    '台积电': ['TSMC wafer fab', 'TSMC semiconductor manufacturing'],
    '英特尔': ['Intel chip fab', 'Intel semiconductor'],
    '华为': ['Huawei chip', 'Huawei tech'],
    '苹果': ['Apple chip M series', 'Apple silicon'],
    '小米': ['Xiaomi smartphone', 'Xiaomi factory'],
    '索尼': ['Sony sensor', 'Sony CMOS image sensor'],
    '京东方': ['BOE display panel', 'BOE OLED factory'],
    '维信诺': ['Visionox OLED', 'Visionox display'],
    '中芯国际': ['SMIC semiconductor', 'SMIC wafer'],
    '寒武纪': ['Cambricon AI chip', 'Cambricon processor', 'Chinese AI chip'],
    '海光信息': ['Hygon GPU', 'Chinese GPU chip', 'Hygon DCU'],
    '燧原科技': ['Enflame AI chip', 'Chinese AI accelerator'],
    '壁仞科技': ['Birentech GPU', 'Chinese GPU design'],
    '摩尔线程': ['Moore Threads GPU', 'MTTS GPU chip'],
}

# 技术词 → 相关视觉搜索词
TECH_KEYWORDS = {
    'HBM': ['HBM memory stack', 'high bandwidth memory chip', '3D stacked memory'],
    'CPO': ['CPO optical module', 'co-packaged optics', 'silicon photonics chip'],
    'OLED': ['OLED display manufacturing', 'OLED pixel close-up'],
    'MicroLED': ['MicroLED display', 'micro LED chip array'],
    '折叠屏': ['foldable display', 'foldable smartphone bend'],
    '硅光': ['silicon photonics wafer', 'photonic integrated circuit'],
    '先进封装': ['advanced packaging chip', 'chiplet packaging', '3D IC packaging'],
    '晶圆': ['silicon wafer fab', 'wafer manufacturing cleanroom'],
    '存储': ['memory chip DDR5', 'NAND flash wafer'],
    '机器人': ['humanoid robot', 'industrial robot arm'],
    'AI芯片': ['AI accelerator chip', 'GPU datacenter server', 'neural network processor'],
    '面板': ['display panel factory', 'LCD OLED production line'],
    'GPU': ['GPU chip closeup', 'graphics processing unit', 'AI GPU server'],
    '算力': ['AI datacenter', 'GPU server rack', 'computing power cluster'],
    '国产替代': ['Chinese semiconductor', 'domestic chip factory', 'indigenous chip'],
    '芯片设计': ['chip design floorplan', 'EDA tool chip layout', 'silicon architecture'],
    'AI推理': ['AI inference chip', 'inference accelerator', 'NPU processor'],
}

# ============ 工具函数 ============
def log(msg):
    print(msg, file=sys.stderr)

def get_source_score(url):
    """根据图片URL来源域名，返回来源质量评分（0.5~3分）"""
    url_lower = url.lower()
    for domain, score in SOURCE_WEIGHTS.items():
        if domain in url_lower:
            return score
    return 1.0  # 默认中等级

def score_content_relevance(img, search_term):
    """
    根据图片的标题和来源，与搜索词匹配度进行内容相关性评分（0~2分）
    - 标题包含搜索词核心词 → +1.5分
    - 标题包含搜索词相关词 → +0.5分  
    - 来源是半导体/科技媒体 → +0.3分（已经通过SOURCE_WEIGHTS处理，这里做补充）
    """
    score = 0.0
    title = img.get('title', '').lower()
    source = img.get('source', '').lower()
    site = img.get('site', '').lower()
    search_lower = search_term.lower()
    
    # 提取搜索词中的核心词（去掉常见介词/动词，取名词）
    stop_words = {'the', 'a', 'an', 'of', 'in', 'for', 'with', 'and', 'or', 'on', 'at', 'to', 'from', 'by', 'news', 'latest', 'new'}
    search_words = [w for w in re.split(r'[\s\-_/]+', search_lower) if w and w not in stop_words]
    
    # 标题匹配评分
    title_match_count = sum(1 for w in search_words if w in title)
    if title_match_count >= 2:
        score += 1.5
    elif title_match_count == 1:
        score += 0.5
    
    # 来源行业相关性（补充SOURCE_WEIGHTS，专注于行业匹配度）
    semi_keywords = ['semi', 'chip', 'tech', 'hardware', 'samsung', 'nvidia', 'intel',
                     'sk', 'micron', 'tsmc', 'broadcom', 'amd', 'huawei', 'apple',
                     'semiconductor', 'display', 'oled', 'memory', 'gpu', 'ai']
    source_text = (source + ' ' + site).lower()
    if any(k in source_text for k in semi_keywords):
        score += 0.3
    
    return min(score, 2.0)

def composite_score(img, search_weight):
    """
    综合评分：来源质量×0.3 + 内容相关性×0.3 + 搜索词权重×0.4
    """
    src = get_source_score(img.get('url', ''))
    content = score_content_relevance(img, img.get('search_term', ''))
    composite = src * 0.3 + content * 0.3 + search_weight * 0.4
    return round(composite, 2)

def download(url, path, min_size=10000, headers=None):
    """下载图片"""
    if headers is None:
        headers = HEADERS.copy()
    for domain, referer in REFERER_MAP.items():
        if domain in url:
            headers['Referer'] = referer
            break
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if len(data) < min_size:
            log(f"  ⚠️ 图片太小: {len(data)} bytes")
            return None
        with open(path, 'wb') as f:
            f.write(data)
        log(f"  ✅ 下载成功: {len(data):,} bytes")
        return data
    except Exception as e:
        log(f"  ⚠️ 下载失败: {e}")
        return None

def resize_cover(path, w=900, h=383):
    """缩放到封面尺寸"""
    try:
        img = Image.open(path)
        target_ratio = w / h
        img_ratio = img.width / img.height
        if img_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 2
            img = img.crop((0, top, img.width, top + new_h))
        img = img.resize((w, h), Image.LANCZOS)
        if img.mode in ('P', 'RGBA', 'LA'):
            img = img.convert('RGB')
        img.save(path, 'JPEG', quality=92)
        log(f"  ✅ 裁剪缩放到 {w}x{h}")
        return True
    except Exception as e:
        log(f"  ⚠️ 缩放失败: {e}")
        return False

def get_category(keyword):
    """根据关键词判断图片类别"""
    kw = keyword.lower()
    if any(w in kw for w in ['芯片', '半导', 'IC', 'DRAM', 'NAND', 'HBM', 'wafer', 'chip', 'semiconductor', '封装', 'GPU', '算力', 'AI芯片', '国产替代']):
        return 'ai_chip'
    if any(w in kw for w in ['OLED', '显示', '屏幕', '面板', '屏', 'display', 'AMOLED', 'UTG', '发光', '折叠']):
        return 'display'
    if any(w in kw for w in ['手机', 'phone', 'smartphone', 'iPhone', '安卓', 'foldable']):
        return 'smartphone'
    if any(w in kw for w in ['机器', '人形', 'robot', '自动化', '具身', '机械臂', 'AI智能']):
        return 'robot'
    if any(w in kw for w in ['数据', '服务器', 'datacenter', '数据中心', 'CPO', '光互联', '硅光', '光纤', '交换机']):
        return 'datacenter'
    if any(w in kw for w in ['电池', '新能', '钠离', '固态电', 'battery']):
        return 'battery'
    if any(w in kw for w in ['汽车', '电动车', '智能驾驶', '新能源车', 'vehicle', 'EV']):
        return 'vehicle'
    return 'semiconductor'

# ============ MD5去重 ============
def load_used_md5():
    try:
        with open(USED_COVERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_used_md5(data):
    with open(USED_COVERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_and_record_md5(path):
    """检查图片MD5是否近7天用过，没用过则记录"""
    with open(path, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    used = load_used_md5()
    cutoff = time.strftime('%Y-%m-%d', time.localtime(time.time() - 7*86400))
    for date_key, md5_list in used.items():
        if date_key >= cutoff and md5 in md5_list:
            log(f"  ⚠️ MD5重复（{date_key}已用过）")
            return False
    today = time.strftime('%Y-%m-%d')
    if today not in used:
        used[today] = []
    used[today].append(md5)
    save_used_md5(used)
    log(f"  ✅ MD5={md5[:8]}... 已记录")
    return True

def _rollback_md5(path):
    """回滚刚记录的MD5（视觉标签去重被拒时使用）"""
    try:
        with open(path, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        used = load_used_md5()
        today = time.strftime('%Y-%m-%d')
        if today in used and md5 in used[today]:
            used[today].remove(md5)
            save_used_md5(used)
            log(f"  ↩️ MD5={md5[:8]}... 已回滚")
    except Exception as e:
        log(f"  ⚠️ MD5回滚失败: {e}")

# ============ 视觉标签去重 ============
def load_visual_tags():
    try:
        with open(VISUAL_TAGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_visual_tags(data):
    os.makedirs(os.path.dirname(VISUAL_TAGS_FILE), exist_ok=True)
    with open(VISUAL_TAGS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_visual_tags_for_url(url, keyword, search_terms=None):
    """
    为图片URL生成视觉标签（v2.0: 支持search_terms传入）
    - search_terms: LLM生成的搜索词列表，用于更精准的标签匹配
    """
    tags = []
    
    # 基于URL来源推断视觉风格
    url_lower = url.lower()
    if 'unsplash' in url:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
        tags.append(f'unsplash-{url_hash}')
    else:
        for domain_key in ['163', 'sina', 'qq', 'sohu', 'toutiao', '36kr',
                           'leiphone', 'bjx', 'icsmart', 'cctime', 'visionox', 'boe',
                           'eefcdn', 'samsung', 'macrumors', 'theverge', 'reuters']:
            if domain_key in url_lower:
                tags.append(f'news-{domain_key}')
                break
    
    # 构图标签（v2.0: 搜索词参与标签匹配）
    composition_tags = []
    
    # 如果有搜索词，用搜索词推断构图类型（更精准）
    if search_terms:
        search_text = ' '.join(search_terms).lower()
        if any(w in search_text for w in ['chip', 'die', 'wafer', 'memory', 'hbm', 'gpu']):
            composition_tags.append('chip-closeup')
        if any(w in search_text for w in ['factory', 'fab', 'manufacturing', 'production', 'line']):
            composition_tags.append('factory-wide')
        if any(w in search_text for w in ['display', 'screen', 'panel', 'oled', 'monitor']):
            composition_tags.append('display-panel')
        if any(w in search_text for w in ['robot', 'humanoid', 'body', 'arm']):
            composition_tags.append('robot-body')
        if any(w in search_text for w in ['server', 'datacenter', 'rack', 'cluster']):
            composition_tags.append('datacenter')
        if any(w in search_text for w in ['optical', 'photonics', 'cpo', 'fiber', 'transceiver']):
            composition_tags.append('optical-module')
        if any(w in search_text for w in ['chart', 'data', 'revenue', 'growth', 'trend', 'financial']):
            composition_tags.append('data-chart')
    
    # 基于原始关键词补充（兜底）
    kw_lower = keyword.lower()
    if any(w in keyword for w in ['芯片特写', '晶圆', 'wafer']) or any(w in kw_lower for w in ['wafer', 'die shot']):
        if 'chip-closeup' not in composition_tags:
            composition_tags.append('chip-closeup')
    if any(w in keyword for w in ['工厂', '产线', '量产', 'fab', '制造']) or any(w in kw_lower for w in ['factory', 'manufacturing', 'fab']):
        if 'factory-wide' not in composition_tags:
            composition_tags.append('factory-wide')
    if any(w in keyword for w in ['OLED', '屏幕', '面板', '显示', 'display']) or any(w in kw_lower for w in ['display', 'screen', 'panel']):
        if 'display-panel' not in composition_tags:
            composition_tags.append('display-panel')
    if any(w in keyword for w in ['机器', 'robot', '人形', '具身']) or any(w in kw_lower for w in ['robot', 'humanoid']):
        if 'robot-body' not in composition_tags:
            composition_tags.append('robot-body')
    if any(w in keyword for w in ['服务器', '数据中心', '算力']) or any(w in kw_lower for w in ['server', 'data center', 'datacenter']):
        if 'datacenter' not in composition_tags:
            composition_tags.append('datacenter')
    if any(w in keyword for w in ['投资', '资本', '融资', '市值']) or any(w in kw_lower for w in ['invest', 'capital', 'fund']):
        if 'capital-flow' not in composition_tags:
            composition_tags.append('capital-flow')
    if any(w in keyword for w in ['半导体', '产业链', '供应链']) or any(w in kw_lower for w in ['semiconductor', 'supply chain']):
        if 'semiconductor-chain' not in composition_tags:
            composition_tags.append('semiconductor-chain')
    if any(w in keyword for w in ['光', 'CPO', '硅光', '光纤', 'photonics']) or any(w in kw_lower for w in ['optical', 'photonics', 'cpo']):
        if 'optical-module' not in composition_tags:
            composition_tags.append('optical-module')
    if any(w in keyword for w in ['封装', 'packaging', 'chiplet']) or any(w in kw_lower for w in ['packaging', 'chiplet', 'interposer']):
        if 'packaging-cross' not in composition_tags:
            composition_tags.append('packaging-cross')
    if any(w in keyword for w in ['AI芯片', '算力', '国产替代', 'GPU']) or any(w in kw_lower for w in ['AI chip', 'GPU', 'AI accelerator']):
        if 'ai-chip' not in composition_tags:
            composition_tags.append('ai-chip')
    
    # 最多保留3个构图标签
    tags.extend(composition_tags[:3])
    
    return tags

def check_visual_diversity(keyword):
    """检查近期视觉标签使用频率，返回应避免的标签"""
    tags_data = load_visual_tags()
    if not tags_data:
        return []
    
    cutoff = time.strftime('%Y-%m-%d', time.localtime(time.time() - 7*86400))
    tag_counts = {}
    for date_key, entries in tags_data.items():
        if date_key >= cutoff:
            for entry in entries:
                for tag in entry.get('tags', []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    avoid = [tag for tag, count in tag_counts.items() if count >= 5]
    if avoid:
        log(f"  🏷️ 建议避开视觉标签: {avoid}")
    return avoid

def record_visual_tag(url, keyword, search_terms=None, source='unknown'):
    """记录图片的视觉标签（v2.0: 支持search_terms）"""
    tags_data = load_visual_tags()
    today = time.strftime('%Y-%m-%d')
    if today not in tags_data:
        tags_data[today] = []
    
    tags = get_visual_tags_for_url(url, keyword, search_terms=search_terms)
    tags_data[today].append({
        'url': url[:80],
        'keyword': keyword,
        'search_terms': search_terms if search_terms else [],
        'tags': tags,
        'source': source,
    })
    save_visual_tags(tags_data)
    log(f"  🏷️ 视觉标签已记录: {tags}")

# ============ AI智能搜索词生成（v2.0: 支持entities） ============
GATEWAY_URL = 'http://127.0.0.1:28789/v1/chat/completions'
GATEWAY_TOKEN = 'a26d1541c2d19f434f09e59c0f1aee37c5cf638d0156c401'
AI_MODEL = 'openclaw'

def ai_generate_search_keywords(title, keyword, entities=''):
    """
    用大模型从文章标题+实体生成精准的英文图片搜索词（v2.0）
    - entities: 文章关键实体（如"寒武纪,海光信息"），逗号分隔
    """
    log("  🤖 AI智能搜索词生成中...")
    
    # 构建实体上下文
    entity_context = ''
    if entities:
        entity_list = [e.strip() for e in entities.split(',') if e.strip()]
        entity_context = f"\n文章关键实体（必须包含在搜索词中）: {', '.join(entity_list)}"
    
    prompt = f"""你是一个专业的图片搜索专家。根据以下文章标题，生成5-8个英文搜索关键词，用于在新闻图片库中搜索合适的封面图。

文章标题：{title}
文章关键词：{keyword}{entity_context}

⚠️ 关键规则（违反会导致搜索结果不相关）：
1. 【必须包含专有名词】搜索词必须包含文章标题或实体中的专有名词/技术术语的英文翻译。
   例如：实体含"寒武纪"则搜索词必须含"Cambricon AI chip"或"Chinese AI chip"；实体含"海光信息"则搜索词含"Hygon GPU"或"Chinese GPU"
2. 【禁止泛化通用词】绝对禁止使用泛化通用词作为主要搜索词（如"semiconductor wafer"、"chip packaging"等）。这些词匹配任何芯片文章，无法体现本文独特主题
3. 【必须可区分】搜索词必须能区分这篇文章和其他同行业文章
4. 搜索词必须是英文，每个2-4个单词
5. 按重要度排序

输出格式：只输出搜索词，每行一个，不要序号、不要解释。

好的示例：
标题"SK海力士HBM4量产" 实体"SK海力士,HBM4" → SK Hynix HBM4 production, HBM4 memory chip closeup, SK hynix wafer fab
标题"国产AI芯片拐点" 实体"寒武纪,海光信息" → Cambricon AI chip, Hygon GPU datacenter, Chinese AI processor chip, domestic semiconductor fab"""
    
    try:
        import urllib.request
        payload = json.dumps({
            'model': AI_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300,
            'temperature': 0.3,
        }).encode('utf-8')
        req = urllib.request.Request(GATEWAY_URL, data=payload, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GATEWAY_TOKEN}',
        })
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode('utf-8'))
        
        content = resp['choices'][0]['message']['content'].strip()
        terms = [line.strip().lstrip('0123456789.-) ') for line in content.split('\n') if line.strip()]
        terms = [t for t in terms if len(t) >= 2][:8]
        
        if not terms:
            log("  ⚠️ AI返回为空，回退到规则引擎")
            return None
        
        result = []
        for i, term in enumerate(terms):
            if i < 3:
                result.append((term, 3))
            elif i < 5:
                result.append((term, 2))
            else:
                result.append((term, 1))
        
        log(f"  🤖 AI生成 {len(result)} 组搜索词: {[t for t, w in result[:5]]}")
        return result
        
    except Exception as e:
        log(f"  ⚠️ AI搜索词生成失败: {e}，回退到规则引擎")
        return None

# ============ 规则引擎关键词生成（v2.0: 支持entities） ============
def generate_search_keywords(title, keyword, entities=''):
    """从文章标题和关键词生成多组搜索词（v2.0: 支持entities）"""
    search_terms = []
    
    # 0. 实体词（权重4，最高）
    if entities:
        entity_map = {
            '寒武纪': ['Cambricon AI chip', 'Cambricon processor'],
            '海光信息': ['Hygon GPU', 'Chinese GPU chip'],
            '燧原科技': ['Enflame AI chip', 'Chinese AI accelerator'],
            '壁仞科技': ['Birentech GPU', 'Chinese GPU design'],
            '摩尔线程': ['Moore Threads GPU', 'MTTS GPU'],
            '三星': ['Samsung semiconductor', 'Samsung chip factory'],
            'SK海力士': ['SK hynix HBM', 'SK hynix memory'],
            '英伟达': ['NVIDIA GPU', 'NVIDIA AI chip'],
            '台积电': ['TSMC wafer fab', 'TSMC semiconductor'],
            '英特尔': ['Intel chip fab', 'Intel semiconductor'],
            '京东方': ['BOE display panel', 'BOE OLED factory'],
        }
        for entity in entities.split(','):
            entity = entity.strip()
            if entity in entity_map:
                for en in entity_map[entity]:
                    search_terms.append((en, 4))
    
    # 1. 原始关键词（权重3）
    if keyword:
        search_terms.append((keyword, 3))
    
    # 2. 标题中提取的技术词（权重3）
    for tech_key, tech_searches in TECH_KEYWORDS.items():
        if tech_key in (title + keyword):
            for ts in tech_searches[:2]:
                search_terms.append((ts, 3))
    
    # 3. 标题中提取的企业名（权重2）
    for brand, brand_searches in BRAND_KEYWORDS.items():
        if brand in (title + keyword):
            for bs in brand_searches[:2]:
                search_terms.append((bs, 2))
    
    # 去重（保留高权重）
    seen = {}
    for term, weight in search_terms:
        if term not in seen or seen[term] < weight:
            seen[term] = weight
    
    result = sorted(seen.items(), key=lambda x: -x[1])
    log(f"  🧠 生成 {len(result)} 组搜索词: {[t for t, w in result[:5]]}")
    return result

# ============ 策略0: ProSearch新闻图片（v2.0: 综合评分排序） ============
def search_prosearch(keyword, cnt=10):
    """通过ProSearch搜索新闻图片"""
    try:
        cmd = ['node', PROSEARCH_PATH, f'--keyword={keyword}', f'--cnt={cnt}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        docs = data.get('data', {}).get('docs', [])
        images = []
        for doc in docs:
            for img_url in doc.get('images', []):
                if img_url and img_url.startswith('http'):
                    images.append({
                        'url': img_url,
                        'title': doc.get('title', ''),
                        'source': doc.get('site', ''),
                        'site': doc.get('site', ''),
                        'search_term': keyword,
                    })
        return images
    except:
        return []

def strategy_prosearch(title, keyword, output_path, w=900, h=383, skip_llm=False, entities=''):
    """策略0: ProSearch智能搜索 v2.0（综合评分排序）"""
    log("  🔍 策略0 - ProSearch智能搜索 v2.0（综合评分）")
    
    avoid_tags = check_visual_diversity(keyword)
    
    # 生成搜索词（AI优先，entities参与）
    if skip_llm:
        log("  ⏭️ 跳过LLM，使用规则引擎")
        search_terms = generate_search_keywords(title, keyword, entities)
    else:
        search_terms = ai_generate_search_keywords(title, keyword, entities)
        if not search_terms:
            search_terms = generate_search_keywords(title, keyword, entities)
    
    # 提取纯搜索词列表（传给视觉标签函数）
    term_list = [t for t, w in search_terms]
    
    # 收集所有候选图片（URL去重）
    all_candidates = []
    seen_urls = set()
    for term, weight in search_terms[:8]:
        log(f"    🔎 搜索: {term} (权重{weight})")
        images = search_prosearch(term, cnt=10)
        for img in images:
            if img['url'] not in seen_urls:
                img['weight'] = weight
                all_candidates.append(img)
                seen_urls.add(img['url'])
        if len(all_candidates) >= 25:
            break
    
    if not all_candidates:
        log("  ⚠️ ProSearch未找到图片")
        return None
    
    log(f"  📷 共找到 {len(all_candidates)} 张候选图片")
    
    # v2.0: 综合评分排序（来源质量×0.3 + 内容相关性×0.3 + 搜索词权重×0.4）
    for img in all_candidates:
        img['_score'] = composite_score(img, img.get('weight', 1))
    
    all_candidates.sort(key=lambda x: -x['_score'])
    
    log(f"  🏆 综合评分Top5:")
    for i, img in enumerate(all_candidates[:5]):
        src_score = get_source_score(img['url'])
        content_score = score_content_relevance(img, img['search_term'])
        log(f"    [{i+1}] 得分{img['_score']} | 来源{src_score} | 内容{content_score:.1f} | {img['url'][:50]}...")
    
    # 逐张下载尝试（按综合评分顺序）
    for i, candidate in enumerate(all_candidates[:20]):
        url = candidate['url']
        log(f"    [{i+1}/{min(len(all_candidates),20)}] 综合评分{candidate['_score']}: {url[:55]}...")
        
        result = download(url, output_path, min_size=10000)
        if not result:
            continue
        
        try:
            img = Image.open(output_path)
            if img.width < 300 or img.height < 200:
                log(f"  ⚠️ 尺寸不足: {img.width}x{img.height}")
                continue
        except:
            continue
        
        resize_cover(output_path, w, h)
        
        if not check_and_record_md5(output_path):
            log("  🔄 MD5重复，换下一张")
            continue
        
        # v2.0: 传入search_terms到视觉标签函数
        img_tags = get_visual_tags_for_url(url, keyword, search_terms=term_list)
        overlap = set(img_tags) & set(avoid_tags)
        if overlap:
            log(f"  🏷️ 视觉标签重叠 {overlap}，换下一张")
            _rollback_md5(output_path)
            continue
        
        # v2.0: 记录视觉标签时传入search_terms
        record_visual_tag(url, keyword, search_terms=term_list, source='prosearch')
        
        return output_path
    
    log("  ⚠️ 所有ProSearch候选图片均不合适")
    
    # 边界处理：视觉标签过滤过严 → 降低阈值重试
    if avoid_tags:
        log("  🔄 视觉标签过滤过严，降低阈值重试（仅MD5去重）")
        for i, candidate in enumerate(all_candidates[:15]):
            url = candidate['url']
            result = download(url, output_path, min_size=10000)
            if not result:
                continue
            try:
                img = Image.open(output_path)
                if img.width < 300 or img.height < 200:
                    continue
            except:
                continue
            resize_cover(output_path, w, h)
            if not check_and_record_md5(output_path):
                continue
            record_visual_tag(url, keyword, search_terms=term_list, source='prosearch-fallback')
            return output_path
        log("  ⚠️ 降低阈值后仍未找到合适图片")
    
    return None

# ============ 策略1: Unsplash池（v2.0: AI chip类别） ============
def strategy_unsplash(keyword, output_path, w=900, h=383):
    """策略1: Unsplash精选池（v2.0: 优化类别匹配）"""
    log("  🔍 策略1 - Unsplash精选池")
    
    category = get_category(keyword)
    urls = UNSPLASH_POOL.get(category, UNSPLASH_POOL['semiconductor'])
    
    avoid_tags = check_visual_diversity(keyword)
    
    seed = int(hashlib.md5(f"{keyword}-{time.time_ns()}".encode()).hexdigest()[:8], 16)
    random.seed(seed)
    shuffled = urls.copy()
    random.shuffle(shuffled)
    
    for url in shuffled[:5]:
        img_tags = get_visual_tags_for_url(url, keyword)
        overlap = set(img_tags) & set(avoid_tags)
        if overlap:
            log(f"  🏷️ 视觉标签重叠 {overlap}，跳过")
            continue
        
        result = download(url, output_path, min_size=20000)
        if not result:
            continue
        resize_cover(output_path, w, h)
        if not check_and_record_md5(output_path):
            log("  🔄 MD5重复，换下一张")
            continue
        record_visual_tag(url, keyword, source='unsplash')
        return output_path
    
    # 放宽限制，取可用图
    log("  ⚠️ 所有Unsplash图都被视觉标签过滤，放宽限制取可用图")
    for url in shuffled[:3]:
        result = download(url, output_path, min_size=20000)
        if not result:
            continue
        resize_cover(output_path, w, h)
        if not check_and_record_md5(output_path):
            continue
        return output_path
    return None

# ============ 主函数 ============
def fetch_cover_bg(title='', keyword='', output_path='/tmp/_cover_bg_auto.jpg',
                   w=900, h=383, skip_llm=False, entities=''):
    """
    智能封面图获取 v2.0
    - title: 文章标题
    - keyword: 关键词
    - entities: 文章关键实体（逗号分隔）
    """
    if not title:
        title = keyword or ''
    if not keyword:
        keyword = title[:10] if title else '科技'
    
    log(f"📥 封面图智能获取 v2.0")
    log(f"  标题: {title}")
    log(f"  关键词: {keyword}")
    if entities:
        log(f"  实体: {entities}")
    
    # 策略0: ProSearch综合评分搜索
    result = strategy_prosearch(title, keyword, output_path, w, h,
                                skip_llm=skip_llm, entities=entities)
    if result:
        log(f"🎉 封面图获取成功（ProSearch v2.0）")
        return result
    
    # 策略1: Unsplash池
    result = strategy_unsplash(keyword, output_path, w, h)
    if result:
        log(f"🎉 封面图获取成功（Unsplash池）")
        return result
    
    log("❌ 所有策略均失败！")
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='封面图智能规划与搜索引擎 v2.0')
    parser.add_argument('keyword', nargs='?', default='', help='关键词（兼容旧调用方式）')
    parser.add_argument('--title', default='', help='文章标题（推荐传入）')
    parser.add_argument('--keyword', dest='keyword_flag', default='', help='关键词（命名参数）')
    parser.add_argument('--entities', default='', help='文章关键实体，逗号分隔（如"寒武纪,海光信息"）')
    parser.add_argument('--output', default='/tmp/_cover_bg_auto.jpg')
    parser.add_argument('--width', type=int, default=900)
    parser.add_argument('--height', type=int, default=383)
    parser.add_argument('--skip-llm', action='store_true', help='跳过LLM搜索词生成')
    args = parser.parse_args()
    
    keyword = args.keyword_flag or args.keyword or ''
    title = args.title or keyword
    entities = args.entities
    
    result = fetch_cover_bg(title=title, keyword=keyword, output_path=args.output,
                           w=args.width, h=args.height, skip_llm=args.skip_llm,
                           entities=entities)
    if result:
        print(result)
    else:
        print("FAILED", file=sys.stderr)
        sys.exit(1)