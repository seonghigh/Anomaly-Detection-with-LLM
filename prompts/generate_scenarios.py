import os

BASE_DIR = "/Users/seongha/Documents/ollama_anomaly/NAB/data"
SCENARIO_DIR = "/Users/seongha/Documents/ollama_anomaly/prompts/scenarios"

# 기본 시나리오 내용
DEFAULT_RULE = """Between 09:00 and 12:00, if the value exceeds 60.0, it is considered abnormal.
Otherwise, it is normal.
"""

def list_subfolders(base_path):
    return [name for name in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, name))]

def prompt_user_to_select_folder(folders):
    print("📁 사용할 폴더를 선택하세요:")
    for idx, folder in enumerate(folders):
        print(f"  [{idx}] {folder}")
    while True:
        try:
            selected = int(input("👉 번호 입력: "))
            if 0 <= selected < len(folders):
                return folders[selected]
            else:
                print("❌ 유효하지 않은 번호입니다.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")

def generate_scenarios(folder_name):
    folder_path = os.path.join(BASE_DIR, folder_name)

    if not os.path.exists(SCENARIO_DIR):
        os.makedirs(SCENARIO_DIR)

    for file in os.listdir(folder_path):
        if not file.endswith(".csv"):
            continue

        scenario_name = file.replace(".csv", ".txt")
        scenario_path = os.path.join(SCENARIO_DIR, scenario_name)

        if os.path.exists(scenario_path):
            print(f"✅ 이미 존재: {scenario_name}")
            continue

        with open(scenario_path, "w") as f:
            f.write(DEFAULT_RULE)
            print(f"📝 생성됨: {scenario_name}")

if __name__ == "__main__":
    folders = list_subfolders(BASE_DIR)
    if not folders:
        print("❌ 폴더가 없습니다.")
        exit(1)

    selected_folder = prompt_user_to_select_folder(folders)
    generate_scenarios(selected_folder)
