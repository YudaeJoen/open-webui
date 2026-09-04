<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getAgents, quickGameDesign, quickFullDevelopment, generateRandomGameIdea } from '$lib/apis/agents';
	import { toast } from 'svelte-sonner';

	let agents = [];
	let loading = false;
	let creating = false;
	let generatingIdea = false;

	// 새 게임 생성 폼
	let gameConcept = '';
	let genre = '';
	let targetPlatform = '';
	let taskType = 'game_design'; // 'game_design' 또는 'full_development'

	onMount(async () => {
		await loadAgents();
		// 5초마다 자동 새로고침
		const interval = setInterval(loadAgents, 5000);
		return () => clearInterval(interval);
	});

	async function loadAgents() {
		try {
			const result = await getAgents(localStorage.token);
			agents = result.sort((a, b) =>
				new Date(b.created_at * 1000).getTime() - new Date(a.created_at * 1000).getTime()
			);
		} catch (error) {
			console.error('Failed to load agents:', error);
		}
	}

	async function generateIdea() {
		generatingIdea = true;
		try {
			const idea = await generateRandomGameIdea(localStorage.token);
			gameConcept = idea.game_concept;
			genre = idea.genre;
			targetPlatform = idea.target_platform;
			toast.success('랜덤 아이디어 생성 완료!');
		} catch (error) {
			console.error('Failed to generate idea:', error);
			toast.error('아이디어 생성 실패: ' + error.message);
		} finally {
			generatingIdea = false;
		}
	}

	async function createAgent() {
		if (!gameConcept || !genre || !targetPlatform) {
			toast.error('모든 필드를 입력해주세요');
			return;
		}

		creating = true;
		try {
			const data = {
				game_concept: gameConcept,
				genre: genre,
				target_platform: targetPlatform
			};

			let result;
			if (taskType === 'game_design') {
				result = await quickGameDesign(localStorage.token, data);
				toast.success('게임 기획서 생성 시작!');
			} else {
				result = await quickFullDevelopment(localStorage.token, data);
				toast.success('전체 게임 개발 시작!');
			}

			// 폼 초기화
			gameConcept = '';
			genre = '';
			targetPlatform = '';

			// 목록 새로고침
			await loadAgents();
		} catch (error) {
			console.error('Failed to create agent:', error);
			toast.error('에이전트 생성 실패: ' + error.message);
		} finally {
			creating = false;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'completed': return 'bg-green-500';
			case 'failed': return 'bg-red-500';
			case 'cancelled': return 'bg-gray-500';
			case 'executing': return 'bg-blue-500 animate-pulse';
			case 'planning': return 'bg-yellow-500 animate-pulse';
			case 'reviewing': return 'bg-purple-500 animate-pulse';
			default: return 'bg-gray-400';
		}
	}

	function getStatusText(status: string) {
		const statusMap = {
			'idle': '대기중',
			'planning': '계획중',
			'executing': '실행중',
			'reviewing': '검토중',
			'completed': '완료',
			'failed': '실패',
			'cancelled': '취소됨'
		};
		return statusMap[status] || status;
	}

	function viewAgent(agentId: string) {
		goto(`/workspace/games/${agentId}`);
	}
</script>

<div class="max-w-7xl mx-auto px-4 py-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
			🎮 Game Agent
		</h1>
		<p class="text-gray-600 dark:text-gray-400">
			AI를 활용한 자동 게임 개발 시스템
		</p>
	</div>

	<!-- 새 게임 생성 폼 -->
	<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
		<h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
			새 게임 만들기
		</h2>

		<div class="space-y-4">
			<!-- 작업 타입 선택 -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					작업 타입
				</label>
				<div class="flex gap-4">
					<label class="flex items-center">
						<input
							type="radio"
							bind:group={taskType}
							value="game_design"
							class="mr-2"
						/>
						<span class="text-gray-700 dark:text-gray-300">
							📝 기획서만 작성
						</span>
					</label>
					<label class="flex items-center">
						<input
							type="radio"
							bind:group={taskType}
							value="full_development"
							class="mr-2"
						/>
						<span class="text-gray-700 dark:text-gray-300">
							🚀 전체 개발 (기획 + 이미지 + 코드)
						</span>
					</label>
				</div>
			</div>

			<!-- 랜덤 아이디어 생성 버튼 -->
			<div class="flex justify-end">
				<button
					on:click={generateIdea}
					disabled={generatingIdea}
					class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400
						   text-white font-semibold rounded-lg transition-colors
						   flex items-center gap-2"
				>
					{#if generatingIdea}
						<svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
						</svg>
						AI 아이디어 생성 중...
					{:else}
						🎲 랜덤 아이디어 생성
					{/if}
				</button>
			</div>

			<!-- 게임 컨셉 -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					게임 컨셉
				</label>
				<textarea
					bind:value={gameConcept}
					placeholder="예: 간단한 슬라임 키우기 게임. 슬라임을 클릭하면 점수가 올라가고, 점수로 업그레이드를 구매할 수 있습니다."
					rows="3"
					class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
						   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
						   focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
			</div>

			<!-- 장르 -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					장르
				</label>
				<input
					type="text"
					bind:value={genre}
					placeholder="예: 아이들 클리커, RPG, 퍼즐, 액션 등"
					class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
						   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
						   focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
			</div>

			<!-- 타겟 플랫폼 -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					타겟 플랫폼
				</label>
				<input
					type="text"
					bind:value={targetPlatform}
					placeholder="예: 웹 브라우저, 모바일, PC 등"
					class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
						   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
						   focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
			</div>

			<!-- 생성 버튼 -->
			<button
				on:click={createAgent}
				disabled={creating}
				class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
					   text-white font-semibold rounded-lg transition-colors
					   flex items-center justify-center gap-2"
			>
				{#if creating}
					<svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
					</svg>
					생성 중...
				{:else}
					{taskType === 'game_design' ? '📝 기획서 생성' : '🚀 게임 개발 시작'}
				{/if}
			</button>
		</div>
	</div>

	<!-- 에이전트 목록 -->
	<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
				게임 프로젝트 ({agents.length})
			</h2>
			<button
				on:click={loadAgents}
				class="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600
					   rounded-lg transition-colors"
			>
				🔄 새로고침
			</button>
		</div>

		{#if agents.length === 0}
			<div class="text-center py-12 text-gray-500 dark:text-gray-400">
				<p class="text-lg mb-2">아직 생성된 게임이 없습니다</p>
				<p class="text-sm">위의 폼을 사용하여 첫 게임을 만들어보세요!</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each agents as agent}
					<div
						class="border border-gray-200 dark:border-gray-700 rounded-lg p-4
							   hover:shadow-md transition-shadow cursor-pointer"
						on:click={() => viewAgent(agent.id)}
					>
						<div class="flex items-start justify-between mb-2">
							<div class="flex-1">
								<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
									{agent.name}
								</h3>
								<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
									<span class={`px-2 py-1 rounded text-white text-xs font-semibold ${getStatusColor(agent.status)}`}>
										{getStatusText(agent.status)}
									</span>
									{#if agent.current_step}
										<span class="text-xs">
											단계: {agent.current_step}
										</span>
									{/if}
								</div>
							</div>
							<div class="text-right text-sm text-gray-500 dark:text-gray-400">
								<div>{new Date(agent.created_at * 1000).toLocaleDateString()}</div>
								<div>{new Date(agent.created_at * 1000).toLocaleTimeString()}</div>
							</div>
						</div>

						{#if agent.artifacts && Object.keys(agent.artifacts).length > 0}
							<div class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
								<div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
									<span>📦 결과물: {Object.keys(agent.artifacts).length}개</span>
									{#if agent.task_type}
										<span>🎯 {agent.task_type === 'game_design' ? '기획서' : '전체 개발'}</span>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	/* 애니메이션 추가 */
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}
</style>
