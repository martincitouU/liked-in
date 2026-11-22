"""Tests de resumen, formato y pipeline, sin llamar a Claude (usamos un resumidor falso)."""

import asyncio

from app.fetcher import Post
from app.pipeline import Pipeline
from app.storage import LocalStorage
from app.summarizer import Summary, parse_response, slugify


class FakeSummarizer:
    def __init__(self, tema="kubernetes"):
        self.tema = tema

    async def summarize(self, text, author, topics):
        return Summary(self.tema, "Pods vs contenedores", "Un Pod agrupa contenedores.", ["Idea 1"], ["k8s"])


def test_parse_response_tolera_texto_extra():
    raw = 'Aquí va: {"tema": "Carrera Profesional", "titulo": "T", "resumen": "R", "ideas_clave": ["a"]}'
    s = parse_response(raw)
    assert s.tema == "carrera-profesional"
    assert s.ideas_clave == ["a"]


def test_slugify_quita_tildes():
    assert slugify("Ingeniería de Datos") == "ingenieria-de-datos"


def test_pipeline_guarda_nota_e_indice(tmp_path):
    pipeline = Pipeline(FakeSummarizer(), LocalStorage(str(tmp_path)))
    post = Post(url="https://lnkd.in/p/abc", text="texto", author="Ana")

    result = asyncio.run(pipeline.process(post))

    assert result.new_topic and result.total_in_topic == 1
    nota = (tmp_path / "kubernetes.md").read_text()
    assert "## Pods vs contenedores" in nota and "(https://lnkd.in/p/abc)" in nota
    assert "[Kubernetes](kubernetes.md)" in (tmp_path / "README.md").read_text()


def test_pipeline_no_duplica(tmp_path):
    pipeline = Pipeline(FakeSummarizer(), LocalStorage(str(tmp_path)))
    post = Post(url="https://lnkd.in/p/abc", text="texto")

    asyncio.run(pipeline.process(post))
    result = asyncio.run(pipeline.process(post))

    assert result.duplicate
    assert (tmp_path / "kubernetes.md").read_text().count("## ") == 1
