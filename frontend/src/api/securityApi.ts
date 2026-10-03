import { apiFetch } from './client';
import { MLStatusInfo, MLPredictResponse } from '../types';

export const securityApi = {
  getMLStatus: (): Promise<MLStatusInfo> => {
    return apiFetch<MLStatusInfo>('/ml/status');
  },

  predictThreat: (payload: string): Promise<MLPredictResponse> => {
    return apiFetch<MLPredictResponse>('/ml/predict', {
      method: 'POST',
      body: JSON.stringify({ payload }),
    });
  },

  evaluatePolicy: (role: string, toolName: string, payload: string, sessionId?: string) => {
    return apiFetch('/policy/evaluate', {
      method: 'POST',
      body: JSON.stringify({
        role,
        tool_name: toolName,
        payload,
        session_id: sessionId || '',
      }),
    });
  },

  interceptToolCall: (sessionId: string, agentId: string, toolName: string, payload: any) => {
    return apiFetch('/proxy/intercept', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        agent_id: agentId,
        tool_name: toolName,
        payload,
      }),
    });
  },
};
