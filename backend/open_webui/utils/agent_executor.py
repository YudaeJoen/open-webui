"""
게임 개발 에이전트 실행 엔진

이 모듈은 게임 개발 에이전트의 핵심 로직을 담당합니다:
1. 사용자 요청 분석 및 실행 계획 수립
2. 단계별 작업 실행 (기획서 작성, 이미지 생성, 로직 개발)
3. 각 단계별 검토 및 피드백
4. 자가 수정 및 재시도 로직
"""

import logging
import json
import time
import asyncio
from typing import Optional, Dict, List, Any

import requests
from fastapi import Request

from open_webui.models.agents import (
    Agents,
    AgentModel,
    AgentStatus,
    AgentTaskType,
    AgentPlan,
    AgentPlanStep,
    AgentExecutionResult,
)
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


class AgentExecutor:
    """에이전트 실행 엔진"""

    def __init__(self, request: Request, agent_id: str, user):
        self.request = request
        self.agent_id = agent_id
        self.user = user
        self.agent = Agents.get_agent_by_id(agent_id)

        if not self.agent:
            raise ValueError(f"Agent {agent_id} not found")

    async def create_plan(self) -> AgentPlan:
        """
        사용자 요청을 분석하여 실행 계획을 수립합니다.

        작업 유형에 따라 다른 계획을 생성:
        - GAME_DESIGN: 기획서 작성 단계들
        - IMAGE_GENERATION: 이미지 생성 단계들
        - LOGIC_DEVELOPMENT: 로직 개발 단계들
        - FULL_DEVELOPMENT: 전체 개발 단계들 (기획 -> 이미지 -> 로직)
        """
        log.info(f"Creating plan for agent {self.agent_id}")
        Agents.update_agent_status(self.agent_id, AgentStatus.PLANNING)

        try:
            # LLM에게 플랜 생성 요청
            plan_prompt = self._build_planning_prompt()
            plan_response = await self._call_llm(plan_prompt, format="json")

            # 플랜 파싱
            plan_data = json.loads(plan_response)
            plan = AgentPlan(
                goal=plan_data.get("goal", self.agent.user_request),
                steps=[
                    AgentPlanStep(**step) for step in plan_data.get("steps", [])
                ],
                review_points=plan_data.get("review_points", []),
            )

            # 플랜 저장
            Agents.update_plan(self.agent_id, plan)

            log.info(f"Plan created with {len(plan.steps)} steps")
            return plan

        except Exception as e:
            log.exception(f"Error creating plan: {e}")
            raise

    def _build_planning_prompt(self) -> str:
        """계획 수립을 위한 프롬프트 생성"""
        task_type = self.agent.task_type
        user_request = self.agent.user_request
        context = self.agent.context

        base_prompt = f"""당신은 게임 개발 전문가입니다. 사용자의 요청을 분석하여 단계별 실행 계획을 수립하세요.

사용자 요청: {user_request}

추가 컨텍스트:
{json.dumps(context, indent=2, ensure_ascii=False)}

작업 유형: {task_type.value}
"""

        if task_type == AgentTaskType.GAME_DESIGN:
            base_prompt += """
게임 기획서를 작성하는 단계별 계획을 만드세요.

포함해야 할 단계:
1. 게임 컨셉 정의 (장르, 타겟, 핵심 메커니즘)
2. 게임플레이 시스템 설계
3. 레벨 디자인 및 진행 구조
4. 캐릭터/아이템 설계
5. UI/UX 설계
6. 기술적 요구사항 정의
7. 최종 검토 및 문서화
"""
        elif task_type == AgentTaskType.IMAGE_GENERATION:
            base_prompt += """
게임 이미지를 생성하는 단계별 계획을 만드세요.

포함해야 할 단계:
1. 이미지 컨셉 및 스타일 정의
2. 프롬프트 생성 및 최적화
3. Stable Diffusion으로 이미지 생성
4. 이미지 품질 검토 및 재생성 (필요시)
5. 최종 이미지 선택 및 저장
"""
        elif task_type == AgentTaskType.LOGIC_DEVELOPMENT:
            base_prompt += """
게임 로직을 개발하는 단계별 계획을 만드세요.

포함해야 할 단계:
1. 게임 로직 구조 설계
2. 핵심 시스템 구현 (플레이어, 적, 충돌 등)
3. 게임플레이 루프 구현
4. 데이터 관리 시스템
5. 로직 테스트 및 디버깅
6. 코드 문서화
"""
        elif task_type == AgentTaskType.FULL_DEVELOPMENT:
            base_prompt += """
전체 게임을 개발하는 단계별 계획을 만드세요.

포함해야 할 단계:
1. 게임 컨셉 및 기획서 작성
2. 아트 스타일 정의 및 샘플 이미지 생성
3. 캐릭터/배경 이미지 생성
4. UI 요소 이미지 생성
5. 게임 로직 구조 설계
6. 핵심 시스템 구현
7. 이미지와 로직 통합
8. 테스트 및 최적화
9. 최종 검토 및 패키징
"""

        base_prompt += """

JSON 형식으로 응답하세요:
{
    "goal": "최종 목표 설명",
    "steps": [
        {
            "step_id": "step_1",
            "name": "단계 이름",
            "description": "단계 설명",
            "dependencies": [],
            "status": "pending"
        }
    ],
    "review_points": [
        "검토 포인트 1",
        "검토 포인트 2"
    ]
}
"""
        return base_prompt

    async def execute_plan(self, start_from_step: Optional[str] = None):
        """실행 계획을 순서대로 실행합니다."""
        log.info(f"Executing plan for agent {self.agent_id}")
        Agents.update_agent_status(self.agent_id, AgentStatus.EXECUTING)

        # 최신 에이전트 정보 가져오기
        self.agent = Agents.get_agent_by_id(self.agent_id)
        plan_data = self.agent.plan

        if not plan_data or not plan_data.get("steps"):
            raise ValueError("No plan found")

        steps = [AgentPlanStep(**step) for step in plan_data["steps"]]

        # 시작 단계 찾기
        start_index = 0
        if start_from_step:
            for i, step in enumerate(steps):
                if step.step_id == start_from_step:
                    start_index = i
                    log.info(f"Starting execution from step {start_from_step} (index {i})")
                    break

        for step in steps[start_index:]:
            # 일시정지 확인
            self.agent = Agents.get_agent_by_id(self.agent_id)
            if self.agent.status == AgentStatus.PAUSED:
                log.info(f"Agent {self.agent_id} paused at step {step.step_id}")
                return

            # 단계 실행
            await self._execute_step(step)

    async def _execute_step(self, step: AgentPlanStep):
        """단계를 실행합니다."""
        log.info(f"Executing step {step.step_id}: {step.name}")

        from open_webui.models.agents import AgentUpdateForm
        Agents.update_agent_by_id(
            self.agent_id,
            AgentUpdateForm(current_step=step.step_id)
        )

        # 스텝 상태를 in_progress로 업데이트
        log.info(f"Updating step {step.step_id} status to in_progress")
        update_result = Agents.update_plan_step_status(self.agent_id, step.step_id, "in_progress")
        log.info(f"Update result for in_progress: {update_result is not None}")

        try:
            # 단계 유형에 따라 실행 (한국어/영문 키워드 지원)
            step_name_lower = step.name.lower()
            
            # 기획/설계 단계 (한국어: 기획, 설계, 정의 / 영문: design, planning, define)
            design_keywords = ["기획", "설계", "정의", "design", "planning", "define"]
            if any(keyword in step_name_lower for keyword in design_keywords):
                result = await self._execute_design_step(step)
            # 이미지 생성 단계 (한국어: 이미지, 아트 / 영문: image, art, visual, asset)
            elif any(keyword in step_name_lower for keyword in ["이미지", "아트", "image", "art", "visual", "asset"]):
                result = await self._execute_image_step(step)
            # 로직/구현 단계 (한국어: 로직, 구현, 개발 / 영문: logic, implement, develop, code)
            elif any(keyword in step_name_lower for keyword in ["로직", "구현", "개발", "logic", "implement", "develop", "code"]):
                result = await self._execute_logic_step(step)
            # 검토/테스트 단계 (한국어: 검토, 테스트 / 영문: review, test, verify)
            elif any(keyword in step_name_lower for keyword in ["검토", "테스트", "review", "test", "verify"]):
                result = await self._execute_review_step(step)
            else:
                result = await self._execute_generic_step(step)

            # 결과 저장
            execution_result = AgentExecutionResult(
                step_id=step.step_id,
                status="success",
                output=result,
                error=None,
                timestamp=int(time.time()),
            )
            Agents.add_execution_history(self.agent_id, execution_result)

            # 결과물 업데이트
            self._update_artifacts(step.step_id, result)

            # 스텝 상태를 completed로 업데이트
            log.info(f"Updating step {step.step_id} status to completed")
            update_result = Agents.update_plan_step_status(self.agent_id, step.step_id, "completed", result)
            log.info(f"Update result for completed: {update_result is not None}")

            log.info(f"Step {step.step_id} completed successfully")

        except Exception as e:
            log.exception(f"Error executing step {step.step_id}: {e}")

            # 스텝 상태를 failed로 업데이트
            log.info(f"Updating step {step.step_id} status to failed")
            update_result = Agents.update_plan_step_status(self.agent_id, step.step_id, "failed")
            log.info(f"Update result for failed: {update_result is not None}")

            execution_result = AgentExecutionResult(
                step_id=step.step_id,
                status="failed",
                output={},
                error=str(e),
                timestamp=int(time.time()),
            )
            Agents.add_execution_history(self.agent_id, execution_result)
            raise

    async def _execute_design_step(self, step: AgentPlanStep) -> Dict[str, Any]:
        """기획/설계 단계 실행"""
        prompt = f"""게임 개발 프로젝트의 다음 단계를 수행하세요:

프로젝트: {self.agent.user_request}
현재 단계: {step.name}
단계 설명: {step.description}

이전 단계 결과:
{self._get_previous_results(step.dependencies)}

상세한 기획서를 작성하세요. 다음 기준을 충족해야 합니다:
1. 구체적인 수치와 파라미터 포함 (예: 점프 높이 2.5m, 중력 -34m/s²)
2. 실제 구현 가능한 상세한 설명
3. 테스트 가능한 명확한 기준
4. 용어의 일관성 유지
5. 코드 스니펫이나 예시 포함 (기술적인 경우)

JSON 형식으로 응답:
{{
    "title": "제목",
    "content": "상세 내용 (최소 500자)",
    "key_points": ["핵심 포인트들 (최소 5개)"],
    "next_steps": ["다음 단계 제안 (최소 3개)"],
    "examples": ["실제 구현 예시 또는 코드 스니펫 (최소 2개)"],
    "risks": ["잠재적 위험 요소 (최소 3개)"],
    "testing": ["테스트 시나리오 (최소 3개)"]
}}
"""

        response = await self._call_llm(prompt, format="json")
        return json.loads(response)

    async def _execute_image_step(self, step: AgentPlanStep) -> Dict[str, Any]:
        """이미지 생성 단계 실행 - 지능형 이미지 요구사항 분석 및 개별 최적화"""

        # STEP 1: 게임 기획 분석 - 필요한 이미지 개수와 타입 결정
        log.info(f"STEP 1: Analyzing game design to determine image requirements")
        analysis_prompt = f"""게임 개발 프로젝트의 기획을 분석하여 필요한 이미지 목록을 작성하세요.

프로젝트: {self.agent.user_request}
현재 단계: {step.name}
단계 설명: {step.description}

이전 단계 결과 (게임 기획서):
{self._get_previous_results(step.dependencies)}

게임을 완성하기 위해 필요한 핵심 이미지를 분석하고 목록화하세요.
각 이미지는 실제 게임에서 사용될 구체적인 용도가 있어야 합니다.
**중요: 이미지는 최대 10개까지만 생성하세요. 가장 중요한 것들만 선택하세요.**

JSON 형식으로 응답:
{{
    "total_images_needed": 5,
    "images": [
        {{
            "id": "img_1",
            "type": "character",
            "name": "플레이어 캐릭터",
            "description": "게임의 주인공 캐릭터, 게임플레이의 핵심",
            "usage": "메인 게임 화면에서 플레이어가 조작하는 캐릭터로 사용",
            "priority": "high"
        }},
        {{
            "id": "img_2",
            "type": "background",
            "name": "게임 배경",
            "description": "게임이 진행되는 메인 배경",
            "usage": "게임 화면의 배경으로 사용",
            "priority": "high"
        }},
        {{
            "id": "img_3",
            "type": "enemy",
            "name": "적 캐릭터",
            "description": "플레이어가 상대할 적",
            "usage": "게임 내 적으로 등장",
            "priority": "medium"
        }}
    ],
    "art_direction": "전체적인 아트 스타일과 방향성",
    "consistency_requirements": "이미지들 간 일관성 유지를 위한 요구사항"
}}
"""

        analysis_response = await self._call_llm(analysis_prompt, format="json")
        image_requirements = json.loads(analysis_response)

        # 이미지 개수를 10개로 제한
        images_list = image_requirements.get("images", [])[:10]
        image_requirements["images"] = images_list
        image_requirements["total_images_needed"] = min(image_requirements.get("total_images_needed", 0), 10)

        log.info(f"Image analysis complete: {len(images_list)} images needed (limited to max 10)")

        # STEP 2: 각 이미지마다 최적화된 SD 설정 생성 및 이미지 생성
        generated_images = []

        for idx, img_spec in enumerate(images_list):
            log.info(f"STEP 2.{idx+1}: Generating optimized SD settings for {img_spec['name']}")

            # 각 이미지에 대한 최적화된 Stable Diffusion 설정 생성
            sd_settings_prompt = f"""이미지 생성을 위한 최적의 Stable Diffusion 설정을 생성하세요.

프로젝트: {self.agent.user_request}
전체 아트 방향: {image_requirements.get('art_direction', 'N/A')}
일관성 요구사항: {image_requirements.get('consistency_requirements', 'N/A')}

생성할 이미지:
- ID: {img_spec['id']}
- 타입: {img_spec['type']}
- 이름: {img_spec['name']}
- 설명: {img_spec['description']}
- 용도: {img_spec['usage']}

이 이미지에 최적화된 Stable Diffusion 설정을 생성하세요.
프롬프트는 매우 구체적이고 상세해야 하며, 이미지 타입에 맞는 LoRA 모델과 설정을 선택하세요.

JSON 형식으로 응답:
{{
    "prompt": "매우 상세한 영문 프롬프트 (200+ words, 구체적인 시각적 요소 포함)",
    "negative_prompt": "제외할 요소들 (영문, 구체적으로)",
    "steps": 50,
    "cfg_scale": 7.5,
    "sampler_name": "DPM++ 2M Karras",
    "width": 512,
    "height": 512,
    "lora_models": [
        {{
            "name": "pixel-art-xl",
            "weight": 0.8
        }}
    ],
    "style_keywords": ["pixel art", "retro gaming", "16-bit"],
    "technical_notes": "이 설정을 선택한 이유와 기대되는 결과"
}}
"""

            sd_settings_response = await self._call_llm(sd_settings_prompt, format="json")
            sd_settings = json.loads(sd_settings_response)

            log.info(f"SD settings generated for {img_spec['name']}: {sd_settings.get('technical_notes', 'N/A')[:100]}")

            # STEP 3: 생성된 설정으로 이미지 생성
            log.info(f"STEP 3.{idx+1}: Generating image with optimized settings")
            image_urls = await self._generate_images_with_settings(sd_settings)

            # STEP 4: 생성 결과 검증
            if image_urls:
                log.info(f"✓ Image {idx+1}/{image_requirements['total_images_needed']} generated successfully: {img_spec['name']}")
                generated_images.append({
                    "id": img_spec['id'],
                    "name": img_spec['name'],
                    "type": img_spec['type'],
                    "description": img_spec['description'],
                    "usage": img_spec['usage'],
                    "url": image_urls[0],  # 첫 번째 이미지 사용
                    "sd_settings": sd_settings,
                    "status": "success"
                })
            else:
                log.warning(f"✗ Failed to generate image: {img_spec['name']}")
                generated_images.append({
                    "id": img_spec['id'],
                    "name": img_spec['name'],
                    "type": img_spec['type'],
                    "description": img_spec['description'],
                    "usage": img_spec['usage'],
                    "url": None,
                    "sd_settings": sd_settings,
                    "status": "failed",
                    "error": "Image generation failed"
                })

        # 최종 결과 반환
        return {
            "title": f"{step.name} - 지능형 이미지 생성",
            "analysis": {
                "total_images_needed": image_requirements['total_images_needed'],
                "art_direction": image_requirements.get('art_direction'),
                "consistency_requirements": image_requirements.get('consistency_requirements')
            },
            "images": generated_images,
            "summary": {
                "requested": image_requirements['total_images_needed'],
                "generated": len([img for img in generated_images if img['status'] == 'success']),
                "failed": len([img for img in generated_images if img['status'] == 'failed'])
            },
            "status": "success" if any(img['status'] == 'success' for img in generated_images) else "all_failed"
        }

    async def _execute_logic_step(self, step: AgentPlanStep) -> Dict[str, Any]:
        """로직 개발 단계 실행"""
        # 이전 결과에서 이미지 정보 추출
        previous_results = self._get_previous_results(step.dependencies)

        prompt = f"""게임 로직을 개발하세요:

프로젝트: {self.agent.user_request}
현재 단계: {step.name}
단계 설명: {step.description}

이전 단계 결과 (기획서 및 생성된 이미지 포함):
{previous_results}

게임 로직 코드를 작성하세요. 이미지가 생성되었다면 해당 이미지를 참조하는 코드를 포함하세요.
JSON 형식으로 응답:
{{
    "language": "프로그래밍 언어 (예: Python, JavaScript, C#, etc.)",
    "framework": "프레임워크 (예: Pygame, Phaser, Unity, etc.)",
    "code": "전체 게임 코드 (주석 포함, 이미지 로딩 코드 포함)",
    "explanation": "코드 상세 설명 (각 주요 함수와 클래스 설명)",
    "dependencies": ["필요한 라이브러리들"],
    "file_structure": {{
        "main.py": "메인 게임 로직",
        "assets.py": "에셋 로딩 및 관리",
        "config.py": "게임 설정"
    }},
    "usage": "실행 방법 및 사용 가이드",
    "image_references": ["생성된 이미지들의 사용 위치 설명"],
    "next_steps": ["추가로 필요한 작업들"]
}}
"""

        response = await self._call_llm(prompt, format="json")
        code_result = json.loads(response)

        # 코드 검증 및 개선 제안
        validation_prompt = f"""다음 게임 코드를 검토하고 개선점을 제안하세요:

코드:
{json.dumps(code_result, indent=2, ensure_ascii=False)}

JSON 형식으로 응답:
{{
    "code_quality": "코드 품질 평가 (1-10)",
    "strengths": ["강점들"],
    "issues": ["발견된 문제점들"],
    "improvements": ["개선 제안들"],
    "security_concerns": ["보안 관련 우려사항"],
    "performance_tips": ["성능 최적화 팁"]
}}
"""

        validation_response = await self._call_llm(validation_prompt, format="json")
        validation = json.loads(validation_response)

        return {
            "title": f"{step.name} - 게임 로직 구현",
            **code_result,
            "validation": validation
        }

    async def _execute_review_step(self, step: AgentPlanStep) -> Dict[str, Any]:
        """검토 단계 실행"""
        # 지금까지의 모든 결과 가져오기
        all_results = self._get_all_results()

        prompt = f"""프로젝트 검토를 수행하세요:

프로젝트: {self.agent.user_request}
검토 단계: {step.name}

지금까지의 결과:
{json.dumps(all_results, indent=2, ensure_ascii=False)}

다음 항목을 검토하고 피드백을 제공하세요:
1. 전체적인 일관성
2. 품질 수준
3. 개선이 필요한 부분
4. 추가로 필요한 작업

JSON 형식으로 응답:
{{
    "overall_assessment": "전체 평가",
    "quality_score": 85,
    "strengths": ["강점들"],
    "improvements_needed": ["개선 필요 사항들"],
    "recommendations": ["추천 사항들"]
}}
"""

        response = await self._call_llm(prompt, format="json")
        result = json.loads(response)

        return {
            "title": f"{step.name} - 검토",
            **result
        }

    async def _execute_generic_step(self, step: AgentPlanStep) -> Dict[str, Any]:
        """일반 단계 실행"""
        prompt = f"""다음 작업을 수행하세요:

프로젝트: {self.agent.user_request}
현재 단계: {step.name}
단계 설명: {step.description}

이전 단계 결과:
{self._get_previous_results(step.dependencies)}

작업을 수행하고 JSON 형식으로 결과를 반환하세요.
"""

        response = await self._call_llm(prompt, format="json")
        result = json.loads(response)

        return {
            "title": step.name,
            **result
        }

    async def final_review(self):
        """최종 검토 및 결과물 정리"""
        log.info(f"Performing final review for agent {self.agent_id}")
        Agents.update_agent_status(self.agent_id, AgentStatus.REVIEWING)

        # 모든 결과물 가져오기
        self.agent = Agents.get_agent_by_id(self.agent_id)
        artifacts = self.agent.artifacts

        # LLM에게 최종 검토 요청
        review_prompt = f"""게임 개발 프로젝트의 최종 검토를 수행하세요:

프로젝트: {self.agent.user_request}
작업 유형: {self.agent.task_type.value}

생성된 결과물:
{json.dumps(artifacts, indent=2, ensure_ascii=False)}

다음 기준으로 철저히 검토하세요:
1. 구체성: 수치, 파라미터, 예시가 충분히 포함되었는가?
2. 구현 가능성: 기술적으로 실현 가능한가?
3. 일관성: 용어와 개념이 전체적으로 일관되는가?
4. 완성도: 프로토타입 구현을 바로 시작할 수 있는 수준인가?
5. 품질: 각 단계별 결과물이 전문적인 수준인가?

최종 검토 보고서를 작성하세요. JSON 형식:
{{
    "summary": "프로젝트 요약 (최소 200자)",
    "deliverables": ["완성된 결과물 목록 (각 단계별)"],
    "quality_assessment": "품질 평가 (점수 포함: X/100, 구체적인 이유)",
    "strengths": ["강점 (최소 3개)"],
    "weaknesses": ["약점 (최소 3개)"],
    "recommendations": ["향후 개선 사항 (최소 5개, 구체적이고 실행 가능한)"],
    "next_actions": ["다음 단계 (최소 3개)"],
    "completion_status": "완료 상태 (예: 완료, 추가 작업 필요, 재작성 권장)"
}}
"""

        review_response = await self._call_llm(review_prompt, format="json")
        review_data = json.loads(review_response)

        # 최종 검토 결과를 artifacts에 추가 (title 포함)
        artifacts["final_review"] = {
            "title": "최종 검토 및 프로젝트 완성도 평가",
            **review_data
        }

        Agents.update_artifacts(self.agent_id, artifacts)

        log.info(f"Final review completed for agent {self.agent_id}")

    async def retry_from_failed_step(self):
        """실패한 단계부터 재시도"""
        # 실행 이력에서 실패한 단계 찾기
        self.agent = Agents.get_agent_by_id(self.agent_id)
        failed_step_id = None

        for record in reversed(self.agent.execution_history):
            if record.get("status") == "failed":
                failed_step_id = record.get("step_id")
                break

        if not failed_step_id:
            log.warning(f"No failed step found for agent {self.agent_id}")
            return

        # 해당 단계부터 재실행
        log.info(f"Retrying from failed step {failed_step_id}")
        await self.execute_plan(start_from_step=failed_step_id)

    async def resume_from_paused_step(self):
        """일시정지된 단계부터 재개"""
        self.agent = Agents.get_agent_by_id(self.agent_id)
        current_step = self.agent.current_step

        if not current_step:
            log.warning(f"No current step found for agent {self.agent_id}")
            return

        log.info(f"Resuming from step {current_step}")
        await self.execute_plan()

    # Helper methods

    async def _call_llm(self, prompt: str, format: str = "text") -> str:
        """LLM 호출"""
        try:
            ollama_base_urls = self.request.app.state.config.OLLAMA_BASE_URLS
            ollama_url = ollama_base_urls[0] if ollama_base_urls else "http://localhost:11434"

            # 기본 모델 가져오기 (설정에서)
            model = None
            try:
                model = getattr(self.request.app.state.config, 'MODEL_DEFAULT', None)
            except (AttributeError, KeyError):
                pass
            
            if not model:
                try:
                    # DEFAULT_MODELS에서 첫 번째 모델 사용
                    default_models = getattr(self.request.app.state.config, 'DEFAULT_MODELS', None)
                    if default_models and isinstance(default_models, list) and len(default_models) > 0:
                        model = default_models[0]
                except (AttributeError, KeyError):
                    pass
                
                if not model:
                    # 환경 변수에서 가져오기
                    import os
                    model = os.environ.get('MODEL_DEFAULT', None)
                    
                    if not model:
                        # 최후의 기본값
                        model = "gpt-oss:20b"

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }

            if format == "json":
                payload["format"] = "json"

            response = await asyncio.to_thread(
                requests.post,
                url=f"{ollama_url}/api/chat",
                json=payload,
                timeout=120,
            )

            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.Timeout as e:
            log.exception(f"LLM call timeout: {e}")
            Agents.update_agent_status(self.agent_id, AgentStatus.FAILED)
            raise RuntimeError(f"LLM 호출 시간 초과: {str(e)}")
        except requests.exceptions.RequestException as e:
            log.exception(f"LLM call failed: {e}")
            Agents.update_agent_status(self.agent_id, AgentStatus.FAILED)
            raise RuntimeError(f"LLM 호출 실패: {str(e)}")
        except Exception as e:
            log.exception(f"Error calling LLM: {e}")
            Agents.update_agent_status(self.agent_id, AgentStatus.FAILED)
            raise

    async def _generate_images(self, prompt: str, negative_prompt: str = "low quality, blurry, distorted", count: int = 1) -> List[str]:
        """Stable Diffusion으로 이미지 생성 (기본 설정)"""
        try:
            log.info(f"Generating {count} image(s) with prompt: {prompt[:100]}...")

            # 이미지 생성 API 호출
            images = await self._call_image_generation_api(prompt, negative_prompt, count)

            if images:
                log.info(f"Successfully generated {len(images)} image(s)")
            else:
                log.warning("No images were generated")

            return images

        except Exception as e:
            log.exception(f"Error generating images: {e}")
            # 오류 발생시 빈 리스트 반환 (치명적 오류가 아니므로 계속 진행)
            return []

    async def _generate_images_with_settings(self, sd_settings: Dict[str, Any]) -> List[str]:
        """Stable Diffusion으로 이미지 생성 (최적화된 설정 사용)"""
        try:
            prompt = sd_settings.get("prompt", "")
            log.info(f"Generating image with optimized settings: {prompt[:100]}...")
            log.info(f"Settings: steps={sd_settings.get('steps')}, cfg={sd_settings.get('cfg_scale')}, sampler={sd_settings.get('sampler_name')}")
            log.info(f"LoRA models: {sd_settings.get('lora_models', [])}")

            # 이미지 생성 API 호출 (최적화된 설정 사용)
            images = await self._call_image_generation_api_with_settings(sd_settings)

            if images:
                log.info(f"Successfully generated image with optimized settings")
            else:
                log.warning("No images were generated with optimized settings")

            return images

        except Exception as e:
            log.exception(f"Error generating images with settings: {e}")
            # 오류 발생시 빈 리스트 반환
            return []

    async def _call_image_generation_api(
        self, prompt: str, negative_prompt: str, count: int = 1
    ) -> List[str]:
        """이미지 생성 API 호출"""
        try:
            from open_webui.routers.images import load_b64_image_data
            import mimetypes
            from fastapi import UploadFile
            import io

            # 이미지 생성이 활성화되어 있는지 확인
            if not self.request.app.state.config.ENABLE_IMAGE_GENERATION:
                log.warning("Image generation is disabled in config")
                return []

            # 직접 Stable Diffusion API 호출
            if self.request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111":
                base_url = self.request.app.state.config.AUTOMATIC1111_BASE_URL

                if not base_url:
                    log.warning("AUTOMATIC1111_BASE_URL is not configured")
                    return []

                # 이미지 크기 설정
                try:
                    width, height = map(
                        int, self.request.app.state.config.IMAGE_SIZE.split("x")
                    )
                except:
                    width, height = 512, 512  # 기본값

                data = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": self.request.app.state.config.IMAGE_STEPS or 30,
                    "batch_size": count,
                }

                log.info(f"Calling Automatic1111 API at {base_url}")
                response = await asyncio.to_thread(
                    requests.post,
                    url=f"{base_url}/sdapi/v1/txt2img",
                    json=data,
                    timeout=300,
                )

                response.raise_for_status()
                result = response.json()

                # 이미지를 파일로 저장하고 URL 반환
                image_urls = []
                for idx, base64_image in enumerate(result.get("images", [])):
                    # base64 데이터 디코딩
                    image_data, content_type = load_b64_image_data(base64_image)

                    if image_data:
                        # 파일 업로드
                        image_format = mimetypes.guess_extension(content_type) or ".png"
                        timestamp = int(time.time() * 1000)
                        file = UploadFile(
                            file=io.BytesIO(image_data),
                            filename=f"agent-{self.agent_id}-{timestamp}-{idx}{image_format}",
                            headers={
                                "content-type": content_type,
                            },
                        )

                        # upload_file 함수 사용
                        from open_webui.routers.files import upload_file
                        file_item = upload_file(
                            self.request,
                            file,
                            metadata={
                                "prompt": prompt,
                                "negative_prompt": negative_prompt,
                                "agent_id": self.agent_id,
                                "step": self.agent.current_step
                            },
                            internal=True,
                            user=self.user
                        )
                        url = self.request.app.url_path_for("get_file_content_by_id", id=file_item.id)
                        image_urls.append(url)
                        log.info(f"Image {idx+1}/{count} uploaded: {url}")

                return image_urls
            else:
                log.warning(f"Unsupported image generation engine: {self.request.app.state.config.IMAGE_GENERATION_ENGINE}")
                return []

        except requests.exceptions.Timeout as e:
            log.exception(f"Image generation API timeout: {e}")
            return []
        except requests.exceptions.RequestException as e:
            log.exception(f"Image generation API request failed: {e}")
            return []
        except Exception as e:
            log.exception(f"Error calling image generation API: {e}")
            return []

    async def _call_image_generation_api_with_settings(self, sd_settings: Dict[str, Any]) -> List[str]:
        """이미지 생성 API 호출 (최적화된 설정 사용 - LoRA, sampler 등 포함)"""
        try:
            from open_webui.routers.images import load_b64_image_data
            import mimetypes
            from fastapi import UploadFile
            import io

            # 이미지 생성이 활성화되어 있는지 확인
            if not self.request.app.state.config.ENABLE_IMAGE_GENERATION:
                log.warning("Image generation is disabled in config")
                return []

            # 직접 Stable Diffusion API 호출
            if self.request.app.state.config.IMAGE_GENERATION_ENGINE == "automatic1111":
                base_url = self.request.app.state.config.AUTOMATIC1111_BASE_URL

                if not base_url:
                    log.warning("AUTOMATIC1111_BASE_URL is not configured")
                    return []

                # SD 설정에서 값 추출
                prompt = sd_settings.get("prompt", "")
                negative_prompt = sd_settings.get("negative_prompt", "low quality, blurry, distorted")
                steps = sd_settings.get("steps", 50)
                cfg_scale = sd_settings.get("cfg_scale", 7.5)
                sampler_name = sd_settings.get("sampler_name", "DPM++ 2M Karras")
                width = sd_settings.get("width", 512)
                height = sd_settings.get("height", 512)
                lora_models = sd_settings.get("lora_models", [])

                # LoRA 프롬프트 추가 (AUTOMATIC1111 형식: <lora:model_name:weight>)
                lora_prompt = ""
                for lora in lora_models:
                    lora_name = lora.get("name", "")
                    lora_weight = lora.get("weight", 1.0)
                    if lora_name:
                        lora_prompt += f" <lora:{lora_name}:{lora_weight}>"

                # 최종 프롬프트에 LoRA 추가
                final_prompt = prompt + lora_prompt

                data = {
                    "prompt": final_prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler_name": sampler_name,
                    "batch_size": 1,  # 한 번에 1개씩 생성
                }

                log.info(f"Calling Automatic1111 API with optimized settings")
                log.info(f"Prompt: {final_prompt[:200]}...")
                log.info(f"Steps: {steps}, CFG: {cfg_scale}, Sampler: {sampler_name}")
                log.info(f"Size: {width}x{height}")

                response = await asyncio.to_thread(
                    requests.post,
                    url=f"{base_url}/sdapi/v1/txt2img",
                    json=data,
                    timeout=300,
                )

                response.raise_for_status()
                result = response.json()

                # 이미지를 파일로 저장하고 URL 반환
                image_urls = []
                for idx, base64_image in enumerate(result.get("images", [])):
                    # base64 데이터 디코딩
                    image_data, content_type = load_b64_image_data(base64_image)

                    if image_data:
                        # 파일 업로드
                        image_format = mimetypes.guess_extension(content_type) or ".png"
                        timestamp = int(time.time() * 1000)
                        file = UploadFile(
                            file=io.BytesIO(image_data),
                            filename=f"agent-{self.agent_id}-{timestamp}-{idx}{image_format}",
                            headers={
                                "content-type": content_type,
                            },
                        )

                        # upload_file 함수 사용
                        from open_webui.routers.files import upload_file
                        file_item = upload_file(
                            self.request,
                            file,
                            metadata={
                                "prompt": final_prompt,
                                "negative_prompt": negative_prompt,
                                "agent_id": self.agent_id,
                                "step": self.agent.current_step,
                                "sd_settings": sd_settings  # 전체 SD 설정 저장
                            },
                            internal=True,
                            user=self.user
                        )
                        url = self.request.app.url_path_for("get_file_content_by_id", id=file_item.id)
                        image_urls.append(url)
                        log.info(f"Image uploaded with optimized settings: {url}")

                return image_urls
            else:
                log.warning(f"Unsupported image generation engine: {self.request.app.state.config.IMAGE_GENERATION_ENGINE}")
                return []

        except requests.exceptions.Timeout as e:
            log.exception(f"Image generation API timeout: {e}")
            return []
        except requests.exceptions.RequestException as e:
            log.exception(f"Image generation API request failed: {e}")
            return []
        except Exception as e:
            log.exception(f"Error calling image generation API with settings: {e}")
            return []

    def _get_previous_results(self, dependencies: List[str]) -> str:
        """의존하는 단계들의 결과 가져오기"""
        results = []
        for dep_id in dependencies:
            for record in self.agent.execution_history:
                if record.get("step_id") == dep_id:
                    results.append(
                        {
                            "step_id": dep_id,
                            "output": record.get("output", {}),
                        }
                    )
                    break

        return json.dumps(results, indent=2, ensure_ascii=False)

    def _get_all_results(self) -> Dict[str, Any]:
        """모든 실행 결과 가져오기"""
        results = {}
        for record in self.agent.execution_history:
            step_id = record.get("step_id")
            if step_id:
                results[step_id] = record.get("output", {})

        return results

    def _update_artifacts(self, step_id: str, result: Dict[str, Any]):
        """결과물 업데이트"""
        self.agent = Agents.get_agent_by_id(self.agent_id)
        artifacts = self.agent.artifacts.copy()

        artifacts[step_id] = result

        Agents.update_artifacts(self.agent_id, artifacts)
