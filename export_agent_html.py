"""
에이전트 결과물을 HTML로 내보내기
"""
import os
import requests
import json
import sys
import io
from datetime import datetime
import html

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:3000/api/v1"
API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def escape_html(text):
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""
    return html.escape(str(text))

def generate_html(agent_id):
    """에이전트 결과를 HTML로 생성"""

    # 에이전트 정보 가져오기
    response = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers, timeout=10)
    agent = response.json()

    # HTML 템플릿 시작
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(agent['name'])} - 게임 개발 결과물</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header .meta {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .status {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 15px;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
        }}

        .status.completed {{
            background: #10b981;
        }}

        .status.failed {{
            background: #ef4444;
        }}

        .summary {{
            background: #f8fafc;
            padding: 30px;
            border-bottom: 3px solid #e2e8f0;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .summary-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .summary-card .label {{
            color: #64748b;
            margin-top: 5px;
            font-size: 0.9em;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
            background: #f8fafc;
            border-radius: 15px;
            padding: 30px;
            border-left: 5px solid #667eea;
        }}

        .section h2 {{
            font-size: 1.8em;
            color: #1e293b;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-icon {{
            font-size: 1.2em;
        }}

        .artifact {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .artifact:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .artifact h3 {{
            color: #667eea;
            font-size: 1.4em;
            margin-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }}

        .artifact-content {{
            color: #475569;
            white-space: pre-wrap;
            line-height: 1.9;
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #e2e8f0;
            margin-top: 10px;
            font-size: 1.05em;
        }}

        .artifact-content p {{
            margin: 15px 0;
        }}

        .artifact-content strong {{
            color: #1e293b;
            font-weight: 600;
        }}

        .images {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}

        .image-card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .image-card img {{
            width: 100%;
            height: auto;
            display: block;
            border-bottom: 3px solid #667eea;
        }}

        .image-card .image-info {{
            padding: 15px;
            background: #f8fafc;
        }}

        .image-card .prompt {{
            font-size: 0.9em;
            color: #64748b;
            margin-top: 5px;
        }}

        .code-container {{
            position: relative;
            margin-top: 15px;
        }}

        .code-header {{
            background: #1e293b;
            padding: 10px 20px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #334155;
        }}

        .code-title {{
            color: #94a3b8;
            font-size: 0.9em;
            font-weight: 600;
        }}

        .copy-button {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 6px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.85em;
            transition: background 0.2s;
        }}

        .copy-button:hover {{
            background: #2563eb;
        }}

        .copy-button:active {{
            background: #1d4ed8;
        }}

        .code-block {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 0;
            border-radius: 0 0 10px 10px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.95em;
            line-height: 1.8;
            margin: 0;
            max-height: 600px;
            overflow-y: auto;
        }}

        .code-block code {{
            display: block;
            padding: 20px;
            counter-reset: line;
        }}

        .code-line {{
            display: block;
            padding-left: 60px;
            position: relative;
            min-height: 1.8em;
        }}

        .code-line:before {{
            content: counter(line);
            counter-increment: line;
            position: absolute;
            left: 0;
            width: 50px;
            text-align: right;
            color: #475569;
            user-select: none;
            padding-right: 15px;
            border-right: 2px solid #334155;
        }}

        .code-line:hover {{
            background: rgba(255,255,255,0.05);
        }}

        /* 간단한 문법 하이라이팅 */
        .keyword {{ color: #c792ea; font-weight: bold; }}
        .string {{ color: #89ddff; }}
        .comment {{ color: #6a9955; font-style: italic; }}
        .function {{ color: #82aaff; }}
        .number {{ color: #f78c6c; }}
        .class-name {{ color: #ffcb6b; }}

        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
            margin: 5px 5px 5px 0;
        }}

        .badge.language {{
            background: #3b82f6;
            color: white;
        }}

        .badge.framework {{
            background: #10b981;
            color: white;
        }}

        .badge.quality {{
            background: #f59e0b;
            color: white;
        }}

        .list-item {{
            padding: 10px 15px;
            margin: 8px 0;
            background: white;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }}

        .key-points {{
            list-style: none;
            padding: 0;
        }}

        .key-points li {{
            padding: 12px 15px;
            margin: 10px 0;
            background: white;
            border-left: 4px solid #10b981;
            border-radius: 5px;
            position: relative;
            padding-left: 40px;
        }}

        .key-points li:before {{
            content: "✓";
            position: absolute;
            left: 15px;
            color: #10b981;
            font-weight: bold;
            font-size: 1.2em;
        }}

        .nav {{
            position: sticky;
            top: 20px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .nav h3 {{
            margin-bottom: 15px;
            color: #1e293b;
        }}

        .nav a {{
            display: block;
            padding: 10px 15px;
            color: #667eea;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.2s;
            margin: 5px 0;
        }}

        .nav a:hover {{
            background: #f1f5f9;
        }}

        @media (max-width: 768px) {{
            .summary-grid {{
                grid-template-columns: 1fr;
            }}

            .images {{
                grid-template-columns: 1fr;
            }}

            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 {escape_html(agent['name'])}</h1>
            <div class="meta">
                <p>{escape_html(agent['user_request'])}</p>
                <div class="status {agent['status']}">{agent['status'].upper()}</div>
            </div>
        </div>

        <div class="summary">
            <h2>📊 결과 요약</h2>
            <div class="summary-grid">
"""

    # 통계 계산
    artifacts = agent.get('artifacts', {})
    total_artifacts = len(artifacts)
    image_count = sum(len(v.get('images', [])) for v in artifacts.values() if isinstance(v, dict))
    code_count = sum(1 for v in artifacts.values() if isinstance(v, dict) and 'code' in v)

    html_content += f"""
                <div class="summary-card">
                    <div class="number">{total_artifacts}</div>
                    <div class="label">총 결과물</div>
                </div>
                <div class="summary-card">
                    <div class="number">{image_count}</div>
                    <div class="label">생성된 이미지</div>
                </div>
                <div class="summary-card">
                    <div class="number">{code_count}</div>
                    <div class="label">코드 섹션</div>
                </div>
                <div class="summary-card">
                    <div class="number">{len(agent.get('plan', {}).get('steps', []))}</div>
                    <div class="label">실행 단계</div>
                </div>
            </div>
        </div>

        <div class="content">
"""

    # 네비게이션
    html_content += """
            <div class="nav">
                <h3>📑 목차</h3>
"""

    for step_id, artifact in artifacts.items():
        if isinstance(artifact, dict):
            title = artifact.get('title', step_id)
            html_content += f'                <a href="#{step_id}">{escape_html(title)}</a>\n'

    html_content += """
            </div>
"""

    # 각 결과물 섹션
    for step_id, artifact in artifacts.items():
        if not isinstance(artifact, dict):
            continue

        title = artifact.get('title', step_id)

        html_content += f"""
            <div class="section" id="{step_id}">
                <h2><span class="section-icon">📄</span>{escape_html(title)}</h2>
                <div class="artifact">
"""

        # 이미지가 있는 경우
        if 'images' in artifact and artifact['images']:
            html_content += """
                    <h3>🖼️ 생성된 이미지</h3>
                    <div class="images">
"""
            for idx, img_url in enumerate(artifact['images']):
                full_url = f"http://localhost:3000{img_url}"
                prompt = artifact.get('prompt', '')
                html_content += f"""
                        <div class="image-card">
                            <img src="{full_url}" alt="Generated Image {idx+1}" loading="lazy">
                            <div class="image-info">
                                <strong>이미지 {idx+1}</strong>
                                {f'<div class="prompt">프롬프트: {escape_html(prompt[:100])}...</div>' if prompt else ''}
                            </div>
                        </div>
"""
            html_content += """
                    </div>
"""

        # 설명
        if 'description' in artifact:
            html_content += f"""
                    <h3>📝 설명</h3>
                    <div class="artifact-content">{escape_html(artifact['description'])}</div>
"""

        # 내용
        if 'content' in artifact:
            html_content += f"""
                    <h3>📋 내용</h3>
                    <div class="artifact-content">{escape_html(artifact['content'])}</div>
"""

        # 주요 포인트
        if 'key_points' in artifact and artifact['key_points']:
            html_content += """
                    <h3>✨ 주요 포인트</h3>
                    <ul class="key-points">
"""
            for point in artifact['key_points']:
                html_content += f"""
                        <li>{escape_html(point)}</li>
"""
            html_content += """
                    </ul>
"""

        # 코드
        if 'code' in artifact:
            language = artifact.get('language', 'Unknown')
            framework = artifact.get('framework', 'Unknown')

            html_content += f"""
                    <h3>💻 코드</h3>
                    <div>
                        <span class="badge language">{escape_html(language)}</span>
                        <span class="badge framework">{escape_html(framework)}</span>
"""

            # 코드 품질
            if 'validation' in artifact:
                validation = artifact['validation']
                quality = validation.get('code_quality', 'N/A')
                html_content += f"""
                        <span class="badge quality">품질: {escape_html(str(quality))}/10</span>
"""

            # 코드를 줄별로 분리하고 포맷팅 (들여쓰기 보존)
            code_lines = artifact['code'].split('\n')
            code_html = '<code>\n'
            for line in code_lines:
                if line.strip():
                    # 공백을 &nbsp;로 변환하여 들여쓰기 유지
                    escaped_line = escape_html(line).replace(' ', '&nbsp;')
                else:
                    escaped_line = '&nbsp;'
                code_html += f'<span class="code-line">{escaped_line}</span>\n'
            code_html += '</code>'

            html_content += f"""
                    </div>
                    <div class="code-container">
                        <div class="code-header">
                            <div class="code-title">📄 {escape_html(language)} Code</div>
                            <button class="copy-button" onclick="copyCode(this)">📋 Copy Code</button>
                        </div>
                        <div class="code-block">{code_html}</div>
                    </div>
"""

            # 코드 설명
            if 'explanation' in artifact:
                html_content += f"""
                    <h3>📖 코드 설명</h3>
                    <div class="artifact-content">{escape_html(artifact['explanation'])}</div>
"""

            # 검증 정보
            if 'validation' in artifact:
                validation = artifact['validation']

                if 'strengths' in validation and validation['strengths']:
                    html_content += """
                    <h3>💪 강점</h3>
                    <ul class="key-points">
"""
                    for strength in validation['strengths']:
                        html_content += f"""
                        <li>{escape_html(strength)}</li>
"""
                    html_content += """
                    </ul>
"""

                if 'improvements' in validation and validation['improvements']:
                    html_content += """
                    <h3>🔧 개선 제안</h3>
                    <ul class="key-points">
"""
                    for improvement in validation['improvements']:
                        html_content += f"""
                        <li>{escape_html(improvement)}</li>
"""
                    html_content += """
                    </ul>
"""

        # 예제
        if 'examples' in artifact and artifact['examples']:
            html_content += """
                    <h3>📚 예제</h3>
"""
            for idx, example in enumerate(artifact['examples']):
                example_str = str(example)
                # 예제가 코드처럼 보이면 코드 블록으로 표시
                if '\n' in example_str and any(keyword in example_str for keyword in ['class ', 'def ', 'function', 'public', 'private', '{', '}']):
                    # 코드 예제
                    example_lines = example_str.split('\n')
                    example_code_html = '<code>\n'
                    for line in example_lines:
                        if line.strip():
                            escaped_line = escape_html(line).replace(' ', '&nbsp;')
                        else:
                            escaped_line = '&nbsp;'
                        example_code_html += f'<span class="code-line">{escaped_line}</span>\n'
                    example_code_html += '</code>'

                    html_content += f"""
                    <div class="code-container">
                        <div class="code-header">
                            <div class="code-title">📝 예제 {idx+1}</div>
                            <button class="copy-button" onclick="copyCode(this)">📋 Copy</button>
                        </div>
                        <div class="code-block">{example_code_html}</div>
                    </div>
"""
                else:
                    # 일반 예제
                    html_content += f"""
                    <div class="list-item">{escape_html(example_str)}</div>
"""

        html_content += """
                </div>
            </div>
"""

    # HTML 종료
    html_content += f"""
        </div>

        <div class="header" style="padding: 20px; text-align: center;">
            <p style="opacity: 0.8;">생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="opacity: 0.8;">🤖 Generated with Claude Code & Open WebUI</p>
        </div>
    </div>

    <script>
        function copyCode(button) {{
            // 코드 블록 찾기
            const codeContainer = button.closest('.code-container');
            const codeBlock = codeContainer.querySelector('.code-block code');

            // 줄 번호 제외하고 텍스트만 추출
            const lines = codeBlock.querySelectorAll('.code-line');
            let codeText = '';
            lines.forEach(line => {{
                const text = line.textContent;
                codeText += text === '\\u00a0' ? '' : text;
                codeText += '\\n';
            }});

            // 클립보드에 복사
            navigator.clipboard.writeText(codeText.trim()).then(() => {{
                // 버튼 텍스트 변경
                const originalText = button.textContent;
                button.textContent = '✅ Copied!';
                button.style.background = '#10b981';

                setTimeout(() => {{
                    button.textContent = originalText;
                    button.style.background = '#3b82f6';
                }}, 2000);
            }}).catch(err => {{
                console.error('Failed to copy:', err);
                button.textContent = '❌ Failed';
                setTimeout(() => {{
                    button.textContent = '📋 Copy Code';
                }}, 2000);
            }});
        }}

        // 부드러운 스크롤
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    return html_content

if __name__ == "__main__":
    print("=" * 80)
    print("에이전트 결과물 HTML 내보내기")
    print("=" * 80)
    print()

    # 명령줄 인자로 에이전트 ID가 제공된 경우
    if len(sys.argv) > 1:
        agent_id = sys.argv[1]
        print(f"에이전트 ID: {agent_id}")

        try:
            response = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                selected_agent = response.json()
                print(f"이름: {selected_agent.get('name', 'N/A')}")
                print(f"상태: {selected_agent.get('status', 'N/A')}")
            else:
                print(f"❌ 에이전트를 찾을 수 없습니다: {response.status_code}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 오류: {e}")
            sys.exit(1)
    else:
        # 완료된 에이전트 목록 가져오기
        try:
            response = requests.get(f"{BASE_URL}/agents/", headers=headers, timeout=10)
            agents = response.json()

            completed_agents = [a for a in agents if a.get('status') == 'completed']
            completed_agents.sort(key=lambda x: x.get('created_at', 0), reverse=True)

            if not completed_agents:
                print("완료된 에이전트가 없습니다.")
                sys.exit(0)

            print(f"완료된 에이전트: {len(completed_agents)}개\n")

            for idx, agent in enumerate(completed_agents[:10], 1):
                print(f"{idx}. {agent['name']}")
                print(f"   ID: {agent['id']}")
                print(f"   작업 타입: {agent['task_type']}")
                print(f"   결과물: {len(agent.get('artifacts', {}))}개")
                print()

            # 사용자 입력
            choice = input(f"\nHTML로 내보낼 에이전트 번호 (1-{min(10, len(completed_agents))}, Enter=최신): ").strip()

            if not choice:
                selected_agent = completed_agents[0]
            else:
                selected_agent = completed_agents[int(choice) - 1]

        except Exception as e:
            print(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # HTML 생성
    print(f"\n'{selected_agent['name']}' HTML 생성 중...")

    html_content = generate_html(selected_agent['id'])

    # 파일 저장
    filename = f"game_result_{selected_agent['id'][:8]}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ HTML 파일 생성 완료: {filename}")
    print(f"\n브라우저에서 열기:")
    print(f"  file:///{filename}")
    print()
