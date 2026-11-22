"""Tests del fetcher con HTML de ejemplo (sin llamadas reales a LinkedIn)."""

from app.fetcher import extract_urls, is_linkedin, parse_html

JSONLD_HTML = """
<html><head>
<meta property="og:title" content="Ana Pérez en LinkedIn: Tips de Kubernetes">
<meta property="og:description" content="Versión corta del post que viene en las etiquetas Open Graph.">
<script type="application/ld+json">
{"@type": "SocialMediaPosting",
 "articleBody": "Post completo: un Pod puede tener varios contenedores que comparten red.",
 "author": {"name": "Ana Pérez"}}
</script>
</head></html>
"""

OG_ONLY_HTML = """
<html><head>
<meta property="og:title" content="Ana Pérez en LinkedIn: Tips de Kubernetes">
<meta property="og:description" content="Versión corta del post que viene en las etiquetas Open Graph.">
</head></html>
"""


def test_prefiere_jsonld():
    post = parse_html("https://lnkd.in/x", JSONLD_HTML)
    assert post.source == "jsonld"
    assert post.author == "Ana Pérez"
    assert post.text.startswith("Post completo")


def test_usa_og_si_no_hay_jsonld():
    post = parse_html("https://lnkd.in/x", OG_ONLY_HTML)
    assert post.source == "og"
    assert post.author == "Ana Pérez"


def test_sin_texto_devuelve_none():
    assert parse_html("https://lnkd.in/x", "<html><head></head></html>") is None


def test_extrae_urls_de_un_mensaje_compartido():
    msg = "Mira esta publicación: https://lnkd.in/p/dzccW8A2 (vía LinkedIn)"
    assert extract_urls(msg) == ["https://lnkd.in/p/dzccW8A2"]


def test_detecta_links_de_linkedin():
    assert is_linkedin("https://www.linkedin.com/posts/abc")
    assert is_linkedin("https://lnkd.in/p/abc")
    assert not is_linkedin("https://github.com")
