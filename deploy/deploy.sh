#!/bin/bash
# Se ejecuta EN la instancia EC2 vía SSM (no en tu Mac ni en GitHub).
# El workflow antepone "export IMAGE_TAG=sha-xxxxxxx" antes de este script.
set -euo pipefail

IMAGE="ghcr.io/martincitouu/liked-in:${IMAGE_TAG:-latest}"
REGION="us-east-2"
ENV_FILE="/opt/liked-in/.env"

echo "==> Leyendo configuración y secretos desde SSM"
umask 077
aws ssm get-parameters-by-path --path /liked-in --with-decryption --region "$REGION" \
  --query "Parameters[].[Name,Value]" --output text |
  while IFS=$'\t' read -r name value; do
    printf '%s=%s\n' "${name##*/}" "$value"
  done >"${ENV_FILE}.tmp"
mv "${ENV_FILE}.tmp" "$ENV_FILE"
echo "    $(wc -l <"$ENV_FILE") variables cargadas"

echo "==> Descargando $IMAGE"
docker pull --quiet "$IMAGE"

echo "==> Reemplazando el contenedor"
docker rm -f liked-in >/dev/null 2>&1 || true
docker run -d --name liked-in --restart unless-stopped \
  --env-file "$ENV_FILE" \
  --log-opt max-size=10m --log-opt max-file=3 \
  "$IMAGE" >/dev/null

echo "==> Verificando que arranque bien"
sleep 15
running=$(docker inspect -f '{{.State.Running}}' liked-in)
restarts=$(docker inspect -f '{{.RestartCount}}' liked-in)
docker logs --tail 10 liked-in
if [ "$running" != "true" ] || [ "$restarts" != "0" ]; then
  echo "ERROR: el contenedor no quedó estable (running=$running, reinicios=$restarts)"
  exit 1
fi

echo "==> Limpiando imágenes de más de 7 días"
docker image prune -af --filter "until=168h" >/dev/null || true

echo "==> Deploy OK: $IMAGE"
