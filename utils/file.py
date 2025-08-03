#utils/file.py
import os
import pandas as pd

def list_subdirectories(parent_dir):
    return [name for name in os.listdir(parent_dir)
            if os.path.isdir(os.path.join(parent_dir, name))]

def list_files_in_directory(dir_path, ext_filter='.csv'):
    return [f for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f)) and f.endswith(ext_filter)]

def read_file(filepath, encoding='utf-8'):
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] 파일 읽기 실패: {filepath} - {e}")
        return None

def read_csv_file(filepath, encoding='utf-8'):
    try:
        return pd.read_csv(filepath, encoding=encoding)
    except Exception as e:
        print(f"[ERROR] CSV 읽기 실패: {filepath} - {e}")
        return None
