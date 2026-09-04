# 게임 개발 에이전트 시스템 가이드

Open WebUI에 통합된 게임 개발 자율 에이전트 시스템입니다. 이 시스템은 Ollama LLM과 Stable Diffusion을 활용하여 게임 개발 과정을 자동화합니다.

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치 및 설정](#설치-및-설정)
- [사용 방법](#사용-방법)
- [API 문서](#api-문서)
- [개발 가이드](#개발-가이드)

## 🎮 개요

게임 개발 에이전트는 사용자의 요청을 받아 **플랜을 자동으로 수립**하고, **단계별로 실행**하며, **자체 검토**를 통해 게임 개발 프로세스를 자동화하는 AI 에이전트 시스템입니다.

### 핵심 특징

- ✅ **자율 실행**: 사용자가 목표만 제시하면 에이전트가 자동으로 계획 수립 및 실행
- ✅ **단계별 검토**: 각 단계마다 자체 검토를 통해 품질 보장
- ✅ **Stable Diffusion 통합**: 게임 아트워크 자동 생성
- ✅ **Ollama LLM 활용**: 기획서 작성, 로직 개발, 코드 생성
- ✅ **일시정지/재개**: 작업 중단 및 재개 가능
- ✅ **실패 재시도**: 실패한 단계부터 자동 재시도

## 🎯 주요 기능

### 1. 게임 기획서 작성 (Game Design)

사용자의 게임 컨셉을 바탕으로 상세한 기획서를 자동 생성합니다.

**포함 내용:**
- 게임 컨셉 및 목표
- 게임플레이 메커니즘
- 레벨 디자인 및 진행 구조
- 캐릭터/아이템 설계
- UI/UX 설계
- 기술적 요구사항

### 2. 이미지 생성 (Image Generation)

Stable Diffusion (AUTOMATIC1111/ComfyUI)을 통해 게임 아트워크를 자동 생성합니다.

**생성 가능한 이미지:**
- 캐릭터 디자인
- 배경 및 환경
- UI 요소
- 아이템 및 오브젝트

**LLM 프롬프트 최적화:**
- 한국어 요청을 영어 프롬프트로 자동 변환
- 컨텐츠 유형에 따른 최적 모델/LoRA 자동 선택
- 이미지 품질 설정 자동 조정

### 3. 게임 로직 개발 (Logic Development)

게임 로직 및 코드를 자동으로 생성합니다.

**생성 가능한 로직:**
- 게임플레이 시스템
- 플레이어 컨트롤
- AI 로직
- 충돌 감지 및 물리
- 게임 상태 관리

### 4. 전체 개발 (Full Development)

기획 → 이미지 생성 → 로직 개발을 통합하여 전체 게임 개발 프로세스를 자동화합니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 요청                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Agent Controller (agents.py)                │
│  - 요청 접수 및 에이전트 생성                              │
│  - 상태 관리 (일시정지/재개/재시도)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Agent Executor (agent_executor.py)               │
│                                                           │
│  Step 1: Planning Phase                                  │
│  ┌────────────────────────────────┐                     │
│  │ LLM에게 작업 분석 요청          │                     │
│  │ → 단계별 실행 계획 수립          │                     │
│  │ → 검토 포인트 설정              │                     │
│  └────────────────────────────────┘                     │
│                                                           │
│  Step 2: Execution Phase                                 │
│  ┌────────────────────────────────┐                     │
│  │ 각 단계별 실행:                │                     │
│  │  - 기획 단계 → LLM 호출         │                     │
│  │  - 이미지 단계 → SD API 호출    │                     │
│  │  - 로직 단계 → LLM 코드 생성    │                     │
│  │ → 결과물 저장 (artifacts)       │                     │
│  └────────────────────────────────┘                     │
│                                                           │
│  Step 3: Review Phase                                    │
│  ┌────────────────────────────────┐                     │
│  │ 각 단계 완료 후 자체 검토        │                     │
│  │ → 품질 평가 및 개선 사항 도출   │                     │
│  │ → 필요시 재실행                 │                     │
│  └────────────────────────────────┘                     │
│                                                           │
│  Step 4: Final Review                                    │
│  ┌────────────────────────────────┐                     │
│  │ 최종 결과물 종합 검토            │                     │
│  │ → 완성도 평가                   │                     │
│  │ → 향후 개선 사항 제안           │                     │
│  └────────────────────────────────┘                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 External Services                        │
│                                                           │
│  ┌──────────────┐  ┌────────────────┐                  │
│  │ Ollama LLM   │  │ Stable Diffusion│                 │
│  │ - 기획서     │  │ - AUTOMATIC1111 │                 │
│  │ - 로직 생성  │  │ - ComfyUI       │                 │
│  │ - 코드 생성  │  │ - 이미지 생성   │                 │
│  └──────────────┘  └────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### 데이터베이스 모델

**Agent 테이블:**
- `id`: 에이전트 고유 ID
- `user_id`: 사용자 ID
- `chat_id`: 연결된 채팅 ID (선택)
- `name`: 에이전트 이름
- `task_type`: 작업 유형 (game_design, image_generation, etc.)
- `status`: 상태 (idle, planning, executing, reviewing, completed, failed, paused)
- `user_request`: 사용자 원본 요청
- `plan`: 실행 계획 (JSON)
- `execution_history`: 실행 이력 (JSON Array)
- `current_step`: 현재 실행 중인 단계
- `artifacts`: 생성된 결과물 (JSON)

## 🚀 설치 및 설정

### 1. 데이터베이스 마이그레이션

에이전트 테이블을 생성합니다:

```bash
# Backend 디렉토리에서
cd backend
alembic revision --autogenerate -m "Add agent table"
alembic upgrade head
```

또는 수동으로 테이블 생성:

```sql
CREATE TABLE agent (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    chat_id VARCHAR,
    name VARCHAR NOT NULL,
    description TEXT,
    task_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'idle',
    user_request TEXT NOT NULL,
    context JSON DEFAULT '{}',
    plan JSON DEFAULT '{}',
    execution_history JSON DEFAULT '[]',
    current_step VARCHAR,
    artifacts JSON DEFAULT '{}',
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    completed_at BIGINT
);
```

### 2. 환경 변수 설정

`.env` 파일에 다음 설정 추가:

```bash
# Ollama 설정 (필수)
OLLAMA_BASE_URL=http://localhost:11434

# Stable Diffusion 설정 (이미지 생성시 필수)
ENABLE_IMAGE_GENERATION=True
IMAGE_GENERATION_ENGINE=automatic1111  # 또는 comfyui

# AUTOMATIC1111 설정
AUTOMATIC1111_BASE_URL=http://localhost:7860
AUTOMATIC1111_PROMPT_GENERATION_MODEL=llama3.2:latest  # 프롬프트 최적화용 모델

# 또는 ComfyUI 설정
COMFYUI_BASE_URL=http://localhost:8188
COMFYUI_API_KEY=your_api_key
```

### 3. 서버 재시작

```bash
# 백엔드 재시작
cd backend
uvicorn open_webui.main:app --reload

# 프론트엔드 재빌드
cd ..
npm run build
```

## 📖 사용 방법

### API를 통한 사용

#### 1. 게임 기획서 생성

```bash
curl -X POST "http://localhost:8080/api/v1/agents/quick/game-design" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_concept": "2D 플랫포머 액션 게임",
    "genre": "액션",
    "target_platform": "PC"
  }'
```

#### 2. 이미지 생성

```bash
curl -X POST "http://localhost:8080/api/v1/agents/quick/image-generation" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "귀여운 캐릭터 디자인, 판타지 스타일",
    "style": "anime",
    "count": 3
  }'
```

#### 3. 전체 게임 개발

```bash
curl -X POST "http://localhost:8080/api/v1/agents/quick/full-development" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_concept": "우주 배경의 슈팅 게임",
    "genre": "슈팅",
    "target_platform": "모바일",
    "art_style": "픽셀아트"
  }'
```

#### 4. 에이전트 상태 확인

```bash
# 에이전트 조회
curl -X GET "http://localhost:8080/api/v1/agents/AGENT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 일시정지
curl -X POST "http://localhost:8080/api/v1/agents/AGENT_ID/pause" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 재개
curl -X POST "http://localhost:8080/api/v1/agents/AGENT_ID/resume" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 재시도 (실패시)
curl -X POST "http://localhost:8080/api/v1/agents/AGENT_ID/retry" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### TypeScript/JavaScript에서 사용

```typescript
import { quickGameDesign, getAgentById } from '$lib/apis/agents';

// 게임 기획서 생성
const agent = await quickGameDesign(token, {
	game_concept: '턴제 전략 RPG 게임',
	genre: 'RPG',
	target_platform: 'PC'
});

console.log('Agent ID:', agent.id);
console.log('Status:', agent.status);

// 진행 상황 확인
const checkProgress = setInterval(async () => {
	const updated = await getAgentById(token, agent.id);
	console.log('Current step:', updated.current_step);
	console.log('Status:', updated.status);

	if (updated.status === 'completed') {
		clearInterval(checkProgress);
		console.log('Artifacts:', updated.artifacts);
	}
}, 5000);
```

## 📚 API 문서

### 에이전트 관리 API

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/agents/` | GET | 사용자의 모든 에이전트 조회 |
| `/api/v1/agents/` | POST | 새 에이전트 생성 |
| `/api/v1/agents/{id}` | GET | 특정 에이전트 조회 |
| `/api/v1/agents/{id}/update` | POST | 에이전트 업데이트 |
| `/api/v1/agents/{id}` | DELETE | 에이전트 삭제 |
| `/api/v1/agents/chat/{chat_id}` | GET | 채팅별 에이전트 조회 |

### 에이전트 제어 API

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/agents/{id}/pause` | POST | 에이전트 일시정지 |
| `/api/v1/agents/{id}/resume` | POST | 에이전트 재개 |
| `/api/v1/agents/{id}/retry` | POST | 실패한 에이전트 재시도 |

### 빠른 실행 API

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/agents/quick/game-design` | POST | 빠른 기획서 생성 |
| `/api/v1/agents/quick/image-generation` | POST | 빠른 이미지 생성 |
| `/api/v1/agents/quick/full-development` | POST | 전체 게임 개발 |

## 🔧 개발 가이드

### 새로운 작업 유형 추가

1. **모델 수정** (`backend/open_webui/models/agents.py`):

```python
class AgentTaskType(str, Enum):
    GAME_DESIGN = "game_design"
    IMAGE_GENERATION = "image_generation"
    LOGIC_DEVELOPMENT = "logic_development"
    FULL_DEVELOPMENT = "full_development"
    YOUR_NEW_TYPE = "your_new_type"  # 추가
```

2. **플래닝 프롬프트 추가** (`backend/open_webui/utils/agent_executor.py`):

```python
elif task_type == AgentTaskType.YOUR_NEW_TYPE:
    base_prompt += """
    새로운 작업 유형에 대한 플래닝 가이드...
    """
```

3. **실행 로직 추가**:

```python
async def _execute_your_new_step(self, step: AgentPlanStep) -> Dict[str, Any]:
    """새로운 작업 유형 실행"""
    # 구현...
    pass
```

### 커스텀 도구 통합

에이전트는 Open WebUI의 도구 시스템과 통합 가능합니다:

```python
# backend/open_webui/utils/agent_executor.py

async def _execute_step_with_tool(self, step: AgentPlanStep, tool_id: str):
    """도구를 사용하여 단계 실행"""
    from open_webui.utils.tools import get_tools, execute_tool

    tools = get_tools(self.request, [tool_id], self.user, {})
    # 도구 실행 로직...
```

### 이미지 생성 커스터마이징

`backend/open_webui/routers/images.py`의 `generate_prompt_with_llm` 함수를 수정하여 프롬프트 생성 로직을 커스터마이징할 수 있습니다.

## 🎓 예제

### 예제 1: 간단한 2D 플랫포머

```typescript
const agent = await quickFullDevelopment(token, {
	game_concept: '마리오 스타일의 2D 플랫포머 게임. 주인공이 점프하며 적을 피하고 코인을 수집합니다.',
	genre: '플랫포머',
	target_platform: 'PC',
	art_style: '픽셀아트'
});
```

**생성되는 결과물:**
- 게임 기획서 (게임플레이, 레벨 디자인 등)
- 캐릭터 스프라이트 이미지
- 배경 및 타일셋 이미지
- 게임 로직 코드 (Python/JavaScript)

### 예제 2: 턴제 RPG

```typescript
const agent = await quickFullDevelopment(token, {
	game_concept: '판타지 세계관의 턴제 RPG. 파티 시스템, 스킬 트리, 퀘스트 시스템 포함',
	genre: 'RPG',
	target_platform: '모바일',
	art_style: '애니메이션 스타일'
});
```

## ⚠️ 주의사항

1. **LLM 모델**: Ollama에 적절한 모델이 설치되어 있어야 합니다 (추천: llama3.2, qwen2.5)
2. **Stable Diffusion**: 이미지 생성 기능을 사용하려면 AUTOMATIC1111 또는 ComfyUI가 실행 중이어야 합니다
3. **메모리**: 에이전트 실행 시 상당한 메모리가 필요할 수 있습니다
4. **타임아웃**: 대규모 프로젝트의 경우 실행 시간이 길어질 수 있습니다

## 🐛 문제 해결

### 에이전트가 시작되지 않음

1. 데이터베이스 테이블이 생성되었는지 확인
2. Ollama 서버가 실행 중인지 확인
3. 로그 확인: `backend/logs/`

### 이미지 생성 실패

1. Stable Diffusion 서버 상태 확인
2. `AUTOMATIC1111_PROMPT_GENERATION_MODEL` 설정 확인
3. 모델이 로드되어 있는지 확인

### 플랜 생성 실패

1. LLM 모델이 JSON 형식을 지원하는지 확인
2. 프롬프트가 너무 길지 않은지 확인
3. 컨텍스트 길이 제한 확인

## 📝 향후 계획

- [ ] 프론트엔드 UI 컴포넌트 추가
- [ ] 실시간 진행 상황 WebSocket 알림
- [ ] 에이전트 템플릿 시스템
- [ ] 다중 에이전트 협업
- [ ] 게임 엔진 통합 (Unity, Godot 등)
- [ ] 코드 실행 및 테스트 자동화

## 🤝 기여하기

이 프로젝트는 오픈소스입니다. 기여를 환영합니다!

## 📄 라이선스

Open WebUI의 라이선스를 따릅니다.

---

**개발자:** AI Agent Team
**버전:** 1.0.0
**최종 업데이트:** 2026-01-07
