#!/bin/bash
# Se ejecuta UNA vez, en el primer arranque de la instancia.
set -euxo pipefail

dnf update -y
dnf install -y docker
systemctl enable --now docker

# Carpeta donde el deploy escribirá el .env (solo root)
install -d -m 700 /opt/liked-in
