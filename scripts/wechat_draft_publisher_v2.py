#!/usr/bin/env python3
"""
WeChat MP Draft Publisher (V2.0)
推送文章到微信公众号草稿箱

Required parameters:
  --config  微信公众号配置文件路径 (JSON)
  --title   文章标题
  --digest  文章摘要
  --content-file  HTML内容文件路径

Optional parameters:
  --keyword      封面搜索关键词 (用于自动搜图)
  --cover-file   指定封面图路径 (如不传则自动搜索)
  --author       作者名称

Usage:
    python3 wechat_draft_publisher_v2.py \
      --config config/wechat_mp.json \
      --title "文章标题" \
      --digest "摘要文字" \
      --content-file article.html \
      --keyword "关键词1 关键词2"
"""

import sys
import os
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime


def load_config(config_path):
    """加载微信公众号配置文件（支持环境变量）"""
    # 优先从环境变量读取
    appid = os.getenv('WECHAT_APPID')
    secret = os.getenv('WECHAT_SECRET')
    if appid and secret:
        return {'appid': appid, 'secret': secret}
    
    # 回退到配置文件
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"❌ Error: Config file '{config_path}' not found.", file=sys.stderr)
        sys.exit(1)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_access_token(appid, secret):
    """获取微信access_token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if 'access_token' in result:
            return result['access_token']
        else:
            print(f"❌ Error getting access_token: {result.get('errmsg', 'Unknown error')}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"❌ Error calling WeChat API: {e}", file=sys.stderr)
        return None


def upload_news(config, title, digest, content, author=None, cover_url=None):
    """上传图文消息到草稿箱"""
    access_token = get_access_token(config['appid'], config['secret'])
    
    if not access_token:
        return False
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    # 构建图文消息
    articles = [{
        "title": title,
        "author": author or "YouthTRY",
        "digest": digest,
        "content": content,
        "content_source_url": "",
        "thumb_media_id": cover_url or "",  # 需要先上传封面图获取media_id
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }]
    
    data = {"articles": articles}
    
    try:
        response = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode('utf-8'), headers={'Content-Type': 'application/json'}, timeout=30)
        result = response.json()
        
        if result.get('errcode') == 0 or result.get('media_id'):
            media_id = result.get('media_id', '')
            print(f"✅ Success! Draft created.")
            print(f"   Media ID: {media_id}")
            print(f"   Title: {title}")
            print(f"   Digest: {digest}")
            return True
        else:
            print(f"❌ Error creating draft: {result.get('errmsg', 'Unknown error')}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ Error calling WeChat API: {e}", file=sys.stderr)
        return False



def upload_cover_image(access_token, image_path):
    """上传封面图到微信公众号素材库，返回media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    
    if not os.path.exists(image_path):
        print(f"❌ Cover image not found: {image_path}", file=sys.stderr)
        return None
    
    try:
        with open(image_path, 'rb') as f:
            files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=30)
        
        result = response.json()
        if 'media_id' in result:
            print(f"✅ Cover uploaded: {result['media_id']}")
            return result['media_id']
        else:
            print(f"❌ Cover upload failed: {result.get('errmsg', 'Unknown')}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"❌ Cover upload error: {e}", file=sys.stderr)
        return None


def search_cover_image(keyword):
    """搜索封面图 (简化版 - 实际应该调用图片搜索API)"""
    print(f"🔍 Searching cover image for keyword: {keyword}")
    print(f"⚠️  Warning: Automatic cover image search not implemented yet.")
    print(f"   Please manually upload a cover image via WeChat MP admin panel.")
    return None


def main():
    parser = argparse.ArgumentParser(description='WeChat MP Draft Publisher (V2.0)')
    parser.add_argument('--config', required=True, help='Config file path (JSON)')
    parser.add_argument('--title', required=True, help='Article title')
    parser.add_argument('--digest', required=True, help='Article digest/summary')
    parser.add_argument('--content-file', required=True, help='HTML content file path')
    parser.add_argument('--keyword', help='Keywords for cover image search')
    parser.add_argument('--cover-file', help='Cover image file path')
    parser.add_argument('--author', default='YouthTRY', help='Author name')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 读取HTML内容
    content_file = Path(args.content_file)
    if not content_file.exists():
        print(f"❌ Error: Content file '{args.content_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📝 Publishing to WeChat MP Draft Box...")
    print(f"   Title: {args.title}")
    print(f"   Digest: {args.digest}")
    print(f"   Content length: {len(content)} characters")
    
    # 处理封面图
    cover_url = None
    if args.cover_file:
        print(f"🖼️  Uploading cover image: {args.cover_file}")
        # 先获取access_token用于上传
        temp_token = get_access_token(config['appid'], config['secret'])
        if temp_token:
            cover_url = upload_cover_image(temp_token, args.cover_file)
        if not cover_url:
            print(f"⚠️  Cover upload failed, article will have no cover.")
    elif args.keyword:
        cover_url = search_cover_image(args.keyword)
    
    # 上传到草稿箱
    success = upload_news(
        config,
        args.title,
        args.digest,
        content,
        author=args.author,
        cover_url=cover_url
    )
    
    if success:
        print(f"\n✅ Article successfully published to WeChat MP Draft Box!")
        print(f"\n📋 Next steps:")
        print(f"   1. Login to WeChat MP admin panel: https://mp.weixin.qq.com")
        print(f"   2. Go to 'Draft Box' (草稿箱)")
        print(f"   3. Find your article and click 'Edit' (编辑)")
        print(f"   4. Upload cover image manually")
        print(f"   5. Set payment/subscription settings if needed")
        print(f"   6. Publish!")
    else:
        print(f"\n❌ Failed to publish article. Please check the error above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
