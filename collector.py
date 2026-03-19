#!/usr/bin/env python3
"""
自媒体数据采集器 - 通过 Cloudflare Worker 抓数据
"""

import os
import json
import requests
from datetime import datetime

# Cloudflare Worker URL
WORKER_URL = "https://silent-scene-f153.meifangyuan2.workers.dev"

# 飞书多维表格
FEISHU_APP_TOKEN = "NdpBbD8jray5fDs77gScXZ9vnId"
FEISHU_TABLE_ID = "tblBBoGrB5W6DfB4"
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# 心象项目相关关键词
KEYWORDS = [
    "星座", "运势", "2026年运", 
    "疗愈", "能量", "冥想",
    "八字", "算命",
    "塔罗", "占卜",
    "MBTI", "天赋",
    "心象画", "潜意识"
]

def get_feishu_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json().get("tenant_access_token")
    except:
        return None

def create_record(token, record_data):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"fields": record_data}, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"写入失败: {e}")
        return {"code": -1}

# 通过 Worker 抓 B站数据
def fetch_bilibili():
    try:
        url = f"{WORKER_URL}/bilibili"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        
        results = []
        if data.get("code") == 0:
            for item in data.get("data", {}).get("list", [])[:10]:
                results.append({
                    "platform": "B站",
                    "title": item.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                    "author": item.get("owner", {}).get("name", ""),
                    "desc": item.get("desc", "")[:200],
                    "views": item.get("stat", {}).get("view", 0),
                    "likes": item.get("stat", {}).get("like", 0),
                })
        return results
    except Exception as e:
        print(f"B站采集失败: {e}")
        return []

def main():
    print(f"=== 数据采集开始 {datetime.now()} ===")
    
    # 抓数据
    data = fetch_bilibili()
    print(f"获取 {len(data)} 条数据")
    
    if not data:
        print("没有数据")
        return
    
    # 输出数据供 AI 分析
    print("=== DATA_JSON_START ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("=== DATA_JSON_END ===")
    
    print("请小岳岳分析数据，生成爆款分析和创作方向建议，然后写入飞书！")

if __name__ == "__main__":
    main()
