"""Dónde se guardan las notas: una carpeta local (desarrollo) o el repo de GitHub (producción)."""

import base64
import os
from pathlib import Path

import httpx

GITHUB_API = "https://api.github.com"


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


class GitHubStorage:
    """Lee y escribe archivos con la Contents API: cada write es un commit en el repo de notas."""

    def __init__(self, token: str, repo: str, branch: str = "main", folder: str = "notas", client=None):
        self.repo, self.branch, self.folder = repo, branch, folder
        self.client = client or httpx.AsyncClient(
            base_url=GITHUB_API,
            timeout=20,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        self._shas: dict[str, str] = {}  # GitHub exige el sha actual para sobrescribir un archivo

    def _path(self, name: str = "") -> str:
        base = f"/repos/{self.repo}/contents/{self.folder}"
        return f"{base}/{name}" if name else base

    async def list_topics(self) -> list[str]:
        resp = await self.client.get(self._path(), params={"ref": self.branch})
        if resp.status_code == 404:  # la carpeta aún no existe
            return []
        resp.raise_for_status()
        return sorted(
            item["name"].removesuffix(".md")
            for item in resp.json()
            if item["type"] == "file" and item["name"].endswith(".md") and item["name"] != "README.md"
        )

    async def read(self, name: str) -> str | None:
        resp = await self.client.get(self._path(name), params={"ref": self.branch})
        if resp.status_code == 404:
            self._shas.pop(name, None)
            return None
        resp.raise_for_status()
        data = resp.json()
        self._shas[name] = data["sha"]
        return base64.b64decode(data["content"]).decode("utf-8")

    async def write(self, name: str, content: str, message: str) -> None:
        body = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode(),
            "branch": self.branch,
        }
        if name in self._shas:
            body["sha"] = self._shas[name]
        resp = await self.client.put(self._path(name), json=body)
        resp.raise_for_status()
        self._shas[name] = resp.json()["content"]["sha"]


def make_storage():
    """Elige el almacenamiento según la variable STORAGE (local por defecto)."""
    if os.getenv("STORAGE", "local") == "github":
        return GitHubStorage(
            token=os.environ["GITHUB_TOKEN"],
            repo=os.environ["GITHUB_REPO"],
            branch=os.getenv("GITHUB_BRANCH", "main"),
            folder=os.getenv("NOTES_DIR", "notas"),
        )
    return LocalStorage(os.getenv("NOTES_LOCAL_DIR", "salida/notas"))
