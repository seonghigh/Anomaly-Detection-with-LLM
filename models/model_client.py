#models/model_client.py
import requests

def query_ollama(prompt: str, model="llama3.1:8b", temperature=0.0) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        return f"[ERROR] Ollama 요청 실패: {e}"
