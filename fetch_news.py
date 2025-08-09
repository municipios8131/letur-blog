import requests, hashlib, sqlite3, datetime
from bs4 import BeautifulSoup
from pathlib import Path

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

def fetch_turismoletur():
    url = "https://turismoletur.com/noticias/"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("Error fetching turismoletur:", e)
        return []
    soup = BeautifulSoup(r.text, 'html.parser')
    posts = []
    # Buscamos artículos en <article> o enlaces en el listado
    for article in soup.select('article'):
        h = article.select_one('h2') or article.select_one('h3')
        if not h: continue
        a = h.find('a')
        title = (a.get_text(strip=True) if a else h.get_text(strip=True))
        link = (a['href'] if a and a.has_attr('href') else None)
        if link and not link.startswith('http'):
            link = requests.compat.urljoin(url, link)
        if link and not seen_before(link):
            posts.append({'title': title, 'url': link, 'content': f"Más info en [fuente]({link})"})
    # fallback: buscar enlaces directos si no hay <article>
    if not posts:
        for a in soup.select('a'):
            href = a.get('href')
            txt = a.get_text(strip=True)
            if href and txt and '/noticias/' in href and not seen_before(href):
                link = href if href.startswith('http') else requests.compat.urljoin(url, href)
                posts.append({'title': txt[:80], 'url': link, 'content': f"Más info en [fuente]({link})"})
    return posts

def save_post(item):
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    fname = CONTENT_DIR / f"{date}-{hashlib.md5(item['url'].encode()).hexdigest()}.md"
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(f"---\ntitle: \"{item['title']}\"\ndate: {date}\n---\n\n{item['content']}\n\nFuente: {item['url']}\n")
    print(f"Post guardado: {fname}")

def main():
    init_db()
    items = []
    items += fetch_turismoletur()
    # Aquí puedes añadir más funciones: fetch_tablon(), fetch_ejemplo(), etc.
    for item in items:
        save_post(item)

if __name__ == "__main__":
    main()
