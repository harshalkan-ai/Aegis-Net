import { apiFetch } from './client';
import { IncidentRecord, ForensicReport, IncidentStatus } from '../types';

export const incidentApi = {
  listIncidents: (statusFilter?: string, limit = 50, offset = 0): Promise<{ incidents: IncidentRecord[]; count: number }> => {
    let url = `/incidents?limit=${limit}&offset=${offset}`;
    if (statusFilter && statusFilter !== 'ALL') {
      url += `&status=${encodeURIComponent(statusFilter)}`;
    }
    return apiFetch<{ incidents: IncidentRecord[]; count: number }>(url);
  },

  getIncident: (incidentId: string): Promise<IncidentRecord> => {
    return apiFetch<IncidentRecord>(`/incidents/${incidentId}`);
  },

  updateStatus: (incidentId: string, newStatus: IncidentStatus) => {
    return apiFetch(`/incidents/${incidentId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ new_status: newStatus }),
    });
  },

  getForensics: (incidentId: string): Promise<ForensicReport> => {
    return apiFetch<ForensicReport>(`/forensics/${incidentId}`);
  },
};
