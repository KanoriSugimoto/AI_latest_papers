import requests
from bs4 import BeautifulSoup
import os
import time

# === 設定 ===
KEYWORDS = [
    " transformer ", " llm ", " large lunguage model ", " convolutional neural network ", " cnn ", " vision transformer ", " vit ", " self-supervised learning ", " representation learning ", " foundation model ", 
    " object detection ", " object localization ", " region proposal ", " fast r-cnn ", " faster r-cnn ", " mask r-cnn ", " ssd ", " yolo ", " retainnet ", 
    " anchor-based detection ", " anchor-free detection ", " multi-class detection ", " image segmentation ", " semantic segmentation ", " instance segmentaion ", " panoptic segmentaion ", " weakly-supervised segmentaiton ", " unsupervised segmentaion ", 
    " u-net ", " deeplab ", " segformer ", " segment anything ", " mask2former ", " fcn ", " scene understanding ", " image classification ", " image recognition ", " keypoint detection ", " anomaly detevction ", 
    " remote sensing ", " satallite image ", " aerial imagery ", " few-shot learning ", " zero-shot learning ", " gemini ", " spatial understanding "
]
# KEYWORDS = [
#     " lunar "
# ]

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL") # channel URL
POSTED_TITLES_FILE = "posted_titles.txt" # for DailyPapers

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

def fetch_huggingface_papers():
    url_list = [
        "https://huggingface.co/papers",
        "https://rss.arxiv.org/rss/cs"
    ]
    for url in url_list:
        try:
            r = requests.get(url)
            r.raise_for_status()
        except Exception as e:
            print(f"Hugging Face 読み込みエラー: {e}")
            return []

    soup = BeautifulSoup(r.text, "html.parser")
    papers = []

    for item in soup.select("article"):
        title_tag = item.select_one("h3 a")
        summary_tag = item.select_one("p")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = "https://huggingface.co" + title_tag.get("href")
            summary = summary_tag.get_text(strip=True) if summary_tag else ""
            papers.append({
                "title": title,
                "summary": summary,
                "link": link
            })
    return papers

# === メイン処理 ===
def main():
    posted_titles = load_posted_titles()
    papers = fetch_huggingface_papers()

    for paper in papers:
        title = paper["title"]
        summary = paper["summary"]
        link = paper["link"]

        if not title or title in posted_titles:
            continue

        text_to_check = title + " " + summary

        if not KEYWORDS or matched_keywords(text_to_check):
            matched = matched_keywords(text_to_check) if KEYWORDS else ["All"]
            tags = " ".join(f"#{k.capitalize().strip()}" for k in matched)
            message = f"{title}\n{link}\n{tags}"
            print("Posting to Slack:\n", message)
            post_to_slack(message)
            save_posted_title(title)
            time.sleep(1) # Slack制限対策

#         matched = matched_keywords(title + " " + summary)
#         if matched:
#             tags = " ".join(f"#{k.capitalize().strip()}" for k in matched)
#             message = f"{title}\n{link}\n{tags}"
#             print("Posting to Slack:\n", message)
#             post_to_slack(message)
#             save_posted_title(title)
#             time.sleep(1) # Slack制限対策

if __name__ == "__main__":
    main()
