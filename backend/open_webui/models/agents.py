import logging
import json
import time
import uuid
from typing import Optional, List
from enum import Enum

from open_webui.internal.db import Base, get_async_db_context

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON, Enum as SQLEnum
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

####################
# Agent DB Schema
####################

log = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """에이전트 실행 상태"""
    IDLE = "idle"  # 대기 중
    PLANNING = "planning"  # 계획 수립 중
    EXECUTING = "executing"  # 실행 중
    REVIEWING = "reviewing"  # 검토 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    PAUSED = "paused"  # 일시정지


class AgentTaskType(str, Enum):
    """에이전트 작업 유형"""
    GAME_DESIGN = "game_design"  # 게임 기획서 작성
    IMAGE_GENERATION = "image_generation"  # 이미지 생성 (Stable Diffusion)
    LOGIC_DEVELOPMENT = "logic_development"  # 게임 로직 개발
    FULL_DEVELOPMENT = "full_development"  # 전체 게임 개발 (기획 + 이미지 + 로직)


class Agent(Base):
    """에이전트 세션 테이블"""
    __tablename__ = "agent"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    chat_id = Column(String, nullable=True)  # 연결된 채팅 ID

    # 기본 정보
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(SQLEnum(AgentTaskType), nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)

    # 사용자 요청 및 컨텍스트
    user_request = Column(Text, nullable=False)  # 사용자 원본 요청
    context = Column(JSON, default={})  # 추가 컨텍스트 정보

    # 계획 및 실행 정보
    plan = Column(JSON, default={})  # 실행 계획 (단계별)
    execution_history = Column(JSON, default=[])  # 실행 이력
    current_step = Column(String, nullable=True)  # 현재 실행 중인 단계

    # 결과물
    artifacts = Column(JSON, default={})  # 생성된 결과물 (기획서, 이미지 URL, 코드 등)

    # 메타데이터
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    completed_at = Column(BigInteger, nullable=True)


class AgentModel(BaseModel):
    """에이전트 Pydantic 모델"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    chat_id: Optional[str] = None

    name: str
    description: Optional[str] = None
    task_type: AgentTaskType
    status: AgentStatus

    user_request: str
    context: dict = {}

    plan: dict = {}
    execution_history: list = []
    current_step: Optional[str] = None

    artifacts: dict = {}

    created_at: int
    updated_at: int
    completed_at: Optional[int] = None


####################
# Forms
####################


class AgentCreateForm(BaseModel):
    """에이전트 생성 요청"""
    name: str
    description: Optional[str] = None
    task_type: AgentTaskType
    user_request: str
    context: dict = {}
    chat_id: Optional[str] = None
    auto_execute: bool = True


class AgentUpdateForm(BaseModel):
    """에이전트 업데이트"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    plan: Optional[dict] = None
    execution_history: Optional[list] = None
    current_step: Optional[str] = None
    artifacts: Optional[dict] = None


class AgentPlanStep(BaseModel):
    """계획 단계"""
    step_id: str
    name: str
    description: str
    dependencies: List[str] = []  # 의존하는 단계 ID들
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[dict] = None


class AgentPlan(BaseModel):
    """에이전트 실행 계획"""
    goal: str  # 목표
    steps: List[AgentPlanStep]  # 실행 단계들
    review_points: List[str] = []  # 검토 포인트


class AgentExecutionResult(BaseModel):
    """단계 실행 결과"""
    step_id: str
    status: str  # success, failed, skipped
    output: dict = {}
    error: Optional[str] = None
    timestamp: int


####################
# Agent Table
####################


class Agents:
    """에이전트 데이터베이스 작업 (async SQLAlchemy)"""

    @staticmethod
    async def _get_agent_row(db: AsyncSession, agent_id: str) -> Optional[Agent]:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalars().first()

    @staticmethod
    async def insert_new_agent(
        user_id: str,
        form_data: AgentCreateForm,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentModel]:
        """새 에이전트 생성"""
        async with get_async_db_context(db) as db:
            try:
                timestamp = int(time.time())
                agent = Agent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    chat_id=form_data.chat_id,
                    name=form_data.name,
                    description=form_data.description,
                    task_type=form_data.task_type,
                    status=AgentStatus.IDLE,
                    user_request=form_data.user_request,
                    context=form_data.context,
                    plan={},
                    execution_history=[],
                    current_step=None,
                    artifacts={},
                    created_at=timestamp,
                    updated_at=timestamp,
                    completed_at=None,
                )
                db.add(agent)
                await db.commit()
                await db.refresh(agent)
                return AgentModel.model_validate(agent)
            except Exception as e:
                await db.rollback()
                log.exception(f"Error creating new agent for user {user_id}: {e}")
                return None

    @staticmethod
    async def get_agent_by_id(
        agent_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[AgentModel]:
        """ID로 에이전트 조회"""
        async with get_async_db_context(db) as db:
            agent = await Agents._get_agent_row(db, agent_id)
            return AgentModel.model_validate(agent) if agent else None

    @staticmethod
    async def get_agents_by_user_id(
        user_id: str, skip: int = 0, limit: int = 50, db: Optional[AsyncSession] = None
    ) -> List[AgentModel]:
        """사용자의 모든 에이전트 조회"""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(Agent)
                .where(Agent.user_id == user_id)
                .order_by(Agent.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return [AgentModel.model_validate(a) for a in result.scalars().all()]

    @staticmethod
    async def get_agents_by_chat_id(
        chat_id: str, db: Optional[AsyncSession] = None
    ) -> List[AgentModel]:
        """채팅 ID로 에이전트 조회"""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(Agent).where(Agent.chat_id == chat_id).order_by(Agent.created_at.desc())
            )
            return [AgentModel.model_validate(a) for a in result.scalars().all()]

    @staticmethod
    async def update_agent_by_id(
        agent_id: str, form_data: AgentUpdateForm, db: Optional[AsyncSession] = None
    ) -> Optional[AgentModel]:
        """에이전트 업데이트"""
        async with get_async_db_context(db) as db:
            try:
                agent = await Agents._get_agent_row(db, agent_id)
                if not agent:
                    return None

                update_data = form_data.model_dump(exclude_unset=True)
                update_data["updated_at"] = int(time.time())

                # completed 상태로 변경시 완료 시간 기록
                if form_data.status == AgentStatus.COMPLETED:
                    update_data["completed_at"] = int(time.time())

                for key, value in update_data.items():
                    setattr(agent, key, value)

                await db.commit()
                await db.refresh(agent)
                return AgentModel.model_validate(agent)
            except Exception as e:
                await db.rollback()
                log.exception(f"Error updating agent {agent_id}: {e}")
                return None

    @staticmethod
    async def update_agent_status(
        agent_id: str,
        status: AgentStatus,
        current_step: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentModel]:
        """에이전트 상태 업데이트"""
        form_data = AgentUpdateForm(status=status, current_step=current_step)
        return await Agents.update_agent_by_id(agent_id, form_data, db=db)

    @staticmethod
    async def add_execution_history(
        agent_id: str, result: AgentExecutionResult, db: Optional[AsyncSession] = None
    ) -> Optional[AgentModel]:
        """실행 이력 추가"""
        async with get_async_db_context(db) as db:
            try:
                agent = await Agents._get_agent_row(db, agent_id)
                if not agent:
                    return None

                history = list(agent.execution_history or [])
                history.append(result.model_dump())
                agent.execution_history = history
                agent.updated_at = int(time.time())

                await db.commit()
                await db.refresh(agent)
                return AgentModel.model_validate(agent)
            except Exception as e:
                await db.rollback()
                log.exception(f"Error adding execution history for agent {agent_id}: {e}")
                return None

    @staticmethod
    async def update_plan(
        agent_id: str, plan: AgentPlan, db: Optional[AsyncSession] = None
    ) -> Optional[AgentModel]:
        """실행 계획 업데이트"""
        async with get_async_db_context(db) as db:
            try:
                agent = await Agents._get_agent_row(db, agent_id)
                if not agent:
                    return None

                agent.plan = plan.model_dump()
                agent.updated_at = int(time.time())

                await db.commit()
                await db.refresh(agent)
                return AgentModel.model_validate(agent)
            except Exception as e:
                await db.rollback()
                log.exception(f"Error updating plan for agent {agent_id}: {e}")
                return None

    @staticmethod
    async def update_plan_step_status(
        agent_id: str,
        step_id: str,
        step_status: str,
        result: Optional[dict] = None,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentModel]:
        """계획 단계 상태 업데이트"""
        async with get_async_db_context(db) as db:
            try:
                agent = await Agents._get_agent_row(db, agent_id)
                if not agent:
                    return None

                plan = dict(agent.plan or {})
                steps = [dict(step) for step in plan.get("steps", [])]
                for step in steps:
                    if step.get("step_id") == step_id:
                        step["status"] = step_status
                        if result:
                            step["result"] = result
                        log.info(f"Updated step {step_id} to status {step_status} in plan")
                        break
                plan["steps"] = steps

                agent.plan = plan
                agent.updated_at = int(time.time())

                await db.commit()
                await db.refresh(agent)
                return AgentModel.model_validate(agent)
            except Exception as e:
                await db.rollback()
                log.exception(
                    f"Error updating plan step status for agent {agent_id}, step {step_id}: {e}"
                )
                return None

    @staticmethod
    async def update_artifacts(
        agent_id: str, artifacts: dict, db: Optional[AsyncSession] = None
    ) -> Optional[AgentModel]:
        """결과물 업데이트"""
        async with get_async_db_context(db) as db:
            try:
                agent = await Agents._get_agent_row(db, agent_id)
                if not agent:
                    return None

                agent.artifacts = artifacts
                agent.updated_at = int(time.time())

                await db.commit()
                await db.refresh(agent)
                return AgentModel.model_validate(agent)
            except Exception as e:
                await db.rollback()
                log.exception(f"Error updating artifacts for agent {agent_id}: {e}")
                return None

    @staticmethod
    async def delete_agent_by_id(agent_id: str, db: Optional[AsyncSession] = None) -> bool:
        """에이전트 삭제"""
        async with get_async_db_context(db) as db:
            try:
                agent = await Agents._get_agent_row(db, agent_id)
                if not agent:
                    return False
                await db.delete(agent)
                await db.commit()
                return True
            except Exception as e:
                await db.rollback()
                log.exception(f"Error deleting agent {agent_id}: {e}")
                return False

    @staticmethod
    async def delete_agents_by_user_id(user_id: str, db: Optional[AsyncSession] = None) -> bool:
        """사용자의 모든 에이전트 삭제"""
        async with get_async_db_context(db) as db:
            try:
                await db.execute(delete(Agent).where(Agent.user_id == user_id))
                await db.commit()
                return True
            except Exception as e:
                await db.rollback()
                log.exception(f"Error deleting agents for user {user_id}: {e}")
                return False
