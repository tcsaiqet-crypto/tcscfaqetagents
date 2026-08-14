"""Test script targeting gemini-3.6-flash and gemini-3.5-flash."""

import sys
import requests
from src.config import config

sys.stdout.reconfigure(encoding='utf-8')

def main():
    api_key = config.get_api_key()
    prompt = "Write a short 2-sentence greeting for Quality Engineers working on CFA Digital Journey."

    for model in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        print(f"[TESTING] Calling model '{model}'...")
        try:
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            if r.status_code == 200:
                text = r.json()['candidates'][0]['content']['parts'][0]['text']
                print(f"\n✨ --- SUCCESS ({model}) --- ✨")
                print(text.strip())
                print("------------------------------------------")
                break
            else:
                print(f"[FAIL] {model} Status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[ERROR] {model} failed: {e}")

if __name__ == "__main__":
    main()
