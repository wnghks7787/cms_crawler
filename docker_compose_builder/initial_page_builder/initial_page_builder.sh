#!/bin/bash

# curl -X POST "http://localhost:10002/wp-admin/install.php?step=2" \
#   -H "Referer: http://localhost:10002/wp-admin/install.php?language=ko_KR" \
#   -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15" \
#   -d "weblog_title=test&user_name=admin&admin_password=admin&admin_password2=admin&admin_email=wnghks7787@naver.com&blog_public=true"

  REPO=$1
  PORT=$2
  VERSION=$3


if [ "$REPO" == "wordpress" ];
then
    curl -X POST "http://localhost:$PORT/wp-admin/install.php?step=2" \
    -H "Referer: http://localhost:$PORT/wp-admin/install.php?language=ko_KR" \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15" \
    -d "weblog_title=test&user_name=admin&admin_password=admin&admin_password2=admin&admin_email=wnghks7787@naver.com&blog_public=true"
elif [ "$REPO" == "joomla" ];
then
    python playwright_builder/joomla_autobuilder.py --portnum $PORT --version $VERSION
elif [ "$REPO" == 'drupal' ];
then
    python playwright_builder/drupal_autobuilder.py --portnum $PORT --version $VERSION
elif [ "$REPO" == 'prestashop' ];
then
    python playwright_builder/prestashop_autobuilder.py --portnum $PORT --version $VERSION
elif [ "$REPO" == 'qloapps_docker'];
then
    python selenium_builder/qloapps_autobuilder.py --portnum $PORT --version $VERSION
fi
