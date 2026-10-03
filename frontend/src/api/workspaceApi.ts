import { apiFetch } from './client';
import { WorkspaceTreeResponse, FileContentResponse, CoderRunResponse } from '../types';

export const workspaceApi = {
  getTree: (sessionId: string, path = '.'): Promise<WorkspaceTreeResponse> => {
    return apiFetch<WorkspaceTreeResponse>(`/workspace/${sessionId}/tree?path=${encodeURIComponent(path)}`);
  },

  getFileContent: (sessionId: string, path: string): Promise<FileContentResponse> => {
    return apiFetch<FileContentResponse>(`/workspace/${sessionId}/file?path=${encodeURIComponent(path)}`);
  },

  runCoder: (sessionId: string, inputQuery?: string, researchNotes?: string): Promise<CoderRunResponse> => {
    return apiFetch<CoderRunResponse>(`/workspace/${sessionId}/coder/run`, {
      method: 'POST',
      body: JSON.stringify({
        input_query: inputQuery,
        research_notes: researchNotes,
      }),
    });
  },
};
