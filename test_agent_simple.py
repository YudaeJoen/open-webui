"""
Simple test script for the autonomous agent system
"""
import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:3000/api/v1"

# Test user credentials (you may need to adjust these)
TEST_USER_ID = "test_user_001"
TEST_CHAT_ID = "test_chat_001"

def test_create_agent():
    """Test creating a simple game design agent"""
    print("=" * 60)
    print("테스트: 게임 디자인 에이전트 생성")
    print("=" * 60)

    # Create agent payload
    payload = {
        "user_id": TEST_USER_ID,
        "chat_id": TEST_CHAT_ID,
        "name": "Simple Puzzle Game Agent",
        "description": "간단한 퍼즐 게임을 만드는 에이전트",
        "task_type": "game_design",
        "user_request": "간단한 2D 퍼즐 게임을 디자인해줘. 블록을 맞추는 게임이면 좋겠어."
    }

    print(f"\n요청 데이터:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            f"{BASE_URL}/agents/",
            json=payload,
            timeout=10
        )

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            agent_data = response.json()
            print(f"\n✓ 에이전트 생성 성공!")
            print(f"Agent ID: {agent_data.get('id')}")
            print(f"Status: {agent_data.get('status')}")
            print(f"Created at: {agent_data.get('created_at')}")
            return agent_data.get('id')
        else:
            print(f"\n✗ 에이전트 생성 실패")
            print(f"응답: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print("\n✗ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return None
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        return None

def test_get_agent(agent_id):
    """Test retrieving agent details"""
    print("\n" + "=" * 60)
    print(f"테스트: 에이전트 조회 (ID: {agent_id})")
    print("=" * 60)

    try:
        response = requests.get(
            f"{BASE_URL}/agents/{agent_id}",
            timeout=10
        )

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            agent_data = response.json()
            print(f"\n✓ 에이전트 조회 성공!")
            print(f"\n에이전트 정보:")
            print(f"  이름: {agent_data.get('name')}")
            print(f"  상태: {agent_data.get('status')}")
            print(f"  작업 타입: {agent_data.get('task_type')}")
            print(f"  사용자 요청: {agent_data.get('user_request')}")

            # Check if plan exists
            plan = agent_data.get('plan', {})
            if plan:
                print(f"\n계획 정보:")
                print(json.dumps(plan, indent=2, ensure_ascii=False))

            # Check execution history
            history = agent_data.get('execution_history', [])
            if history:
                print(f"\n실행 기록: {len(history)}개 단계")

            return agent_data
        else:
            print(f"\n✗ 에이전트 조회 실패")
            print(f"응답: {response.text}")
            return None

    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        return None

def test_list_agents():
    """Test listing all agents"""
    print("\n" + "=" * 60)
    print("테스트: 모든 에이전트 목록 조회")
    print("=" * 60)

    try:
        response = requests.get(
            f"{BASE_URL}/agents/",
            timeout=10
        )

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            agents = response.json()
            print(f"\n✓ 에이전트 목록 조회 성공!")
            print(f"총 {len(agents)}개의 에이전트")

            for i, agent in enumerate(agents, 1):
                print(f"\n  {i}. {agent.get('name')}")
                print(f"     ID: {agent.get('id')}")
                print(f"     상태: {agent.get('status')}")
                print(f"     타입: {agent.get('task_type')}")

            return agents
        else:
            print(f"\n✗ 에이전트 목록 조회 실패")
            print(f"응답: {response.text}")
            return None

    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        return None

def test_quick_game_design():
    """Test quick game design endpoint"""
    print("\n" + "=" * 60)
    print("테스트: 빠른 게임 디자인 생성")
    print("=" * 60)

    payload = {
        "user_id": TEST_USER_ID,
        "chat_id": TEST_CHAT_ID,
        "request": "간단한 벽돌깨기 게임을 만들어줘. 레트로 스타일로 해줘."
    }

    print(f"\n요청 데이터:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            f"{BASE_URL}/agents/quick/game-design",
            json=payload,
            timeout=30
        )

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ 빠른 게임 디자인 생성 성공!")
            print(f"\n응답 데이터:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print(f"\n✗ 빠른 게임 디자인 생성 실패")
            print(f"응답: {response.text}")
            return None

    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        return None

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("자율 에이전트 시스템 테스트 시작")
    print("=" * 60)

    # Test 1: Create agent
    agent_id = test_create_agent()

    if agent_id:
        # Wait a bit for agent to initialize
        time.sleep(2)

        # Test 2: Get agent details
        test_get_agent(agent_id)

        # Test 3: List all agents
        test_list_agents()

    # Test 4: Quick game design (independent test)
    # test_quick_game_design()  # Uncomment to test quick endpoint

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
