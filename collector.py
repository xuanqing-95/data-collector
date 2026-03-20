#!/usr/bin/env python3
"""
自媒体数据采集器 - GitHub Actions 版本
直接抓取各平台数据，不依赖 Worker
"""

import os
import json
import requests
from datetime import datetime

# 飞书多维表格
FEISHU_APP_TOKEN = "NdpBbD8jray5fDs77gScXZ9vnId"
FEISHU_TABLE_ID = "tblBBoGrB5W6DfB4"
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

def get_feishu_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json().get("tenant_access_token")
    except Exception as e:
        print(f"获取 token 失败: {e}")
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

# B站热门
def fetch_bilibili():
    try:
        url = "https://api.bilibili.com/x/web-interface/popular"
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
                })
        return results
    except Exception as e:
        print(f"B站采集失败: {e}")
        return []

# 微博热搜
def fetch_weibo():
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=30)
        data = resp.json()
        
        results = []
        if data.get("ok") == 1:
            for item in data.get("data", {}).get("realtime", [])[:10]:
                results.append({
                    "platform": "微博",
                    "title": item.get("word", ""),
                    "url": f"https://s.weibo.com/weibo?q={item.get('word', '')}",
                    "views": item.get("num", 0),
                })
        return results
    except Exception as e:
        print(f"微博采集失败: {e}")
        return []

def main():
    print(f"=== 数据采集开始 {datetime.now()} ===")
    
    all_data = []
    
    # 抓各平台
    print("抓取 B站...")
    bilibili_data = fetch_bilibili()
    print(f"  B站: {len(bilibili_data)} 条")
    all_data.extend(bilibili_data)
    
    print("抓取 微博...")
    weibo_data = fetch_weibo()
    print(f"  微博: {len(weibo_data)} 条")
    all_data.extend(weibo_data)
    
    print(f"\n总计: {len(all_data)} 条数据")
    
    if not all_data:
        print("没有数据，退出")
        return
    
    # 输出 JSON 供后续处理
    print("\n=== DATA_JSON_START ===")
    print(json.dumps(all_data, ensure_ascii=False, indent=2))
    print("=== DATA_JSON_END ===")
    
    # 获取飞书 token
    token = get_feishu_access_token()
    if not token:
        print("无法获取飞书 token")
        return
    
    print(f"\n飞书 token 获取成功，开始写入...")
    
    # 写入飞书（只写 B站数据作为示例）
    for item in bilibili_data[:5]:
        record = {
            "平台": item.get("platform", ""),
            "标题": item.get("title", ""),
            "链接": item.get("url", ""),
            "作者": item.get("author", ""),
            "播放量": item.get("views", 0),
            "点赞数": item.get("likes", 0),
            "采集时间": int(datetime.now().timestamp() * 1000),
            "状态": "待分析"
        }
        result = create_record(token, record)
        if result.get("code") == 0:
            print(f"  写入成功: {item['title'][:20]}...")
        else:
            print(f"  写入失败: {result}")
    
    print("\n完成!")

if __name__ == "__main__":
    main()
