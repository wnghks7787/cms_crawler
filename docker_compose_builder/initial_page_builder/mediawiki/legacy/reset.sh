#!/usr/bin/env bash
set -euo pipefail

# 처리할 버전:포트
VERSIONS=(
  "1.24.6:8102"
  "1.25.6:8103"
  "1.26.4:8104"
  "1.27.7:8105"
)

COMPOSE=~/mediawiki/legacy/compose.yml
PHPBASE_DEFAULT="php:5.6-apache"

for entry in "${VERSIONS[@]}"; do
  ver="${entry%%:*}"
  port="${entry##*:}"
  proj="mw_legacy_${ver//./_}"       # compose 프로젝트명(언더스코어)
  wiki="mw-legacy-${ver}"            # 컨테이너 이름(대시)
  db="${wiki}-db"                    # DB 컨테이너 이름(대시)

  echo "=== RESET MW ${ver} (port ${port}, project ${proj}) ==="

  # 1) 완전 초기화: 컨테이너/네트워크/볼륨 삭제
  MW_VER="$ver" docker compose -p "$proj" -f "$COMPOSE" down -v || true

  # 2) 재기동 (필수 env 넘기기)
  MW_VER="$ver" HOST_PORT="$port" PHP_BASE="${PHPBASE_DEFAULT}" \
  docker compose -p "$proj" -f "$COMPOSE" up -d

  # 3) DB 헬스체크 대기
  echo "[*] wait db health for ${db} ..."
  for i in {1..60}; do
    st="$(docker inspect --format '{{.State.Health.Status}}' "$db" 2>/dev/null || true)"
    [[ "$st" == "healthy" ]] && break
    sleep 2
  done

  # 4) 설치 + LocalSettings.php 주입
  echo "[*] run install.php on ${wiki} ..."
  docker exec -i "$wiki" bash -c "
    set -e; cd /var/www/html
    NEWPASS=\$(tr -dc A-Za-z0-9 </dev/urandom | head -c 20)A9!
    php maintenance/install.php \
      --dbtype mysql --dbserver \"\$MW_DB_HOST\" \
      --dbname \"\$MW_DB_NAME\" --dbuser \"\$MW_DB_USER\" --dbpass \"\$MW_DB_PASS\" \
      --scriptpath \"\" --lang en --pass \"\$NEWPASS\" \
      \"\$MW_SITE_NAME\" \"\$MW_ADMIN_USER\"

    printf '\n\$wgServer = \"http://localhost:${port}\";\n\$wgCanonicalServer = \$wgServer;\n' >> LocalSettings.php
    printf '\n\$wgShowExceptionDetails = true;\n' >> LocalSettings.php
    chown www-data:www-data LocalSettings.php
    php -l LocalSettings.php
    echo \"[INFO] Admin: \$MW_ADMIN_USER  Password: \$NEWPASS\"
  "

  # 5) 빠른 헬스체크
  echo "[*] check ${port}"
  curl -sSI "http://localhost:${port}/" | head -n 1 || true
  curl -sSI "http://localhost:${port}/api.php" | head -n 1 || true
done

echo "=== DONE ==="

