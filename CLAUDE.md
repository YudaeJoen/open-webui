# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Open WebUI(Python/FastAPI 백엔드 + Svelte 4/SvelteKit 프론트엔드)의 **커스텀 포크**입니다. 업스트림 `main`(v0.6.15) 위에 아래 변경이 커밋되지 않은 워킹트리 상태로 얹혀 있습니다:

- **게임 개발 자율 에이전트 시스템** (기획서 → Stable Diffusion 이미지 → 게임 코드 파이프라인)
- **AUTOMATIC1111 이미지 생성 설정 확장** (seed, clip_skip, VAE, hires fix, LoRA 등)
- **브랜딩**: 앱 이름 `Myme AI` (`env.py`의 `WEBUI_NAME`, `src/lib/constants.ts`의 `APP_NAME`), 파비콘/로고 교체
- **기본 포트 3000** (업스트림 8080 아님) — `start_windows.bat`, `constants.ts`의 `WEBUI_HOSTNAME`, 루트의 테스트 스크립트 모두 3000 기준
- Python 3.10 호환 패치 (`env.py`의 `getLevelNamesMapping`, `retrieval/vector/type.py`의 `StrEnum` 폴백), DB 연결 재시도 (`internal/db.py`), Windows cp949 콘솔 대응 (`main.py`)

업스트림 변경을 머지할 때 위 파일들이 충돌 지점입니다.

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

### 백엔드 (Python, Windows 기준)

```bash
# 가상환경은 저장소 루트의 .venv (start_windows.bat이 ..\.venv\Scripts\uvicorn.exe를 직접 호출)
backend/start_windows.bat                 # 포트 3000, 마이그레이션 자동 실행
# 또는 backend 디렉토리에서:
python run_server.py                      # uvicorn, 포트 3000 고정
python start_server.py                    # 포트 점유 프로세스 kill 후 시작
# 수동:
PORT=3000 uvicorn open_webui.main:app --host 0.0.0.0 --forwarded-allow-ips '*' --reload

# 단일 pytest
pytest backend/open_webui/test/apps/webui/routers/test_auths.py -v

# Alembic 마이그레이션 (backend 디렉토리에서, PYTHONPATH=현재 디렉토리)
alembic -c open_webui/alembic.ini upgrade head
```

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
- `backend/open_webui/config.py` — `PersistentConfig`로 정의된 설정. 환경변수 → DB(`config` 테이블)에 저장되며 **DB 값이 환경변수보다 우선**. 새 설정을 추가하면 `config.py` 정의 + `main.py`에서 `app.state.config.X = X` 등록 두 곳을 모두 수정해야 함
- `backend/open_webui/migrations/versions/` — Alembic. 현재 head는 `d4e8b9c3a1f0` (agent 테이블, `9f0c9cd09105` 뒤)

### 게임 에이전트 시스템 (포크 추가분)

요청 흐름: `workspace/games` 페이지 → `POST /api/v1/agents` (또는 `/quick/*`) → DB에 agent 행 생성 → `asyncio.create_task`로 백그라운드 실행 → 프론트가 5초마다 폴링.

| 레이어 | 파일 | 역할 |
|---|---|---|
| 모델 | `backend/open_webui/models/agents.py` | `Agent` 테이블, `AgentStatus`/`AgentTaskType` enum, `AgentPlan`/`AgentPlanStep`, `Agents` CRUD |
| 라우터 | `backend/open_webui/routers/agents.py` | CRUD + `pause/resume/retry/start`, `quick/game-design`, `quick/image-generation`, `quick/full-development`, `random-idea`. `execute_agent_workflow()`가 계획→실행→최종검토를 orchestration |
| 실행기 | `backend/open_webui/utils/agent_executor.py` | `AgentExecutor`: LLM에 JSON 계획을 받아 단계별 `_execute_{design,image,logic,review,generic}_step` 실행. 상태/이력/artifacts는 매 단계 DB에 기록 |
| 프론트 | `src/lib/apis/agents/index.ts`, `src/routes/(app)/workspace/games/` | 목록 페이지 + `[id]` 상세 페이지. 워크스페이스 레이아웃에 "🎮 Game Agent" 탭 추가 |

동작상 주의점:
- LLM 호출(`_call_llm`)은 Open WebUI 모델 라우팅을 거치지 않고 **`OLLAMA_BASE_URLS[0]/api/chat`을 직접 호출**합니다. 모델은 `MODEL_DEFAULT` 설정(기본 `gpt-oss:20b`) → `DEFAULT_MODELS[0]` → 환경변수 순으로 결정.
- 이미지 단계는 LLM이 이미지 요구사항을 분석해 개수를 정하고, 이미지마다 SD 설정(prompt/negative/steps/cfg/sampler 등)을 별도 생성한 뒤 `_call_image_generation_api_with_settings`로 A1111 `/sdapi/v1/txt2img` 호출. 결과는 `routers/images.py`의 저장 경로를 재사용.
- 각 단계는 `dependencies`로 이전 단계 결과를 참조하며, `retry`는 실패한 단계부터, `resume`은 일시정지 단계부터 재개.
- 라우터/실행기 간 순환 import를 피하려고 `AgentExecutor`는 함수 내부에서 import 합니다.

### 이미지 생성 확장 (`routers/images.py`, `admin/Settings/Images.svelte`)

A1111용 추가 엔드포인트: `/automatic1111/{samplers,schedulers,loras,sd-vae,upscalers,embeddings,options}`, `/generate-prompt` (LLM이 SD 프롬프트 + 권장 설정 JSON 생성, 템플릿은 `config.py`의 `DEFAULT_IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE`), `/optimize-settings`, `/generations/advanced`. 클라이언트는 `src/lib/apis/images/index.ts`.

## 코드 스타일

- **TypeScript/Svelte:** ESLint + Prettier, 탭 들여쓰기, 작은따옴표, 100자 너비
- **Python:** Black, Pylint, 타입 힌트
- 포크 추가 코드의 주석/문서/로그 메시지는 한국어로 작성되어 있음 — 같은 관례 유지
- 일부 `.svelte`/`.ts` 파일이 CRLF로 저장되어 git 경고가 뜨지만 내용 변경이 아니므로 무시

## 저장소 정리 관련 주의

- `open-webui/` (루트 하위 디렉토리)는 **업스트림 저장소 복사본**입니다. 편집 대상이 아니며 검색 시 제외하세요. `open-webui_0121.zip`도 동일.
- `backend/open_webui/static/_app/`, `index.html` 등은 프론트 빌드 결과가 복사된 untracked 파일입니다 (정상 경로는 `build/`).
- `agent_*_results.*`, `game_result_*.html`, `err_log`는 에이전트 실행 산출물입니다.
- `GAME_AGENT_GUIDE.md`, `FULL_PIPELINE_GUIDE.md`, `IMAGE_GENERATION_UPGRADE.md`, `IMPLEMENTATION_SUMMARY.md`, `HTML_EXPORT_IMPROVEMENTS.md` 등에 기능 설계 배경과 API 사용 예시가 정리되어 있습니다.

## 환경 설정

`.env.example`을 `.env`로 복사. 이 포크에서 중요한 변수:

- `OLLAMA_BASE_URL` (기본 http://localhost:11434) — 에이전트가 직접 호출
- `MODEL_DEFAULT` (기본 `gpt-oss:20b`) — 에이전트 LLM 모델
- `ENABLE_IMAGE_GENERATION=true`, `IMAGE_GENERATION_ENGINE=automatic1111`, `AUTOMATIC1111_BASE_URL=http://localhost:7860`
- `AUTOMATIC1111_*` 확장 설정 (SEED, CLIP_SKIP, VAE, ENABLE_HR, HR_SCALE, HR_UPSCALER, DENOISING_STRENGTH, BATCH_COUNT, RESTORE_FACES, TILING, LORAS, PROMPT_GENERATION_MODEL)
- `WEBUI_SECRET_KEY`, `AIOHTTP_CLIENT_TIMEOUT` (업스트림과 동일)

설정은 DB에 영속되므로, `.env`를 바꿔도 이미 DB에 저장된 값이 있으면 관리자 설정 화면에서 바꾸거나 `RESET_CONFIG_ON_START=true`가 필요합니다.

## 업스트림 PR 요구사항 (업스트림에 기여할 때만)

- `dev` 브랜치 대상, Changelog 항목 포함, 제목 접두사 `feat:`/`fix:`/`docs:`/`refactor:`/`test:`, `.github/pull_request_template.md` 준수

## 참고사항

- 번역 파일: `src/lib/i18n/locales/{lang-CODE}/`
- Docker는 `host.docker.internal`로 호스트 Ollama 접근
- Ollama 자체 이슈는 https://github.com/ollama/ollama
