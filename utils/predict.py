import re
import pandas as pd
from datetime import datetime
from typing import List

from utils.file import read_csv_file
from utils.prompt import load_template, build_prompt
from models.model_client import query_ollama  # ✅ Ollama 인터페이스 함수

# 경로 설정
SCENARIO_DIR = "/Users/seongha/Documents/ollama_anomaly/prompts/scenarios"
PROMPT_PATH = "/Users/seongha/Documents/ollama_anomaly/prompts/base_prompt.txt"

def convert_csv_to_text(df: pd.DataFrame) -> str:
    """CSV → 프롬프트용 텍스트 변환"""
    lines = []
    for _, row in df.iterrows():
        lines.append(f"Time: {row['timestamp']}")
        for col in row.index:
            if col != 'timestamp':
                lines.append(f"{col}: {row[col]}")
        lines.append("")  # 행 구분 공백
    return "\n".join(lines)

# 이전 'extract_abnormal_timestamps' 제거
def extract_iso_timestamps(response: str) -> List[datetime]:
    """LLM 응답에서 YYYY-MM-DD HH:MM:SS 형식의 timestamp만 추출"""
    pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    matches = re.findall(pattern, response)
    timestamps = []
    for ts in matches:
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            timestamps.append(dt)
        except ValueError:
            print(f"⚠️ 파싱 실패: {ts}")
    if not timestamps:
        print("⚠️ 모델 응답에서 timestamp를 찾지 못했습니다.")
    return timestamps


# def load_scenario_by_filename(file_path: str) -> str:
#     """CSV와 동일한 이름의 시나리오 텍스트 로드"""
#     import os
#     from pathlib import Path
#     filename = Path(file_path).name.replace(".csv", ".txt")
#     scenario_path = Path(SCENARIO_DIR) / filename
#     if not scenario_path.exists():
#         raise FileNotFoundError(f"❌ 시나리오 파일 없음: {scenario_path}")
#     return scenario_path.read_text(encoding="utf-8")
def load_scenario_by_filename(file_path: str, original_file_name: str = None) -> str:
    """
    CSV와 동일한 이름의 시나리오 텍스트 로드.
    original_file_name이 주어지면 그것을 기준으로 로드.
    """
    from pathlib import Path
    path = Path(file_path)

    # 원본 파일 이름을 우선 사용
    if original_file_name:
        filename = Path(original_file_name).name.replace(".csv", ".txt")
    else:
        filename = path.name.replace(".csv", ".txt")

    scenario_path = Path(SCENARIO_DIR) / filename
    if not scenario_path.exists():
        raise FileNotFoundError(f"❌ 시나리오 파일 없음: {scenario_path}")
    return scenario_path.read_text(encoding="utf-8")


# def query_ollama_and_extract_timestamps(
#     file_path: str,
#     model_name: str = "llama3.1:8b",
#     temperature: float = 0.0,
#     num_rows: int = 1000
# ) -> List[datetime]:
#     """CSV + 시나리오 → 프롬프트 → Ollama → 이상 시점 추출"""
#     df = read_csv_file(file_path)
#     if df is None:
#         raise RuntimeError(f"❌ CSV 파일 로드 실패: {file_path}")
    
#     sliced_df = df.head(num_rows)
#     text_block = convert_csv_to_text(sliced_df)

#     scenario = load_scenario_by_filename(file_path)
#     prompt_template = load_template(PROMPT_PATH)
#     prompt = build_prompt(prompt_template, scenario, text_block)

#     print("🧠 Ollama 모델 호출 중...")
#     response = query_ollama(prompt, model=model_name, temperature=temperature)

#     print("📤 모델 응답 완료\n" + "-"*80)
#     print(response)

#     # 응답에서 timestamp만 추출하는 함수로 교체
#     return extract_iso_timestamps(response)
def query_ollama_and_extract_timestamps(
    file_path: str,
    model_name: str = "llama3.1:8b",
    temperature: float = 0.0,
    num_rows: int = 1000,
    original_file_name: str = None
) -> List[datetime]:
    """
    CSV + 시나리오 → 프롬프트 → Ollama → 이상 시점 추출.
    original_file_name이 있으면 시나리오 로딩에 사용.
    """
    df = read_csv_file(file_path)
    if df is None:
        raise RuntimeError(f"❌ CSV 파일 로드 실패: {file_path}")
    
    sliced_df = df.head(num_rows)
    text_block = convert_csv_to_text(sliced_df)

    # 시나리오 로드
    scenario = load_scenario_by_filename(file_path, original_file_name)
    prompt_template = load_template(PROMPT_PATH)
    prompt = build_prompt(prompt_template, scenario, text_block)

    print("🧠 Ollama 모델 호출 중...")
    response = query_ollama(prompt, model=model_name, temperature=temperature)

    print("📤 모델 응답 완료\n" + "-"*80)
    print(response)

    return extract_iso_timestamps(response)

