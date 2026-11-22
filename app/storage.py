"""Dónde se guardan las notas. Por ahora, una carpeta local (en el paso 7 se suma GitHub)."""

from pathlib import Path


class LocalStorage:
    def __init__(self, folder: str):
        self.dir = Path(folder)
        self.dir.mkdir(parents=True, exist_ok=True)

    async def list_topics(self) -> list[str]:
        return sorted(p.stem for p in self.dir.glob("*.md") if p.stem != "README")

    async def read(self, name: str) -> str | None:
        path = self.dir / name
        return path.read_text(encoding="utf-8") if path.exists() else None

    async def write(self, name: str, content: str, message: str) -> None:
        (self.dir / name).write_text(content, encoding="utf-8")
