import os
import re
import html
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import time

URL = "https://tikpanel.app/noticias/index.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def extraer_og_image(article_url):
    """Descarga la noticia y devuelve su imagen original (og:image / twitter:image).

    Cada post publicado en TikPanel ya incluye la imagen de la fuente original en sus
    metadatos Open Graph (los añade panel/backfill_og.php). Aquí simplemente la leemos
    en lugar de inventar una imagen aleatoria.
    """
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  No se pudo leer la imagen de {article_url}: {e}")
        return ""

    h = resp.text
    patrones = [
        r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url|:url)?["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']og:image(?::secure_url|:url)?["\']',
        r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*name=["\']twitter:image(?::src)?["\']',
    ]
    for patron in patrones:
        m = re.search(patron, h, re.IGNORECASE)
        if m:
            # Decodificar entidades HTML (&amp; -> &) para que la URL sea válida
            return html.unescape(m.group(1).strip())
    return ""


def scrape_news():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
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

        # Imagen original de la noticia: la que ya trae el propio post en su og:image
        # (imagen de la fuente original). Si el post no tuviera imagen, se queda vacía
        # y el artículo simplemente se publica sin imagen destacada.
        image_url = extraer_og_image(link)

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

        img = article.get('image')
        if img:
            content_html = (
                f'<p><img src="{img}" alt="{article["title"]}" style="width:100%; max-width:600px; height:auto; border-radius:8px;" /></p>'
                f'<p>{article["description"]}</p>'
                f'<p><a href="{article["link"]}">Leer artículo completo en TikPanel</a></p>'
            )
        else:
            content_html = (
                f'<p>{article["description"]}</p>'
                f'<p><a href="{article["link"]}">Leer artículo completo en TikPanel</a></p>'
            )
        fe.description(content_html)
        if img:
            fe.enclosure(img, 0, 'image/jpeg')
        fe.pubDate(article['date'].astimezone().strftime('%a, %d %b %Y %H:%M:%S %z'))

    fg.rss_file('feed.xml', pretty=True)
    print(f"¡Feed regenerado usando la imagen original de cada noticia!")


if __name__ == "__main__":
    news = scrape_news()
    if news:
        generate_rss(news)
    else:
        print("No se encontraron elementos de noticias válidos.")
