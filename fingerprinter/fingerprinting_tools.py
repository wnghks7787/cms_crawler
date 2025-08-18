import os
import hashlib

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"

    unit = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(unit) -1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes: .2f} {unit[i]}"

def check_and_save_file_size(file_path, output_file_path):
    try:
        # 1. 파일 크기 확인 (바이트 단위)
        file_size_bytes = os.path.getsize(file_path)
        
        # 2. 크기를 보기 좋은 형식으로 변환
        file_size_formatted = format_size(file_size_bytes)
        
        print(f"파일 '{file_path}'의 크기는 {file_size_formatted}입니다.")
        
        # 3. 정보를 출력 파일에 저장
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"파일 경로: {file_path}\n")
            f.write(f"파일 크기 (바이트): {file_size_bytes} B\n")
            f.write(f"파일 크기 (표준 형식): {file_size_formatted}\n")
            
        print(f"파일 크기 정보가 '{output_file_path}'에 성공적으로 저장되었습니다.")
            
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


if __name__ == '__main__':

    check_and_save_file_size("../docker_runner/initial_page_builder/assets_file/wordpress-6.8.1.yml/style.css", "testfile")