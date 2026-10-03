import { apiFetch } from './client';
import { SandboxStatusResponse } from '../types';

export const sandboxApi = {
  getSandbox: (sessionId: string): Promise<SandboxStatusResponse> => {
    return apiFetch<SandboxStatusResponse>(`/sandbox/${sessionId}`);
  },

  releaseQuarantine: (sessionId: string, agentId: string) => {
    return apiFetch('/containment/quarantine/release', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, agent_id: agentId }),
    });
  },

  tripCircuitBreaker: (sessionId: string, reason?: string) => {
    return apiFetch('/containment/circuit-breaker/trip', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, reason: reason || 'Manual user trip' }),
    });
  },

  resetCircuitBreaker: (sessionId: string) => {
    return apiFetch('/containment/circuit-breaker/reset', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    });
  },
};
