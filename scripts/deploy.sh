#!/bin/bash
set -e

echo "=== git pull ==="
git pull

echo "=== fastapi 빌드 & 푸시 ==="
docker build -t landsoftdocker/clms-fastapi:latest ./backend
docker push landsoftdocker/clms-fastapi:latest

echo "=== nuxt 빌드 & 푸시 ==="
docker build -t landsoftdocker/clms-nuxt:latest ./frontend
docker push landsoftdocker/clms-nuxt:latest

echo "=== 배포 완료 ==="