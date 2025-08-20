import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_cms_version(url):
    """
    주어진 URL의 웹사이트 CMS와 버전을 탐지합니다.
    """
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        response.raise_for_status()
        
        # HTML 소스코드 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. <meta name="generator"> 태그 확인
        meta_generator = soup.find('meta', attrs={'name': 'generator'})
        if meta_generator and 'content' in meta_generator.attrs:
            content = meta_generator['content']
            if 'WordPress' in content:
                print(f"CMS: WordPress, 버전: {content.split(' ')[-1]}")
                return "WordPress", content.split(' ')[-1]
            elif 'Joomla' in content:
                print(f"CMS: Joomla, 버전: {content.split(' ')[-1]}")
                return "Joomla", content.split(' ')[-1]
            elif 'Drupal' in content:
                print(f"CMS: Drupal, 버전: {content.split(' ')[-1]}")
                return "Drupal", content.split(' ')[-1]
            
            # 기타 CMS
            print(f"CMS (meta tag): {content}")
            return content, None

        # 2. 특정 파일 경로 확인
        # 흔한 CMS별 파일 경로를 정의합니다.
        cms_signatures = {
            "WordPress": ["/wp-login.php", "/wp-content/", "/wp-includes/"],
            "Joomla": ["/administrator/", "/templates/", "/media/"],
            "Drupal": ["/core/CHANGELOG.txt", "/sites/all/"]
        }

        print("`meta` 태그를 찾지 못했습니다. 파일 경로를 확인합니다.")
        for cms_name, paths in cms_signatures.items():
            for path in paths:
                test_url = urljoin(response.url, path)
                try:
                    test_response = requests.head(test_url, allow_redirects=True, timeout=5)
                    if test_response.status_code == 200:
                        print(f"CMS: {cms_name} (경로 발견: {path})")
                        # 버전 정보는 경로만으로 파악하기 어려움
                        return cms_name, None
                except requests.exceptions.RequestException:
                    continue
        
        # 3. 추가적인 흔적 찾기 (예: 헤더, 소스 코드 내 패턴)
        # 소스 코드에 'wp-content' 같은 문자열이 있는지 확인
        if 'wp-content' in response.text:
            print("CMS: WordPress (소스 코드 패턴 발견)")
            return "WordPress", None
        
        if 'Joomla!' in response.text:
            print("CMS: Joomla (소스 코드 패턴 발견)")
            return "Joomla", None
            
        print("CMS를 탐지하지 못했습니다.")
        return None, None

    except requests.exceptions.RequestException as e:
        print(f"웹사이트에 접근하는 중 오류 발생: {e}")
        return None, None
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return None, None

# 사용 예시
if __name__ == "__main__":
    target_url = "https://www.wordpress.com" # 여기에 테스트할 URL 입력
    get_cms_version(target_url)

    target_url_2 = "https://www.joomla.org"
    get_cms_version(target_url_2)

    target_url_3 = "https://www.wikipedia.org" # CMS가 아닌 일반 사이트
    get_cms_version(target_url_3)