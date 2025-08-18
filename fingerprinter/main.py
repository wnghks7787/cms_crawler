import hashlib

def get_file_hash(file_path):
    """파일 경로를 받아 MD5 해시 값을 반환합니다."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except FileNotFoundError:
        return None


if __name__ == '__main__':
    # wp6_8 = get_file_hash('../docker_runner/initial_page_builder/assets_file/wordpress-6.7.1.yml/style.css')
    wp6_8_2 = get_file_hash('../docker_runner/initial_page_builder/assets_file/wordpress-6.8.2.yml/view.min.js')
    mellowads = get_file_hash('view.min.js')

    print("<<hash of view.min.js>>")
    print(f'wp6.8.2: {wp6_8_2}')
    print(f'mellowads: {mellowads}')