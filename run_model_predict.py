import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import tempfile
import os

from utils.labeling import (
    load_json_file,
    simple_mark_anormal_flexible,
    compare_label_accuracy,
)
from utils.predict import query_ollama_and_extract_timestamps
from utils.file import read_csv_file

# 절대 경로 기반 프로젝트 루트
PROJECT_ROOT = Path("/Users/seongha/Documents/ollama_anomaly")
BASE_DIR = PROJECT_ROOT / "NAB/data"
LABEL_JSON_PATH = PROJECT_ROOT / "NAB/labels/combined_windows.json"


# 📌 timestamp 파싱 함수
def parse_timestamp(ts: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(ts)


# 문자열 기반 비교를 위해 datetime → str 변환
def format_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 📌 LLM 예측 결과를 CSV로 저장
def save_labeled_csv(base_csv_path: Path, anomaly_timestamps: List[datetime], output_path: Path):
    # 미리 문자열 형태로 anomaly timestamp 목록 준비
    anomaly_ts_strs = set(format_ts(ts) for ts in anomaly_timestamps)

    with open(base_csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        # 문자열로 직접 비교
        ts_str = row["timestamp"].strip()
        row["label"] = "anomaly" if ts_str in anomaly_ts_strs else "normal"

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ 예측 라벨 저장: {output_path}")


# 🧩 label 모드
def run_label_mode(folder: str, file: str):
    file_path = BASE_DIR / folder / file
    label_data = load_json_file(LABEL_JSON_PATH)
    relative_key = f"{folder}/{file}"

    if relative_key not in label_data:
        print(f"❌ 레이블 정보 없음: {relative_key}")
        return

    label_dir = BASE_DIR / folder / "label"
    label_dir.mkdir(parents=True, exist_ok=True)
    label_path = label_dir / f"{Path(file).stem}_label.csv"

    simple_mark_anormal_flexible(str(file_path), str(label_path), label_data[relative_key])
    print(f"✅ 정답 라벨 저장: {label_path}")


# 🧩 predict 모드
# def run_predict_mode(folder: str, file: str, model_name: str, temperature: float, num_rows: int):
#     file_path = BASE_DIR / folder / file
#     print(f"🧠 Ollama 예측 시작: {model_name} (T={temperature})")

#     predicted_timestamps = query_ollama_and_extract_timestamps(
#         str(file_path), model_name, temperature, num_rows
#     )

#     result_dir = file_path.parent / file_path.stem
#     result_dir.mkdir(exist_ok=True)

#     version_prefix = f"{file_path.stem}_v1_"
#     existing = list(result_dir.glob(f"{version_prefix}*.csv"))
#     next_version = (
#         max(
#             [int(f.stem.split("_v1_")[-1]) for f in existing if f.stem.split("_v1_")[-1].isdigit()]
#             + [0]
#         )
#         + 1
#     )

#     result_path = result_dir / f"{version_prefix}{next_version}.csv"
#     save_labeled_csv(file_path, predicted_timestamps, result_path)


def run_predict_mode(folder: str, file: str, model_name: str, temperature: float, num_rows: int):
    file_path = BASE_DIR / folder / file
    print(f"🧠 Ollama 예측 시작: {model_name} (T={temperature})")

    # 전체 CSV 로드
    df = read_csv_file(str(file_path))
    if df is None or df.empty:
        print("❌ CSV 데이터를 읽을 수 없습니다.")
        return

    stride = num_rows // 2  # ✅ 슬라이딩 간격 (중첩 50%)
    total_rows = len(df)
    all_predicted = []

    for start in range(0, total_rows, stride):
        end = start + num_rows
        if start >= total_rows:
            break

        sliced_df = df.iloc[start:end].copy()
        if sliced_df.empty:
            continue

         # ✅ 슬라이스를 임시 파일로 저장
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="", encoding="utf-8") as tmp_file:
            sliced_df.to_csv(tmp_file.name, index=False)
            temp_file_path = tmp_file.name

        # ✅ 각 슬라이스에 대해 모델 예측 (원본 파일 이름 전달)
        predicted_ts = query_ollama_and_extract_timestamps(
            temp_file_path, model_name, temperature, num_rows, original_file_name=file
        )
        all_predicted.extend(predicted_ts)

        print(f"📈 슬라이스 {start}~{end} → {len(predicted_ts)}개 예측")

        # ✅ 임시 파일 삭제
        os.remove(temp_file_path)


    # 중복 제거 및 정렬
    unique_predicted = sorted(set(all_predicted))

    # 결과 저장
    result_dir = file_path.parent / file_path.stem
    result_dir.mkdir(exist_ok=True)

    version_prefix = f"{file_path.stem}_v1_"
    existing = list(result_dir.glob(f"{version_prefix}*.csv"))
    next_version = (
        max(
            [int(f.stem.split("_v1_")[-1]) for f in existing if f.stem.split("_v1_")[-1].isdigit()]
            + [0]
        )
        + 1
    )

    result_path = result_dir / f"{version_prefix}{next_version}.csv"
    save_labeled_csv(file_path, unique_predicted, result_path)
    print(f"✅ 전체 예측 라벨 저장 완료: {result_path}")


# 🧩 evaluate 모드
def run_evaluate_mode(folder: str, file: str):
    pred_path = Path(file)
    if not pred_path.is_absolute():
        pred_path = BASE_DIR / folder / file

    if not pred_path.exists():
        print(f"❌ 예측 결과 파일이 존재하지 않습니다: {pred_path}")
        return

    label_path = pred_path.parent.parent / "label" / f"{pred_path.stem.split('_v1_')[0]}_label.csv"
    if not label_path.exists():
        print(f"❌ 정답 라벨 파일이 존재하지 않습니다: {label_path}")
        return

    accuracy = compare_label_accuracy(str(label_path), str(pred_path))
    if accuracy is not None:
        print(f"✅ 정확도: {accuracy * 100:.2f}%")
    else:
        print("⚠️ 비교 실패: 두 파일의 행 개수가 다릅니다.")


# 🚀 메인 함수
def main(
    folder: str,
    file: str,
    mode: str,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    num_rows: int = 1000,
):
    file_path = BASE_DIR / folder / file
    if mode in {"label", "predict"} and not file_path.exists():
        print(f"❌ 데이터 파일이 존재하지 않습니다: {file_path}")
        return

    if mode == "label":
        run_label_mode(folder, file)
    elif mode == "predict":
        if not model_name or temperature is None:
            print("❌ 모델 이름과 temperature 값을 모두 입력해야 합니다.")
            return
        run_predict_mode(folder, file, model_name, temperature, num_rows)
    elif mode == "evaluate":
        run_evaluate_mode(folder, file)
    else:
        print(f"❌ 지원하지 않는 모드입니다: {mode}")


# 🧵 CLI 실행
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, required=True, help="데이터 폴더 이름")
    parser.add_argument("--file", type=str, required=True, help="CSV 파일 이름")
    parser.add_argument("--mode", type=str, choices=["label", "predict", "evaluate"], required=True)
    parser.add_argument("--model", type=str, help="Ollama 모델 이름 (예: mistral, llama3 등)")
    parser.add_argument("--temp", type=float, help="LLM temperature 값")
    parser.add_argument("--num_rows", type=int, default=1000, help="LLM에 넣을 row 수 제한")

    args = parser.parse_args()

    main(
        folder=args.folder,
        file=args.file,
        mode=args.mode,
        model_name=args.model,
        temperature=args.temp,
        num_rows=args.num_rows,
    )
