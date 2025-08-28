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
        
        # # 1. <script> 태그 (JS 파일) 찾기
        # script_tags = soup.find_all('script', src=True)
        
        # # 2. <link> 태그 (CSS 파일) 찾기
        # link_tags = soup.find_all('link', rel='stylesheet', href=True)

        # # 3. <img> 태그 (이미지 파일) 찾기
        # # 'src' 속성을 가진 모든 <img> 태그를 찾습니다.
        # img_tags = soup.find_all('img', src=True)

        # # 4. module preload 파트 찾기
        # module_preload_tags = soup.find_all('link', rel='modulepreload', href=True)

        # # 5. icon 찾기
        # icon_tags = soup.find_all('link', rel='icon', href=True)
        
        # print(f"{final_url}에서 {len(script_tags)}개의 JS 파일, {len(link_tags)}개의 CSS 파일, {len(img_tags) + len(icon_tags)}개의 이미지파일, {len(module_preload_tags)}개의 모듈 파일을 찾았습니다.")
        
        # # 모든 에셋(JS, CSS, Image) URL을 리스트에 모으기
        # asset_urls = []
        # for tag in script_tags:
        #     asset_urls.append(tag['src'])
        # for tag in link_tags:
        #     asset_urls.append(tag['href'])
        # for tag in img_tags:
        #     asset_urls.append(tag['src'])
        # for tag in module_preload_tags:
        #     asset_urls.append(tag['href'])
        # for tag in icon_tags:
        #     asset_urls.append(tag['href'])

        all_asset_urls = get_all_assets(soup)

        if not all_asset_urls:
            print("소스 코드에 리소스 파일이 없습니다.")
            return

        for asset_url in set(all_asset_urls):
            if asset_url.startswith('data:'):
                # TODO: 내부데이터를 받아올 수 있는 방법을 찾아올 것!
                continue
                
            # 상대 경로를 절대 경로로 변환 (최종 URL 기준)
            absolute_asset_url = urljoin(final_url, asset_url)
            
            # 파일 이름 추출
            parsed_url = urlparse(absolute_asset_url)
            filename = os.path.basename(parsed_url.path)

            if not filename or '.' not in filename:
                unique_id = hashlib.sha256(url.encode()).hexdigest()
                
                if '.' in parsed_url.path:
                    ext = parsed_url.split('.')[-1]
                    filename = f'resources_{unique_id}.{ext}'
                else:
                    filename = f'resources_{unique_id}'

                # # 1. 특정 확장자를 가진 경우
                # if ext in ['js', 'css']:
                #     filename = f"asset_{hash(absolute_asset_url) % 10000}.{ext}"
                # # 2. 이미지 확장자를 가진 경우
                # elif ext in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
                #     filename = f"image_{hash(absolute_asset_url) % 10000}.{ext}"
                # # 3. 그 외 알 수 없는 확장자의 경우
                # else:
                #     filename = f"unknown_{hash(absolute_asset_url) % 10000}.{ext if ext else ''}"
            
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
                file_type = file_extension.lstrip('.') if file_extension else 'unknown'

                # 파일 크기 확인
                file_size_bytes = check_file_size(filepath)

                # 파일 해시값 생성
                file_hash = get_file_hash(filepath)

                with open(os.path.join(output_dir, "fileinfo.csv"), 'a') as f:
                    f.write(f'{file_type},{filename},{urlparse(absolute_asset_url).path},{file_size_bytes},{file_hash}\n')
                
            except requests.exceptions.RequestException as e:
                print(f"다운로드 실패: {absolute_asset_url}")
                print(f"  - 오류: {e}")
                
    except requests.exceptions.RequestException as e:
        print(f"웹 페이지를 가져오는 중 치명적인 오류 발생: {url}")
        print(f"  - 상세 오류: {e}")
        
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

def get_all_assets(soup):
    """
    HTML 콘텐츠에서 src, href 속성을 가진 모든 리소스 URL을 찾습니다.
    """

    src_urls = [tag['src'] for tag in soup.find_all(src=True)]
    href_urls = [tag['href'] for tag in soup.find_all(href=True)]
    
    all_asset_urls = set(src_urls + href_urls)

    print(f'총 리소스 숫자: {len(all_asset_urls)}')

    return all_asset_urls

def check_file_size(file_path):
    try:
        # 1. 파일 크기 확인 (바이트 단위)
        file_size_bytes = os.path.getsize(file_path)

        return file_size_bytes
            
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