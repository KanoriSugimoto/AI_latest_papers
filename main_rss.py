import feedparser
import requests
import os
import time

# === 設定 ===
RSS_FEEDS = [
    "https://export.arxiv.org/rss/cs.LG", # Arxiv
]

KEYWORDS = [
    " transformer ", 
    " object detection ", " single shot detection ", 
    " image segmentation ", " semantic segmentation ", " instance segmentation ",
    " scene understanding ", " image classification ", " image recognition ", " feature extraction ", " keypoint detection ", " anomaly detection ", " remote sensing ", " satellite image ", " aerial imagery ", " few-shot learning ", " zero-shot learning "
] # "planet", "solar system",  "kuiper belt", "pluto", "eris", "ceres", "makemake", "haumea", 

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
POSTED_TITLES_FILE = "posted_titles.txt"

# === ユーティリティ関数 ===
def load_posted_titles():
    if os.path.exists(POSTED_TITLES_FILE):
        with open(POSTED_TITLES_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_posted_title(title):
    with open(POSTED_TITLES_FILE, "a", encoding="utf-8") as f:
        f.write(title + "\n")

def contains_keywords(text):
    text = text.lower()
    return any(keyword in text for keyword in KEYWORDS)

def matched_keywords(text):
    text = text.lower()
    matched = [keyword for keyword in KEYWORDS if keyword in text]
    return matched

def post_to_slack(message):
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code != 200:
        print(f"Slack送信失敗: {response.status_code} {response.text}")

# === メイン処理 ===
def main():
    posted_titles = load_posted_titles()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"RSS読み込みエラー: {feed_url} : {e}")
            continue

        journal = feed.feed.get("title", "Unknown journal")

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()
            link = entry.get("link", "")

            if not title or title in posted_titles:
                continue

            text_to_check = title + " " + summary
            # if contains_keywords(text_to_check):
            matched = matched_keywords(text_to_check)
            if matched:
                # タグの生成（例: "#Mercury #Comet"）
                tags = " ".join(f"#{k.capitalize()}" for k in matched)

                # 著者名から first author を抽出
                # author = entry.get("author", "Unknown author")
                if hasattr(entry, "author") and entry.author:
                    raw_author = entry.author.strip()
                    if "," in raw_author:
                        first_author = raw_author.split(",")[0].strip()
                    elif " and " in raw_author:
                        first_author = raw_author.split(" and ")[0].strip()
                    else:
                        first_author = raw_author
                else:
                    first_author = "Unknown author"

                message = f"{title}\n{link}\n{tags}"
                # message = f"{title}\n{first_author}, {journal}, {link}"
                print("Posting to Slack:\n", message)
                post_to_slack(message)
                save_posted_title(title)
                time.sleep(1)  # Slack制限対策

if __name__ == "__main__":
    main()
