# legacy/Dockerfile
ARG PHP_BASE=php:5.6-apache
FROM ${PHP_BASE}

ARG MW_VER=1.29.3
ENV MW_VER=${MW_VER}

# === stretch 아카이브 미러 + 만료체크/서명 완화 ===
RUN set -eux; \
    # 만료/서명 검사 완화 (archive는 Valid-Until 만료된 경우가 많음)
    printf 'Acquire::Check-Valid-Until "false";\nAcquire::AllowInsecureRepositories "true";\n' > /etc/apt/apt.conf.d/99no-check-valid; \
    # 일부 이미지에선 allow-unauth 필요
    printf 'APT::Get::AllowUnauthenticated "true";\n' > /etc/apt/apt.conf.d/99allow-unauth; \
    # sources.list를 아카이브로 "완전히" 교체 (https 말고 http 사용)
    printf 'deb http://archive.debian.org/debian stretch main contrib non-free\n' > /etc/apt/sources.list; \
    printf 'deb http://archive.debian.org/debian-security stretch/updates main\n' >> /etc/apt/sources.list; \
    apt-get -o Acquire::Check-Valid-Until=false update; \
    # 레거시 최소 패키지 (gd/zip은 5.6에서 자주 깨지니 일단 제외)
    apt-get -o Acquire::Check-Valid-Until=false -y --no-install-recommends install \
        ca-certificates curl unzip \
        libicu-dev zlib1g-dev \
        libpng-dev libjpeg-dev libfreetype6-dev; \
    # php ext: mysqli + intl (필수급). zip/gd는 필요시 나중에 별도 시도
    docker-php-ext-install -j"$(nproc)" mysqli intl; \
    a2enmod rewrite; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

# 미디어위키 소스 내려받기
RUN set -eux; \
    curl -fsSL -o mw.tgz "http://releases.wikimedia.org/mediawiki/${MW_VER%.*}/mediawiki-${MW_VER}.tar.gz"; \
    tar -xzf mw.tgz --strip-components=1; \
    rm mw.tgz; \
    chown -R www-data:www-data /var/www/html

