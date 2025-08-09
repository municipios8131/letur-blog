import requests
import hashlib
import sqlite3
import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

DB = 'posted.db'
CONTENT_DIR = Path('content/noticias')

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('CREATE TABLE IF NOT EXISTS seen(url TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

def seen_before(url):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT 1 FROM seen WHERE url=?', (url,))
    r = c.fetchone()
    if r:
        conn.close()
        return True
    c.execute('INSERT INTO seen(url) VALUES(?)', (url,))
    conn.commit()
    conn.close()
    return False

def fetch_google_news_rss(query="turismo Letur"):
    rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=es&gl=ES&ceid=ES:es"
    try:
        r = requests.get(rss_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("Error fetching Google News RSS:", e)
        return []
    root = ET.fromstring(r.text)
    items = []
    for item in root.findall('.//item'):
        title = item.find('title').text
        link = item.find('link').text
        if link and not seen_before(link):
            items.append({'title': title, 'url': link})
    return items

def save_post(item):
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    safe_title = item['title'].replace('"', '').replace("'", "")
    fname = CONTENT_DIR / f"{date}-{hashlib.md5(item['url'].encode()).hexdigest()}.md"
    content = f"---\ntitle: \"{safe_title}\"\ndate: {date}\n---\n\nÚltimas noticias relacionadas:\n\n- [{item['title']}]({item['url']})\n\nFuente: [Google News](https://news.google.com)\n"
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Noticia guardada: {fname}")

def main():
    init_db()
    news = fetch_google_news_rss()
    for item in news:
        save_post(item)

if __name__ == "__main__":
    main()
