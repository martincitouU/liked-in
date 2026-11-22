import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.fetcher import extract_urls, fetch_post, is_linkedin

load_dotenv()
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
# httpx registra cada URL, y las URLs de Telegram llevan el token: lo silenciamos.
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("liked-in")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hola! Compárteme un post de LinkedIn (Compartir → Telegram) y lo leo.")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    links = [u for u in extract_urls(update.message.text) if is_linkedin(u)]
    if not links:
        await update.message.reply_text("Mándame un link de LinkedIn.")
        return

    post = await fetch_post(links[0])
    if post is None:
        await update.message.reply_text("No pude leer ese post. Más adelante te pediré el texto.")
        return

    autor = post.author or "?"
    await update.message.reply_text(
        f"Leído ✅\nAutor: {autor}\nFuente: {post.source} · {len(post.text)} caracteres\n\n{post.text[:300]}…"
    )


def main() -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    allowed_user = int(os.environ["ALLOWED_USER_ID"])

    app = Application.builder().token(token).build()
    only_me = filters.User(user_id=allowed_user)
    app.add_handler(CommandHandler("start", start, filters=only_me))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & only_me, on_text))

    log.info("liked-in escuchando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
EOF
