#!/usr/bin/env python3
"""
公众号文章HTML格式检查脚本 (V5.4)
支持两种格式：常规行业分析(V5.3) 和 产业链投资建议类(V4.6)
在推送前检查HTML是否符合格式规范
"""

import re
import sys

def check_html_format(html_file, article_type=None):
    """
    检查HTML文件是否符合格式规范
    article_type: 'regular' 或 'investment'，None则自动检测
    """
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 自动检测文章类型
    if article_type is None:
        if '投资推演' in content or '逻辑强度' in content or '标的' in content:
            article_type = 'investment'
        else:
            article_type = 'regular'
    
    print(f"📋 检测到文章类型: {'产业链投资建议类' if article_type == 'investment' else '常规行业分析'}")
    print()
    
    errors = []
    warnings = []
    
    # ========== 通用检查 ==========
    
    # 1. 检查嵌套span
    nested_span = re.findall(r'<span[^>]*>[^<]*<span', content)
    if nested_span:
        errors.append(f"❌ 嵌套span: {len(nested_span)}处")
    else:
        print("✅ 嵌套span: 0")
    
    # 2. 检查嵌套section换行（只检查真正的嵌套：外section开标签后换行+内section开标签）
    nested_section_newline = re.findall(r'<section[^>]*>\s*\n\s*<section', content)
    if nested_section_newline:
        errors.append(f"❌ 嵌套section换行: {len(nested_section_newline)}处（必须单行写法）")
    else:
        print("✅ 嵌套section换行: 0")
    
    # 3. 检查禁止元素
    if '<style>' in content:
        errors.append("❌ 使用了<style>标签")
    else:
        print("✅ 无<style>标签")
    
    if 'class=' in content:
        errors.append("❌ 使用了class属性")
    else:
        print("✅ 无class属性")
    
    # 4. 检查公司名格式（禁止方框和#号）
    if 'border:1px solid #4A90D9' in content:
        errors.append("❌ 公司名/关键词加了方框（border:1px solid #4A90D9）")
    else:
        print("✅ 公司名无方框")
    
    # ========== 标题检查 ==========
    
    # 匹配两种padding的标题卡片
    title_match = re.search(
        r'<section style="margin:18px 0 10px;background:linear-gradient\(135deg,#1B3A6B 0%,#2D5A8A 100%\);padding:(\d+px \d+px);border-radius:10px;box-shadow:[^"]*"><section style="font-size:17px;font-weight:700;color:#fff[^"]*">([^<]+)</section></section>',
        content
    )
    if title_match:
        padding = title_match.group(1)
        title = title_match.group(2)
        title_bytes = len(title.encode('utf-8'))
        
        if article_type == 'investment':
            expected_padding = '8px 16px'
        else:
            expected_padding = '12px 16px'
        
        if padding != expected_padding:
            errors.append(f"❌ 标题卡片padding错误: 当前{padding}，应为{expected_padding}")
        else:
            print(f"✅ 标题padding: {padding}")
        
        if title_bytes > 30:
            errors.append(f"❌ 标题超过30字节: {title_bytes}字节 - {title}")
        else:
            print(f"✅ 标题: {title_bytes}字节 - {title}")
    else:
        warnings.append("⚠️ 未找到H2标题卡片")
    
    # ========== 投资类专属检查 ==========
    
    if article_type == 'investment':
        # V4.6规范：投资推演区使用渐变左边框卡片（✅正确样式）
        investment_section_match = re.search(r'投资推演.*?(?=底部渐变卡片|$)', content, re.DOTALL)
        if investment_section_match:
            investment_section = investment_section_match.group(0)
            left_border_cards = re.findall(r'border-left:4px solid #2D5A8A;border-image:linear-gradient', investment_section)
            if left_border_cards:
                print(f"✅ 投资推演区渐变左边框卡片: {len(left_border_cards)}处（V4.6正确样式）")
            else:
                warnings.append("⚠️ 投资推演区未找到渐变左边框卡片")
        else:
            print("⚠️ 未找到投资推演区范围，跳过检查")
        
        # 检查是否有投资推演区
        if '投资推演' not in content:
            warnings.append("⚠️ 未找到投资推演区")
        else:
            print("✅ 投资推演区: 存在")
        
        # 检查底部卡片padding
        bottom_match = re.search(r'持续关注.*?padding:(\d+px \d+px)', content, re.DOTALL)
        if bottom_match:
            bottom_padding = bottom_match.group(1)
            if bottom_padding != '12px 16px':
                errors.append(f"❌ 底部卡片padding错误: 当前{bottom_padding}，应为12px 16px")
            else:
                print(f"✅ 底部卡片padding: {bottom_padding}")
    
    # ========== 常规类专属检查 ==========
    
    if article_type == 'regular':
        # 检查引导语
        if '投资机会' in content or '投资逻辑' in content or '受益标的' in content:
            errors.append("❌ 引导语包含投资类描述（常规分析不应有）")
        else:
            print("✅ 引导语无投资类描述")
    
    # ========== 输出结果 ==========
    
    print("\n" + "=" * 50)
    if errors:
        print("❌ 检查失败！以下问题需要修复：")
        for e in errors:
            print(f"  {e}")
        return False
    else:
        print("✅ 所有检查通过！")
        if warnings:
            for w in warnings:
                print(f"  {w}")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 check_html_format.py <html_file> [regular|investment]")
        sys.exit(1)
    
    html_file = sys.argv[1]
    article_type = sys.argv[2] if len(sys.argv) > 2 else None
    success = check_html_format(html_file, article_type)
    sys.exit(0 if success else 1)
