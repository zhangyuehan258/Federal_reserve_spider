import os
import json
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

# 美联储货币政策新闻稿 RSS 源
FEED_URL = "https://www.federalreserve.gov/feeds/press_monetary.xml"
# 源中所有条目都存档；只有 FOMC 声明会更新 latest/previous，以保证前后两期可比
STATEMENT_KEYWORD = "FOMC statement"
DATA_DIR = "data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
STATE_FILE = os.path.join(DATA_DIR, "last_seen.json")
LATEST_TEXT_FILE = os.path.join(DATA_DIR, "latest_policy.txt")
PREV_TEXT_FILE = os.path.join(DATA_DIR, "previous_policy.txt")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"
}

def fetch_article_body(url):
    """进入具体的新闻稿链接，提取政策声明正文"""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    
    # 美联储新闻稿正文通常包裹在 id="article" 的 div 中
    article_div = soup.find("div", id="article")
    if article_div:
        return article_div.get_text(separator="\n", strip=True)
    
    # 兜底方案：提取所有段落文本
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return "\n".join(paragraphs)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_date": None, "seen_links": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def update_latest_statement(record):
    """新的 FOMC 声明：旧的 latest_policy.txt 备份为 previous_policy.txt，供 AI 做措辞边际对比"""
    if os.path.exists(LATEST_TEXT_FILE):
        with open(LATEST_TEXT_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()
        with open(PREV_TEXT_FILE, "w", encoding="utf-8") as f:
            f.write(old_content)
    with open(LATEST_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(record)

def main():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    print("正在连接政策发布源检查最新公告...")
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    
    # 解析 XML 格式的 RSS 源
    soup = BeautifulSoup(resp.content, "xml")
    items = []
    for item in soup.find_all("item"):
        date_str = item.find("pubDate").text.strip()
        items.append({
            "title": item.find("title").text.strip(),
            "link": item.find("link").text.strip(),
            "date": date_str,
            "dt": parsedate_to_datetime(date_str),
        })
    
    # 增量规则：发布时间不早于上次记录、且链接未抓过的条目都算新条目
    # （同一时刻可能发布多条，如 FOMC 声明与经济预测，所以用 >= 加链接去重）
    state = load_state()
    last_dt = parsedate_to_datetime(state["last_date"]) if state["last_date"] else None
    seen = set(state["seen_links"])
    new_items = [
        it for it in items
        if it["link"] not in seen and (last_dt is None or it["dt"] >= last_dt)
    ]
    
    if not new_items:
        print(f"[无更新] 最新公告仍是：{items[0]['title']} ({items[0]['date']})")
        return
    
    # 按发布时间从旧到新依次抓取，保证 latest/previous 的先后顺序正确
    new_items.sort(key=lambda it: it["dt"])
    print(f"[发现 {len(new_items)} 条新公告]")
    for it in new_items:
        print(f"正在抓取：{it['date']} | {it['title']}")
        body_text = fetch_article_body(it["link"])
        record = f"标题: {it['title']}\n发布时间: {it['date']}\n原文链接: {it['link']}\n\n--- 正文内容 ---\n{body_text}"
        
        archive_name = os.path.splitext(os.path.basename(it["link"]))[0] + ".txt"
        with open(os.path.join(ARCHIVE_DIR, archive_name), "w", encoding="utf-8") as f:
            f.write(record)
        
        if STATEMENT_KEYWORD.lower() in it["title"].lower():
            update_latest_statement(record)
            print("  -> 新 FOMC 声明，已更新 data/latest_policy.txt")
        
        # 每抓完一条就保存进度，中途失败时下次可从断点继续
        state["seen_links"].append(it["link"])
        state["last_date"] = it["date"]
        save_state(state)
        
    print(f"抓取完成！全部公告已存档至 {ARCHIVE_DIR}")

if __name__ == "__main__":
    main()