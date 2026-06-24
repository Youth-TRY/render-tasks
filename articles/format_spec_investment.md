# 产业链投资建议类文章格式规范

> 适用文章类型:产业链投资推演、投资逻辑分析、标的推荐类
> 版本：V4.9（2026-06-21，新增多空辩论机制，参考TradingAgents-AShare红蓝对抗）
> 参考文件:`/Users/zhangxuewei/Documents/daily_article_20260523_v5.html`
> ⚠️ 本规范与常规行业分析完全独立,升级时互不影响

---

## 一、文章结构

### 顶部渐变条(4px)
```html
<section style="height:4px;background:linear-gradient(to right,#1B3A6B,#4A90D9,#0D7C66,#4A90D9,#1B3A6B);border-radius:2px;margin-bottom:16px;"></section>
```

### 关注提示
```html
<section style="margin:0 0 12px;font-size:13px;color:#64748b;text-align:center;">点击顶部「蓝色字」关注 · 设为星标优先获取更新</section>
```

### 标题(深蓝渐变卡片,单行写法)
```html
<section style="margin:18px 0 10px;background:linear-gradient(135deg,#1B3A6B 0%,#2D5A8A 100%);padding:8px 16px;border-radius:10px;box-shadow:0 3px 12px rgba(26,42,74,0.18);"><section style="font-size:17px;font-weight:700;color:#ffffff;letter-spacing:0.8px;line-height:1.5;text-shadow:0 1px 2px rgba(0,0,0,0.15);">标题文字</section></section>
```
- ≤30字节
- 用爆款标题6大公式之一
- ⚠️ **必须单行写法**,外`<section>`和内`<section>`之间不能有换行

### 摘要/导语(标题下方,渐变左边框卡片)
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;">据行业消息,xxx信号意味着xxx。</section>
```
- ⚠️ 这里是**事件摘要/导语**,不是"关注YouthTRY"引导语
- 用一句话概括核心事件 + 一句话点明意义

### 正文开头
- ⚠️ 第一句话必须直接切入内容,**绝对不能**重写或复述文章标题
- ❌ 禁止出现文章标题中的关键词作为开头

### 正文(1500-2000字)

**H2标题**(青绿色字体加粗,单行写法):
```html
<p style="margin:18px 0 10px;font-size:17px;font-weight:700;color:#0D7C66;line-height:1.5;letter-spacing:0.5px;">章节标题</p>
```

**H3标题**(青绿竖线,单行写法):
```html
<section style="margin:14px 0 6px;display:flex;align-items:center;justify-content:space-between;"><section style="display:flex;align-items:center;flex:1;"><section style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#0D7C66 0%,#14B8A6 100%);margin-right:12px;flex-shrink:0;"></section><section style="font-size:15px;font-weight:600;color:#1A202C;line-height:1.5;">子章节标题</section></section></section>
```

**段落**:
```html
<p style="margin:4px 0;line-height:1.8;font-size:15px;color:#1A202C;text-align:justify;letter-spacing:0.2px;">段落文字</p>
```

**数据标签**(字体标颜色):
```html
<span style="color:#2D5A8A;font-weight:700;">90%</span>
```

**公司名/关键词**(蓝字,无方框,无#号):
```html
<span style="color:#2D5A8A;font-weight:700;">OLED</span>
```

**数字列表**(圆形编号+flex布局):
```html
<section style="display:flex;align-items:baseline;margin:6px 0;"><section style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#2D5A8A;color:#fff;font-size:11px;font-weight:600;margin-right:8px;flex-shrink:0;">1</section><section style="flex:1;font-size:15px;color:#1A202C;line-height:1.8;"><strong style="color:#2D5A8A;font-weight:600;">标题</strong>:内容描述</section></section>
```

**引导语块**(渐变左边框卡片,用于正文中的重要观点):
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;">重要观点或总结性文字</section>
```

### 风险提示(正文内,普通H2标题)
```html
<p style="margin:18px 0 10px;font-size:17px;font-weight:700;color:#0D7C66;line-height:1.5;letter-spacing:0.5px;">风险提示</p>
```
- 内容用普通段落,分点列出风险

### 结语(普通H2标题)
```html
<p style="margin:18px 0 10px;font-size:17px;font-weight:700;color:#0D7C66;line-height:1.5;letter-spacing:0.5px;">结语</p>
```
- 金句升华(2-3段)

---

## 二、投资推演区(结语之后,文末渐变卡片之前)

投资推演区由**多个渐变左边框卡片**组成(⚠️ 不是黄色底色,渐变左边框是V4.6正确样式),顺序固定,全部单行写法:

### 卡片1:投资推演标题
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;"><strong style="color:#2D5A8A;font-weight:600;">投资推演</strong></section>
```

### 卡片2:标的摘要
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;">基于上述分析,以下标的受益逻辑最强(仅列举,不构成投资建议):</section>
```

### 卡片3-N:每个标的单独一个卡片
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;"><strong style="color:#2D5A8A;font-weight:600;">公司名</strong>:投资逻辑描述。逻辑强度⭐⭐⭐⭐。</section>
```

### 风险提示卡片(投资推演区内)
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;"><strong style="color:#2D5A8A;font-weight:600;">风险提示</strong>:风险1描述;风险2描述;风险3描述。</section>
```

### 免责声明卡片(投资推演区内)
```html
<section style="margin:8px 0;padding:12px 14px 12px 18px;background:linear-gradient(135deg,#EEF3FA 0%,#f0f7ff 100%);border-left:4px solid #2D5A8A;border-image:linear-gradient(180deg,#1B3A6B,#0D7C66) 1;border-right:none;border-top:none;border-bottom:none;border-radius:0 10px 10px 0;box-shadow:0 2px 8px rgba(26,42,74,0.08);font-size:14px;color:#4A5568;line-height:1.8;"><strong style="color:#2D5A8A;font-weight:600;">免责声明</strong>:本文仅为行业分析,不构成任何投资建议。股市有风险,投资需谨慎。</section>
```

---

## 三、底部渐变卡片(文末最后一个元素,单行写法)

```html
<section style="margin-top:24px;padding:12px 16px;background:linear-gradient(135deg,#1B3A6B 0%,#2D5A8A 60%,#0D7C66 100%);border-radius:12px;text-align:center;box-shadow:0 4px 16px rgba(26,42,74,0.2);"><section style="font-size:15px;font-weight:700;color:#ffffff;margin-bottom:6px;letter-spacing:1px;">🌟 持续关注 YouthTRY</section><section style="font-size:13px;color:rgba(255,255,255,0.85);line-height:1.8;">OLED显示 I 机器人 I 存储 I 封装 I CPO产业链</section></section>
```

---

## 四、HTML单行规则(V4.6新增,最高优先级)

### ⚠️ 核心规则
**所有嵌套的`<section>`标签必须写在同一行,禁止换行!**

换行会在微信公众号渲染时产生**空行**,破坏排版。

### 正确写法(单行)
```html
<section style="外层样式"><section style="内层样式">内容</section></section>
```

### 错误写法(多行 → 产生空行)
```html
<section style="外层样式">
  <section style="内层样式">内容</section>
</section>
```

### 适用范围
以下组件全部必须单行写法:
- ✅ 标题卡片(外section + 内section)
- ✅ H2章节标题(外section + 内section)
- ✅ H3子标题(3层嵌套section + 2层嵌套section)
- ✅ 底部渐变卡片(外section + 2个内section)
- ✅ 投资推演区所有卡片(单层section,本身已是单行)

### 快速检查方法
```bash
# 检查是否有嵌套section换行(结果应为0)
grep -c '<section[^>]*>\s*<section' article.html
```

---

## 五、完整结构模板

```
顶部渐变条(4px)
关注提示
标题(深蓝渐变卡片,单行)
摘要/导语(渐变左边框卡片)

开头段落(直接切入内容)

H2章节(单行)→ 段落 → 数据标签
知识图谱引用卡片(📚 引用概念+网站链接)
H2章节(单行)→ H3子标题(单行)→ 段落
H2章节(单行)→ 段落 → 数字列表
...

风险提示(H2标题 + 段落)

结语(H2标题 + 金句升华)

-- 投资推演区(多个渐变左边框卡片)--
投资推演(卡片标题)
基于上述分析...(卡片摘要)
公司名1:逻辑强度⭐⭐⭐⭐(卡片)
公司名2:逻辑强度⭐⭐⭐⭐⭐(卡片)
...
风险提示(卡片)
免责声明(卡片)
-- 投资推演区结束 --

底部渐变卡片(🌟 持续关注 YouthTRY,单行)
```

---

## 六、投资推演模式核心流程

### 触发条件
- 行业头部公司发布新品/新技术/并购
- 行业数据出现拐点(涨价/跌价/渗透率突破)
- 重大政策/事件影响产业链

### 写作流程(6步)

1. **事件识别**:确认事件是否有投资信号价值

2. **多空辩论**(⚠️ 新增,强制执行)
   - 选题确定后,必须进行一轮多空辩论,然后才进入供应链拆解
   - **🟢 多头论证**:利好逻辑、受益标的、催化剂强度、业绩兑现路径
   - **🔴 空头论证**:风险点、Price in程度、翻车案例、核心风险
   - **辩论规则**:空头优先、数据说话、翻车案例必查、置信度校准
   - **置信度应用**:≥70%正常写、50-70%调整角度、<50%放弃
   - 详见下方"多空辩论机制"章节

3. **查图谱**:打开 `articles/supply_chain_map.md` 找对应板块
4. **拆供应链**:找到受益环节 + 标的
5. **验证逻辑**:搜索标的与事件关联性
6. **输出文章**:标题用"悬念+投资线索"公式

---

## 七、多空辩论机制(⚠️ 新增,参考TradingAgents-AShare红蓝对抗)

> **目的**:避免"只看利好"的单向思维,通过正反两方论证筛选选题、发现风险、优化写作角度。
> **灵感来源**:TradingAgents-AShare的15个AI Agent多空辩论对抗机制。

### 执行方式

选题确定后(Step 1完成后),**必须**进行一轮多空辩论,然后才进入供应链拆解。

**🟢 多头(Bull)论证**:
- 这个事件的利好逻辑是什么?
- 受益标的有哪些?业绩兑现路径?
- 催化剂有多强?是短期炒作还是长期逻辑?
- 历史类似事件的股价表现?

**🔴 空头(Bear)论证**:
- 这个事件的利空/风险是什么?
- 市场是否已经Price in?(近1个月涨幅>20%需警惕)
- 公司基本面能否支撑?(有没有业绩兑现的可能)
- 类似事件的"翻车"案例?(如TCL科技澄清无新建OLED产线)
- 政策/技术/市场三类风险分别是什么?

### 辩论输出格式

```
【多空辩论结果】
选题:XXX

🟢 多头观点:
- 利好逻辑:XXX
- 受益标的:XXX
- 催化剂强度:⭐⭐⭐⭐⭐(1-5星)
- 业绩兑现路径:清晰/模糊/无

🔴 空头观点:
- 风险点:XXX
- Price in程度:已涨XX%/未反映
- 翻车概率:高/中/低
- 核心风险:政策/技术/市场

⚖️ 裁决:
- 是否继续写:是/否
- 写作角度调整:XXX
- 需要额外验证的信息:XXX
- 置信度:XX%(多头逻辑成立的概率)
```

### 辩论规则
1. **空头优先**:先听空头观点,再听多头反驳(避免先入为主)
2. **用数据说话**:每个观点必须有数据支撑(涨幅、估值、订单、产能)
3. **翻车案例必查**:搜索"XXX 失败/翻车/暴跌/澄清",找到历史反面教材
4. **裁决必须明确**:不能模棱两可,要么写(说明角度),要么不写(说明原因)
5. **置信度校准**:板块近1个月涨幅>20%时,置信度自动降低10-20%

### 辩论结果的应用
- **置信度≥70%**:正常推进,按原选题写作
- **置信度50-70%**:调整写作角度,增加风险提示比重
- **置信度<50%**:放弃选题,重新选择
- **翻车概率=高**:直接放弃,不浪费时间深挖

### 辩论结果在文章中的体现
- 空头观点中的核心风险 → 文章"风险提示"章节
- 翻车案例 → 文章正文中的风险论证
- Price in程度 → 投资推演区的逻辑强度评级参考

---

## 八、合规要求

- ✅ 只提公司名,不写股票代码
- ✅ 目标读者:散户投资者(语言通俗易懂,避免过于专业术语)
- ✅ 文末投资推演区需包含免责声明
- ❌ 不推荐具体买卖时机
- ❌ 不承诺收益
- ❌ 不使用"必涨""稳赚"等绝对化用语

---

## 九、禁止项

- ❌ `#` 一级标题
- ❌ `---` 分隔线
- ❌ `**粗体**` 标记(用 `<strong style="color:#2D5A8A;font-weight:600;">` 替代)
- ❌ 📌 ▸ 等指针/图标符号
- ❌ `<span>` 嵌套(必须独立闭合)
- ❌ 公司名加方框(`border:1px solid #4A90D9`)
- ❌ 公司名加#号前缀
- ❌ 正文第一句复述文章标题
- ❌ 红色警告框风险提示(用普通H2标题)
- ❌ 数据来源/撰写时间/格式版本
- ❌ **`<section>`嵌套换行**(必须单行写法,见第四节)
- ❌ 投资推演区用黄色底色卡片(必须用渐变左边框卡片)
