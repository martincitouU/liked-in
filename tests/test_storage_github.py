"""Tests de GitHubStorage con un servidor falso de httpx (no se llama a GitHub)."""

import asyncio
import base64
import json

import httpx

from app.storage import GitHubStorage


class FakeGitHub:
    """Simula la Contents API guardando los archivos en un diccionario."""

    def __init__(self):
        self.files: dict[str, tuple[str, str]] = {}  # ruta -> (contenido, sha)
        self.commits: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path.removeprefix("/repos/yo/aprendizaje/contents/")
        if request.method == "GET":
            if path == "notas":
                items = [{"name": p.split("/")[-1], "type": "file"} for p in self.files]
                return httpx.Response(200, json=items) if items else httpx.Response(404)
            if path not in self.files:
                return httpx.Response(404)
            content, sha = self.files[path]
            encoded = base64.b64encode(content.encode()).decode()
            return httpx.Response(200, json={"content": encoded, "sha": sha})

        body = json.loads(request.content)
        if path in self.files and body.get("sha") != self.files[path][1]:
            return httpx.Response(409)  # GitHub rechaza sobrescribir sin el sha correcto
        new_sha = f"sha{len(self.commits) + 1}"
        self.files[path] = (base64.b64decode(body["content"]).decode(), new_sha)
        self.commits.append(body["message"])
        return httpx.Response(200, json={"content": {"sha": new_sha}})


def make(fake: FakeGitHub) -> GitHubStorage:
    client = httpx.AsyncClient(base_url="https://api.github.com", transport=httpx.MockTransport(fake.handler))
    return GitHubStorage("token-falso", "yo/aprendizaje", client=client)


def test_crea_y_actualiza_un_archivo():
    fake = FakeGitHub()
    storage = make(fake)

    async def flujo():
        assert await storage.read("k8s.md") is None
        await storage.write("k8s.md", "v1", "nota 1")
        assert await storage.read("k8s.md") == "v1"
        await storage.write("k8s.md", "v2", "nota 2")

    asyncio.run(flujo())
    assert fake.files["notas/k8s.md"][0] == "v2"
    assert fake.commits == ["nota 1", "nota 2"]


def test_lista_temas_sin_readme():
    fake = FakeGitHub()
    fake.files = {"notas/README.md": ("", "a"), "notas/k8s.md": ("", "b"), "notas/aws.md": ("", "c")}
    assert asyncio.run(make(fake).list_topics()) == ["aws", "k8s"]


def test_carpeta_inexistente_no_tiene_temas():
    assert asyncio.run(make(FakeGitHub()).list_topics()) == []
