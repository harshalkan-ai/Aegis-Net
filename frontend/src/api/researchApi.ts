import { apiFetch } from './client';
import { ResearchSessionRecord } from '../types';

export const researchApi = {
  startResearch: (query: string, agentId = 'agent-researcher-01'): Promise<ResearchSessionRecord> => {
    return apiFetch<ResearchSessionRecord>('/research/start', {
      method: 'POST',
      body: JSON.stringify({ query, agent_id: agentId }),
    });
  },

  getSession: (sessionId: string): Promise<ResearchSessionRecord> => {
    return apiFetch<ResearchSessionRecord>(`/research/${sessionId}`);
  },

  testTavily: (): Promise<{ success: boolean; message: string; result_count: number }> => {
    return apiFetch<{ success: boolean; message: string; result_count: number }>('/tavily/test');
  },
};

