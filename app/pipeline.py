"""Une las piezas: post -> resumen -> entrada en el .md del tema."""

from dataclasses import dataclass

from app import notes
from app.fetcher import Post
from app.summarizer import Summary


@dataclass
class Result:
    summary: Summary
    topic_file: str
    total_in_topic: int
    new_topic: bool
    duplicate: bool = False


class Pipeline:
    def __init__(self, summarizer, storage):
        self.summarizer = summarizer
        self.storage = storage

    async def process(self, post: Post) -> Result:
        topics = await self.storage.list_topics()
        summary = await self.summarizer.summarize(post.text, post.author, topics)
        name = f"{summary.tema}.md"

        current = await self.storage.read(name)
        if current and post.url and f"({post.url})" in current:
            return Result(summary, name, notes.count_entries(current), False, duplicate=True)

        updated = notes.append_entry(current, summary.tema, notes.format_entry(post, summary))
        await self.storage.write(name, updated, f"nota: {summary.titulo}")

        new_topic = summary.tema not in topics
        if new_topic:
            await self.storage.read("README.md")  # GitHub necesita el sha si el índice ya existe
            index = notes.build_index([*topics, summary.tema])
            await self.storage.write("README.md", index, "índice: nuevo tema")
        return Result(summary, name, notes.count_entries(updated), new_topic)
