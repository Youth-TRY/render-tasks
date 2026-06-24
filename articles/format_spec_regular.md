# 常规行业分析文章格式规范

> 适用文章类型：CPO、机器人、OLED显示、存储、封装等常规行业深度解读
> 版本：V5.6（2026-06-11，H2标题去掉渐变卡片背景改为青绿色字体加粗，H3不变）
> 来源：https://mp.weixin.qq.com/s/m90pLAJMkU0T6J99nlc_7A

---

## 一、文章结构

### 标题
- ≤30字节（约15个汉字）
- 用爆款标题6大公式之一
- 核心原则：冲突>信息，数字是武器，用动词不用名词，留悬念

### 开头（V5.1 重要规则）
- ⚠️ 第一句话必须直接切入内容，**绝对不能**重写或复述文章标题
- 用人物/企业案例切入 或 一句话结论开篇
- ❌ 禁止出现文章标题中的关键词作为开头
- ❌ 禁止H2标题卡片后第一段重述标题内容
- ✅ 正确做法：标题卡片后，第一段直接用具体事实/数据/场景切入，与标题零重叠
- ✅ 检查方法：对比标题关键词和第一段首句，确保无重复信息

### 正文（1500-2000字）
- PART分章：PART 1 / PART 2 / PART 3...
- 每个PART下用H3子标题
- 首次出现技术名词附加英文

### 封面图（V5.4 新增）
- ✅ 必须用cover_intelligence.py搜索实物照片
- ❌ 禁止用PIL/Pillow生成文字图片
- 搜索关键词：用英文（如"humanoid robot"、"OLED panel"）

### 结尾
- 金句升华（不加互动邀请）
- ❌ 删除"你怎么看？欢迎留言～"
- ❌ 删除"关注「YouthTRY」"引导语卡片
- ✅ 保留渐变名片卡（🌟持续关注 YouthTRY + 领域列表）
- ❌ 不要写“【风险提示】”
- ❌ 不要写免责声明

---

## 二、HTML样式（严格匹配5/21文章）

### 顶部渐变条
```html
<section style="height:4px;background:linear-gradient(to right,#1B3A6B,#4A90D9,#0D7C66,#4A90D9,#1B3A6B);border-radius:2px;margin-bottom:16px;"></section>
```

### 关注提示
```html
<section style="margin:0 0 12px;font-size:13px;color:#64748b;text-align:center;">点击顶部「蓝色字」关注 · 设为星标优先获取更新</section>
```

### H2（PART标题）— 青绿色字体加粗
```html
<p style="margin:18px 0 10px;font-size:17px;font-weight:700;color:#0D7C66;line-height:1.5;letter-spacing:0.5px;">PART 1：标题文字</p>
```

⚠️ **重要规则（V5.3）**：
1. 嵌套`<section>`必须写在一行，**禁止换行**
2. 嵌套`<section>`之间**禁止空格/缩进**
3. 错误示例：`</section>\n  <section` → 会导致渲染空行
4. 正确示例：`</section><section` → 无空行

### H3（子标题）— 青绿渐变竖线 + flex布局
```html
<section style="margin:14px 0 6px;display:flex;align-items:center;justify-content:space-between;"><section style="display:flex;align-items:center;flex:1;"><section style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#0D7C66 0%,#14B8A6 100%);margin-right:12px;flex-shrink:0;"></section><section style="font-size:15px;font-weight:600;color:#1A202C;line-height:1.5;">子标题文字</section></section></section>
```

⚠️ **重要规则（V5.3）**：嵌套`<section>`必须写在一行，禁止换行/空格

### 段落
```html
<p style="margin:4px 0;line-height:1.8;font-size:15px;color:#1A202C;text-align:justify;letter-spacing:0.2px;">段落文字</p>
```

### 数据标签（通用）
```html
<span style="color:#2D5A8A;font-weight:700;">67%</span>
```

### 数据标签（金额）
```html
<span style="color:#C8872A;font-weight:700;">295亿元</span>
```

### 公司名/关键词（蓝字，无方框，无#号）
```html
<strong style="color:#2D5A8A;font-weight:600;">公司名</strong>
```

### 引导语 — 渐变左边框卡片
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;">关注「YouthTRY」，深度解读 OLED显示 ｜机器人 ｜存储｜封装｜ CPO产业链</section>
```

### 底部 — 渐变卡片（无名片卡）
```html
<section style="margin-top:24px;padding:16px;background:linear-gradient(135deg,#1B3A6B 0%,#2D5A8A 60%,#0D7C66 100%);border-radius:12px;text-align:center;box-shadow:0 4px 16px rgba(26,42,74,0.2);"><section style="font-size:15px;font-weight:700;color:#ffffff;margin-bottom:6px;letter-spacing:1px;">🌟 持续关注 YouthTRY</section><section style="font-size:13px;color:rgba(255,255,255,0.85);line-height:1.8;">OLED显示 Ⅰ 机器人 Ⅰ 存储 Ⅰ 封装 Ⅰ CPO产业链</section></section>
```

⚠️ **重要规则（V5.3）**：嵌套`<section>`必须写在一行，禁止换行/空格

---

## 三、标题公式

| 公式 | 结构 | 示例 |
|------|------|------|
| 冲突+突破 | [动作]+[对象], [结果] | `打破三星垄断，京东方8.6代量产` |
| 数字+跃升 | [数字]倍/%, [事件] | `15月10倍！智元万台下线` |
| 悬念+身份 | [现象], [谁在做什么] | `涨400%！谁在囤货谁裸泳` |
| 转折+格局 | [传统], [新变化] | `三星旗舰屏，首次用中国造` |
| 代价+博弈 | [投入], [赌局] | `630亿押注IT-OLED，赌对了吗` |
| 时间+紧迫 | [比对手], [抢跑] | `比三星早一个月，京东方抢跑8.6代` |

---

## 四、固定模板

### 引导语内容（仅以下版本，不含投资/机会类描述）
```
关注「YouthTRY」，深度解读 OLED显示 ｜机器人 ｜存储｜封装｜ CPO产业链
```

❌ 禁止使用投资类引导语：
- ❌ “关注「YouthTRY」,每周深度解读产业链投资机会。”
- ❌ “关注「YouthTRY」,深度解读产业链投资机会。”
- ❌ 任何含“投资机会”“投资逻辑”“受益标的”等投资类描述的引导语

---

## 五、合规要求

- ✅ 只提公司名，不写股票代码
- ✅ 目标读者：散户投资者（语言通俗易懂，避免过于专业术语）
- ❌ 不推荐具体买卖时机
- ❌ 不承诺收益
- ❌ 不写免责声明（常规分析类文章不需要）
- ❌ 不写“【风险提示】”

---

## 五、封面图规范（V2.1，2026-05-24 更新）

⚠️ **重要**：所有嵌套`<section>`必须写在一行，禁止换行（换行会导致渲染空行）

### 核心规则
- ❌ **禁止用PIL/Pillow自己生成封面图**
- ✅ **必须用关键词搜索真实照片**
- ✅ **推送时必须确保封面图存在，不能缺失**
- 使用 `scripts/cover_intelligence.py` 搜索

### ⚠️ 重要：封面图必须存在
- 推送草稿箱时，**必须确保封面图文件存在且有效**
- 如果封面图缺失，推送会失败或显示空白封面
- 检查方法：推送前确认 `--cover-file` 参数指向的文件存在

### 搜索策略
1. **LLM语义理解**：调用Gateway生成5-8组精准英文视觉搜索词
2. **规则引擎fallback**：BRAND_KEYWORDS（13家企业）+ TECH_KEYWORDS（12项技术）
3. **多源图片获取**：ProSearch新闻图片 + Unsplash精选池

### 封面图分类
- **企业类文章**（标题含企业名）→ 搜索企业相关真实照片
- **行业类文章**（标题含技术词）→ 搜索技术/行业相关真实照片

### 调用方式
```bash
# 方式1：自动搜索封面图（推荐）
python3 scripts/cover_intelligence.py --title "文章标题" --keyword "关键词" --output /path/to/cover.jpg

# 方式2：推送草稿时自动调用（不传--cover-file时）
python3 scripts/wechat_draft_publisher_v2.py --title "xxx" --content-file xxx.html

# 方式3：指定已有封面图（确保文件存在）
python3 scripts/wechat_draft_publisher_v2.py --title "xxx" --cover-file /path/to/existing.jpg --content-file xxx.html
```

### Fallback链
```
LLM搜索词 → 规则引擎搜索词 → ProSearch → Unsplash → 纯色fallback
```

### 常见错误（避免）
- ❌ 推送时不指定封面图，导致封面缺失
- ❌ 用PIL/Pillow自己生成封面图（质量差，不符合公众号风格）
- ❌ 封面图文件路径错误或文件不存在

---

## 六、禁止项（V5.2，2026-05-24 更新）

- ❌ `#` 一级标题
- ❌ `---` 分隔线
- ❌ `**粗体**` 标记（用 `<strong style="color:#2D5A8A;font-weight:600;">` 替代）
- ❌ 📌 ▸ 等指针/图标符号
- ❌ `<span>` 嵌套（必须独立闭合）
- ❌ 公司名加方框（`border:1px solid #4A90D9`）
- ❌ 公司名加#号前缀
- ❌ 正文第一句复述文章标题
- ❌ H2标题卡片后第一段重述标题内容
- ❌ 引导语含“投资机会”“投资逻辑”等投资类描述
- ❌ “【风险提示】”
- ❌ 免责声明（本类文章不需要）
- ❌ 用PIL/Pillow自己生成封面图
- ❌ 推送时不指定封面图（导致封面缺失）
- ❌ 嵌套`<section>`换行（导致渲染空行）
