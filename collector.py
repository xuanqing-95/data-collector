#!/usr/bin/env python3
"""
自媒体数据采集器 - 写入飞书选题库
心象项目相关：星座、疗愈、玄学、心象画、能量、MBTI、塔罗、八字、冥想
"""

import os
import json
import asyncio
import aiohttp
import requests
from datetime import datetime

# 飞书多维表格
FEISHU_APP_TOKEN = "NdpBbD8jray5fDs77gScXZ9vnId"
FEISHU_TABLE_ID = "tblBBoGrB5W6DfB4"
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# 心象项目相关关键词
KEYWORDS = [
    "星座运势", "本周运势", "2026年运", 
    "疗愈", "能量", "脉轮", "冥想引导",
    "八字", "八字入门", "八字算命",
    "塔罗", "塔罗占卜", "塔罗牌",
    "MBTI", "人格测试", "天赋",
    "心象画", "潜意识画", "绘画疗愈",
    "阿卡西", "阿卡西阅读",
    "玄学", "生肖", "属相"
]

def get_feishu_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        return resp.json().get("tenant_access_token")
    except:
        return None

def create_record(token, record_data):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    try:
        resp = requests.post(url, headers=headers, json={"fields": record_data}, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"写入失败: {e}")
        return {"code": -1}

# B站采集
async def fetch_bilibili(keyword):
    try:
        url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={keyword}&order=click&jsonp=jsonp"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return parse_bilibili(data, keyword)
    except Exception as e:
        print(f"B站采集失败: {e}")
    return []

def parse_bilibili(data, keyword):
    results = []
    if data.get("code") != 0:
        return results
    for item in data.get("data", {}).get("result", [])[:5]:
        results.append({
            "platform": "B站",
            "title": item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
            "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
            "author": item.get("author", ""),
            "desc": item.get("description", ""),
            "keyword": keyword,
            "views": item.get("play", 0),
        })
    return results

# 知乎采集
async def fetch_zhihu(keyword):
    try:
        url = f"https://www.zhihu.com/api/v4/search_v5?keyword={keyword}&type=general"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return parse_zhihu(data, keyword)
    except Exception as e:
        print(f"知乎采集失败: {e}")
    return []

def parse_zhihu(data, keyword):
    results = []
    for item in data.get("data", [])[:5]:
        info = item.get("detail_object", {})
        results.append({
            "platform": "知乎",
            "title": info.get("title", ""),
            "url": info.get("url", ""),
            "author": info.get("author", {}).get("name", ""),
            "desc": info.get("excerpt", ""),
            "keyword": keyword,
        })
    return results

# 主程序
async def main():
    print(f"=== 数据采集开始 {datetime.now()} ===")
    print(f"关键词: {KEYWORDS}")

    all_data = []
    
    print("正在采集 B站...")
    for kw in KEYWORDS[:5]:
        data = await fetch_bilibili(kw)
        all_data.extend(data)
    print(f"  B站: 获取 {len(all_data)} 条")
    
    print("正在采集 知乎...")
    for kw in KEYWORDS[:5]:
        data = await fetch_zhihu(kw)
        all_data.extend(data)
    print(f"  知乎: 获取 {len(all_data)} 条")

    print(f"总计: {len(all_data)} 条")

    if not all_data:
        print("没有采集到数据")
        return

    # 去重
    seen = set()
    unique_data = []
    for item in all_data:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_data.append(item)
    
    print(f"去重后: {len(unique_data)} 条")

    filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {filename}")
    
    print("=== DATA_JSON_START ===")
    print(json.dumps(unique_data, ensure_ascii=False, indent=2))
    print("=== DATA_JSON_END ===")
    
    print("请根据以上数据，生成爆款分析和创作方向建议，然后写入飞书！")

if __name__ == "__main__":
    asyncio.run(main())
