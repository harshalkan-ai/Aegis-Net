import { apiFetch } from './client';
import { DeployerRunResponse } from '../types';

export const deploymentApi = {
  runDeployer: (sessionId: string, generatedCode?: string, targetEnvironment = 'staging'): Promise<DeployerRunResponse> => {
    return apiFetch<DeployerRunResponse>(`/deployer/${sessionId}/run`, {
      method: 'POST',
      body: JSON.stringify({
        generated_code: generatedCode,
        target_environment: targetEnvironment,
      }),
    });
  },
};
