import requests
import hashlib
import sqlite3
import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
import os
import openai

DB = 'posted.db'
CONTENT_DIR = Path('content/noticias')

# Inicializar OpenAI con la API key desde variable de entorno
openai.api_key = os.getenv('OPENAI_API_KEY')

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

def generate_news_content(title, url):
    prompt = (
        f"Escribe un breve artículo de noticias en español basado en este título: \"{title}\".\n"
        f"La noticia está basada en esta fuente: {url}\n"
        "Hazlo claro, informativo y profesional, alrededor de 100 palabras."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        text = response['choices'][0]['message']['content'].strip()
        return text
    except Exception as e:
        print("Error generando texto con OpenAI:", e)
        return f"Más información en [fuente]({url})"

def save_post(item, content):
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    safe_title = item['title'].replace('"', '').replace("'", "")
    fname = CONTENT_DIR / f"{date}-{hashlib.md5(item['url'].encode()).hexdigest()}.md"
    md = f"---\ntitle: \"{safe_title}\"\ndate: {date}\n---\n\n{content}\n\nFuente: [{item['title']}]({item['url']})\n"
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"Noticia guardada: {fname}")

def main():
    init_db()
    # Lista de búsquedas que quieras seguir
    queries = [
        "Letur Albacete",
        "turismo Letur",
        "Ayuntamiento de Letur"
    ]
    for query in queries:
        news_items = fetch_google_news_rss(query)
        for item in news_items:
            content = generate_news_content(item['title'], item['url'])
            save_post(item, content)


if __name__ == "__main__":
    main()
