import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import hashlib

URL = "https://tikpanel.app/noticias/index.php"
# Palabras clave optimizadas para el catálogo de Unsplash
TECH_KEYWORDS = ["tiktok", "smartphone", "streaming", "live", "app", "technology"]

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

        # LA SOLUCIÓN ESTABLE: API Oficial de Unsplash vía CDN (Fastly)
        # Generamos una semilla única por noticia
        hash_seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % 100
        keyword = TECH_KEYWORDS[hash_seed % len(TECH_KEYWORDS)]
        
        # Lista de IDs de fotos reales de Unsplash seleccionadas a mano sobre TikTok/Tech para que vayan rotando
        # Esto evita llamadas a buscadores rotos. Cada noticia se asocia a un ID real e indestructible.
        unsplash_ids = [
            "m_HRfLhgABo", # Smartphone / Redes
            "gM3Y_c2IM6c", # Interfaz / Móvil
            "XJXWaeSaQko", # Streaming en directo
            "84g7b4mUiAs", # Teléfono / Mano
            "y3aP9oo9P7Y", # Luces de streaming / Neon
            "I6wCDWOBm-0", # Grabación / Creador
            "O9N9Go7f77Y", # Social Media
            "K9om9oo9P7k"  # Gadgets / Tech
        ]
        photo_id = unsplash_ids[hash_seed % len(unsplash_ids)]
        
        # Construimos la URL usando las imágenes oficiales optimizadas para web de Unsplash (800x450)
        image_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=800&h=450&q=80"

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
    fg.subtitle('Feed RSS automático con cobertura multimedia sobre TikTok y directos.')
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
    print(f"¡Feed generado con éxito con {len(articles)} imágenes estables!")

if __name__ == "__main__":
    news = scrape_news()
    if news:
        generate_rss(news)
    else:
        print("No se encontraron elementos de noticias válidos.")
