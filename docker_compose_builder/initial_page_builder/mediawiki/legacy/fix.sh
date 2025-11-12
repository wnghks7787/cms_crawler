#!/usr/bin/env bash
set -euo pipefail

VERS_FILE="${VERS_FILE:-versions.txt}"
COMPOSE_FILE="${COMPOSE_FILE:-compose.yml}"
ONLY="${ONLY:-}"

[[ -f "$VERS_FILE" ]] || { echo "[FATAL] $VERS_FILE not found"; exit 1; }
[[ -f "$COMPOSE_FILE" ]] || { echo "[FATAL] $COMPOSE_FILE not found"; exit 1; }

ensure_running() {
  local ver="$1" port="$2" phpbase="$3"
  local proj="mw_legacy_${ver//./_}"

  echo "[*] compose up: ${ver} (project: ${proj}, port: ${port}, php: ${phpbase})"
  MW_VER="$ver" HOST_PORT="$port" PHP_BASE="$phpbase" \
  docker compose -p "$proj" -f "$COMPOSE_FILE" up -d

  echo "[*] wait db health for mw-legacy-${ver}-db ..."
  for i in {1..60}; do
    st="$(docker inspect --format '{{.State.Health.Status}}' "mw-legacy-${ver}-db" 2>/dev/null || true)"
    [[ "$st" == "healthy" ]] && break
    sleep 2
  done
}

db_reset() {
  local ver="$1"
  local db_container="mw-legacy-${ver}-db"
  echo "[*] DB reset: ${db_container}"
  docker exec -i "$db_container" \
    mysql -uroot -prootpass <<'SQL'
DROP DATABASE IF EXISTS mw;
CREATE DATABASE mw CHARACTER SET utf8;
GRANT ALL ON mw.* TO 'mw'@'%' IDENTIFIED BY 'mwpass';
FLUSH PRIVILEGES;
SQL
}

reinstall_localsettings() {
  local ver="$1" port="$2"
  local wiki_container="mw-legacy-${ver}"
  echo "[*] reinstall LocalSettings.php in ${wiki_container}"
  docker exec -i "$wiki_container" bash -c "
set -e
cd /var/www/html
[ -f LocalSettings.php ] && mv LocalSettings.php LocalSettings.bak.\$(date +%s).php
NEWPASS=\$(tr -dc A-Za-z0-9 </dev/urandom | head -c 20)A9!
php maintenance/install.php \
  --dbtype mysql --dbserver \"\$MW_DB_HOST\" \
  --dbname \"\$MW_DB_NAME\" --dbuser \"\$MW_DB_USER\" --dbpass \"\$MW_DB_PASS\" \
  --scriptpath \"\" --lang en --pass \"\$NEWPASS\" \
  \"\$MW_SITE_NAME\" \"\$MW_ADMIN_USER\"

printf '\n\$wgServer = \"http://localhost:%s\";\n\$wgCanonicalServer = \$wgServer;\n' \"$port\" >> LocalSettings.php
printf '\n\$wgShowExceptionDetails = true;\n' >> LocalSettings.php
chown www-data:www-data LocalSettings.php
php -l LocalSettings.php
echo \"[INFO] Admin: \$MW_ADMIN_USER  Password: \$NEWPASS\"
"
}

quick_check() {
  local port="$1"
  echo "    - HEAD / :";       curl -sSI "http://localhost:${port}/" | head -n 1 || true
  echo "    - HEAD /api.php :";curl -sSI "http://localhost:${port}/api.php" | head -n 1 || true
}

main() {
  exec 9<"$VERS_FILE"
  while IFS=, read -r ver port phpbase <&9; do
    [[ -z "${ver}" ]] && continue
    [[ "${ver}" =~ ^# ]] && continue
    [[ -z "${phpbase}" ]] && continue

    if [[ -n "$ONLY" ]]; then
      ok=0; IFS=',' read -ra want <<<"$ONLY"
      for w in "${want[@]}"; do [[ "$w" == "$ver" ]] && ok=1; done
      [[ $ok -eq 0 ]] && continue
    fi

    echo; echo "=== FIX ${ver} (port: ${port}) ==="
    ensure_running "$ver" "$port" "$phpbase"
    db_reset "$ver"
    reinstall_localsettings "$ver" "$port"
    echo "[*] quick health check"; quick_check "$port"
  done
  exec 9<&-
  echo; echo "=== All requested legacy instances fixed. ==="
}

main "$@"

