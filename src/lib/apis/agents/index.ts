import { WEBUI_API_BASE_URL } from '$lib/constants';

// Types
export type AgentStatus =
	| 'idle'
	| 'planning'
	| 'executing'
	| 'reviewing'
	| 'completed'
	| 'failed'
	| 'paused';

export type AgentTaskType =
	| 'game_design'
	| 'image_generation'
	| 'logic_development'
	| 'full_development';

export interface AgentModel {
	id: string;
	user_id: string;
	chat_id?: string;
	name: string;
	description?: string;
	task_type: AgentTaskType;
	status: AgentStatus;
	user_request: string;
	context: Record<string, any>;
	plan: Record<string, any>;
	execution_history: Array<any>;
	current_step?: string;
	artifacts: Record<string, any>;
	created_at: number;
	updated_at: number;
	completed_at?: number;
}

export interface AgentCreateForm {
	name: string;
	description?: string;
	task_type: AgentTaskType;
	user_request: string;
	context?: Record<string, any>;
	chat_id?: string;
}

export interface AgentUpdateForm {
	name?: string;
	description?: string;
	status?: AgentStatus;
	plan?: Record<string, any>;
	execution_history?: Array<any>;
	current_step?: string;
	artifacts?: Record<string, any>;
}

// Quick Actions
export interface QuickGameDesignForm {
	game_concept: string;
	genre?: string;
	target_platform?: string;
	chat_id?: string;
}

export interface QuickImageGenerationForm {
	description: string;
	style?: string;
	count?: number;
	chat_id?: string;
}

export interface QuickFullDevelopmentForm {
	game_concept: string;
	genre?: string;
	target_platform?: string;
	art_style?: string;
	chat_id?: string;
}

/**
 * Get all agents for the current user
 */
export const getAgents = async (
	token: string,
	skip: number = 0,
	limit: number = 50
): Promise<AgentModel[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/?skip=${skip}&limit=${limit}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Get a specific agent by ID
 */
export const getAgentById = async (token: string, agentId: string): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Get agents by chat ID
 */
export const getAgentsByChatId = async (
	token: string,
	chatId: string
): Promise<AgentModel[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/chat/${chatId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Create a new agent
 */
export const createAgent = async (
	token: string,
	form: AgentCreateForm
): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(form)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Update an agent
 */
export const updateAgent = async (
	token: string,
	agentId: string,
	form: AgentUpdateForm
): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(form)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Delete an agent
 */
export const deleteAgent = async (token: string, agentId: string): Promise<boolean> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res?.success || false;
};

/**
 * Pause an agent
 */
export const pauseAgent = async (token: string, agentId: string): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}/pause`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Resume an agent
 */
export const resumeAgent = async (token: string, agentId: string): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}/resume`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Retry a failed agent
 */
export const retryAgent = async (token: string, agentId: string): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}/retry`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Quick Actions

/**
 * Quick game design creation
 */
export const quickGameDesign = async (
	token: string,
	form: QuickGameDesignForm
): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/quick/game-design`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(form)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Quick image generation
 */
export const quickImageGeneration = async (
	token: string,
	form: QuickImageGenerationForm
): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/quick/image-generation`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(form)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Quick full game development
 */
export const quickFullDevelopment = async (
	token: string,
	form: QuickFullDevelopmentForm
): Promise<AgentModel> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/quick/full-development`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(form)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Generate random game idea using LLM
 */
export interface RandomGameIdea {
	game_concept: string;
	genre: string;
	target_platform: string;
}

export const generateRandomGameIdea = async (token: string): Promise<RandomGameIdea> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/random-idea`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
