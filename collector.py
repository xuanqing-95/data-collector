#!/usr/bin/env python3
"""
自媒体数据采集器 - 写入飞书选题库
"""

import os
import json
import asyncio
import aiohttp
import requests
from datetime import datetime

FEISHU_APP_TOKEN = "S4kBbJ1Zda4pnVsjg7dcS2vEnMb"
FEISHU_TABLE_ID = "tblFey62KG0YPlNo"
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

def get_feishu_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    resp = requests.post(url, headers=headers, json=data)
    return resp.json().get("tenant_access_token")

def create_record(token, record_data):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(url, headers=headers, json={"fields": record_data})
    return resp.json()

async def fetch_bilibili_hot():
    try:
        url = "https://api.bilibili.com/x/web-interface/popular"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://www.bilibili.com"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return parse_bilibili(data)
    except Exception as e:
        print(f"B站采集失败: {e}")
    return []

def parse_bilibili(data):
    results = []
    if data.get("code") != 0:
        return results
    for item in data.get("data", {}).get("list", [])[:10]:
        results.append({
            "platform": "B站",
            "title": item.get("title", ""),
            "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
            "author": item.get("owner", {}).get("name", ""),
            "views": item.get("view", 0),
            "likes": item.get("like", 0),
            "favorites": item.get("favorite", 0),
            "desc": item.get("desc", "")[:200]
        })
    return results

async def fetch_zhihu_hot():
    try:
        url = "https://www.zhihu.com/api/v3/feed/top-story/hot-lists/total?limit=20"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return parse_zhihu(data)
    except Exception as e:
        print(f"知乎采集失败: {e}")
    return []

def parse_zhihu(data):
    results = []
    for item in data.get("data", [])[:10]:
        detail = item.get("detail_item", {})
        results.append({
            "platform": "知乎",
            "title": item.get("title", ""),
            "url": detail.get("link", {}).get("url", ""),
            "author": item.get("author", {}).get("name", ""),
            "likes": detail.get("voteup_count", 0),
            "comments": detail.get("comment_count", 0),
            "desc": item.get("excerpt", "")[:200]
        })
    return results

async def main():
    print(f"=== 数据采集开始 {datetime.now()} ===")

    bilibili_data = await fetch_bilibili_hot()
    print(f"B站: 获取 {len(bilibili_data)} 条")

    zhihu_data = await fetch_zhihu_hot()
    print(f"知乎: 获取 {len(zhihu_data)} 条")

    all_data = bilibili_data + zhihu_data
    print(f"总计: {len(all_data)} 条")

    if not all_data:
        print("没有采集到数据")
        return

    # 保存到文件
    filename = f"data_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {filename}")
    
    # 输出数据到日志
    print("=== DATA_JSON_START ===")
    print(json.dumps(all_data, ensure_ascii=False))
    print("=== DATA_JSON_END ===")

if __name__ == "__main__":
    asyncio.run(main())
