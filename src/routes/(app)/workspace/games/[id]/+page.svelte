<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getAgentById } from '$lib/apis/agents';
	import { toast } from 'svelte-sonner';

	let agent = null;
	let loading = true;
	let interval;

	$: agentId = $page.params.id;

	onMount(async () => {
		await loadAgent();
		// 3초마다 자동 새로고침 (진행 중일 때만)
		interval = setInterval(async () => {
			if (agent && ['planning', 'executing', 'reviewing'].includes(agent.status)) {
				await loadAgent();
			}
		}, 3000);
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});

	async function loadAgent() {
		try {
			agent = await getAgentById(localStorage.token, agentId);
			console.log('Loaded agent:', agent);
			loading = false;
		} catch (error) {
			console.error('Failed to load agent:', error);
			toast.error('에이전트를 불러올 수 없습니다');
			loading = false;
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

	function downloadHTML() {
		// HTML 내보내기 기능 (추후 구현)
		toast.success('HTML 내보내기 준비중...');
	}

	function copyCode(code: string) {
		navigator.clipboard.writeText(code).then(() => {
			toast.success('코드가 클립보드에 복사되었습니다!');
		}).catch(() => {
			toast.error('복사 실패');
		});
	}
</script>

{#if loading}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<svg class="animate-spin h-12 w-12 mx-auto mb-4 text-blue-500" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
			</svg>
			<p class="text-gray-600 dark:text-gray-400">로딩 중...</p>
		</div>
	</div>
{:else if agent}
	<div class="max-w-7xl mx-auto px-4 py-8">
		<!-- 헤더 -->
		<div class="mb-8">
			<button
				on:click={() => goto('/workspace/games')}
				class="mb-4 text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2"
			>
				← 목록으로 돌아가기
			</button>

			<div class="flex items-start justify-between">
				<div>
					<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
						{agent.name}
					</h1>
					<div class="flex items-center gap-3">
						<span class={`px-3 py-1 rounded text-white text-sm font-semibold ${getStatusColor(agent.status)}`}>
							{getStatusText(agent.status)}
						</span>
						{#if agent.current_step}
							<span class="text-sm text-gray-600 dark:text-gray-400">
								현재 단계: {agent.current_step}
							</span>
						{/if}
					</div>
				</div>

				<button
					on:click={downloadHTML}
					class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg
						   transition-colors flex items-center gap-2"
				>
					📄 HTML 내보내기
				</button>
			</div>

			<div class="mt-4 text-sm text-gray-600 dark:text-gray-400">
				생성일: {new Date(agent.created_at * 1000).toLocaleString()}
			</div>
		</div>

		<!-- 결과물 -->
		{#if agent.artifacts && Object.keys(agent.artifacts).length > 0}
			<div class="space-y-6">
				{#each Object.entries(agent.artifacts) as [stepId, artifact]}
					{@const actualArtifact = artifact?.output || artifact || {}}
					{@const title = actualArtifact.title || artifact.title || stepId}
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
							{title}
						</h2>

						<!-- 이미지 -->
						{#if actualArtifact.images && Array.isArray(actualArtifact.images) && actualArtifact.images.length > 0}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									🖼️ 생성된 이미지 ({actualArtifact.images.length}개)
								</h3>
								<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
									{#each actualArtifact.images as imageUrl}
										{@const imageUrlStr = typeof imageUrl === 'string' ? imageUrl : (imageUrl?.url || imageUrl?.image_url || JSON.stringify(imageUrl))}
										{#if imageUrlStr && imageUrlStr !== 'undefined' && imageUrlStr !== 'null'}
											<div class="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900">
												<img
													src={typeof imageUrlStr === 'string' && imageUrlStr.startsWith('http') ? imageUrlStr : `${imageUrlStr}?token=${localStorage.token}`}
													alt="Generated Image"
													class="w-full h-auto object-contain"
													loading="lazy"
													on:error={(e) => {
														console.error('Image load error:', imageUrlStr);
														e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3EImage not available%3C/text%3E%3C/svg%3E';
													}}
												/>
												<div class="p-2 text-xs text-gray-500 dark:text-gray-400 break-all">
													{imageUrlStr}
												</div>
											</div>
										{/if}
									{/each}
								</div>
							</div>
						{/if}

						<!-- 설명 -->
						{#if actualArtifact.description}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									📝 설명
								</h3>
								<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 whitespace-pre-wrap">
									<p class="text-gray-700 dark:text-gray-300 leading-relaxed">
										{actualArtifact.description}
									</p>
								</div>
							</div>
						{/if}

						<!-- 기획 내용 (Content) -->
						{#if actualArtifact.content}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									📄 상세 내용
								</h3>
								<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 whitespace-pre-wrap">
									<p class="text-gray-700 dark:text-gray-300 leading-relaxed">
										{actualArtifact.content}
									</p>
								</div>
							</div>
						{/if}

						<!-- 핵심 포인트 -->
						{#if actualArtifact.key_points && actualArtifact.key_points.length > 0}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									🎯 핵심 포인트
								</h3>
								<ul class="list-disc list-inside space-y-2 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
									{#each actualArtifact.key_points as point}
										<li class="text-gray-700 dark:text-gray-300">{point}</li>
									{/each}
								</ul>
							</div>
						{/if}

						<!-- 코드 -->
						{#if actualArtifact.code}
							<div class="mb-6">
								<div class="flex items-center justify-between mb-3">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white">
										💻 코드
									</h3>
									<button
										on:click={() => copyCode(actualArtifact.code)}
										class="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded
											   transition-colors"
									>
										📋 복사
									</button>
								</div>
								<div class="bg-gray-900 rounded-lg overflow-hidden">
									<pre class="p-4 overflow-x-auto"><code class="text-gray-100 text-sm font-mono">{actualArtifact.code}</code></pre>
								</div>
							</div>
						{/if}

						<!-- 프롬프트 -->
						{#if actualArtifact.prompt}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									✨ 프롬프트
								</h3>
								<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
									<p class="text-gray-700 dark:text-gray-300 text-sm">
										{actualArtifact.prompt}
									</p>
								</div>
							</div>
						{/if}

						<!-- 예제 -->
						{#if actualArtifact.examples && actualArtifact.examples.length > 0}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									📚 예제
								</h3>
								<div class="space-y-3">
									{#each actualArtifact.examples as example, idx}
										<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
											<p class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
												예제 {idx + 1}
											</p>
											<pre class="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">{typeof example === 'string' ? example : JSON.stringify(example, null, 2)}</pre>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- 다음 단계 -->
						{#if actualArtifact.next_steps && actualArtifact.next_steps.length > 0}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									➡️ 다음 단계
								</h3>
								<ul class="list-disc list-inside space-y-2 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
									{#each actualArtifact.next_steps as step}
										<li class="text-gray-700 dark:text-gray-300">{step}</li>
									{/each}
								</ul>
							</div>
						{/if}

						<!-- 위험 요소 -->
						{#if actualArtifact.risks && actualArtifact.risks.length > 0}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									⚠️ 위험 요소
								</h3>
								<ul class="list-disc list-inside space-y-2 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
									{#each actualArtifact.risks as risk}
										<li class="text-gray-700 dark:text-gray-300">{risk}</li>
									{/each}
								</ul>
							</div>
						{/if}

						<!-- 테스트 계획 -->
						{#if actualArtifact.testing}
							<div class="mb-6">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
									🧪 테스트 계획
								</h3>
								<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 whitespace-pre-wrap">
									<p class="text-gray-700 dark:text-gray-300 leading-relaxed">
										{actualArtifact.testing}
									</p>
								</div>
							</div>
						{/if}

						<!-- 최종 검토 전용 필드들 -->
						{#if stepId === 'final_review'}
							<!-- 프로젝트 요약 -->
							{#if actualArtifact.summary}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										📋 프로젝트 요약
									</h3>
									<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 whitespace-pre-wrap">
										<p class="text-gray-700 dark:text-gray-300 leading-relaxed">
											{actualArtifact.summary}
										</p>
									</div>
								</div>
							{/if}

							<!-- 완성된 결과물 -->
							{#if actualArtifact.deliverables && actualArtifact.deliverables.length > 0}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										✅ 완성된 결과물
									</h3>
									<ul class="list-disc list-inside space-y-2 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
										{#each actualArtifact.deliverables as deliverable}
											<li class="text-gray-700 dark:text-gray-300">{deliverable}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- 품질 평가 -->
							{#if actualArtifact.quality_assessment}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										⭐ 품질 평가
									</h3>
									<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 whitespace-pre-wrap">
										<p class="text-gray-700 dark:text-gray-300 leading-relaxed">
											{actualArtifact.quality_assessment}
										</p>
									</div>
								</div>
							{/if}

							<!-- 강점 -->
							{#if actualArtifact.strengths && actualArtifact.strengths.length > 0}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										💪 강점
									</h3>
									<ul class="list-disc list-inside space-y-2 bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
										{#each actualArtifact.strengths as strength}
											<li class="text-gray-700 dark:text-gray-300">{strength}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- 약점 -->
							{#if actualArtifact.weaknesses && actualArtifact.weaknesses.length > 0}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										⚠️ 약점 및 개선 필요 사항
									</h3>
									<ul class="list-disc list-inside space-y-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
										{#each actualArtifact.weaknesses as weakness}
											<li class="text-gray-700 dark:text-gray-300">{weakness}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- 향후 개선 사항 -->
							{#if actualArtifact.recommendations && actualArtifact.recommendations.length > 0}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										💡 향후 개선 사항
									</h3>
									<ul class="list-disc list-inside space-y-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
										{#each actualArtifact.recommendations as recommendation}
											<li class="text-gray-700 dark:text-gray-300">{recommendation}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- 다음 단계 액션 -->
							{#if actualArtifact.next_actions && actualArtifact.next_actions.length > 0}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										🚀 다음 단계 액션
									</h3>
									<ul class="list-disc list-inside space-y-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
										{#each actualArtifact.next_actions as action}
											<li class="text-gray-700 dark:text-gray-300">{action}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- 완료 상태 -->
							{#if actualArtifact.completion_status}
								<div class="mb-6">
									<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
										📊 완료 상태
									</h3>
									<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 whitespace-pre-wrap">
										<p class="text-gray-700 dark:text-gray-300 leading-relaxed">
											{actualArtifact.completion_status}
										</p>
									</div>
								</div>
							{/if}
						{/if}
					</div>
				{/each}
			</div>
		{:else}
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
				{#if agent.status === 'planning' || agent.status === 'executing' || agent.status === 'reviewing'}
					<div class="mb-4">
						<svg class="animate-spin h-12 w-12 mx-auto text-blue-500" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
						</svg>
					</div>
					<p class="text-lg text-gray-600 dark:text-gray-400">
						작업이 진행 중입니다...
					</p>
					<p class="text-sm text-gray-500 dark:text-gray-500 mt-2">
						현재 상태: {getStatusText(agent.status)}
					</p>
				{:else}
					<p class="text-lg text-gray-600 dark:text-gray-400">
						아직 결과물이 생성되지 않았습니다
					</p>
				{/if}
			</div>
		{/if}
	</div>
{:else}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<p class="text-xl text-gray-600 dark:text-gray-400 mb-4">
				에이전트를 찾을 수 없습니다
			</p>
			<button
				on:click={() => goto('/workspace/games')}
				class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
			>
				목록으로 돌아가기
			</button>
		</div>
	</div>
{/if}

<style>
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}
</style>
