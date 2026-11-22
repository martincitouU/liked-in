"""Formato Markdown: una entrada por post, un archivo por tema."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.fetcher import Post
from app.summarizer import Summary

TZ = ZoneInfo("America/Santiago")


def topic_title(slug: str) -> str:
    return slug.replace("-", " ").capitalize()


def format_entry(post: Post, summary: Summary, now: datetime | None = None) -> str:
    now = now or datetime.now(TZ)
    meta = [now.strftime("%Y-%m-%d")]
    if post.url:
        meta.append(f"[post original]({post.url})")
    if post.author:
        meta.append(post.author)

    lines = [f"## {summary.titulo}", "", f"*{' · '.join(meta)}*", "", summary.resumen, ""]
    if summary.ideas_clave:
        lines += [f"- {idea}" for idea in summary.ideas_clave] + [""]
    if summary.etiquetas:
        lines += [" ".join(f"`#{t}`" for t in summary.etiquetas), ""]
    lines += ["---", ""]
    return "\n".join(lines)


def append_entry(current: str | None, slug: str, entry: str) -> str:
    base = current or f"# {topic_title(slug)}\n\nNotas generadas por liked-in.\n"
    return base.rstrip("\n") + "\n\n" + entry


def build_index(topics: list[str]) -> str:
    lines = ["# Índice de aprendizaje", ""]
    lines += [f"- [{topic_title(slug)}]({slug}.md)" for slug in sorted(topics)]
    return "\n".join(lines) + "\n"


def count_entries(content: str) -> int:
    return sum(1 for line in content.splitlines() if line.startswith("## "))
