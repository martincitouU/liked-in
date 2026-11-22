"""Bot de Telegram de liked-in: lee posts de LinkedIn, los resume y los guarda como notas."""

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.fetcher import extract_urls, fetch_post, is_linkedin
from app.pipeline import Pipeline
from app.storage import make_storage
from app.summarizer import Summarizer

load_dotenv()
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
# httpx registra cada URL, y las URLs de Telegram llevan el token: lo silenciamos.
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("liked-in")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hola! Compárteme un post de LinkedIn (Compartir → Telegram) y lo guardo."
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    links = [u for u in extract_urls(update.message.text) if is_linkedin(u)]
    if not links:
        await update.message.reply_text("Mándame un link de LinkedIn.")
        return

    post = await fetch_post(links[0])
    if post is None:
        await update.message.reply_text("No pude leer ese post. Más adelante te pediré el texto.")
        return

    status = await update.message.reply_text("Resumiendo…")
    try:
        result = await context.application.bot_data["pipeline"].process(post)
    except Exception:
        log.exception("Error procesando %s", post.url)
        await status.edit_text("Algo falló al resumir o guardar. Revisa la terminal.")
        return

    if result.duplicate:
        await status.edit_text(f"Ese post ya estaba guardado en {result.topic_file}.")
        return

    s = result.summary
    nuevo = " (tema nuevo)" if result.new_topic else ""
    ideas = "\n".join(f"• {idea}" for idea in s.ideas_clave)
    header = f"✅ {result.topic_file}{nuevo} · {result.total_in_topic} nota(s)"
    await status.edit_text(f"{header}\n\n{s.titulo}\n{s.resumen}\n\n{ideas}")


def main() -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    allowed_user = int(os.environ["ALLOWED_USER_ID"])
    summarizer = Summarizer(os.environ["ANTHROPIC_API_KEY"], os.getenv("LLM_MODEL", "claude-haiku-5-5"))
    storage = make_storage()

    app = Application.builder().token(token).build()
    app.bot_data["pipeline"] = Pipeline(summarizer, storage)
    only_me = filters.User(user_id=allowed_user)
    app.add_handler(CommandHandler("start", start, filters=only_me))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & only_me, on_text))

    log.info("liked-in escuchando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
