# 전체 게임 개발 파이프라인 가이드

이 가이드는 게임 기획서 작성부터 이미지 생성, 게임 프로그래밍까지 전체 파이프라인을 설명합니다.

## 개요

Open WebUI의 자율 에이전트 시스템은 다음 작업을 자동으로 수행할 수 있습니다:

1. **게임 기획서 작성** (GAME_DESIGN)
2. **이미지 생성** (IMAGE_GENERATION) - Stable Diffusion 사용
3. **게임 프로그래밍** (LOGIC_DEVELOPMENT)
4. **전체 개발** (FULL_DEVELOPMENT) - 위 모든 단계를 통합

## 전제 조건

### 1. Ollama 설치 및 실행
```bash
# Ollama가 실행 중이어야 합니다
ollama serve

# 적절한 모델 설치 (예: gpt-oss:20b)
ollama pull gpt-oss:20b
```

### 2. Stable Diffusion (선택사항)
이미지 생성을 사용하려면 AUTOMATIC1111 Stable Diffusion WebUI가 필요합니다:

```bash
# Stable Diffusion WebUI 실행
cd stable-diffusion-webui
./webui.sh --api  # 또는 Windows: webui-user.bat --api
```

환경 변수 설정:
```bash
export ENABLE_IMAGE_GENERATION=true
export IMAGE_GENERATION_ENGINE=automatic1111
export AUTOMATIC1111_BASE_URL=http://localhost:7860
```

또는 Open WebUI 관리자 설정에서 이미지 생성을 활성화할 수 있습니다.

## 사용 방법

### API를 통한 사용

#### 1. 게임 기획서만 작성

```python
import requests

BASE_URL = "http://localhost:3000/api/v1"
API_KEY = "your-api-key-here"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 기획서 작성 요청
payload = {
    "name": "Space Shooter Game",
    "task_type": "game_design",
    "user_request": "Create a 2D space shooter game with power-ups and boss battles",
    "auto_execute": True
}

response = requests.post(f"{BASE_URL}/agents/", json=payload, headers=headers)
agent = response.json()
agent_id = agent['id']

# 진행 상태 모니터링
response = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers)
status = response.json()['status']
```

#### 2. 전체 개발 파이프라인 실행

```python
# 전체 개발 (기획 + 이미지 + 코드)
payload = {
    "name": "Complete Puzzle Game",
    "task_type": "full_development",
    "user_request": "Create a match-3 puzzle game with colorful gems and particle effects",
    "auto_execute": True
}

response = requests.post(f"{BASE_URL}/agents/", json=payload, headers=headers)
agent = response.json()
agent_id = agent['id']

# 완료까지 대기 (시간이 걸릴 수 있음)
import time
while True:
    response = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers)
    data = response.json()
    status = data['status']

    if status in ['completed', 'failed']:
        break

    time.sleep(5)

# 결과물 확인
artifacts = data['artifacts']
for step_id, artifact in artifacts.items():
    print(f"{step_id}: {artifact.get('title', 'N/A')}")
```

### 테스트 스크립트 사용

제공된 테스트 스크립트를 사용할 수 있습니다:

```bash
# 전체 파이프라인 테스트
python test_full_pipeline.py

# 결과 확인
python view_agent_results.py
```

## 작업 타입별 설명

### GAME_DESIGN
게임 기획서만 작성합니다. 다음 단계들을 수행:
1. 게임 컨셉 정의
2. 게임플레이 시스템 설계
3. 레벨 디자인
4. 캐릭터/아이템 설계
5. UI/UX 설계
6. 기술적 요구사항
7. 최종 검토

**예상 시간**: 30-60초

### IMAGE_GENERATION
Stable Diffusion을 사용하여 게임 이미지를 생성합니다:
1. 이미지 컨셉 정의
2. 프롬프트 생성
3. 이미지 생성
4. 품질 검토

**예상 시간**: 이미지당 30-60초 (Stable Diffusion 설정에 따라 다름)

**주의**: 이미지 생성이 활성화되어 있어야 합니다.

### LOGIC_DEVELOPMENT
게임 로직 코드를 생성합니다:
1. 로직 구조 설계
2. 핵심 시스템 구현
3. 게임플레이 루프
4. 데이터 관리
5. 코드 검증

**예상 시간**: 60-120초

### FULL_DEVELOPMENT
전체 파이프라인을 실행합니다:
1. 게임 기획서 작성
2. 아트 스타일 정의 및 샘플 이미지
3. 캐릭터/배경 이미지 생성
4. UI 요소 이미지 생성
5. 게임 로직 설계
6. 핵심 시스템 구현
7. 이미지와 로직 통합
8. 테스트 및 최적화
9. 최종 검토

**예상 시간**: 3-5분 (이미지 생성 포함시)

## 결과물 구조

에이전트가 완료되면 다음과 같은 결과물이 생성됩니다:

```json
{
  "id": "agent-id",
  "name": "게임 이름",
  "status": "completed",
  "artifacts": {
    "step_1": {
      "title": "게임 컨셉",
      "content": "...",
      "key_points": [],
      "examples": []
    },
    "step_2": {
      "description": "캐릭터 이미지",
      "prompt": "...",
      "images": ["/api/files/image-url"],
      "count": 1
    },
    "step_3": {
      "language": "Python",
      "framework": "Pygame",
      "code": "...",
      "validation": {...}
    }
  }
}
```

## 생성된 이미지 접근

이미지는 Open WebUI의 파일 시스템에 저장되며 URL로 접근할 수 있습니다:

```python
# 이미지 URL 가져오기
artifacts = agent_data['artifacts']
for step_id, artifact in artifacts.items():
    if 'images' in artifact:
        for image_url in artifact['images']:
            full_url = f"http://localhost:3000{image_url}"
            print(f"Image: {full_url}")
```

## 에이전트 제어

### 일시정지
```python
response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/pause",
    headers=headers
)
```

### 재개
```python
response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/resume",
    headers=headers
)
```

### 재시도 (실패한 단계부터)
```python
response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/retry",
    headers=headers
)
```

## 문제 해결

### 이미지가 생성되지 않음
1. `ENABLE_IMAGE_GENERATION=true` 확인
2. Stable Diffusion WebUI가 실행 중인지 확인
3. `AUTOMATIC1111_BASE_URL`이 올바른지 확인
4. 로그에서 오류 확인: `backend/open_webui/logs/`

### LLM 타임아웃
- 더 작은 모델 사용
- 타임아웃 시간 증가 (agent_executor.py의 timeout 파라미터)

### 메모리 부족
- 더 작은 모델 사용
- 배치 크기 줄이기 (이미지 생성)

## 고급 사용

### 커스텀 컨텍스트 제공
```python
payload = {
    "name": "Custom Game",
    "task_type": "full_development",
    "user_request": "Create an RPG game",
    "context": {
        "art_style": "pixel art",
        "target_platform": "web browser",
        "framework": "Phaser 3",
        "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"]
    },
    "auto_execute": True
}
```

### 단계별 수동 실행
```python
# auto_execute를 False로 설정
payload = {
    "name": "Manual Game",
    "task_type": "full_development",
    "user_request": "Create a platformer game",
    "auto_execute": False
}

response = requests.post(f"{BASE_URL}/agents/", json=payload, headers=headers)
agent_id = response.json()['id']

# 계획만 생성
# (에이전트는 자동으로 계획을 생성하고 대기)

# 실행 시작
response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/resume",
    headers=headers
)
```

## 참고 자료

- [GAME_AGENT_GUIDE.md](GAME_AGENT_GUIDE.md) - 에이전트 시스템 전체 가이드
- [test_full_pipeline.py](test_full_pipeline.py) - 전체 파이프라인 테스트 스크립트
- [view_agent_results.py](view_agent_results.py) - 결과 확인 스크립트
- Open WebUI 문서: https://docs.openwebui.com

## 예제

완전한 예제는 `test_full_pipeline.py`를 참조하세요.

## 기여

이슈나 개선 사항이 있다면 GitHub 이슈로 제출해주세요.
