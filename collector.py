#!/usr/bin/env python3
"""
自媒体数据采集器 - GitHub Actions 版本
通过 Worker 抓数据，绕过跨境限制
"""

import os
import json
import requests
from datetime import datetime

# Worker URL
WORKER_URL = "https://silent-scene-f153.meifangyuan2.workers.dev"

# 飞书多维表格
FEISHU_APP_TOKEN = "NdpBbD8jray5fDs77gScXZ9vnId"
FEISHU_TABLE_ID = "tblBBoGrB5W6DfB4"
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

def get_feishu_access_token():
    print(f"FEISHU_APP_ID: {FEISHU_APP_ID}")
    print(f"FEISHU_APP_SECRET: {FEISHU_APP_SECRET[:10] if FEISHU_APP_SECRET else 'None'}...")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        print(f"Token 响应: {result}")
        return result.get("tenant_access_token")
    except Exception as e:
        print(f"获取 token 失败: {e}")
        return None

def create_record(token, record_data):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"fields": record_data}, timeout=10)
        result = resp.json()
        print(f"写入响应: {result}")
        return result
    except Exception as e:
        print(f"写入失败: {e}")
        return {"code": -1}

# 通过 Worker 抓 B站
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
                    "views": item.get("stat", {}).get("view", 0),
                    "likes": item.get("stat", {}).get("like", 0),
                    "desc": item.get("desc", "")[:200],
                })
        return results
    except Exception as e:
        print(f"B站采集失败: {e}")
        return []

def main():
    print(f"=== 数据采集开始 {datetime.now()} ===")
    
    # 通过 Worker 抓 B站
    print("抓取 B站...")
    bilibili_data = fetch_bilibili()
    print(f"  B站: {len(bilibili_data)} 条")
    
    if not bilibili_data:
        print("没有数据，退出")
        return
    
    # 获取飞书 token
    print("\n获取飞书 token...")
    token = get_feishu_access_token()
    if not token:
        print("无法获取飞书 token，退出")
        return
    
    print(f"飞书 token 获取成功: {token[:20]}...")
    
    # 写入飞书
    print("\n开始写入飞书...")
    for item in bilibili_data[:3]:
        record = {
            "选题标题": item.get("title", "")[:100],
            "来源平台": item.get("platform", ""),
            "原始链接": item.get("url", ""),
            "内容摘要": item.get("desc", "")[:500],
            "采集时间": int(datetime.now().timestamp() * 1000),
        }
        print(f"\n写入: {item['title'][:30]}...")
        result = create_record(token, record)
        if result.get("code") == 0:
            print(f"  写入成功!")
        else:
            print(f"  写入失败: {result}")
    
    print("\n完成!")

if __name__ == "__main__":
    main()
