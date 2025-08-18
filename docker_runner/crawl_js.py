import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def download_assets(url, output_dir="web_assets"):
    """
    주어진 URL의 HTML에서 발견된 모든 JavaScript 및 CSS 파일을 다운로드합니다.
    """
    try:
        # 출력 디렉토리가 없으면 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"웹 페이지 가져오는 중: {url}")

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()  
        
        final_url = response.url
        if url != final_url:
            print(f"리디렉션 감지. 최종 URL: {final_url}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. <script> 태그 (JS 파일) 찾기
        script_tags = soup.find_all('script', src=True)
        
        # 2. <link> 태그 (CSS 파일) 찾기
        link_tags = soup.find_all('link', rel='stylesheet', href=True)
        
        print(f"{final_url}에서 {len(script_tags)}개의 JS 파일과 {len(link_tags)}개의 CSS 파일을 찾았습니다.")
        
        # 모든 에셋(JS, CSS) URL을 리스트에 모으기
        asset_urls = []
        for tag in script_tags:
            asset_urls.append(tag['src'])
        for tag in link_tags:
            asset_urls.append(tag['href'])

        if not asset_urls:
            print("소스 코드에 외부 JavaScript 또는 CSS 파일이 없습니다.")
            return

        for asset_url in asset_urls:
            # 상대 경로를 절대 경로로 변환 (최종 URL 기준)
            absolute_asset_url = urljoin(final_url, asset_url)
            
            # 파일 이름 추출
            filename = os.path.basename(urlparse(absolute_asset_url).path)
            
            if not filename or '.' not in filename:
                # 파일 이름이 없거나 확장자가 없는 경우 고유한 이름 생성
                # 확장자 구분을 위해 URL의 마지막 경로를 사용하거나 해시값 사용
                url_path_parts = urlparse(absolute_asset_url).path.split('/')
                ext = url_path_parts[-1].split('.')[-1] if '.' in url_path_parts[-1] else ''
                filename = f"asset_{hash(absolute_asset_url) % 10000}.{ext if ext in ['js', 'css'] else 'unknown'}"
            
            filepath = os.path.join(output_dir, filename)
            
            print(f"다운로드 중: {absolute_asset_url}")
            
            try:
                asset_response = requests.get(absolute_asset_url, headers=headers, allow_redirects=True)
                asset_response.raise_for_status()
                
                # 파일 다운로드 및 저장
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(asset_response.text)
                
                print(f"성공적으로 다운로드: {filepath}")
                
            except requests.exceptions.RequestException as e:
                print(f"다운로드 실패: {absolute_asset_url}")
                print(f"  - 오류: {e}")
                
    except requests.exceptions.RequestException as e:
        print(f"웹 페이지를 가져오는 중 치명적인 오류 발생: {url}")
        print(f"  - 상세 오류: {e}")
        
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

# 사용 예시
if __name__ == "__main__":
    host_port = "10000"
    name = "my_project"
    output_dir_path = f"web_assets/{name}"

    try:
        # URL에 'http://' 스키마를 반드시 추가해야 함
        target_url = f"http://localhost:10000"
        download_assets(target_url, output_dir=output_dir_path)
    except Exception as e:
        print(f"스크립트 실행 중 오류 발생: {e}")