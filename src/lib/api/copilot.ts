import { apiClient } from './client';

export type CopilotRole = 'user' | 'assistant' | 'system';
export type CopilotPlanStatus = 'PLANNED' | 'EXECUTING' | 'COMPLETED' | 'PARTIAL' | 'FAILED';
export type CopilotToolStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface StructuredCopilotResponse {
  summary: string;
  findings: string[];
  decision_context: Record<string, any>;
  evidence: Array<{
    dimension: string;
    source: string;
    status: string;
    metric: string;
  }>;
  risks: Array<{
    type: string;
    severity: string;
    active_count?: number;
    cost_usd?: number;
    description: string;
  }>;
  economics: {
    total_voyage_cost_usd: number;
    cost_per_mt: number;
    freight_cost_usd?: number;
    bunker_cost_usd?: number;
    port_dues_usd?: number;
    time_charter_usd?: number;
    delay_exposure_usd?: number;
    repositioning_usd?: number;
  };
  assumptions: string[];
  uncertainties: string[];
  data_quality: {
    overall_status: string;
    confidence_score: number;
    provenance_verified: boolean;
  };
  actions: Array<{
    label: string;
    route: string;
  }>;
}

export interface CopilotMessage {
  id: string;
  session_id: string;
  role: CopilotRole;
  content: string;
  structured_response?: StructuredCopilotResponse;
  plan_id?: string;
  created_at?: string;
}

export interface CopilotSession {
  id: string;
  title: string;
  cargo_request_id?: string;
  vessel_id?: string;
  voyage_id?: string;
  context_data?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  message_count?: number;
  cargo_requirement?: {
    title: string;
    quantity_mt: number;
    cargo_type: string;
  };
  vessel?: {
    name: string;
    vessel_class: string;
  };
}

export interface CopilotPlanStep {
  step_number: number;
  tool_name: string;
  reason: string;
  arguments: Record<string, any>;
  status: CopilotToolStatus;
}

export interface CopilotPlan {
  id: string;
  session_id: string;
  user_goal: string;
  status: CopilotPlanStatus;
  steps: CopilotPlanStep[];
  created_at?: string;
  completed_at?: string;
}

export interface ToolTraceItem {
  id: string;
  tool_name: string;
  arguments: Record<string, any>;
  status: CopilotToolStatus;
  execution_time_ms: number;
  source: string;
  data_status: string;
  result?: any;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface SessionTrace {
  session_id: string;
  title: string;
  total_tools_executed: number;
  total_execution_time_ms: number;
  latest_plan?: CopilotPlan;
  tools_trace: Array<{
    tool_name: string;
    status: string;
    execution_time_ms: number;
    source: string;
    data_status: string;
    error?: string;
  }>;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  stream?: boolean;
  cargo_request_id?: string;
  vessel_id?: string;
  voyage_id?: string;
  scenario_preset?: string;
}

export const copilotApi = {
  getSessions: async (limit = 50): Promise<CopilotSession[]> => {
    return apiClient<CopilotSession[]>(`/copilot/sessions?limit=${limit}`);
  },

  getSession: async (id: string): Promise<CopilotSession> => {
    return apiClient<CopilotSession>(`/copilot/sessions/${id}`);
  },

  getMessages: async (sessionId: string): Promise<CopilotMessage[]> => {
    return apiClient<CopilotMessage[]>(`/copilot/sessions/${sessionId}/messages`);
  },

  getTools: async (sessionId: string): Promise<ToolTraceItem[]> => {
    return apiClient<ToolTraceItem[]>(`/copilot/sessions/${sessionId}/tools`);
  },

  getTrace: async (sessionId: string): Promise<SessionTrace> => {
    return apiClient<SessionTrace>(`/copilot/sessions/${sessionId}/trace`);
  },

  previewPlan: async (query: string, sessionId?: string): Promise<{ query: string; steps: CopilotPlanStep[]; total_tools: number }> => {
    return apiClient(`/copilot/plan`, {
      method: 'POST',
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  },

  chatSync: async (req: ChatRequest): Promise<any> => {
    return apiClient(`/copilot/chat`, {
      method: 'POST',
      body: JSON.stringify({ ...req, stream: false }),
    });
  },

  chatStream: async (
    req: ChatRequest,
    onStep: (step: any) => void,
    onMessage: (data: any) => void,
    onError: (err: any) => void,
    onDone: () => void
  ) => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
    try {
      const response = await fetch(`${API_BASE_URL}/copilot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ ...req, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;
          const matchEvent = block.match(/event:\s*([^\n]+)/);
          const matchData = block.match(/data:\s*([^\n]+)/);

          const eventType = matchEvent ? matchEvent[1].trim() : 'message';
          const rawData = matchData ? matchData[1].trim() : '';

          if (!rawData) continue;

          try {
            const parsed = JSON.parse(rawData);
            if (eventType === 'step') {
              onStep(parsed);
            } else if (eventType === 'message') {
              onMessage(parsed);
            } else if (eventType === 'error') {
              onError(parsed);
            } else if (eventType === 'done') {
              onDone();
            }
          } catch (e) {
            console.error('Failed to parse SSE payload:', rawData, e);
          }
        }
      }
      onDone();
    } catch (err) {
      onError(err);
    }
  },
};
