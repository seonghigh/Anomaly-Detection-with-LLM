#utils/data_loader.py
import os

def load_text_data(data_dir: str, num_samples: int):
    files = sorted(f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f)))
    selected = files[:num_samples]
    
    result = []
    for fname in selected:
        with open(os.path.join(data_dir, fname), 'r', encoding='utf-8') as f:
            result.append((fname, f.read()))
    return result
