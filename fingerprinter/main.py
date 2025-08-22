import wordpress_fingerprinter as wp
import os

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
RESOURCES_DIR = os.path.abspath(os.path.join(PARENT_DIR, 'resources/fingerprintable_file'))
TOYSET_DIR = os.path.join(BASE_DIR, 'toyset')

if __name__ == "__main__":

    result_csv = os.path.join(BASE_DIR, 'result.csv')

    toplevel_items = os.listdir(TOYSET_DIR)

    for item_name in toplevel_items:
        toplevel_path = os.path.join(TOYSET_DIR, item_name)

        # 해당 경로가 폴더인지 확인합니다.
        if os.path.isdir(toplevel_path):
            # 찾으려는 파일의 전체 경로를 구성합니다.
            target_file_path = os.path.join(toplevel_path, 'root', 'html.html')

            print(f"확인 중인 경로: {target_file_path}")

            # 최종 경로에 파일이 실제로 존재하는지 확인합니다.
            if os.path.isfile(target_file_path):
                print(f"  -> 파일 찾음: {target_file_path}")
                # 이 파일로 원하는 작업을 수행하면 됩니다.
                site = item_name
                versions = wp.find_version(target_file_path)

                with open(result_csv, 'a', encoding='utf-8') as f:
                    f.write(f'{site},{versions}\n')

                print(f'site: {site}, ver: {versions}')
            else:
                print("  -> 파일 없음")

    # for root, dirs, files in os.walk(TOYSET_DIR):
    #     site = os.path.basename(root)
    #     versions = wp.find_version(root)

    #     print(versions)
        
    
    # def version_checker_in_csv(target):
    # csv_file = 'fileinfo.csv'

    # target_csv_file = os.path.join(target, csv_file)
    # if not find_files(target_csv_file):
    #     return None

    # versions = []
    # for root, dirs, files in os.walk(RESOURCES_DIR):
    #     comparison_csv_file = os.path.join(root, csv_file)
    #     if csv_checker(target_csv_file, comparison_csv_file):
    #         versions.append(os.path.basename(root))

    # return versions