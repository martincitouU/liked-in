"""Prueba el paso delicado ANTES de montar todo: ¿puedo leer tus posts de LinkedIn?

Uso:
    python probar_links.py "https://www.linkedin.com/posts/..." "https://lnkd.in/..."
"""

import asyncio
import sys

from app.fetcher import fetch_post


async def main(urls: list[str]) -> None:
    ok = 0
    for url in urls:
        post = await fetch_post(url)
        if post:
            ok += 1
            autor = post.author or "?"
            print(f"✅ {url}\n   fuente: {post.source} | autor: {autor} | {len(post.text)} caracteres")
            print(f"   {post.text[:160].replace(chr(10), ' ')}…\n")
        else:
            print(f"❌ {url}\n   bloqueado o sin texto: el bot te pediría pegarlo\n")
    print(f"{ok}/{len(urls)} leídos automáticamente")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1:]))
