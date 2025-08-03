#!/bin/bash

BASE_DIR="/Users/seongha/Documents/ollama_anomaly/NAB/data"

# 1. 폴더 선택
FOLDERS=($(ls -d "$BASE_DIR"/*/ | xargs -n 1 basename))
echo "📁 폴더 목록:"
for i in "${!FOLDERS[@]}"; do
  echo "  [$i] ${FOLDERS[$i]}"
done

read -p "👉 사용할 폴더 번호를 입력하세요: " FOLDER_INDEX
SELECTED_FOLDER="${FOLDERS[$FOLDER_INDEX]}"

# 2. 파일 선택
# TARGET_DIR="$BASE_DIR/$SELECTED_FOLDER"
# FILES=($(find "$TARGET_DIR" -maxdepth 1 -type f -name "*.csv" -exec basename {} \;))

# if [ ${#FILES[@]} -eq 0 ]; then
#   echo "❌ 선택한 폴더에 .csv 파일이 없습니다."
#   exit 1
# fi

# echo "📄 파일 목록:"
# for i in "${!FILES[@]}"; do
#   echo "  [$i] ${FILES[$i]}"
# done

# read -p "👉 사용할 파일 번호를 입력하세요: " FILE_INDEX
# SELECTED_FILE="${FILES[$FILE_INDEX]}"

# 3. 모델 및 temperature 선택
read -p "🧠 사용할 모델 이름 (기본: llama3.1:8b): " MODEL_NAME
MODEL_NAME=${MODEL_NAME:-llama3.1:8b}

read -p "🌡️  Temperature 값 (기본: 0.0): " TEMP
TEMP=${TEMP:-0.0}

read -p "🔍 실행할 행 개수 (기본: 10): " ROWS
ROWS=${ROWS:-10}

# 4. 실행
echo ""
echo "🚀 실행 중: python/python2.py --folder \"$SELECTED_FOLDER\" --model \"$MODEL_NAME\" --temp \"$TEMP\" --rows \"$ROWS\""
python3 main2.py --folder "$SELECTED_FOLDER" --model "$MODEL_NAME" --temp "$TEMP" --rows "$ROWS"
