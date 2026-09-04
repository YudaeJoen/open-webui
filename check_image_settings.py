"""
이미지 생성 설정 확인 스크립트
"""
import os
import requests
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:3000/api/v1"
API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("이미지 생성 설정 확인")
print("=" * 80)

try:
    # Admin settings 엔드포인트 시도
    response = requests.get(f"{BASE_URL}/configs", headers=headers, timeout=10)

    if response.status_code == 200:
        config = response.json()
        print("\n현재 설정:")
        print(f"  ENABLE_IMAGE_GENERATION: {config.get('ENABLE_IMAGE_GENERATION', 'Not set')}")
        print(f"  IMAGE_GENERATION_ENGINE: {config.get('IMAGE_GENERATION_ENGINE', 'Not set')}")
        print(f"  AUTOMATIC1111_BASE_URL: {config.get('AUTOMATIC1111_BASE_URL', 'Not set')}")
        print(f"  IMAGE_SIZE: {config.get('IMAGE_SIZE', 'Not set')}")
        print(f"  IMAGE_STEPS: {config.get('IMAGE_STEPS', 'Not set')}")
    else:
        print(f"\n설정 조회 실패: HTTP {response.status_code}")
        print(f"응답: {response.text[:200]}")

    print("\n" + "=" * 80)
    print("이미지 생성 활성화 방법:")
    print("=" * 80)
    print("\n1. Open WebUI 관리자 페이지에서 설정:")
    print("   - http://localhost:3000/admin/settings 접속")
    print("   - 'Images' 섹션으로 이동")
    print("   - 'Enable Image Generation' 활성화")
    print("   - 'Image Generation Engine'을 'Automatic1111'로 설정")
    print("   - 'Automatic1111 Base URL'을 Stable Diffusion WebUI 주소로 설정")
    print("     (예: http://127.0.0.1:7860)")

    print("\n2. 또는 환경 변수로 설정 (.env 파일):")
    print("   ENABLE_IMAGE_GENERATION=true")
    print("   IMAGE_GENERATION_ENGINE=automatic1111")
    print("   AUTOMATIC1111_BASE_URL=http://127.0.0.1:7860")

    print("\n3. Stable Diffusion WebUI 실행 확인:")
    try:
        # 먼저 config에서 URL 확인
        sd_url = config.get('AUTOMATIC1111_BASE_URL', 'http://127.0.0.1:7860')
        if not sd_url:
            sd_url = 'http://127.0.0.1:7860'

        sd_response = requests.get(f"{sd_url}/sdapi/v1/sd-models", timeout=5)
        if sd_response.status_code == 200:
            models = sd_response.json()
            print(f"   ✅ Stable Diffusion WebUI 실행 중 ({sd_url})")
            print(f"   사용 가능한 모델: {len(models)}개")
            if models:
                print(f"   현재 모델: {models[0].get('model_name', 'Unknown')}")
        else:
            print(f"   ❌ Stable Diffusion WebUI 응답 이상: HTTP {sd_response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Stable Diffusion WebUI에 연결할 수 없습니다 ({sd_url})")
        print("      Stable Diffusion WebUI를 시작하세요:")
        print("      cd stable-diffusion-webui")
        print("      ./webui.sh --api  (또는 Windows: webui-user.bat --api)")
    except Exception as e:
        print(f"   ⚠️  확인 중 오류: {e}")

    print("\n" + "=" * 80)

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

print()
