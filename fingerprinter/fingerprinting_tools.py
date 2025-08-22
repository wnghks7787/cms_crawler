import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
RESOURCES_DIR = os.path.abspath(os.path.join(PARENT_DIR, 'resources/fingerprintable_file'))

def sort(target_path, sort_columns=[0, 1, 2], ascending=True):
    target_csv_file = os.path.join(target_path, "fileinfo.csv")

    # CSV 파일 존재 여부 확인
    if not os.path.exists(target_csv_file):
        print(f"오류: CSV 파일 '{target_csv_file}'을 찾을 수 없습니다.")
        return None

    try:
        df = pd.read_csv(target_csv_file, header=None)

        for col_index in sort_columns:
            if col_index >= len(df.columns) or col_index < 0:
                print(f"오류: 유효하지 않은 열 인덱스({col_index})가 포함되어 있습니다.")
                return None
        
        df_sorted = df.sort_values(by=sort_columns, ascending=ascending)

        df_sorted.to_csv(target_csv_file, index=False, header=False)

        print(f"{target_csv_file} 파일이 성공적으로 정렬되었습니다.")
    
    except pd.errors.EmptyDataError:
        print(f"오류: 파일 {target_csv_file} 에 데이터가 존재하지 않습니다.")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

def find_files(file):
    if not os.path.exists(file):
        print(f"오류: 파일 '{file}' 을 찾을 수 없습니다.")
        return None
    else:
        return True

def version_checker_in_csv(target):
    csv_file = 'fileinfo.csv'
    if not os.path.isdir(RESOURCES_DIR):
        print(f"오류: RESOURCES 파일이 존재하지 않습니다.")
        return None

    target_csv_file = os.path.join(target, csv_file)
    if not find_files(target_csv_file):
        return None

    versions = []
    for root, dirs, files in os.walk(RESOURCES_DIR):
        comparison_csv_file = os.path.join(root, csv_file)
        if csv_checker(target_csv_file, comparison_csv_file):
            versions.append(os.path.basename(root))

    return versions
            

def csv_checker(target_csv_file, comparison_csv_file):
    if not (find_files(target_csv_file) and find_files(comparison_csv_file)):
        return None
    
    try:
        col_name = ['exp', 'file_name', 'path', 'file_size_byte', 'file_size_readable', 'hash_val']
        compare_cols = ['exp', 'file_name', 'hash_val']

        target_df = pd.read_csv(target_csv_file, header=None, names=col_name)
        comparison_df = pd.read_csv(comparison_csv_file, header=None, names=col_name)
        
        target_df['merged'] = target_df[compare_cols].astype(str).agg('-'.join, axis=1)
        comparison_df['merged'] = comparison_df[compare_cols].astype(str).agg('-'.join, axis=1)

        matching_rows = target_df[target_df['merged'].isin(comparison_df['merged'])]
        
        if not matching_rows.empty:
            print('--- 다음 항목이 일치합니다. ---')
            print(matching_rows)
            return True
        else:
            return False

    except FileNotFoundError:
        print("오류: 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")

if __name__ == '__main__':
    sort('newsprofin')