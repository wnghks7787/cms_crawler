# fingerprint_json 파일 생성하는 코드

import json
import os

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
RESOURCES_DIR = os.path.abspath(os.path.join(PARENT_DIR, 'resources/fingerprintable_file'))

class JsonGenerator:
    def __init__(self, repo_name: str):

        if not repo_name or not repo_name.strip():
            raise ValueError('[Error!] REPO 이름이 비어있습니다.')
        
        self.repo_name = repo_name
        self.versions_data = {}
        print(f'\'{repo_name}\' 데이터 생성을 시작합니다.')
    
    def add_version(self, version_name: str, raw_data: str):
        resource_hashes = set()

        lines = raw_data.strip().split('\n')

        for line in lines:
            if not line.strip():
                continue

            parts = line.strip().split(',')

            if len(parts) >= 5:
                file_hash = parts[-1]
                resource_hashes.add(file_hash)
            else:
                print(f'[Warning] {version_name} 버전의 데이터 형식이 잘못되었습니다. 파일을 건너뜁니다. {line}')

        self.versions_data[version_name] = {
            "resources": sorted(list(resource_hashes))
        }
        print(f'✅ 버전 {version_name} 처리 완료.')

    def save_to_file(self, directory: str = '.'):
        def version_key_func(version_str):
            parts = []

            for part in version_str.split('.'):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(0)
            return parts
        sorted_version_keys = sorted(self.versions_data.keys(), key=version_key_func, reverse=True)

        sorted_data = {key: self.versions_data[key] for key in sorted_version_keys}

        output_filename = f'{self.repo_name}.json'
        output_filepath = os.path.join(directory, output_filename)

        os.makedirs(directory, exist_ok=True)

        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=4, ensure_ascii=False)
            print(f'\n🎉 성공! 모든 데이터가 {output_filepath} 에 저장되었습니다.')
        except IOError as e:
            print(f'\n❌ [Error!] 파일 저장에 실패하였습니다: {e}')

if __name__ == '__main__':
    generator_wordpress = JsonGenerator('wordpress')
    generator_joomla = JsonGenerator('joomla')
    generator_drupal = JsonGenerator('drupal')
    generator_prestashop = JsonGenerator('prestashop')
    generator_qloapps = JsonGenerator('qloapps')

    for root, dirs, files in os.walk(RESOURCES_DIR):
        if os.path.basename(root) == os.path.basename(RESOURCES_DIR):
            continue

        root_names = os.path.basename(root).split('-')


        repo = root_names[0]
        ver = root_names[1]

        if 'fileinfo.csv' in files:
            with open(os.path.join(root, 'fileinfo.csv'), 'r', encoding='utf-8') as f:
                content = f.read()

                if repo == 'wordpress':
                    generator_wordpress.add_version(ver, content)
                if repo == 'joomla':
                    generator_joomla.add_version(ver, content)
                if repo == 'drupal':
                    generator_drupal.add_version(ver, content)
                if repo == 'prestashop':
                    generator_prestashop.add_version(ver, content)
                if repo == 'qloapps':
                    generator_qloapps.add_version(ver, content)
        else:
            with open('empty_fileinfo', 'a', encoding='utf-8') as f:
                f.write(f'{repo}-{ver}\n')
    os.makedirs('./fingerprint_json', exist_ok=True)
    
    generator_wordpress.save_to_file('./fingerprint_json')
    generator_joomla.save_to_file('./fingerprint_json')
    generator_drupal.save_to_file('./fingerprint_json')
    generator_prestashop.save_to_file('./fingerprint_json')
    generator_qloapps.save_to_file('./fingerprint_json')