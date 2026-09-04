"""
이미지 생성 설정 직접 확인
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Open WebUI config 직접 import
from backend.open_webui.config import (
    ENABLE_IMAGE_GENERATION,
    IMAGE_GENERATION_ENGINE,
    AUTOMATIC1111_BASE_URL,
    IMAGE_SIZE,
    IMAGE_STEPS
)

print("=" * 80)
print("이미지 생성 설정 (직접 확인)")
print("=" * 80)

print(f"\nENABLE_IMAGE_GENERATION: {ENABLE_IMAGE_GENERATION}")
print(f"IMAGE_GENERATION_ENGINE: {IMAGE_GENERATION_ENGINE}")
print(f"AUTOMATIC1111_BASE_URL: {AUTOMATIC1111_BASE_URL}")
print(f"IMAGE_SIZE: {IMAGE_SIZE}")
print(f"IMAGE_STEPS: {IMAGE_STEPS}")

print("\n" + "=" * 80)

if not ENABLE_IMAGE_GENERATION:
    print("\n⚠️  이미지 생성이 비활성화되어 있습니다!")
    print("\n활성화 방법:")
    print("1. 관리자 페이지에서: http://localhost:3000/admin/settings")
    print("2. 환경 변수 설정: ENABLE_IMAGE_GENERATION=true")
    print("3. 데이터베이스 직접 수정")

if IMAGE_GENERATION_ENGINE != "automatic1111":
    print(f"\n⚠️  이미지 생성 엔진이 '{IMAGE_GENERATION_ENGINE}'로 설정되어 있습니다!")
    print("Automatic1111로 변경하려면:")
    print("1. 관리자 페이지에서 변경")
    print("2. 환경 변수: IMAGE_GENERATION_ENGINE=automatic1111")

if not AUTOMATIC1111_BASE_URL:
    print("\n⚠️  AUTOMATIC1111_BASE_URL이 설정되지 않았습니다!")
    print("환경 변수로 설정: AUTOMATIC1111_BASE_URL=http://127.0.0.1:7860")

# Stable Diffusion 연결 테스트
if AUTOMATIC1111_BASE_URL:
    import requests
    try:
        print(f"\nStable Diffusion 연결 테스트: {AUTOMATIC1111_BASE_URL}")
        response = requests.get(f"{AUTOMATIC1111_BASE_URL}/sdapi/v1/sd-models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 연결 성공! 사용 가능한 모델: {len(models)}개")
            if models:
                print(f"   현재 모델: {models[0].get('model_name', 'Unknown')}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 연결 실패: Stable Diffusion WebUI가 실행되지 않았습니다")
        print(f"   URL: {AUTOMATIC1111_BASE_URL}")
    except Exception as e:
        print(f"❌ 오류: {e}")

print("\n" + "=" * 80)
