import React, { useEffect, useState } from 'react';
import { ListOrdered, RefreshCw, Filter, ShieldCheck } from 'lucide-react';
import { auditApi } from '../api/auditApi';
import { AuditLogEntry } from '../types';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [eventNameFilter, setEventNameFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await auditApi.getLogs(eventNameFilter || undefined, actorFilter || undefined);
      setLogs(data || []);
    } catch (err) {
      // Error handling
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [eventNameFilter, actorFilter]);

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="glass-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.25)' }}>
            <ListOrdered className="w-5 h-5 text-yellow-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">System Audit Stream</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Immutable, real-time audit trail recording every agent action and security gate interception
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="btn-ghost"
            style={{ padding: '8px 14px', fontSize: '12px' }}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Audit Logs</span>
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left dark-table">
            <thead>
              <tr>
                <th className="p-4">Timestamp</th>
                <th className="p-4">Event Name</th>
                <th className="p-4">Actor / Agent</th>
                <th className="p-4">Tool Target</th>
                <th className="p-4">ML Score</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Decision</th>
                <th className="p-4">Envelope Token</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[11px]">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-12 text-center text-slate-500 font-sans">
                    <ShieldCheck className="w-10 h-10 mx-auto mb-3 opacity-50" />
                    No audit log entries recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log, idx) => {
                  const p = log.payload || {};
                  const decision = p.decision || 'ALLOW';

                  return (
                    <tr key={log.id || idx}>
                      <td className="p-4 text-slate-500">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td className="p-4 font-bold text-white">
                        {log.event_name}
                      </td>
                      <td className="p-4 text-blue-300 font-medium">
                        {log.actor}
                      </td>
                      <td className="p-4 text-slate-400">
                        {p.tool_name || '--'}
                      </td>
                      <td className="p-4 font-bold text-red-400">
                        {p.threat_score !== undefined ? Number(p.threat_score).toFixed(4) : '--'}
                      </td>
                      <td className="p-4 font-bold text-red-400">
                        {p.risk_score !== undefined ? Number(p.risk_score).toFixed(4) : '--'}
                      </td>
                      <td className="p-4 font-sans">
                        <span className={decision === 'ALLOW' ? 'badge-allow' : decision === 'REVIEW' ? 'badge-review' : 'badge-block'}>
                          {decision}
                        </span>
                      </td>
                      <td className="p-4 text-purple-400 truncate max-w-[120px]" title={p.envelope_token}>
                        {p.envelope_token || '--'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
