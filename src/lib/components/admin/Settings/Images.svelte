<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config as backendConfig, user } from '$lib/stores';

	import { getBackendConfig } from '$lib/apis';
	import {
		getImageGenerationModels,
		getImageGenerationConfig,
		updateImageGenerationConfig,
		getConfig,
		updateConfig,
		verifyConfigUrl,
		getAutomatic1111Samplers,
		getAutomatic1111Schedulers,
		getAutomatic1111Loras,
		getAutomatic1111Vaes,
		getAutomatic1111Upscalers,
		refreshAutomatic1111Loras,
		optimizeSettings
	} from '$lib/apis/images';
	import { getOllamaModels } from '$lib/apis/ollama';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	const dispatch = createEventDispatcher();

	const i18n = getContext('i18n');

	let loading = false;

	let config = null;
	let imageGenerationConfig = null;

	let models = null;
	let ollamaModels = null;

	// Dynamic lists from SD WebUI
	let sdSamplers = null;
	let sdSchedulers = null;
	let sdLoras = null;
	let sdVaes = null;
	let sdUpscalers = null;

	// Selected LoRAs for configuration
	let selectedLoras: { name: string; weight: number }[] = [];

	// Optimize settings
	let optimizing = false;
	let testPrompt = '';
	let optimizeResult: any = null;

	// Fallback static lists
	let samplers = [
		'DPM++ 2M',
		'DPM++ SDE',
		'DPM++ 2M SDE',
		'DPM++ 2M SDE Heun',
		'DPM++ 2S a',
		'DPM++ 3M SDE',
		'Euler a',
		'Euler',
		'LMS',
		'Heun',
		'DPM2',
		'DPM2 a',
		'DPM fast',
		'DPM adaptive',
		'Restart',
		'DDIM',
		'DDIM CFG++',
		'PLMS',
		'UniPC'
	];

	let schedulers = [
		'Automatic',
		'Uniform',
		'Karras',
		'Exponential',
		'Polyexponential',
		'SGM Uniform',
		'KL Optimal',
		'Align Your Steps',
		'Simple',
		'Normal',
		'DDIM',
		'Beta'
	];

	let requiredWorkflowNodes = [
		{
			type: 'prompt',
			key: 'text',
			node_ids: ''
		},
		{
			type: 'model',
			key: 'ckpt_name',
			node_ids: ''
		},
		{
			type: 'width',
			key: 'width',
			node_ids: ''
		},
		{
			type: 'height',
			key: 'height',
			node_ids: ''
		},
		{
			type: 'steps',
			key: 'steps',
			node_ids: ''
		},
		{
			type: 'seed',
			key: 'seed',
			node_ids: ''
		}
	];

	const getModels = async () => {
		models = await getImageGenerationModels(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
	};

	const loadOllamaModels = async () => {
		ollamaModels = await getOllamaModels(localStorage.token).catch((error) => {
			console.error('Failed to load Ollama models:', error);
			return null;
		});
	};

	const loadSDWebUIData = async () => {
		if (config?.engine !== 'automatic1111') return;

		try {
			// Load all SD WebUI data in parallel
			const [samplersRes, schedulersRes, lorasRes, vaesRes, upscalersRes] = await Promise.all([
				getAutomatic1111Samplers(localStorage.token).catch(() => null),
				getAutomatic1111Schedulers(localStorage.token).catch(() => null),
				getAutomatic1111Loras(localStorage.token).catch(() => null),
				getAutomatic1111Vaes(localStorage.token).catch(() => null),
				getAutomatic1111Upscalers(localStorage.token).catch(() => null)
			]);

			if (samplersRes) {
				sdSamplers = samplersRes.map((s: any) => s.name);
			}
			if (schedulersRes) {
				sdSchedulers = schedulersRes.map((s: any) => s.name);
			}
			if (lorasRes) {
				sdLoras = lorasRes;
			}
			if (vaesRes) {
				sdVaes = vaesRes.map((v: any) => v.model_name);
			}
			if (upscalersRes) {
				sdUpscalers = upscalersRes.map((u: any) => u.name);
			}
		} catch (error) {
			console.error('Failed to load SD WebUI data:', error);
		}
	};

	const handleRefreshLoras = async () => {
		try {
			await refreshAutomatic1111Loras(localStorage.token);
			const lorasRes = await getAutomatic1111Loras(localStorage.token);
			if (lorasRes) {
				sdLoras = lorasRes;
				toast.success($i18n.t('LoRA list refreshed'));
			}
		} catch (error) {
			toast.error(`${error}`);
		}
	};

	const handleOptimizeSettings = async () => {
		if (!testPrompt.trim()) {
			toast.error($i18n.t('Please enter a prompt to optimize'));
			return;
		}

		optimizing = true;
		optimizeResult = null;

		try {
			const currentSettings = {
				steps: imageGenerationConfig?.IMAGE_STEPS,
				cfg_scale: config?.automatic1111?.AUTOMATIC1111_CFG_SCALE,
				sampler: config?.automatic1111?.AUTOMATIC1111_SAMPLER,
				scheduler: config?.automatic1111?.AUTOMATIC1111_SCHEDULER,
				size: imageGenerationConfig?.IMAGE_SIZE
			};

			const result = await optimizeSettings(localStorage.token, testPrompt, '', currentSettings);

			if (result) {
				optimizeResult = result;
				toast.success($i18n.t('Settings optimized successfully'));
			}
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			optimizing = false;
		}
	};

	const applyOptimizedSettings = () => {
		if (!optimizeResult) return;

		// Apply optimized settings to config
		if (optimizeResult.sampler_name) {
			config.automatic1111.AUTOMATIC1111_SAMPLER = optimizeResult.sampler_name;
		}
		if (optimizeResult.scheduler) {
			config.automatic1111.AUTOMATIC1111_SCHEDULER = optimizeResult.scheduler;
		}
		if (optimizeResult.cfg_scale) {
			config.automatic1111.AUTOMATIC1111_CFG_SCALE = optimizeResult.cfg_scale;
		}
		if (optimizeResult.seed !== undefined) {
			config.automatic1111.AUTOMATIC1111_SEED = optimizeResult.seed;
		}
		if (optimizeResult.clip_skip) {
			config.automatic1111.AUTOMATIC1111_CLIP_SKIP = optimizeResult.clip_skip;
		}
		if (optimizeResult.enable_hr !== undefined) {
			config.automatic1111.AUTOMATIC1111_ENABLE_HR = optimizeResult.enable_hr;
		}
		if (optimizeResult.hr_scale) {
			config.automatic1111.AUTOMATIC1111_HR_SCALE = optimizeResult.hr_scale;
		}
		if (optimizeResult.denoising_strength) {
			config.automatic1111.AUTOMATIC1111_DENOISING_STRENGTH = optimizeResult.denoising_strength;
		}
		if (optimizeResult.restore_faces !== undefined) {
			config.automatic1111.AUTOMATIC1111_RESTORE_FACES = optimizeResult.restore_faces;
		}

		// Apply to image generation config
		if (optimizeResult.steps) {
			imageGenerationConfig.IMAGE_STEPS = optimizeResult.steps;
		}
		if (optimizeResult.width && optimizeResult.height) {
			imageGenerationConfig.IMAGE_SIZE = `${optimizeResult.width}x${optimizeResult.height}`;
		}

		toast.success($i18n.t('Optimized settings applied'));
	};

	const addLora = () => {
		selectedLoras = [...selectedLoras, { name: '', weight: 1.0 }];
	};

	const removeLora = (index: number) => {
		selectedLoras = selectedLoras.filter((_, i) => i !== index);
	};

	const updateConfigHandler = async () => {
		const res = await updateConfig(localStorage.token, config)
			.catch((error) => {
				toast.error(`${error}`);
				return null;
			})
			.catch((error) => {
				toast.error(`${error}`);
				return null;
			});

		if (res) {
			config = res;
		}

		if (config.enabled) {
			backendConfig.set(await getBackendConfig());
			getModels();
		}
	};

	const validateJSON = (json) => {
		try {
			const obj = JSON.parse(json);

			if (obj && typeof obj === 'object') {
				return true;
			}
		} catch (e) {}
		return false;
	};

	const saveHandler = async () => {
		loading = true;

		if (config?.comfyui?.COMFYUI_WORKFLOW) {
			if (!validateJSON(config.comfyui.COMFYUI_WORKFLOW)) {
				toast.error('Invalid JSON format for ComfyUI Workflow.');
				loading = false;
				return;
			}
		}

		if (config?.comfyui?.COMFYUI_WORKFLOW) {
			config.comfyui.COMFYUI_WORKFLOW_NODES = requiredWorkflowNodes.map((node) => {
				return {
					type: node.type,
					key: node.key,
					node_ids:
						node.node_ids.trim() === '' ? [] : node.node_ids.split(',').map((id) => id.trim())
				};
			});
		}

		// Save selected LoRAs to config
		if (config?.automatic1111) {
			config.automatic1111.AUTOMATIC1111_LORAS = selectedLoras.filter((l) => l.name);
		}

		await updateConfig(localStorage.token, config).catch((error) => {
			toast.error(`${error}`);
			loading = false;
			return null;
		});

		await updateImageGenerationConfig(localStorage.token, imageGenerationConfig).catch((error) => {
			toast.error(`${error}`);
			loading = false;
			return null;
		});

		getModels();
		dispatch('save');
		loading = false;
	};

	onMount(async () => {
		if ($user?.role === 'admin') {
			const res = await getConfig(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				config = res;
			}

			if (config.enabled) {
				getModels();
				loadSDWebUIData();
			}

			// Load Ollama models for prompt generation
			loadOllamaModels();

			if (config.comfyui.COMFYUI_WORKFLOW) {
				try {
					config.comfyui.COMFYUI_WORKFLOW = JSON.stringify(
						JSON.parse(config.comfyui.COMFYUI_WORKFLOW),
						null,
						2
					);
				} catch (e) {
					console.error(e);
				}
			}

			requiredWorkflowNodes = requiredWorkflowNodes.map((node) => {
				const n = config.comfyui.COMFYUI_WORKFLOW_NODES.find((n) => n.type === node.type) ?? node;

				console.debug(n);

				return {
					type: n.type,
					key: n.key,
					node_ids: typeof n.node_ids === 'string' ? n.node_ids : n.node_ids.join(',')
				};
			});

			// Load selected LoRAs from config
			if (config.automatic1111?.AUTOMATIC1111_LORAS) {
				selectedLoras = config.automatic1111.AUTOMATIC1111_LORAS.map((l: any) => ({
					name: l.name || '',
					weight: l.weight || 1.0
				}));
			}

			const imageConfigRes = await getImageGenerationConfig(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (imageConfigRes) {
				imageGenerationConfig = imageConfigRes;
			}
		}
	});
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={async () => {
		saveHandler();
	}}
>
	<div class=" space-y-3 overflow-y-scroll scrollbar-hidden pr-2">
		{#if config && imageGenerationConfig}
			<div>
				<div class=" mb-1 text-sm font-medium">{$i18n.t('Image Settings')}</div>

				<div>
					<div class=" py-1 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">
							{$i18n.t('Image Generation (Experimental)')}
						</div>

						<div class="px-1">
							<Switch
								bind:state={config.enabled}
								on:change={(e) => {
									const enabled = e.detail;

									if (enabled) {
										if (
											config.engine === 'automatic1111' &&
											config.automatic1111.AUTOMATIC1111_BASE_URL === ''
										) {
											toast.error($i18n.t('AUTOMATIC1111 Base URL is required.'));
											config.enabled = false;
										} else if (
											config.engine === 'comfyui' &&
											config.comfyui.COMFYUI_BASE_URL === ''
										) {
											toast.error($i18n.t('ComfyUI Base URL is required.'));
											config.enabled = false;
										} else if (config.engine === 'openai' && config.openai.OPENAI_API_KEY === '') {
											toast.error($i18n.t('OpenAI API Key is required.'));
											config.enabled = false;
										} else if (config.engine === 'gemini' && config.gemini.GEMINI_API_KEY === '') {
											toast.error($i18n.t('Gemini API Key is required.'));
											config.enabled = false;
										}
									}

									updateConfigHandler();
								}}
							/>
						</div>
					</div>
				</div>

				{#if config.enabled}
					<div class=" py-1 flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Image Prompt Generation')}</div>
						<div class="px-1">
							<Switch bind:state={config.prompt_generation} />
						</div>
					</div>
				{/if}

				<div class=" py-1 flex w-full justify-between">
					<div class=" self-center text-xs font-medium">{$i18n.t('Image Generation Engine')}</div>
					<div class="flex items-center relative">
						<select
							class=" dark:bg-gray-900 w-fit pr-8 cursor-pointer rounded-sm px-2 p-1 text-xs bg-transparent outline-hidden text-right"
							bind:value={config.engine}
							placeholder={$i18n.t('Select Engine')}
							on:change={async () => {
								updateConfigHandler();
							}}
						>
							<option value="openai">{$i18n.t('Default (Open AI)')}</option>
							<option value="comfyui">{$i18n.t('ComfyUI')}</option>
							<option value="automatic1111">{$i18n.t('Automatic1111')}</option>
							<option value="gemini">{$i18n.t('Gemini')}</option>
						</select>
					</div>
				</div>
			</div>
			<hr class=" border-gray-100 dark:border-gray-850" />

			<div class="flex flex-col gap-2">
				{#if (config?.engine ?? 'automatic1111') === 'automatic1111'}
					<div>
						<div class=" mb-2 text-sm font-medium">{$i18n.t('AUTOMATIC1111 Base URL')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<input
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
									placeholder={$i18n.t('Enter URL (e.g. http://127.0.0.1:7860/)')}
									bind:value={config.automatic1111.AUTOMATIC1111_BASE_URL}
								/>
							</div>
							<button
								class="px-2.5 bg-gray-50 hover:bg-gray-100 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-100 rounded-lg transition"
								type="button"
								on:click={async () => {
									await updateConfigHandler();
									const res = await verifyConfigUrl(localStorage.token).catch((error) => {
										toast.error(`${error}`);
										return null;
									});

									if (res) {
										toast.success($i18n.t('Server connection verified'));
									}
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-4 h-4"
								>
									<path
										fill-rule="evenodd"
										d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>
						</div>

						<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Include `--api` flag when running stable-diffusion-webui')}
							<a
								class=" text-gray-300 font-medium"
								href="https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/3734"
								target="_blank"
							>
								{$i18n.t('(e.g. `sh webui.sh --api`)')}
							</a>
						</div>
					</div>

					<div>
						<div class=" mb-2 text-sm font-medium">
							{$i18n.t('AUTOMATIC1111 Api Auth String')}
						</div>
						<SensitiveInput
							placeholder={$i18n.t('Enter api auth string (e.g. username:password)')}
							bind:value={config.automatic1111.AUTOMATIC1111_API_AUTH}
							required={false}
						/>

						<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Include `--api-auth` flag when running stable-diffusion-webui')}
							<a
								class=" text-gray-300 font-medium"
								href="https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/13993"
								target="_blank"
							>
								{$i18n
									.t('(e.g. `sh webui.sh --api --api-auth username_password`)')
									.replace('_', ':')}
							</a>
						</div>
					</div>

					<!---Sampler-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Sampler')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Enter Sampler (e.g. Euler a)')} placement="top-start">
									<input
										list="sampler-list"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Enter Sampler (e.g. Euler a)')}
										bind:value={config.automatic1111.AUTOMATIC1111_SAMPLER}
									/>

									<datalist id="sampler-list">
										{#each samplers ?? [] as sampler}
											<option value={sampler}>{sampler}</option>
										{/each}
									</datalist>
								</Tooltip>
							</div>
						</div>
					</div>
					<!---Scheduler-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Scheduler')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Enter Scheduler (e.g. Karras)')} placement="top-start">
									<input
										list="scheduler-list"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Enter Scheduler (e.g. Karras)')}
										bind:value={config.automatic1111.AUTOMATIC1111_SCHEDULER}
									/>

									<datalist id="scheduler-list">
										{#each schedulers ?? [] as scheduler}
											<option value={scheduler}>{scheduler}</option>
										{/each}
									</datalist>
								</Tooltip>
							</div>
						</div>
					</div>
					<!---CFG scale-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set CFG Scale')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Enter CFG Scale (e.g. 7.0)')} placement="top-start">
									<input
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Enter CFG Scale (e.g. 7.0)')}
										bind:value={config.automatic1111.AUTOMATIC1111_CFG_SCALE}
									/>
								</Tooltip>
							</div>
						</div>
					</div>

					<!---Seed-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Seed')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Enter Seed (-1 for random)')} placement="top-start">
									<input
										type="number"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Enter Seed (-1 for random)')}
										bind:value={config.automatic1111.AUTOMATIC1111_SEED}
									/>
								</Tooltip>
							</div>
						</div>
					</div>

					<!---CLIP Skip-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set CLIP Skip')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Enter CLIP Skip (e.g. 1, 2)')} placement="top-start">
									<input
										type="number"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Enter CLIP Skip (e.g. 1, 2)')}
										bind:value={config.automatic1111.AUTOMATIC1111_CLIP_SKIP}
									/>
								</Tooltip>
							</div>
						</div>
					</div>

					<!---VAE-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set VAE')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Select VAE model')} placement="top-start">
									<input
										list="vae-list"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Select VAE model')}
										bind:value={config.automatic1111.AUTOMATIC1111_VAE}
									/>

									<datalist id="vae-list">
										{#each sdVaes ?? [] as vae}
											<option value={vae}>{vae}</option>
										{/each}
									</datalist>
								</Tooltip>
							</div>
						</div>
					</div>

					<!---Batch Count-->
					<div>
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Batch Count')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Number of batches to generate')} placement="top-start">
									<input
										type="number"
										min="1"
										max="16"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Enter Batch Count (e.g. 1)')}
										bind:value={config.automatic1111.AUTOMATIC1111_BATCH_COUNT}
									/>
								</Tooltip>
							</div>
						</div>
					</div>

					<!---Hires Fix Settings-->
					<div class="border dark:border-gray-850 rounded-lg p-3 mt-2">
						<div class=" py-1 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Enable Hires Fix')}</div>
							<div class="px-1">
								<Switch bind:state={config.automatic1111.AUTOMATIC1111_ENABLE_HR} />
							</div>
						</div>

						{#if config.automatic1111.AUTOMATIC1111_ENABLE_HR}
							<div class="mt-2 space-y-2">
								<div>
									<div class=" mb-1 text-xs">{$i18n.t('HR Scale')}</div>
									<input
										type="number"
										step="0.1"
										min="1"
										max="4"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										bind:value={config.automatic1111.AUTOMATIC1111_HR_SCALE}
									/>
								</div>
								<div>
									<div class=" mb-1 text-xs">{$i18n.t('HR Upscaler')}</div>
									<input
										list="upscaler-list"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										bind:value={config.automatic1111.AUTOMATIC1111_HR_UPSCALER}
									/>

									<datalist id="upscaler-list">
										{#each sdUpscalers ?? ['Latent', 'Latent (nearest)', 'Latent (nearest-exact)', 'None', 'Lanczos', 'Nearest'] as upscaler}
											<option value={upscaler}>{upscaler}</option>
										{/each}
									</datalist>
								</div>
								<div>
									<div class=" mb-1 text-xs">{$i18n.t('Denoising Strength')}</div>
									<input
										type="number"
										step="0.05"
										min="0"
										max="1"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										bind:value={config.automatic1111.AUTOMATIC1111_DENOISING_STRENGTH}
									/>
								</div>
							</div>
						{/if}
					</div>

					<!---Additional Options-->
					<div class="mt-2 space-y-1">
						<div class=" py-1 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Restore Faces')}</div>
							<div class="px-1">
								<Switch bind:state={config.automatic1111.AUTOMATIC1111_RESTORE_FACES} />
							</div>
						</div>

						<div class=" py-1 flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{$i18n.t('Tiling')}</div>
							<div class="px-1">
								<Switch bind:state={config.automatic1111.AUTOMATIC1111_TILING} />
							</div>
						</div>
					</div>

					<!---LoRA Configuration-->
					<div class="border dark:border-gray-850 rounded-lg p-3 mt-2">
						<div class="flex justify-between items-center mb-2">
							<div class="text-sm font-medium">{$i18n.t('LoRA Configuration')}</div>
							<div class="flex gap-1">
								<button
									type="button"
									class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 rounded"
									on:click={handleRefreshLoras}
								>
									{$i18n.t('Refresh')}
								</button>
								<button
									type="button"
									class="px-2 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded"
									on:click={addLora}
								>
									{$i18n.t('Add LoRA')}
								</button>
							</div>
						</div>

						{#each selectedLoras as lora, index}
							<div class="flex gap-2 mb-2 items-center">
								<div class="flex-1">
									<input
										list="lora-list"
										class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Select LoRA')}
										bind:value={lora.name}
									/>
								</div>
								<div class="w-20">
									<input
										type="number"
										step="0.1"
										min="0"
										max="2"
										class="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder="Weight"
										bind:value={lora.weight}
									/>
								</div>
								<button
									type="button"
									class="p-2 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/20 rounded"
									on:click={() => removeLora(index)}
								>
									<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
										<path fill-rule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clip-rule="evenodd" />
									</svg>
								</button>
							</div>
						{/each}

						<datalist id="lora-list">
							{#each sdLoras ?? [] as lora}
								<option value={lora.name}>{lora.alias || lora.name}</option>
							{/each}
						</datalist>

						{#if selectedLoras.length === 0}
							<div class="text-xs text-gray-500 text-center py-2">
								{$i18n.t('No LoRAs configured. Click "Add LoRA" to add one.')}
							</div>
						{/if}
					</div>

					<!---Prompt Generation Model-->
					<div class="mt-2">
						<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Prompt Generation Model')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<Tooltip content={$i18n.t('Select Ollama model for prompt generation')} placement="top-start">
									<input
										list="ollama-model-list"
										class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
										placeholder={$i18n.t('Select Ollama model')}
										bind:value={config.automatic1111.AUTOMATIC1111_PROMPT_GENERATION_MODEL}
									/>

									<datalist id="ollama-model-list">
										{#each ollamaModels?.models ?? [] as model}
											<option value={model.name}>{model.name}</option>
										{/each}
									</datalist>
								</Tooltip>
							</div>
						</div>
						<div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Used for generating optimized prompts from user descriptions')}
						</div>
					</div>

					<!---Optimize Settings-->
					<div class="border dark:border-gray-850 rounded-lg p-3 mt-2">
						<div class="text-sm font-medium mb-2">{$i18n.t('Optimize Settings')}</div>
						<div class="text-xs text-gray-500 mb-3">
							{$i18n.t('Enter a test prompt to get AI-optimized settings for that content type')}
						</div>

						<div class="flex gap-2 mb-3">
							<input
								class="flex-1 rounded-lg py-2 px-3 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								placeholder={$i18n.t('Enter test prompt (e.g. portrait of a woman, anime character, landscape)')}
								bind:value={testPrompt}
							/>
							<button
								type="button"
								class="px-3 py-2 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center gap-1 {optimizing ? 'opacity-50 cursor-not-allowed' : ''}"
								on:click={handleOptimizeSettings}
								disabled={optimizing}
							>
								{#if optimizing}
									<svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
										<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
										<path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" class="opacity-75"/>
									</svg>
								{:else}
									<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
										<path fill-rule="evenodd" d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z" clip-rule="evenodd" />
									</svg>
								{/if}
								{$i18n.t('Optimize')}
							</button>
						</div>

						{#if optimizeResult}
							<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-xs space-y-2">
								<div class="font-medium text-sm mb-2">{$i18n.t('Optimized Settings')}</div>

								<div class="grid grid-cols-2 gap-2">
									<div><span class="text-gray-500">Sampler:</span> {optimizeResult.sampler_name}</div>
									<div><span class="text-gray-500">Scheduler:</span> {optimizeResult.scheduler}</div>
									<div><span class="text-gray-500">Steps:</span> {optimizeResult.steps}</div>
									<div><span class="text-gray-500">CFG Scale:</span> {optimizeResult.cfg_scale}</div>
									<div><span class="text-gray-500">Size:</span> {optimizeResult.width}x{optimizeResult.height}</div>
									<div><span class="text-gray-500">CLIP Skip:</span> {optimizeResult.clip_skip}</div>
									<div><span class="text-gray-500">Hires Fix:</span> {optimizeResult.enable_hr ? 'Yes' : 'No'}</div>
									<div><span class="text-gray-500">Restore Faces:</span> {optimizeResult.restore_faces ? 'Yes' : 'No'}</div>
								</div>

								{#if optimizeResult.reasoning}
									<div class="mt-2 pt-2 border-t dark:border-gray-800">
										<span class="text-gray-500">{$i18n.t('Reasoning')}:</span> {optimizeResult.reasoning}
									</div>
								{/if}

								<div class="mt-3 flex gap-2">
									<button
										type="button"
										class="px-3 py-1.5 text-xs bg-green-500 hover:bg-green-600 text-white rounded"
										on:click={applyOptimizedSettings}
									>
										{$i18n.t('Apply Settings')}
									</button>
									<button
										type="button"
										class="px-3 py-1.5 text-xs bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded"
										on:click={() => optimizeResult = null}
									>
										{$i18n.t('Dismiss')}
									</button>
								</div>
							</div>
						{/if}
					</div>
				{:else if config?.engine === 'comfyui'}
					<div class="">
						<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI Base URL')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<input
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
									placeholder={$i18n.t('Enter URL (e.g. http://127.0.0.1:7860/)')}
									bind:value={config.comfyui.COMFYUI_BASE_URL}
								/>
							</div>
							<button
								class="px-2.5 bg-gray-50 hover:bg-gray-100 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-100 rounded-lg transition"
								type="button"
								on:click={async () => {
									await updateConfigHandler();
									const res = await verifyConfigUrl(localStorage.token).catch((error) => {
										toast.error(`${error}`);
										return null;
									});

									if (res) {
										toast.success($i18n.t('Server connection verified'));
									}
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-4 h-4"
								>
									<path
										fill-rule="evenodd"
										d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>
						</div>
					</div>

					<div class="">
						<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI API Key')}</div>
						<div class="flex w-full">
							<div class="flex-1 mr-2">
								<SensitiveInput
									placeholder={$i18n.t('sk-1234')}
									bind:value={config.comfyui.COMFYUI_API_KEY}
									required={false}
								/>
							</div>
						</div>
					</div>

					<div class="">
						<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI Workflow')}</div>

						{#if config.comfyui.COMFYUI_WORKFLOW}
							<textarea
								class="w-full rounded-lg mb-1 py-2 px-4 text-xs bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden disabled:text-gray-600 resize-none"
								rows="10"
								bind:value={config.comfyui.COMFYUI_WORKFLOW}
								required
							/>
						{/if}

						<div class="flex w-full">
							<div class="flex-1">
								<input
									id="upload-comfyui-workflow-input"
									hidden
									type="file"
									accept=".json"
									on:change={(e) => {
										const file = e.target.files[0];
										const reader = new FileReader();

										reader.onload = (e) => {
											config.comfyui.COMFYUI_WORKFLOW = e.target.result;
											e.target.value = null;
										};

										reader.readAsText(file);
									}}
								/>

								<button
									class="w-full text-sm font-medium py-2 bg-transparent hover:bg-gray-100 border border-dashed dark:border-gray-850 dark:hover:bg-gray-850 text-center rounded-xl"
									type="button"
									on:click={() => {
										document.getElementById('upload-comfyui-workflow-input')?.click();
									}}
								>
									{$i18n.t('Click here to upload a workflow.json file.')}
								</button>
							</div>
						</div>

						<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Make sure to export a workflow.json file as API format from ComfyUI.')}
						</div>
					</div>

					{#if config.comfyui.COMFYUI_WORKFLOW}
						<div class="">
							<div class=" mb-2 text-sm font-medium">{$i18n.t('ComfyUI Workflow Nodes')}</div>

							<div class="text-xs flex flex-col gap-1.5">
								{#each requiredWorkflowNodes as node}
									<div class="flex w-full items-center border dark:border-gray-850 rounded-lg">
										<div class="shrink-0">
											<div
												class=" capitalize line-clamp-1 font-medium px-3 py-1 w-20 text-center rounded-l-lg bg-green-500/10 text-green-700 dark:text-green-200"
											>
												{node.type}{node.type === 'prompt' ? '*' : ''}
											</div>
										</div>
										<div class="">
											<Tooltip content="Input Key (e.g. text, unet_name, steps)">
												<input
													class="py-1 px-3 w-24 text-xs text-center bg-transparent outline-hidden border-r dark:border-gray-850"
													placeholder="Key"
													bind:value={node.key}
													required
												/>
											</Tooltip>
										</div>

										<div class="w-full">
											<Tooltip
												content="Comma separated Node Ids (e.g. 1 or 1,2)"
												placement="top-start"
											>
												<input
													class="w-full py-1 px-4 rounded-r-lg text-xs bg-transparent outline-hidden"
													placeholder="Node Ids"
													bind:value={node.node_ids}
												/>
											</Tooltip>
										</div>
									</div>
								{/each}
							</div>

							<div class="mt-2 text-xs text-right text-gray-400 dark:text-gray-500">
								{$i18n.t('*Prompt node ID(s) are required for image generation')}
							</div>
						</div>
					{/if}
				{:else if config?.engine === 'openai'}
					<div>
						<div class=" mb-1.5 text-sm font-medium">{$i18n.t('OpenAI API Config')}</div>

						<div class="flex gap-2 mb-1">
							<input
								class="flex-1 w-full text-sm bg-transparent outline-hidden"
								placeholder={$i18n.t('API Base URL')}
								bind:value={config.openai.OPENAI_API_BASE_URL}
								required
							/>

							<SensitiveInput
								placeholder={$i18n.t('API Key')}
								bind:value={config.openai.OPENAI_API_KEY}
							/>
						</div>
					</div>
				{:else if config?.engine === 'gemini'}
					<div>
						<div class=" mb-1.5 text-sm font-medium">{$i18n.t('Gemini API Config')}</div>

						<div class="flex gap-2 mb-1">
							<input
								class="flex-1 w-full text-sm bg-transparent outline-none"
								placeholder={$i18n.t('API Base URL')}
								bind:value={config.gemini.GEMINI_API_BASE_URL}
								required
							/>

							<SensitiveInput
								placeholder={$i18n.t('API Key')}
								bind:value={config.gemini.GEMINI_API_KEY}
							/>
						</div>
					</div>
				{/if}
			</div>

			{#if config?.enabled}
				<hr class=" border-gray-100 dark:border-gray-850" />

				<div>
					<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Default Model')}</div>
					<div class="flex w-full">
						<div class="flex-1 mr-2">
							<div class="flex w-full">
								<div class="flex-1">
									<Tooltip content={$i18n.t('Enter Model ID')} placement="top-start">
										<input
											list="model-list"
											class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
											bind:value={imageGenerationConfig.MODEL}
											placeholder="Select a model"
											required
										/>

										<datalist id="model-list">
											{#each models ?? [] as model}
												<option value={model.id}>{model.name}</option>
											{/each}
										</datalist>
									</Tooltip>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div>
					<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Image Size')}</div>
					<div class="flex w-full">
						<div class="flex-1 mr-2">
							<Tooltip content={$i18n.t('Enter Image Size (e.g. 512x512)')} placement="top-start">
								<input
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
									placeholder={$i18n.t('Enter Image Size (e.g. 512x512)')}
									bind:value={imageGenerationConfig.IMAGE_SIZE}
									required
								/>
							</Tooltip>
						</div>
					</div>
				</div>

				<div>
					<div class=" mb-2.5 text-sm font-medium">{$i18n.t('Set Steps')}</div>
					<div class="flex w-full">
						<div class="flex-1 mr-2">
							<Tooltip content={$i18n.t('Enter Number of Steps (e.g. 50)')} placement="top-start">
								<input
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden"
									placeholder={$i18n.t('Enter Number of Steps (e.g. 50)')}
									bind:value={imageGenerationConfig.IMAGE_STEPS}
									required
								/>
							</Tooltip>
						</div>
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex flex-row space-x-1 items-center {loading
				? ' cursor-not-allowed'
				: ''}"
			type="submit"
			disabled={loading}
		>
			{$i18n.t('Save')}

			{#if loading}
				<div class="ml-2 self-center">
					<svg
						class=" w-4 h-4"
						viewBox="0 0 24 24"
						fill="currentColor"
						xmlns="http://www.w3.org/2000/svg"
						><style>
							.spinner_ajPY {
								transform-origin: center;
								animation: spinner_AtaB 0.75s infinite linear;
							}
							@keyframes spinner_AtaB {
								100% {
									transform: rotate(360deg);
								}
							}
						</style><path
							d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z"
							opacity=".25"
						/><path
							d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
							class="spinner_ajPY"
						/></svg
					>
				</div>
			{/if}
		</button>
	</div>
</form>
