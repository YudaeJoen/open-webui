import logging
import asyncio
import os
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.models.agents import (
    Agents,
    AgentModel,
    AgentCreateForm,
    AgentUpdateForm,
    AgentStatus,
    AgentTaskType,
    AgentPlan,
    AgentPlanStep,
    AgentExecutionResult,
)
from open_webui.models.config import Config
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.constants import ERROR_MESSAGES
# AgentExecutor import will be done inside functions to avoid circular imports

log = logging.getLogger(__name__)

router = APIRouter()

############################
# Agent CRUD Operations
############################


@router.get("/", response_model=List[AgentModel])
async def get_agents(
    skip: int = 0,
    limit: int = 50,
    user=Depends(get_verified_user),
):
    """사용자의 모든 에이전트 조회"""
    return await Agents.get_agents_by_user_id(user.id, skip=skip, limit=limit)


@router.get("/{agent_id}", response_model=AgentModel)
async def get_agent_by_id(
    agent_id: str,
    user=Depends(get_verified_user),
):
    """ID로 에이전트 조회"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # 권한 확인
    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    return agent


@router.post("/", response_model=AgentModel)
async def create_agent(
    request: Request,
    form_data: AgentCreateForm,
    user=Depends(get_verified_user),
):
    """새 에이전트 생성"""
    try:
        agent = await Agents.insert_new_agent(user_id=user.id, form_data=form_data)

        # auto_execute가 True인 경우에만 백그라운드에서 에이전트 실행
        if form_data.auto_execute:
            async def run_agent_safely():
                try:
                    await execute_agent_workflow(request, agent.id, user)
                except Exception as e:
                    log.exception(f"Agent {agent.id} execution failed in background: {e}")

            asyncio.create_task(run_agent_safely())
        else:
            log.info(f"Agent {agent.id} created but auto_execute is False, not starting workflow")

        return agent
    except Exception as e:
        log.exception(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


@router.post("/{agent_id}/update", response_model=AgentModel)
async def update_agent(
    agent_id: str,
    form_data: AgentUpdateForm,
    user=Depends(get_verified_user),
):
    """에이전트 업데이트"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # 권한 확인
    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    updated_agent = await Agents.update_agent_by_id(agent_id, form_data)
    return updated_agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    user=Depends(get_verified_user),
):
    """에이전트 삭제"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # 권한 확인
    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = await Agents.delete_agent_by_id(agent_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT("Failed to delete agent"),
        )

    return {"success": True}


############################
# Agent Control Operations
############################


@router.post("/{agent_id}/pause")
async def pause_agent(
    agent_id: str,
    user=Depends(get_verified_user),
):
    """에이전트 일시정지"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    updated_agent = await Agents.update_agent_status(agent_id, AgentStatus.PAUSED)
    return updated_agent


@router.post("/{agent_id}/resume")
async def resume_agent(
    request: Request,
    agent_id: str,
    user=Depends(get_verified_user),
):
    """에이전트 재개"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if agent.status != AgentStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not paused",
        )

    # 백그라운드에서 에이전트 재개
    async def run_agent_safely():
        try:
            await execute_agent_workflow(request, agent.id, user, resume=True)
        except Exception as e:
            log.exception(f"Agent {agent_id} resume failed in background: {e}")

    asyncio.create_task(run_agent_safely())

    return await Agents.update_agent_status(agent_id, AgentStatus.EXECUTING)


@router.post("/{agent_id}/retry")
async def retry_agent(
    request: Request,
    agent_id: str,
    user=Depends(get_verified_user),
):
    """실패한 에이전트 재시도"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if agent.status != AgentStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent has not failed",
        )

    # 백그라운드에서 에이전트 재시도
    async def run_agent_safely():
        try:
            await execute_agent_workflow(request, agent.id, user, retry=True)
        except Exception as e:
            log.exception(f"Agent {agent_id} retry failed in background: {e}")

    asyncio.create_task(run_agent_safely())

    return await Agents.update_agent_status(agent_id, AgentStatus.PLANNING)


@router.post("/{agent_id}/start")
async def start_agent(
    request: Request,
    agent_id: str,
    user=Depends(get_verified_user),
):
    """에이전트 시작"""
    agent = await Agents.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if agent.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if agent.status != AgentStatus.IDLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not idle",
        )

    # 백그라운드에서 에이전트 실행
    async def run_agent_safely():
        try:
            await execute_agent_workflow(request, agent.id, user)
        except Exception as e:
            log.exception(f"Agent {agent_id} execution failed in background: {e}")

    asyncio.create_task(run_agent_safely())

    return await Agents.update_agent_status(agent_id, AgentStatus.PLANNING)


############################
# Agent Query Operations
############################


@router.get("/chat/{chat_id}", response_model=List[AgentModel])
async def get_agents_by_chat(
    chat_id: str,
    user=Depends(get_verified_user),
):
    """채팅 ID로 에이전트 조회"""
    agents = await Agents.get_agents_by_chat_id(chat_id)

    # 권한 확인
    for agent in agents:
        if agent.user_id != user.id and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ERROR_MESSAGES.UNAUTHORIZED,
            )

    return agents


############################
# Agent Execution Workflow
############################


async def execute_agent_workflow(
    request: Request,
    agent_id: str,
    user,
    resume: bool = False,
    retry: bool = False,
):
    """
    에이전트 실행 워크플로우

    1. Planning: 사용자 요청 분석 및 실행 계획 수립
    2. Execution: 계획에 따라 각 단계 실행
    3. Review: 각 단계별 검토 및 피드백
    4. Completion: 최종 결과물 생성
    """
    try:
        # Import here to avoid circular dependency
        from open_webui.utils.agent_executor import AgentExecutor

        executor = await AgentExecutor.create(request, agent_id, user)

        if retry:
            # 재시도 - 실패한 단계부터 재시작
            await executor.retry_from_failed_step()
        elif resume:
            # 재개 - 일시정지된 단계부터 재시작
            await executor.resume_from_paused_step()
        else:
            # 새로운 실행
            # Step 1: Planning
            await executor.create_plan()

            # Step 2: Execute plan
            await executor.execute_plan()

            # Step 3: Final review
            await executor.final_review()

        # Mark as completed
        await Agents.update_agent_status(agent_id, AgentStatus.COMPLETED)

    except Exception as e:
        log.exception(f"Error executing agent workflow: {e}")
        await Agents.update_agent_status(agent_id, AgentStatus.FAILED)

        # Add error to execution history
        error_result = AgentExecutionResult(
            step_id="error",
            status="failed",
            output={},
            error=str(e),
            timestamp=int(time.time()),
        )
        await Agents.add_execution_history(agent_id, error_result)


############################
# Quick Actions
############################


class QuickGameDesignForm(BaseModel):
    """빠른 게임 기획서 생성"""
    game_concept: str  # 게임 컨셉
    genre: Optional[str] = None  # 장르
    target_platform: Optional[str] = None  # 타겟 플랫폼
    chat_id: Optional[str] = None


@router.post("/quick/game-design", response_model=AgentModel)
async def quick_game_design(
    request: Request,
    form_data: QuickGameDesignForm,
    user=Depends(get_verified_user),
):
    """빠른 게임 기획서 생성"""
    context = {
        "genre": form_data.genre,
        "target_platform": form_data.target_platform,
    }

    agent_form = AgentCreateForm(
        name=f"게임 기획: {form_data.game_concept[:30]}",
        description="자동 생성된 게임 기획서",
        task_type=AgentTaskType.GAME_DESIGN,
        user_request=form_data.game_concept,
        context=context,
        chat_id=form_data.chat_id,
    )

    return await create_agent(request, agent_form, user)


class QuickImageGenerationForm(BaseModel):
    """빠른 이미지 생성"""
    description: str  # 이미지 설명
    style: Optional[str] = None  # 스타일
    count: int = 1  # 생성할 이미지 수
    chat_id: Optional[str] = None


@router.post("/quick/image-generation", response_model=AgentModel)
async def quick_image_generation(
    request: Request,
    form_data: QuickImageGenerationForm,
    user=Depends(get_verified_user),
):
    """빠른 이미지 생성"""
    context = {
        "style": form_data.style,
        "count": form_data.count,
    }

    agent_form = AgentCreateForm(
        name=f"이미지 생성: {form_data.description[:30]}",
        description="자동 생성된 게임 이미지",
        task_type=AgentTaskType.IMAGE_GENERATION,
        user_request=form_data.description,
        context=context,
        chat_id=form_data.chat_id,
    )

    return await create_agent(request, agent_form, user)


class QuickFullDevelopmentForm(BaseModel):
    """전체 게임 개발"""
    game_concept: str  # 게임 컨셉
    genre: Optional[str] = None
    target_platform: Optional[str] = None
    art_style: Optional[str] = None  # 아트 스타일
    chat_id: Optional[str] = None


@router.post("/quick/full-development", response_model=AgentModel)
async def quick_full_development(
    request: Request,
    form_data: QuickFullDevelopmentForm,
    user=Depends(get_verified_user),
):
    """전체 게임 개발 (기획 + 이미지 + 로직)"""
    context = {
        "genre": form_data.genre,
        "target_platform": form_data.target_platform,
        "art_style": form_data.art_style,
    }

    agent_form = AgentCreateForm(
        name=f"게임 개발: {form_data.game_concept[:30]}",
        description="전체 게임 개발 (기획서 + 이미지 + 로직)",
        task_type=AgentTaskType.FULL_DEVELOPMENT,
        user_request=form_data.game_concept,
        context=context,
        chat_id=form_data.chat_id,
    )

    return await create_agent(request, agent_form, user)


############################
# Random Game Idea Generator
############################


class RandomGameIdeaResponse(BaseModel):
    game_concept: str
    genre: str
    target_platform: str


@router.post("/random-idea", response_model=RandomGameIdeaResponse)
async def generate_random_game_idea(
    request: Request,
    user=Depends(get_verified_user),
):
    """LLM을 사용해 랜덤 게임 아이디어 생성"""
    import json
    import random
    import time
    import hashlib

    # 훨씬 더 다양한 랜덤 요소 추가
    game_concepts = [
        "시간을 되감아 실수를 수정하는", "중력을 자유자재로 조작하는", "색깔을 조합해 새로운 능력을 얻는",
        "리듬에 맞춰 장애물을 피하는", "물리 법칙을 거스르는", "순간의 타이밍이 승부를 가르는",
        "빠른 반사신경으로 생존하는", "패턴을 기억하여 돌파하는", "전략적 사고가 필요한",
        "협동해서만 클리어할 수 있는", "다른 플레이어와 경쟁하는", "희귀 아이템을 수집하는",
        "캐릭터를 육성하고 성장시키는", "극한의 환경에서 생존하는", "미지의 세계를 탐험하는",
        "자원을 모아 건설하는", "가게나 농장을 경영하는", "요리를 만들어 손님을 만족시키는",
        "음악을 연주하거나 작곡하는", "그림을 그리고 창작하는", "스포츠 경기에서 승리하는",
        "빠른 속도로 레이싱하는", "복잡한 퍼즐을 해결하는", "카드 덱을 구성하여 싸우는",
        "보드게임처럼 전략을 짜는", "미로를 탈출하는", "숨은 그림을 찾는",
        "단어를 조합하는", "숫자 퍼즐을 푸는", "공간을 효율적으로 배치하는",
        "순서를 맞추는", "매칭 패턴을 찾는", "체인 콤보를 연결하는",
        "타워를 방어하는", "영토를 확장하는", "팀을 관리하는",
        "스토리를 선택하며 진행하는", "캐릭터를 커스터마이징하는", "퀘스트를 완료하는"
    ]

    settings = [
        "우주 정거장", "심해", "사막", "정글", "미래 도시", "판타지 왕국",
        "좀비 아포칼립스", "중세 시대", "사이버펑크", "스팀펑크", "고대 유적",
        "학교", "회사", "공원", "지하철", "쇼핑몰", "병원", "공항", "카페",
        "비행선", "해적선", "우주선", "잠수함", "열차", "성", "동굴", "하늘 위",
        "마법 학교", "닌자 마을", "로봇 공장", "요리 대회", "음악 축제"
    ]

    player_roles = [
        "로봇", "마법사", "요리사", "DJ", "탐험가", "건축가", "농부", "의사",
        "우주비행사", "해적", "닌자", "기사", "상인", "예술가", "과학자", "운동선수",
        "탐정", "소방관", "경찰", "교사", "학생", "배달원", "청소부", "기자"
    ]

    goals = [
        "최고 점수 달성", "시간 내 완주", "모든 적 물리치기", "아이템 수집",
        "레벨 업", "보스 격파", "퍼즐 해결", "스테이지 클리어", "순위 올리기",
        "미션 완수", "목표 도달", "기록 경신", "생존", "탈출", "구조"
    ]

    # 타임스탬프 기반 완전 랜덤 시드
    timestamp = str(time.time()).encode()
    random_hash = hashlib.md5(timestamp).hexdigest()
    seed = int(random_hash[:8], 16) % 100000

    # 매번 다른 조합 생성
    concept = random.choice(game_concepts)
    setting = random.choice(settings)
    role = random.choice(player_roles)
    goal = random.choice(goals)

    genres = ["액션", "퍼즐", "어드벤처", "시뮬레이션", "RPG", "슈팅", "플랫포머", "캐주얼", "전략", "리듬", "레이싱"]
    platforms = ["PC", "모바일", "웹"]

    suggested_genre = random.choice(genres)
    suggested_platform = random.choice(platforms)

    # 매우 구체적이고 다양한 프롬프트
    prompt = f"""당신은 게임 디자이너입니다. 아래 요소들을 바탕으로 완전히 새로운 게임을 디자인하세요.

[랜덤 시드: {seed}]
[핵심 컨셉]: {concept}
[배경/설정]: {setting}
[플레이어 역할]: {role}
[목표]: {goal}
[추천 장르]: {suggested_genre}
[추천 플랫폼]: {suggested_platform}

위 요소들을 **자유롭게 조합하거나 변형**하여, 독창적이고 재미있는 게임 컨셉을 만들어주세요.
기존 게임을 답습하지 말고, 완전히 새로운 아이디어를 제시하세요.

**무조건 아래 JSON 형식으로만 답변하세요** (다른 텍스트 절대 금지):

{{
  "game_concept": "게임 컨셉 상세 설명 (한글, 1-2문장)",
  "genre": "장르 (액션/퍼즐/어드벤처/시뮬레이션/RPG/슈팅/플랫포머/캐주얼/전략/리듬/레이싱 중 하나)",
  "target_platform": "플랫폼 (PC/모바일/웹 중 하나)"
}}

JSON만 출력:"""

    try:
        # Ollama API 직접 호출로 temperature 제어
        import aiohttp

        ollama_base_urls = await Config.get("ollama.base_urls", []) or []
        ollama_url = ollama_base_urls[0] if ollama_base_urls else "http://localhost:11434"

        # 에이전트 기본 모델 (agents.default_model 설정 > env > 기본값)
        model = (
            await Config.get("agents.default_model", None)
            or os.environ.get("AGENT_DEFAULT_MODEL")
            or os.environ.get("MODEL_DEFAULT")
            or "gpt-oss:20b"
        )

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 게임 디자이너입니다. 매 요청마다 완전히 다른 독창적인 게임을 만들어야 합니다. JSON만 출력하세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 1.2,  # 매우 높은 temperature로 최대 다양성
                "top_p": 0.95,
                "top_k": 50,
                "repeat_penalty": 1.5  # 반복 방지
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ollama_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                result = await resp.json()
                response = result.get("message", {}).get("content", "")

        # JSON 파싱
        try:
            # 마크다운 코드 블록 제거
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            idea = json.loads(response)

            # 필수 필드 검증
            if not all(key in idea for key in ["game_concept", "genre", "target_platform"]):
                raise ValueError("Missing required fields")

            return RandomGameIdeaResponse(
                game_concept=idea["game_concept"],
                genre=idea["genre"],
                target_platform=idea["target_platform"]
            )

        except (json.JSONDecodeError, ValueError) as e:
            log.error(f"Failed to parse LLM response: {response}, error: {e}")
            # 파싱 실패시 기본값 반환
            return RandomGameIdeaResponse(
                game_concept="플레이어가 다양한 장애물을 피하며 점수를 획득하는 캐주얼 게임",
                genre="액션",
                target_platform="모바일"
            )

    except Exception as e:
        log.exception(f"Random idea generation failed: {e}")
        # 에러 발생시 기본값 반환
        return RandomGameIdeaResponse(
            game_concept="간단하고 중독성 있는 원터치 게임으로 타이밍을 맞춰 목표를 달성하는 게임",
            genre="캐주얼",
            target_platform="모바일"
        )
