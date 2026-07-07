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

        # IDs manuales de Unsplash (Móviles, streaming, setups e interfaces de apps)
        unsplash_ids = [
            "1511707171634-5f897ff02aa9", # Smartphone rosa/tecnología
            "1611162617213-7d7a39e9b1d7", # Icono de TikTok/Redes en pantalla
            "1516321318423-f06f85e504b3", # Pantalla digital/App
            "1616469829581-73993eb86b02", # Teléfono móvil en mano
            "1542751371-adc38448a05e", # Pantalla de streaming/Gaming
            "1563986768609-322da13575f3", # Interfaz móvil / Mobile app
            "1611605698335-8b15d27e83f9", # Redes sociales en smartphone
            "1460925895917-afdab827c52f"  # Analíticas / Panel de control tech
        ]
        
        hash_seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % len(unsplash_ids)
        photo_id = unsplash_ids[hash_seed]
        
        # Añadimos `&cb=` con el timestamp actual. Esto destruye la caché del lector RSS de raíz
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
    print(f"¡Feed regenerado con bypass de caché para imágenes!")

if __name__ == "__main__":
    news = scrape_news()
    if news:
        generate_rss(news)
    else:
        print("No se encontraron elementos de noticias válidos.")
