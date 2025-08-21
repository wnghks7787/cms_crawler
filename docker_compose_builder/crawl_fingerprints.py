import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib


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

        # 3. <img> 태그 (이미지 파일) 찾기
        # 'src' 속성을 가진 모든 <img> 태그를 찾습니다.
        img_tags = soup.find_all('img', src=True)

        # 4. module preload 파트 찾기
        module_preload_tags = soup.find_all('link', rel='modulepreload', href=True)

        # 5. icon 찾기
        icon_tags = soup.find_all('link', rel='icon', href=True)
        
        print(f"{final_url}에서 {len(script_tags)}개의 JS 파일, {len(link_tags)}개의 CSS 파일, {len(img_tags) + len(icon_tags)}개의 이미지파일, {len(module_preload_tags)}개의 모듈 파일을 찾았습니다.")
        
        # 모든 에셋(JS, CSS, Image) URL을 리스트에 모으기
        asset_urls = []
        for tag in script_tags:
            asset_urls.append(tag['src'])
        for tag in link_tags:
            asset_urls.append(tag['href'])
        for tag in img_tags:
            asset_urls.append(tag['src'])
        for tag in module_preload_tags:
            asset_urls.append(tag['href'])
        for tag in icon_tags:
            asset_urls.append(tag['href'])

        if not asset_urls:
            print("소스 코드에 외부 Resources(JS, CSS, Image) 파일이 없습니다.")
            return

        for asset_url in set(asset_urls):
            if asset_url.startswith('data:'):
                continue
                
            # 상대 경로를 절대 경로로 변환 (최종 URL 기준)
            absolute_asset_url = urljoin(final_url, asset_url)
            
            # 파일 이름 추출
            filename = os.path.basename(urlparse(absolute_asset_url).path)
            
            # if not filename or '.' not in filename:
            #     # 파일 이름이 없거나 확장자가 없는 경우 고유한 이름 생성
            #     # 확장자 구분을 위해 URL의 마지막 경로를 사용하거나 해시값 사용
            #     url_path_parts = urlparse(absolute_asset_url).path.split('/')
            #     ext = url_path_parts[-1].split('.')[-1] if '.' in url_path_parts[-1] else ''
            #     filename = f"asset_{hash(absolute_asset_url) % 10000}.{ext if ext in ['js', 'css'] else 'unknown'}"

            if not filename or '.' not in filename:
                ext = absolute_asset_url.split('.')[-1].split('?')[0].split('#')[0].lower()

                # 1. 특정 확장자를 가진 경우
                if ext in ['js', 'css']:
                    filename = f"asset_{hash(absolute_asset_url) % 10000}.{ext}"
                # 2. 이미지 확장자를 가진 경우
                elif ext in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
                    filename = f"image_{hash(absolute_asset_url) % 10000}.{ext}"
                # 3. 그 외 알 수 없는 확장자의 경우
                else:
                    filename = f"unknown_{hash(absolute_asset_url) % 10000}.{ext if ext else ''}"
            
            filepath = os.path.join(output_dir, filename)
            
            print(f"다운로드 중: {absolute_asset_url}")
            
            try:
                asset_response = requests.get(absolute_asset_url, headers=headers, allow_redirects=True)
                asset_response.raise_for_status()

                file_extension = os.path.splitext(filename)[1].lower()

                is_text = file_extension in ['.js', '.css']

                if is_text:
                    # 파일 다운로드 및 저장
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(asset_response.text)
                else:
                    with open(filepath, 'wb') as f:
                        f.write(asset_response.content)
                
                print(f"성공적으로 다운로드: {filepath}")

                # 파일 종류 식별
                file_type = ''
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.js', '.css']:
                    file_type = file_extension.split('.')[-1]
                else:
                    file_type = 'unknown'

                # 파일 크기 확인
                file_size_bytes, file_size_formatted = check_file_size(filepath)

                # 파일 해시값 생성
                file_hash = get_file_hash(filepath)

                with open(os.path.join(output_dir, "fileinfo.csv"), 'a') as f:
                    f.write(f'{file_type},{filename},{urlparse(absolute_asset_url).path},{file_size_bytes},{file_size_formatted},{file_hash}\n')
                
            except requests.exceptions.RequestException as e:
                print(f"다운로드 실패: {absolute_asset_url}")
                print(f"  - 오류: {e}")
                
    except requests.exceptions.RequestException as e:
        print(f"웹 페이지를 가져오는 중 치명적인 오류 발생: {url}")
        print(f"  - 상세 오류: {e}")
        
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"

    unit = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(unit) -1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes: .2f} {unit[i]}"

def check_file_size(file_path):
    try:
        # 1. 파일 크기 확인 (바이트 단위)
        file_size_bytes = os.path.getsize(file_path)
        
        # 2. 크기를 보기 좋은 형식으로 변환
        file_size_formatted = format_size(file_size_bytes)

        return file_size_bytes, file_size_formatted
            
    except FileNotFoundError:
        # 파일이 존재하지 않는 경우 오류 처리
        print(f"오류: 지정된 파일 '{file_path}'를 찾을 수 없습니다.")
        
    except Exception as e:
        # 그 외 예상치 못한 오류 처리
        print(f"오류가 발생했습니다: {e}")

def get_file_hash(file_path):
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except FileNotFoundError:
        return None

# 사용 예시
if __name__ == "__main__":
    host_port = "10001"
    name = "my_project"
    output_dir_path = f"web_assets/{name}"

    try:
        # URL에 'http://' 스키마를 반드시 추가해야 함
        target_url = f"http://localhost:{host_port}"
        download_assets(target_url, output_dir=output_dir_path)
    except Exception as e:
        print(f"스크립트 실행 중 오류 발생: {e}")