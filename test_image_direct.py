"""
이미지 생성 API 직접 테스트
"""
import os
import sys
import io
import requests
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("이미지 생성 API 테스트")
print("=" * 80)

# 이미지 생성 요청
data = {
    "prompt": "pixel art game character, simple 2D sprite, colorful",
    "n": 1,
    "size": "512x512",
    "model": ""
}

print(f"\n요청 데이터: {json.dumps(data, indent=2)}")
print(f"\n이미지 생성 요청 중...")

try:
    response = requests.post(
        f"{BASE_URL}/images/generations",
        headers=headers,
        json=data,
        timeout=120
    )

    print(f"\n응답 상태: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"\n생성된 이미지: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if 'data' in result and result['data']:
            for idx, img in enumerate(result['data']):
                print(f"\n이미지 {idx+1} URL: {img.get('url', 'N/A')}")
    else:
        print(f"❌ 실패")
        print(f"응답: {response.text}")

except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
