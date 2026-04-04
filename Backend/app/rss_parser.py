import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import httpx


def _fix_xml(content: str) -> str:
    """Исправляет незакрытые самозакрывающиеся теги в RSS."""
    # Простой подход: ищем <tag ...> без /> и заменяем > на />
    for tag in ("atom:link", "enclosure"):
        pattern = rf'(<{re.escape(tag)}\b[^>]*?)(?<!/)>'
        content = re.sub(pattern, r'\1/>', content)
    return content


async def validate_feed(url: str) -> dict | None:
    """
    Проверяет RSS/ATOM фид по URL.
    Возвращает dict с title, description, favicon_url или None если невалидный.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content = resp.text
    except Exception:
        return None

    content = _fix_xml(content)

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return None

    # RSS 2.0
    if root.tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return None
        title = _text(channel, "title")
        description = _text(channel, "description")
        link = _text(channel, "link")
        image_url = _text(channel, "image/url")
        favicon_url = image_url or _favicon_from_link(link)
        return {
            "title": title or urlparse(url).hostname,
            "description": description,
            "link": link,
            "favicon_url": favicon_url,
        }

    # ATOM
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    if root.tag == "{http://www.w3.org/2005/Atom}feed" or root.tag == "feed":
        title = _text_ns(root, "atom:title", ns) or _text(root, "title")
        subtitle = _text_ns(root, "atom:subtitle", ns) or _text(root, "subtitle")
        link_el = root.find("atom:link[@rel='alternate']", ns) or root.find("atom:link", ns)
        if link_el is None:
            link_el = root.find("link[@rel='alternate']") or root.find("link")
        link = link_el.get("href") if link_el is not None else None
        icon = _text_ns(root, "atom:icon", ns) or _text(root, "icon")
        logo = _text_ns(root, "atom:logo", ns) or _text(root, "logo")
        favicon_url = icon or logo or _favicon_from_link(link)
        return {
            "title": title or urlparse(url).hostname,
            "description": subtitle,
            "link": link,
            "favicon_url": favicon_url,
        }

    # RDF (RSS 1.0)
    rdf_ns = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
              "rss": "http://purl.org/rss/1.0/"}
    channel = root.find("rss:channel", rdf_ns)
    if channel is not None:
        title = _text_ns(channel, "rss:title", rdf_ns)
        description = _text_ns(channel, "rss:description", rdf_ns)
        link = _text_ns(channel, "rss:link", rdf_ns)
        return {
            "title": title or urlparse(url).hostname,
            "description": description,
            "link": link,
            "favicon_url": _favicon_from_link(link),
        }

    return None


def _text(el: ET.Element, path: str) -> str | None:
    child = el.find(path)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _text_ns(el: ET.Element, path: str, ns: dict) -> str | None:
    child = el.find(path, ns)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _favicon_from_link(link: str | None) -> str | None:
    if not link:
        return None
    parsed = urlparse(link)
    if parsed.scheme and parsed.hostname:
        return f"{parsed.scheme}://{parsed.hostname}/favicon.ico"
    return None
