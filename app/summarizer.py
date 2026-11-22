"""Resume un post con Claude y lo clasifica en un tema."""

import json
import re
from dataclasses import dataclass, field

from anthropic import AsyncAnthropic

PROMPT = """Eres mi asistente de aprendizaje. Te paso un post de LinkedIn que guardé.
Responde SOLO con un objeto JSON (sin texto extra ni ```), en español, con estas claves:

- "tema": slug corto en minúsculas con guiones que agrupe el post (ej. "kubernetes",
  "carrera-profesional", "ia-generativa"). Si encaja en un tema existente, usa ese mismo slug.
  Temas existentes: {temas}
- "titulo": título breve y descriptivo (máx. 10 palabras), no copies la primera línea.
- "resumen": 2 a 3 oraciones con lo esencial.
- "ideas_clave": lista de 2 a 5 aprendizajes concretos.
- "etiquetas": lista de 1 a 4 etiquetas cortas en minúsculas.

Autor: {autor}
Post:
\"\"\"
{texto}
\"\"\""""


@dataclass
class Summary:
    tema: str
    titulo: str
    resumen: str
    ideas_clave: list[str] = field(default_factory=list)
    etiquetas: list[str] = field(default_factory=list)


def slugify(value: str) -> str:
    value = value.lower().strip()
    for a, b in zip("áéíóúüñ", "aeiouun", strict=True):
        value = value.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "general"


def parse_response(raw: str) -> Summary:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"El modelo no devolvió JSON: {raw[:200]}")
    data = json.loads(match.group(0))
    return Summary(
        tema=slugify(str(data.get("tema", "general"))),
        titulo=str(data.get("titulo", "Sin título")).strip(),
        resumen=str(data.get("resumen", "")).strip(),
        ideas_clave=[str(x).strip() for x in data.get("ideas_clave", []) if str(x).strip()],
        etiquetas=[slugify(str(x)) for x in data.get("etiquetas", []) if str(x).strip()],
    )


class Summarizer:
    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def summarize(self, text: str, author: str, topics: list[str]) -> Summary:
        prompt = PROMPT.format(
            temas=", ".join(topics) or "(ninguno aún)",
            autor=author or "desconocido",
            texto=text[:12000],
        )
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(block.text for block in msg.content if block.type == "text")
        return parse_response(raw)
