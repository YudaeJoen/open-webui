# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Open WebUI(Python/FastAPI 백엔드 + Svelte 5/SvelteKit 프론트엔드)의 **커스텀 포크 "Myme AI"** 입니다.

- 원격: `origin` = https://github.com/YudaeJoen/open-webui (포크), `upstream` = 공식 저장소
- **`myme-ai`**: 작업 브랜치. 업스트림 v0.11.3(`2a960a59f`) 위에 포크 변경을 얹은 것. 로컬 기본 브랜치
- **`legacy-0.6.15`**: 업그레이드 전(v0.6.15 기반) 전체 스냅샷. 참고용, 새 작업 금지
- `main`: 업스트림 그대로

포크가 업스트림에 추가한 것:
- **게임 개발 자율 에이전트** (기획서 → Stable Diffusion 이미지 → 게임 코드). 아래 아키텍처 참고
- **브랜딩**: `Myme AI` (`env.py`의 `WEBUI_NAME`, `src/lib/constants.ts`의 `APP_NAME`, 파비콘)
- **기본 포트 3000** (`start_windows.bat`)
- `config.py`의 `_restamp_legacy_agent_revision()`: v0.6.15 시절 DB의 alembic 버전 꼬임 자동 보정 (아래 마이그레이션 참고)
- `AGENT_DEFAULT_MODEL` 설정 (`agents.default_model`, 기본 `gpt-oss:20b`)

업스트림 라이선스는 30일 기준 사용자 50명 미만 배포에서만 브랜딩 변경을 허용합니다. 코드 곳곳의 `LICENSE covers this Open WebUI ...` 주석이 그 지점입니다.

## 개발 명령어

### 프론트엔드 (npm)

```bash
npm run dev              # pyodide 다운로드 후 vite dev (포트 5173, 백엔드는 localhost:3000 기대)
npm run build            # build/ 디렉토리에 정적 빌드 (백엔드가 FRONTEND_BUILD_DIR로 서빙)
npm run check            # svelte-check 타입 체크
npm run lint             # eslint + svelte-check + pylint
npm run format           # Prettier
npm run format:backend   # Black
npm run test:frontend    # vitest
npx vitest run src/lib/components/SomeComponent.test.ts   # 단일 테스트
npm run i18n:parse       # 번역 키 추출
```

### 백엔드 (Python 3.12, Windows 기준)

업스트림 v0.11.x는 **Python >= 3.11, < 3.13**을 요구합니다. 가상환경은 저장소 루트의 `.venv312` (Python 3.12). 구버전 `.venv`(3.10)는 `legacy-0.6.15` 전용입니다.

```bash
# backend 디렉토리에서 (포트 3000)
../.venv312/Scripts/python.exe -m uvicorn open_webui.main:app --host 0.0.0.0 --port 3000 --forwarded-allow-ips '*' --reload
# 또는 .venv312 활성화 후 backend/start_windows.bat

# 의존성 재설치
.venv312/Scripts/python.exe -m pip install -r backend/requirements.txt

# 단일 pytest
pytest backend/open_webui/test/apps/webui/routers/test_auths.py -v

# Alembic (backend 디렉토리에서). 서버 기동 시 config.py의 run_migrations()가 자동 실행함
alembic -c open_webui/alembic.ini upgrade head
```

Node는 `package.json`의 engines가 `<=22`라 Node 24에서는 `npm install --engine-strict=false`가 필요합니다.

### 게임 에이전트 통합 테스트

루트의 `test_*.py`, `check_*.py`, `monitor_*.py`, `list_agents.py`, `export_agent_html.py`는 **실행 중인 서버(localhost:3000)에 requests로 직접 호출하는 임시 스크립트**입니다. pytest 테스트가 아니며 API 키가 하드코딩되어 있으므로 실행 전 `API_KEY`를 확인하세요. Ollama(`gpt-oss:20b`)와 A1111(7860)이 떠 있어야 합니다.

```bash
python test_full_pipeline.py     # 기획→이미지→코드 전체 파이프라인
python check_agent_db.py         # DB의 agent 테이블 직접 조회
python export_agent_html.py      # 에이전트 결과를 game_result_<id>.html로 내보내기
```

## 아키텍처

### 디렉토리 구조 (업스트림)

- `src/lib/apis/` — 도메인별 API 클라이언트, `src/lib/components/`, `src/lib/stores/`, `src/routes/`
- `backend/open_webui/routers/` — API 라우터, `models/` — SQLAlchemy 모델 + Pydantic 폼, `utils/`, `retrieval/` (RAG), `storage/`
- `backend/open_webui/config.py` — 설정은 환경변수로 기본값을 정의하고 `DEFAULT_CONFIG` 딕셔너리(`'ollama.base_urls': ...` 형태)에 키를 등록. 런타임에는 `await Config.get('key')` / `Config.get_many(...)`(`models/config.py`)로 읽음. **`app.state.config`는 더 이상 없음**. DB 값이 환경변수보다 우선
- DB 접근은 **async SQLAlchemy** (`internal/db.py`의 `get_async_db_context`, `AsyncSession`). 모델 클래스의 메서드는 전부 `async def`이며 `await db.execute(select(...))` 패턴. 동기 `get_db()`는 없음
- `backend/open_webui/migrations/versions/` — Alembic. head는 `d4e8b9c3a1f0` (agent 테이블, 업스트림 `d4c1a8e37b62` 뒤). 이 마이그레이션은 테이블이 이미 있으면 건너뜀

### 게임 에이전트 시스템 (포크 추가분)

요청 흐름: `workspace/games` 페이지 → `POST /api/v1/agents` (또는 `/quick/*`) → DB에 agent 행 생성 → `asyncio.create_task`로 백그라운드 실행 → 프론트가 5초마다 폴링. 실행기는 `await AgentExecutor.create(request, agent_id, user)` 팩토리로 생성합니다 (생성자에서 DB를 읽지 않음).

| 레이어 | 파일 | 역할 |
|---|---|---|
| 모델 | `backend/open_webui/models/agents.py` | `Agent` 테이블, `AgentStatus`/`AgentTaskType` enum, `AgentPlan`/`AgentPlanStep`, `Agents` CRUD |
| 라우터 | `backend/open_webui/routers/agents.py` | CRUD + `pause/resume/retry/start`, `quick/game-design`, `quick/image-generation`, `quick/full-development`, `random-idea`. `execute_agent_workflow()`가 계획→실행→최종검토를 orchestration |
| 실행기 | `backend/open_webui/utils/agent_executor.py` | `AgentExecutor`: LLM에 JSON 계획을 받아 단계별 `_execute_{design,image,logic,review,generic}_step` 실행. 상태/이력/artifacts는 매 단계 DB에 기록 |
| 프론트 | `src/lib/apis/agents/index.ts`, `src/routes/(app)/workspace/games/` | 목록 페이지 + `[id]` 상세 페이지. 워크스페이스 레이아웃에 "🎮 Game Agent" 탭 추가 |

동작상 주의점:
- LLM 호출(`_call_llm`)은 Open WebUI 모델 라우팅을 거치지 않고 **`Config.get('ollama.base_urls')[0]/api/chat`을 직접 호출**합니다. 모델은 `agents.default_model` → `ui.default_models` 첫 항목 → 환경변수 `AGENT_DEFAULT_MODEL`/`MODEL_DEFAULT` → `gpt-oss:20b` 순.
- 이미지 단계는 LLM이 이미지 요구사항을 분석해 개수를 정하고, 이미지마다 SD 설정을 별도 생성한 뒤 `_run_txt2img`로 A1111 `/sdapi/v1/txt2img` 호출. 설정은 `image_generation.*` 키에서 읽고, 관리자 화면의 `AUTOMATIC1111_PARAMS`(JSON)를 기본값으로 깐 뒤 에이전트 값이 덮어씀. 저장은 `routers/images.py`의 `get_image_data` + `upload_image` 재사용.
- 각 단계는 `dependencies`로 이전 단계 결과를 참조하며, `retry`는 실패한 단계부터, `resume`은 일시정지 단계부터 재개.
- 라우터/실행기 간 순환 import를 피하려고 `AgentExecutor`는 함수 내부에서 import 합니다.

### A1111 이미지 설정 확장 (보류)

v0.6.15 시절의 A1111 확장 UI/엔드포인트(seed, hires fix, LoRA 선택 등)는 업스트림이 `AUTOMATIC1111_PARAMS`(관리자 화면 JSON)로 흡수했기 때문에 `myme-ai`에는 이식하지 않았습니다. `src/lib/apis/images/index.ts`에 남아 있는 `getAutomatic1111*`, `generatePromptWithOllama` 등의 클라이언트 함수는 **백엔드 엔드포인트가 없어 호출하면 404**입니다. 필요하면 `legacy-0.6.15`의 `routers/images.py`를 참고해 다시 구현하세요.

### 마이그레이션 주의

v0.6.15 기반 DB는 `alembic_version`이 `d4e8b9c3a1f0`인데, 이 리비전을 업스트림 최신 head 뒤로 재연결했기 때문에 그대로 두면 업스트림 마이그레이션 41개가 건너뛰어집니다. `config.py`의 `_restamp_legacy_agent_revision()`이 `chat.timer_at` 컬럼 부재를 보고 `9f0c9cd09105`로 stamp한 뒤 정상 체인을 태웁니다. 새로 만드는 DB에는 영향이 없습니다.

## 코드 스타일

- **TypeScript/Svelte:** ESLint + Prettier, 탭 들여쓰기, 작은따옴표, 100자 너비
- **Python:** 업스트림은 ruff 기반 작은따옴표 스타일(`config.py`, `main.py` 등). 포크 파일(`models/agents.py` 등)은 Black 스타일 큰따옴표. 각 파일의 기존 스타일을 따를 것
- 포크 추가 코드의 주석/문서/로그 메시지는 한국어로 작성되어 있음 — 같은 관례 유지
- 일부 `.svelte`/`.ts` 파일이 CRLF로 저장되어 git 경고가 뜨지만 내용 변경이 아니므로 무시

## 저장소 정리 관련 주의

- `open-webui/` (루트 하위 디렉토리)는 **업스트림 저장소 복사본**입니다. 편집 대상이 아니며 검색 시 제외하세요. `open-webui_0121.zip`도 동일.
- `backend/open_webui/static/_app/`, `index.html` 등은 구버전에서 프론트 빌드 결과를 복사해 둔 잔재입니다 (`.gitignore` 처리됨). 정상 경로는 `build/`.
- `agent_*_results.*`, `game_result_*.html`, `err_log`는 에이전트 실행 산출물입니다.
- `GAME_AGENT_GUIDE.md`, `FULL_PIPELINE_GUIDE.md`, `IMAGE_GENERATION_UPGRADE.md`, `IMPLEMENTATION_SUMMARY.md`, `HTML_EXPORT_IMPROVEMENTS.md` 등에 기능 설계 배경과 API 사용 예시가 정리되어 있습니다.

## 환경 설정

`.env.example`을 `.env`로 복사. 이 포크에서 중요한 변수:

- `OLLAMA_BASE_URL` (기본 http://localhost:11434) — 에이전트가 직접 호출
- `AGENT_DEFAULT_MODEL` (구 `MODEL_DEFAULT`, 기본 `gpt-oss:20b`) — 에이전트 LLM 모델. DB 키 `agents.default_model`
- `ENABLE_IMAGE_GENERATION=true`, `IMAGE_GENERATION_ENGINE=automatic1111`, `AUTOMATIC1111_BASE_URL=http://localhost:7860`
- `AUTOMATIC1111_PARAMS` — txt2img에 그대로 합쳐지는 JSON (예: `{"cfg_scale": 7, "sampler_name": "DPM++ 2M", "seed": -1}`)
- `WEBUI_SECRET_KEY`, `AIOHTTP_CLIENT_TIMEOUT` (업스트림과 동일)

설정은 DB에 영속되므로, `.env`를 바꿔도 이미 DB에 저장된 값이 있으면 관리자 설정 화면에서 바꾸거나 `RESET_CONFIG_ON_START=true`가 필요합니다.

## 업스트림 PR 요구사항 (업스트림에 기여할 때만)

- `dev` 브랜치 대상, Changelog 항목 포함, 제목 접두사 `feat:`/`fix:`/`docs:`/`refactor:`/`test:`, `.github/pull_request_template.md` 준수

## 참고사항

- 번역 파일: `src/lib/i18n/locales/{lang-CODE}/`
- Docker는 `host.docker.internal`로 호스트 Ollama 접근
- Ollama 자체 이슈는 https://github.com/ollama/ollama
