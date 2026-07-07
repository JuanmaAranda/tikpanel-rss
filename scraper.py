import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import random
import hashlib

URL = "https://tikpanel.app/noticias/index.php"
TECH_KEYWORDS = ["tiktok", "smartphone", "streaming", "live-stream", "influencer", "social-media"]

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

    # Buscamos bloques comunes de noticias en PHP (filas, columnas, contenedores de post)
    items = soup.find_all(['div', 'article', 'section'], class_=lambda c: c and any(w in c.lower() for w in ['post', 'noticia', 'item', 'card', 'block', 'row', 'col']))
    
    # Si la lista es muy genérica, buscamos directamente donde haya enlaces significativos
    if not items or len(items) < 2:
        items = soup.find_all(['h2', 'h3', 'h4', 'p', 'a'])

    for i, item in enumerate(items):
        # 1. ENCONTRAR EL ENLACE Y EL TÍTULO
        link_el = item.find('a', href=True) if hasattr(item, 'find') else None
        if not link_el and item.name == 'a' and item.has_attr('href'):
            link_el = item
            
        if not link_el:
            continue
            
        link = link_el['href']
        # Saltar enlaces internos irrelevantes o vacíos
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

        # Evitar duplicados exactos de enlaces en la misma ejecución
        if any(a['link'] == link for a in articles):
            continue

        # 2. CAPTURAR EL TEXTO / PRIMER PÁRRAFO
        # Buscamos el texto adyacente o un párrafo dentro del mismo bloque
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

        # 3. IMÁGENES ESTABLES
        # Usamos el título para generar una semilla única. Así la foto de una noticia 
        # siempre será la misma y no cambiará cada vez que el script se vuelva a ejecutar.
        hash_seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % 100
        keyword = TECH_KEYWORDS[hash_seed % len(TECH_KEYWORDS)]
        image_url = f"https://picsum.photos/800/450?random={hash_seed}"

        # 4. FECHA ESTABLE
        # Al no tener fecha en el HTML, si cambia cada hora el lector piensa que es una noticia nueva.
        # Marcamos la fecha de hoy a las 00:00 para evitar que los lectores se vuelvan locos duplicando posts.
        stable_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        articles.append({
            "title": title,
            "link": link,
            "description": desc,
            "image": image_url,
            "date": stable_date
        })

    return articles[:15] # Devolvemos un máximo de 15 noticias limpias

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
        
        # Inyectamos la imagen directamente en formato HTML limpio dentro del contenido
        content_html = (
            f'<p><img src="{article["image"]}" alt="{article["title"]}" style="width:100%; max-width:600px; height:auto; border-radius:8px;" /></p>'
            f'<p>{article["description"]}</p>'
            f'<p><a href="{article["link"]}">Leer artículo completo en TikPanel</a></p>'
        )
        fe.description(content_html)
        fe.enclosure(article['image'], 0, 'image/jpeg')
        fe.pubDate(article['date'].astimezone().strftime('%a, %d %b %Y %H:%M:%S %z'))

    fg.rss_file('feed.xml', pretty=True)
    print(f"¡Feed generado con éxito con {len(articles)} artículos!")

if __name__ == "__main__":
    news = scrape_news()
    if news:
        generate_rss(news)
    else:
        print("No se encontraron elementos de noticias válidos.")
