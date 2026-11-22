"""Obtiene el texto de un post público de LinkedIn.

Estrategia, de mejor a peor:
1. JSON-LD (<script type="application/ld+json">) -> articleBody completo + autor.
2. Etiquetas Open Graph (og:description) -> texto, a veces truncado.
Si LinkedIn devuelve el muro de login (authwall) o el código 999 anti-bots,
devuelve None y el bot le pide el texto al usuario.
"""

import json
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)
URL_RE = re.compile(r"https?://\S+")
MIN_TEXT_LEN = 40  # menos que esto no vale la pena resumir


@dataclass
class Post:
    url: str
    text: str
    author: str = ""
    source: str = ""  # "jsonld", "og" o "manual"


def extract_urls(message: str) -> list[str]:
    return [u.rstrip(").,>\"'") for u in URL_RE.findall(message or "")]


def is_linkedin(url: str) -> bool:
    return "linkedin.com" in url or "lnkd.in" in url


def _from_jsonld(soup: BeautifulSoup) -> tuple[str, str]:
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            if not isinstance(item, dict):
                continue
            body = item.get("articleBody") or item.get("text") or ""
            if body:
                author = item.get("author") or {}
                if isinstance(author, list):
                    author = author[0] if author else {}
                name = author.get("name", "") if isinstance(author, dict) else str(author)
                return body.strip(), name.strip()
    return "", ""


def _from_og(soup: BeautifulSoup) -> tuple[str, str]:
    def meta(prop: str) -> str:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        return (tag.get("content") or "").strip() if tag else ""

    text = meta("og:description") or meta("description")
    title = meta("og:title")
    # og:title suele venir como "Nombre en LinkedIn: texto..."
    author = title.split(" en LinkedIn")[0].split(" on LinkedIn")[0] if title else ""
    return text, author


def parse_html(url: str, html: str) -> Post | None:
    soup = BeautifulSoup(html, "html.parser")
    text, author = _from_jsonld(soup)
    source = "jsonld"
    if len(text) < MIN_TEXT_LEN:
        text, author = _from_og(soup)
        source = "og"
    if len(text) < MIN_TEXT_LEN:
        return None
    return Post(url=url, text=text, author=author, source=source)


async def fetch_post(url: str, client: httpx.AsyncClient | None = None) -> Post | None:
    own_client = client is None
    client = client or httpx.AsyncClient(
        follow_redirects=True,
        timeout=20,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        },
    )
    try:
        resp = await client.get(url)
    except httpx.HTTPError:
        return None
    finally:
        if own_client:
            await client.aclose()

    final_url = str(resp.url)
    if resp.status_code != 200 or "authwall" in final_url or "/login" in final_url:
        return None
    return parse_html(url, resp.text)
