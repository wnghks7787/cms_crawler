#!/usr/bin/env bash
set -euo pipefail

exec 9< versions.txt
while IFS=, read -r ver port phpbase <&9; do
  [[ -z "${ver}" ]] && continue
  [[ "${ver}" =~ ^# ]] && continue
  [[ -z "${phpbase}" ]] && continue

  safe_ver="${ver//./_}"        # ← 점을 언더스코어로 치환
  proj="mw_legacy_${safe_ver}"  # 프로젝트명: mw_legacy_1_23_17

  echo "=== Build & Up MW ${ver} (PHP ${phpbase}) at :${port}  [project: ${proj}]"

  MW_VER="$ver" HOST_PORT="$port" PHP_BASE="$phpbase" \
  docker compose -p "$proj" -f compose.yml build

  MW_VER="$ver" HOST_PORT="$port" PHP_BASE="$phpbase" \
  docker compose -p "$proj" -f compose.yml up -d

  echo "[*] wait db health..."
  for i in {1..60}; do
    st="$(docker inspect --format '{{.State.Health.Status}}' ${proj}-db 2>/dev/null || true)"
    [[ "$st" == "healthy" ]] && break
    sleep 2
  done

  echo "[*] install.php ..."
  docker compose -p "$proj" -f compose.yml exec -T wiki bash -lc "
    set -e
    cd /var/www/html
    if [ ! -f LocalSettings.php ]; then
      NEWPASS=\"\$(tr -dc A-Za-z0-9 </dev/urandom | head -c 20)A9!\"
      php maintenance/install.php \
        --dbtype mysql --dbserver \"\$MW_DB_HOST\" \
        --dbname \"\$MW_DB_NAME\" --dbuser \"\$MW_DB_USER\" --dbpass \"\$MW_DB_PASS\" \
        --scriptpath \"\" --lang en --pass \"\$NEWPASS\" \
        \"\$MW_SITE_NAME\" \"\$MW_ADMIN_USER\"
      chown www-data:www-data LocalSettings.php
      printf '\n\$wgServer = \"http://localhost:${port}\";\n\$wgCanonicalServer = \$wgServer;\n' >> LocalSettings.php
      echo \"[INFO] Admin: \$MW_ADMIN_USER  Password: \$NEWPASS\"
    else
      echo \"[SKIP] LocalSettings.php exists\"
    fi
  " </dev/null
done
exec 9<&-
echo "=== Legacy done."

