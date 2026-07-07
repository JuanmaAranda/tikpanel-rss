import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import hashlib
import time

URL = "https://tikpanel.app/noticias/index.php"

def scrape_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error al conectar con la web: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    items = soup.find_all(['div', 'article', 'section'], class_=lambda c: c and any(w in c.lower() for w in ['post', 'noticia', 'item', 'card', 'block', 'row', 'col']))
    
    if not items or len(items) < 2:
        items = soup.find_all(['h2', 'h3', 'h4', 'p', 'a'])

    for i, item in enumerate(items):
        link_el = item.find('a', href=True) if hasattr(item, 'find') else None
        if not link_el and item.name == 'a' and item.has_attr('href'):
            link_el = item
            
        if not link_el:
            continue
            
        link = link_el['href']
        if link.startswith('#') or 'javascript' in link or len(link) < 3:
            continue
            
        if link.startswith('/'):
            link = "https://tikpanel.app" + link
        elif not link.startswith('http'):
            link = "https://tikpanel.app/noticias/" + link

        title = link_el.get_text(strip=True)
        if not title and hasattr(item, 'get_text'):
            title = item.get_text(strip=True)
            
        if not title or len(title) < 8 or title.lower() in ['leer más', 'ver más', 'noticias', 'inicio', 'index']:
            continue

        if any(a['link'] == link for a in articles):
            continue

        desc = ""
        if hasattr(item, 'find_next'):
            next_p = item.find_next('p')
            if next_p:
                desc = next_p.get_text(strip=True)
        
        if not desc and hasattr(item, 'parent') and item.parent:
            p_elements = item.parent.find_all('p')
            for p in p_elements:
                p_text = p.get_text(strip=True)
                if p_text and len(p_text) > 15:
                    desc = p_text
                    break
                    
        if not desc or len(desc) < 10:
            desc = f"Últimas novedades publicadas en la sección de noticias de TikPanel: {title}."

        # Galería ampliada de 30 imágenes fijas sobre streaming, smartphones y apps
        unsplash_ids = [
            "1511707171634-5f897ff02aa9", "1611162617213-7d7a39e9b1d7", "1516321318423-f06f85e504b3",
            "1616469829581-73993eb86b02", "1542751371-adc38448a05e", "1563986768609-322da13575f3",
            "1611605698335-8b15d27e83f9", "1460925895917-afdab827c52f", "1611162616305-c47c3ae6302e",
            "1526374965328-7f61d4dc18c5", "1550751827-4bd374c3f58b", "1531297484001-80022131f5a1",
            "1618005182384-a83a8bd57fbe", "1607604276583-eef5d076aa5f", "1588702547919-201b11722234",
            "1614064641938-3bbee52942c7", "1573164713988-8665fc963095", "1562577309-4932fdd64cd1",
            "1544197150-b99a580bb7a8", "1519389950473-47ba0277781c", "1611926653458-09294b3142bf",
            "1555066931-4365d14bab8c", "1626379616456-b36cff125028", "1547082299-de196ea013d6",
            "1611162616415-fbd343a4de62", "1568605117036-5fe5e7bab0b7", "1610563166150-b34df4f3bcd6",
            "1548345680-f5475ea5df84", "1523961131990-5ea7c61b2107", "1611162617254-2a7410f02157"
        ]
        
        # El hash asegura que a cada título le toque un ID de la lista de forma matemática y pseudoaleatoria
        hash_seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % len(unsplash_ids)
        photo_id = unsplash_ids[hash_seed]
        
        cache_buster = int(time.time())
        image_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=800&h=450&q=80&cb={cache_buster}"

        stable_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        articles.append({
            "title": title,
            "link": link,
            "description": desc,
            "image": image_url,
            "date": stable_date
        })

    return articles[:15]

def generate_rss(articles):
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("TikPanel Noticias")
    fg.author({'name': 'Juanma Aranda'})
    fg.link(href=URL, rel='alternate')
    fg.subtitle('Feed RSS automático enfocado en TikTok y herramientas de streaming.')
    fg.language('es')

    for article in articles:
        fe = fg.add_entry()
        fe.id(article['link'])
        fe.title(article['title'])
        fe.link(href=article['link'])
        
        content_html = (
            f'<p><img src="{article["image"]}" alt="{article["title"]}" style="width:100%; max-width:600px; height:auto; border-radius:8px;" /></p>'
            f'<p>{article["description"]}</p>'
            f'<p><a href="{article["link"]}">Leer artículo completo en TikPanel</a></p>'
        )
        fe.description(content_html)
        fe.enclosure(article['image'], 0, 'image/jpeg')
        fe.pubDate(article['date'].astimezone().strftime('%a, %d %b %Y %H:%M:%S %z'))

    fg.rss_file('feed.xml', pretty=True)
    print(f"¡Feed regenerado con un catálogo de 30 imágenes de tecnología!")

if __name__ == "__main__":
    news = scrape_news()
    if news:
        generate_rss(news)
    else:
        print("No se encontraron elementos de noticias válidos.")
