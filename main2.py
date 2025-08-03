import argparse
import os
import pandas as pd
import re

from glob import glob
from utils.file import read_csv_file
from utils.prompt import load_template, build_prompt
from models.model_client import query_ollama

BASE_DIR = "/Users/seongha/Documents/ollama_anomaly/NAB/data"
SCENARIO_DIR = "/Users/seongha/Documents/ollama_anomaly/prompts/scenarios"  
#SCENARIO_PATH = "prompts/scenario.txt"
PROMPT_PATH = "prompts/base_prompt.txt"

def convert_csv_to_text(df) -> str:
    """DataFrame (여러 row) → 텍스트 덩어리로 변환"""
    lines = []
    for _, row in df.iterrows():
        lines.append(f"Time: {row['timestamp']}")
        for col in row.index:
            if col != 'timestamp':
                lines.append(f"{col}: {row[col]}")
        lines.append("")  # 행 사이에 공백
    return "\n".join(lines)

def load_scenario_by_filename(file_path):
    filename = os.path.basename(file_path)
    scenario_name = filename.replace(".csv", ".txt")
    scenario_path = os.path.join(SCENARIO_DIR, scenario_name)
    if not os.path.exists(scenario_path):
        print(f"❌ 시나리오 파일 없음: {scenario_path}")
        return None
    with open(scenario_path, "r") as f:
        return f.read()

def run_single_file(file_path, model_name, temperature, num_rows):
    print(f"\n📄 파일 처리 중: {file_path}")

    # 1. CSV 로드
    df = read_csv_file(file_path)
    if df is None:
        print("❌ CSV 파일을 불러오지 못했습니다.")
        return (os.path.basename(file_path), "Error", "File read failed")
    
    # ✅ 2. 시나리오 개별 불러오기
    scenario = load_scenario_by_filename(file_path)
    if scenario is None:
        return (os.path.basename(file_path), "Error", "Scenario load failed")

    prompt_template = load_template(PROMPT_PATH)

    # # 2. 시나리오/프롬프트 불러오기
    # scenario = load_template(SCENARIO_PATH)
    # prompt_template = load_template(PROMPT_PATH)

    # 3. 텍스트 변환
    sliced_df = df.head(num_rows)
    text_block = convert_csv_to_text(sliced_df)
    prompt = build_prompt(prompt_template, scenario, text_block)

    # 4. Ollama 호출
    print(f"🧠 모델 '{model_name}' 호출 중 (temperature={temperature})...")
    response = query_ollama(prompt, model=model_name, temperature=temperature)

    # 5. 출력
    print("\n📤 Ollama 응답:\n")
    print(response)
    print("-" * 80)
    
    # 결과 판단
    match = re.search(r'final result:\s*\*\*(normal|abnormal)\*\*', response.lower())
    if match:
        decision = match.group(1).capitalize()            
    else:
        decision = "Unknown"

    return (os.path.basename(file_path), decision, response.strip())

def main(folder_name, model_name, temperature, num_rows):
    folder_path = os.path.join(BASE_DIR, folder_name)
    csv_files = glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        print("❌ CSV 파일이 존재하지 않습니다.")
        return

    print(f"✅ 총 {len(csv_files)}개 파일을 처리합니다...\n")

    results = []

    for file_path in csv_files:
        file_name, decision, _ = run_single_file(file_path, model_name, temperature, num_rows)
        results.append({"File": file_name, "Result": decision})

    # 결과 출력 (종합 요약)
    print("\n📊 전체 결과 요약:")
    result_df = pd.DataFrame(results)
    print(result_df.to_string(index=False))  # 🔸 콘솔에만 표로 출력

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=str, required=True)
    #parser.add_argument('--file', type=str, required=True)
    parser.add_argument('--model', type=str, default="llama3.1:8b")
    parser.add_argument('--temp', type=float, default=0.0)
    parser.add_argument('--rows', type=int, default=10, help="실험할 CSV 행 개수 (기본: 10)")
    args = parser.parse_args()

    #main(args.folder, args.file, args.model, args.temp, args.rows)
    main(args.folder, args.model, args.temp, args.rows)
