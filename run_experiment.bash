#!/bin/bash

PROJECT_ROOT="/Users/seongha/Documents/ollama_anomaly"
PYTHON_SCRIPT="$PROJECT_ROOT/run_model_predict.py"
DATA_DIR="$PROJECT_ROOT/NAB/data"

echo "🧪 실험 모드를 선택하세요:"
select mode in "label" "predict" "evaluate"; do
    [[ -n "$mode" ]] && break
done

# 📁 폴더 선택
echo "📁 데이터 폴더 선택:"
folders=($(find "$DATA_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;))
select folder in "${folders[@]}"; do
    [[ -n "$folder" ]] && break
done

# 📄 파일 선택
echo "📄 CSV 파일 선택:"
files=($(find "$DATA_DIR/$folder" -maxdepth 1 -name "*.csv" -exec basename {} \;))
select file in "${files[@]}"; do
    [[ -n "$file" ]] && break
done

# ⚙️ 옵션: predict 모드
if [ "$mode" == "predict" ]; then
    read -p "🧠 사용할 모델 이름 (기본: llama3.1:8b): " model
    model=${model:-llama3.1:8b}

    read -p "🔥 temperature 값 (기본: 0.0): " temp
    temp=${temp:-0.0}

    read -p "📏 사용할 row 수 (기본 1000): " num_rows
    num_rows=${num_rows:-1000}

    # ✅ 반복 횟수 입력 추가
    read -p "🔁 반복 횟수 입력 (기본: 1): " repeat
    repeat=${repeat:-1}

    echo "🚀 모델 예측 반복 실행 중..."

    # ✅ 루프 추가
    for ((i=1; i<=repeat; i++)); do
        echo "🔂 실행 $i / $repeat"
        python3 "$PYTHON_SCRIPT" --folder "$folder" --file "$file" --mode "$mode" --model "$model" --temp "$temp" --num_rows "$num_rows"
    done

    # echo "🚀 모델 예측 실행 중..."
    # python3 "$PYTHON_SCRIPT" --folder "$folder" --file "$file" --mode "$mode" --model "$model" --temp "$temp" --num_rows "$num_rows"

# ⚙️ 옵션: evaluate 모드
elif [ "$mode" == "evaluate" ]; then
    echo "📊 예측 결과 파일 선택:"
    file_stem="${file%.csv}"  # 확장자 제거
    pred_dir="$DATA_DIR/$folder/$file_stem"
    pred_files=($(find "$pred_dir" -maxdepth 1 -name "*_v1_*.csv" -exec basename {} \;))

    if [ ${#pred_files[@]} -eq 0 ]; then
        echo "❌ 예측 결과 파일이 없습니다: $pred_dir"
        exit 1
    fi

    select pred_file in "${pred_files[@]}"; do
        [[ -n "$pred_file" ]] && break
    done

    echo "📐 정확도 비교 중..."
    # 🔧 수정: 예측 파일 경로에 하위 폴더 포함
    python3 "$PYTHON_SCRIPT" --folder "$folder" --file "$file_stem/$pred_file" --mode "$mode"


# ⚙️ label 모드
else
    echo "🏷 정답 라벨 생성 중..."
    python3 "$PYTHON_SCRIPT" --folder "$folder" --file "$file" --mode "$mode"
fi
