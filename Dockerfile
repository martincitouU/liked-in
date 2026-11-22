FROM python:3.12-slim
# Aplica los parches de seguridad de Debian que la imagen base aún no trae
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
    
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Primero las dependencias: esta capa se cachea mientras requirements.txt no cambie
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Nunca correr como root dentro del contenedor
RUN useradd --create-home --uid 10001 bot
USER bot

CMD ["python", "-m", "app.bot"]
