import os
from typing import List, Tuple

import json
from pathlib import Path
from typing import Any

import csv
from pathlib import Path
from typing import List, Dict, Union
from datetime import datetime

def compare_label_accuracy(csv_path1: str, csv_path2: str) -> Union[float, None]:
    """
    두 개의 CSV 파일에서 'label' 필드 값을 비교하여 일치율(정확도)을 반환합니다.

    :param csv_path1: 첫 번째 CSV 경로
    :param csv_path2: 두 번째 CSV 경로
    :return: 0~1 사이 float (일치 비율), 행 개수가 다르면 None 반환
    """
    with open(csv_path1, encoding="utf-8") as f1, open(csv_path2, encoding="utf-8") as f2:
        reader1 = list(csv.DictReader(f1))
        reader2 = list(csv.DictReader(f2))

    if len(reader1) != len(reader2):
        print("행 개수가 다릅니다.")
        return None

    match_count = 0
    total_count = len(reader1)

    for row1, row2 in zip(reader1, reader2):
        if row1.get("label") == row2.get("label"):
            match_count += 1

    accuracy = match_count / total_count
    return accuracy

def simple_mark_anormal_flexible(input_csv: str, output_csv: str, abnormal_ranges: List[List[str]]):
    def parse_timestamp(ts: str) -> datetime:
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            # iso 포맷 아닌 경우 fallback
            formats = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"]
            for fmt in formats:
                try:
                    return datetime.strptime(ts, fmt)
                except ValueError:
                    continue
            raise ValueError(f"지원하지 않는 timestamp 포맷: {ts}")

    abnormal_periods = [
        (parse_timestamp(start), parse_timestamp(end))
        for start, end in abnormal_ranges
    ]

    with open(input_csv, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in reader:
        ts = parse_timestamp(row["timestamp"])
        row["label"] = "normal"
        for start, end in abnormal_periods:
            if start <= ts <= end:
                row["label"] = "anomaly"
                break

    fieldnames = reader[0].keys()

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

    print(f"{output_csv} 저장 완료.")

def load_json_file(file_path: Union[str, Path]) -> Any:
    """
    주어진 JSON 파일 경로를 받아 내용을 반환합니다.
    :param file_path: JSON 파일 경로 (str 또는 Path)
    :return: JSON 파싱 결과 (dict 또는 list)
    """
    path = Path(file_path)
    
    if not path.is_file():
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
    
    with path.open(encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def get_all_files_with_dirs(base_path: str) -> List[Tuple[str, List[str]]]:
    """
    주어진 base_path 하위 모든 폴더와 파일 이름들을 가져옴.
    
    반환: [(폴더 경로, [파일 리스트]), ...] 형태
    """
    result = []
    for root, dirs, files in os.walk(base_path):
        if files:  # 파일이 있는 경우에만 추가
            result.append((root, files))
    return result

DELETE_PATH=Path("/Users/seongha/Documents/ollama_anomaly/NAB/data")

def lstrip_one_space(s: str) -> str:
    return s[1:]

# 사용 예시:
if __name__ == "__main__":
    base_path = Path("/Users/seongha/Documents/ollama_anomaly/NAB/data")
    file_structure = get_all_files_with_dirs(str(base_path))
    
    label_json_path = Path("/Users/seongha/Documents/ollama_anomaly/NAB/labels/combined_windows.json")
    label_data = load_json_file(label_json_path)

    a = Path("/Users/seongha/Documents/ollama_anomaly/NAB/data/artificialWithAnomaly/art_daily_flatmiddle_label.csv")
    b = Path("/Users/seongha/Documents/ollama_anomaly/NAB/data/artificialWithAnomaly/art_daily_flatmiddle_label_v1.csv")

    # a = r"C:\Users\ojuic\Documents\anormal\NAB\data\realTweets\Twitter_volume_AAPL_label.csv"
    # b = r"C:\Users\ojuic\Documents\anormal\NAB\data\realTweets\Twitter_volume_AAPL_label_v1.csv"


    # 비교하는 함수.
    # print(compare_label_accuracy(a, b) * 100)
    for folder_path, file_list in file_structure:
        for file_name in file_list:
            if file_name == "README.md":
                continue

            full_path = Path(folder_path) / file_name  # ✅ 수정됨: Path 객체로 통합

            try:
                relative_path = full_path.relative_to(DELETE_PATH)  # ✅ 수정됨: 안전한 상대 경로 추출
            except ValueError:
                print(f"⚠️ 경고: 기준 경로 밖 파일 무시 → {full_path}")
                continue

            relative_key = str(relative_path)  # 예: 'realTweets/Twitter_volume_AAPL.csv'

            if relative_key not in label_data:
                print(f"❌ 레이블 정보 없음: {relative_key}")
                continue

            output_path = full_path.with_name(full_path.stem + "_label.csv")  # ✅ 수정됨: _label.csv 저장 경로

            simple_mark_anormal_flexible(
                str(full_path),
                str(output_path),
                label_data[relative_key]
            )