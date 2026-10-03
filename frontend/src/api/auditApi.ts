import { apiFetch } from './client';
import { AuditLogEntry } from '../types';

export const auditApi = {
  getLogs: (eventName?: string, actor?: string, limit = 50, offset = 0): Promise<AuditLogEntry[]> => {
    let url = `/audit/logs?limit=${limit}&offset=${offset}`;
    if (eventName) url += `&event_name=${encodeURIComponent(eventName)}`;
    if (actor) url += `&actor=${encodeURIComponent(actor)}`;
    return apiFetch<AuditLogEntry[]>(url);
  },
};
