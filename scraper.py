import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import random

# URL de la sección de noticias
URL = "https://tikpanel.app/noticias/index.php"

# Términos de búsqueda para que Unsplash devuelva fotos relevantes
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

    items = soup.find_all(['article', 'div'], class_=lambda c: c and any(word in c.lower() for word in ['post', 'noticia', 'item', 'card']))
    
    if not items:
        items = soup.find_all('article')
        
    if not items:
        items = soup.find_all('h2') or soup.find_all('h3')

    for i, item in enumerate(items[:15]):
        title_el = item.find(['h2', 'h3', 'h4', 'a']) or item
        title = title_el.get_text(strip=True)
        
        if not title or len(title) < 5:
            continue

        link_el = item.find('a', href=True) if hasattr(item, 'find') else None
        if not link_el and item.name == 'a':
            link_el = item
            
        link = link_el['href'] if link_el else URL
        if link.startswith('/'):
            link = "https://tikpanel.app" + link
        elif not link.startswith('http'):
            link = "https://tikpanel.app/noticias/" + link

        desc_el = item.find(['p', 'div'], class_=lambda c: c and 'desc' in str(c).lower())
        desc = desc_el.get_text(strip=True) if desc_el else "Nueva actualización en TikPanel Noticias."

        # Elegimos una palabra clave aleatoria priorizando TikTok y streaming
        keyword = random.choice(TECH_KEYWORDS)
        
        # Usamos el servicio de Unsplash Source para obtener fotos de stock gratuitas basadas en la palabra clave.
        # Añadimos el índice "sig={i}" para forzar a que cada artículo tenga una foto distinta en el lector de RSS.
        image_url = f"https://source.unsplash.com/featured/800x450/?{keyword}&sig={i}"

        articles.append({
            "title": title,
            "link": link,
            "description": desc,
            "image": image_url,
            "date": datetime.now()
        })

    return articles

def generate_rss(articles):
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("TikPanel Noticias - RSS Feed")
    fg.author({'name': 'TikPanel RSS Scraper'})
    fg.link(href=URL, rel='alternate')
    fg.logo('https://tikpanel.app/favicon.ico')
    fg.subtitle('Feed RSS automatizado con imágenes de TikTok y tecnología')
    fg.language('es')

    for article in articles:
        fe = fg.add_entry()
        fe.id(article['link'])
        fe.title(article['title'])
        fe.link(href=article['link'])
        
        # Estructura visual para lectores RSS modernos
        content_with_image = f'<img src="{article["image"]}" alt="{article["title"]}" style="width:100%; max-width:600px; height:auto; margin-bottom:10px;"/><br/>{article["description"]}'
        fe.description(content_with_image)
        
        fe.enclosure(article['image'], 0, 'image/jpeg')
        fe.pubDate(article['date'].astimezone().strftime('%a, %d %b %Y %H:%M:%S %z'))

    fg.rss_file('feed.xml', pretty=True)
    print("¡Archivo feed.xml actualizado con imágenes temáticas de TikTok!")

if __name__ == "__main__":
    news = scrape_news()
    if news:
        generate_rss(news)
    else:
        print("No se pudieron extraer noticias.")
