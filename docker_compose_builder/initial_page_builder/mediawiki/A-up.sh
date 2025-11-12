#!/usr/bin/env bash
set -euo pipefail

lineno=0

# A-versions.txt 를 FD 9로 열고 그 FD로만 읽는다 (stdin 오염 방지)
exec 9< A-versions.txt

while IFS=, read -r ver port <&9 || [ -n "${ver-}" ]; do
  lineno=$((lineno+1))
  ver="${ver//[[:space:]]/}"
  port="${port//[[:space:]]/}"
  [[ -z "${ver}" ]] && continue
  [[ "${ver}" =~ ^# ]] && continue
  [[ -z "${port}" ]] && { echo "[$lineno] WARN: missing port for version ${ver}, skip"; continue; }

  stack="mw-${ver//./-}"
  echo "=== Launch MW ${ver} at http://localhost:${port} (project: ${stack})"

  MW_VERSION="$ver" HOST_PORT="$port" \
  docker compose -p "$stack" -f A-compose.yml up -d

  echo "[*] wait db health..."
  for i in {1..60}; do
    st="$(docker inspect --format '{{.State.Health.Status}}' "${stack}-db" 2>/dev/null || true)"
    [[ "${st}" == "healthy" ]] && break
    sleep 2
  done

  echo "[*] install.php ..."
  # 👇 stdin을 확실히 닫아버린다 (</dev/null)
  MW_VERSION="$ver" \
  docker compose -p "$stack" -f A-compose.yml exec -T wiki bash -lc '
    set -e
    cd /var/www/html
    if [ ! -f LocalSettings.php ]; then
      NEWPASS="$(openssl rand -base64 18 | tr -d "=+/" )!A9"
      php maintenance/install.php \
        --dbtype mysql \
        --dbserver "$MW_DB_HOST" \
        --dbname "$MW_DB_NAME" \
        --dbuser "$MW_DB_USER" \
        --dbpass "$MW_DB_PASS" \
        --scriptpath "" \
        --lang en \
        --pass "$NEWPASS" \
        "$MW_SITE_NAME" "$MW_ADMIN_USER"
      chown www-data:www-data LocalSettings.php
      printf "\n\$wgServer = \"http://localhost:%s\";\n\$wgCanonicalServer = \$wgServer;\n" "$HOST_PORT" >> LocalSettings.php
      echo "[INFO] Admin: $MW_ADMIN_USER  Password: $NEWPASS"
    else
      echo "[SKIP] LocalSettings.php exists"
    fi
  ' </dev/null   # <-- 여기!

done

# FD 정리
exec 9<&-

echo "=== All done."

