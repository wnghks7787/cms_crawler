import requests
import re
from urllib.parse import urljoin

def check_wordpress_version_from_php(url):
    """
    version.php 파일에서 워드프레스 버전을 확인합니다.
    """
    version_php_url = urljoin(url, 'wp-includes/version.php')

    try:
        response = requests.get(version_php_url, timeout=10)
        response.raise_for_status()

        # 정규 표현식을 사용해 '$wp_version = '6.8.2';' 패턴 찾기
        match = re.search(r"\$wp_version\s*=\s*'([^']+)';", response.text)
        if match:
            version = match.group(1)
            print(f"URL: {url}")
            print(f"version.php에서 워드프레스 버전: {version}")
            return version
        else:
            print("version detect fail")
            return None

    except requests.exceptions.RequestException as e:
        print(f"URL {url} 접근 중 오류 발생: {e}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

    return None

# 사용 예시
url_681 = "http://localhost:10001/"
url_682 = "http://localhost:10002/"

check_wordpress_version_from_php(url_681)
check_wordpress_version_from_php(url_682)