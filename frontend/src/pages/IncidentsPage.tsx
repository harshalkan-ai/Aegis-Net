import React, { useEffect, useState } from 'react';
import {
  AlertOctagon, CheckCircle2, X, RefreshCw, Sparkles, Loader2,
  AlertTriangle, ChevronRight, ShieldAlert, Eye, Target, Zap,
  TrendingUp, Activity, Lock, Brain
} from 'lucide-react';
import { incidentApi } from '../api/incidentApi';
import { IncidentRecord, ForensicReport, IncidentStatus } from '../types';

interface IncidentsPageProps {
  incidents: IncidentRecord[];
  onRefreshIncidents: () => void;
  onShowRiskModal: (assessment: any) => void;
}

export const IncidentsPage: React.FC<IncidentsPageProps> = ({ incidents, onRefreshIncidents, onShowRiskModal }) => {
  const [filter, setFilter] = useState<string>('ALL');
  const [selectedIncident, setSelectedIncident] = useState<IncidentRecord | null>(null);
  const [forensicReport, setForensicReport] = useState<ForensicReport | null>(null);
  const [forensicLoading, setForensicLoading] = useState(false);
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredIncidents = incidents.filter((inc) => {
    if (filter === 'ALL') return true;
    return inc.status === filter;
  });

  const handleOpenIncident = async (inc: IncidentRecord) => {
    setSelectedIncident(inc);
    setForensicReport(null);
    setError(null);
    fetchForensics(inc.id);
  };

  const fetchForensics = async (incidentId: string) => {
    setForensicLoading(true);
    try {
      const report = await incidentApi.getForensics(incidentId);
      setForensicReport(report);
    } catch (err: any) {
      // Non-fatal — forensics may still be generating
    } finally {
      setForensicLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus: IncidentStatus) => {
    if (!selectedIncident) return;
    setStatusUpdateLoading(true);
    try {
      await incidentApi.updateStatus(selectedIncident.id, newStatus);
      setSelectedIncident({ ...selectedIncident, status: newStatus });
      onRefreshIncidents();
    } catch (err: any) {
      setError(`Status update failed: ${err.message}`);
    } finally {
      setStatusUpdateLoading(false);
    }
  };

  const SEVERITY_STYLES: Record<string, { bg: string; border: string; color: string }> = {
    CRITICAL: { bg: 'rgba(248,113,113,0.12)', border: 'rgba(248,113,113,0.3)', color: '#f87171' },
    HIGH:     { bg: 'rgba(251,146,60,0.1)',   border: 'rgba(251,146,60,0.25)',  color: '#fb923c' },
    MEDIUM:   { bg: 'rgba(251,191,36,0.1)',   border: 'rgba(251,191,36,0.25)', color: '#fbbf24' },
    LOW:      { bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.2)', color: '#94a3b8' },
  };

  const STATUS_STYLES: Record<string, string> = {
    OPEN:          'bg-red-500/10 text-red-400 border-red-500/20',
    INVESTIGATING: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    RESOLVED:      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    FALSE_POSITIVE:'bg-slate-500/10 text-slate-400 border-slate-500/20',
  };

  const CONFIDENCE_COLOR = (c: number) => c >= 0.8 ? '#34d399' : c >= 0.5 ? '#fbbf24' : '#f87171';

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="glass-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(248,113,113,0.12)', border: '1px solid rgba(248,113,113,0.25)' }}>
              <AlertOctagon className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Security Incident Management</h1>
              <p className="text-xs text-slate-500">
                Auto-created from BLOCK/REVIEW gateway decisions · Gemini CISO forensic post-mortems
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex p-1 rounded-lg gap-1" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(99,148,255,0.1)' }}>
            {['ALL', 'OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE'].map((st) => (
              <button
                key={st}
                onClick={() => setFilter(st)}
                className="px-3 py-1.5 rounded-md text-xs font-medium transition"
                style={filter === st ? {
                  background: 'rgba(79,142,247,0.15)',
                  color: '#4f8ef7',
                  border: '1px solid rgba(79,142,247,0.25)',
                } : {
                  color: '#64748b',
                  border: '1px solid transparent',
                }}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            onClick={onRefreshIncidents}
            className="btn-ghost"
            style={{ padding: '8px 12px' }}
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: 'Total',         count: incidents.length,                                                color: '#94a3b8' },
          { label: 'Open',          count: incidents.filter(i => i.status === 'OPEN').length,          color: '#f87171' },
          { label: 'Investigating', count: incidents.filter(i => i.status === 'INVESTIGATING').length,  color: '#fbbf24' },
          { label: 'Resolved',      count: incidents.filter(i => i.status === 'RESOLVED').length,      color: '#34d399' },
          { label: 'Critical',      count: incidents.filter(i => i.severity === 'CRITICAL').length,    color: '#f97316' },
        ].map((s, i) => (
          <div key={i} className="metric-card" style={{ padding: '16px', borderColor: s.color + '20' }}>
            <div className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: s.color + '90' }}>{s.label}</div>
            <div className="text-2xl font-bold font-mono" style={{ color: s.color }}>{s.count}</div>
          </div>
        ))}
      </div>

      {/* Incidents Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left dark-table">
            <thead>
              <tr>
                <th className="p-4">Severity</th>
                <th className="p-4">Incident ID</th>
                <th className="p-4">Agent / Role</th>
                <th className="p-4">Target Tool</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Decision</th>
                <th className="p-4">Status</th>
                <th className="p-4">Created</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredIncidents.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-12 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <CheckCircle2 className="w-10 h-10 text-emerald-500 opacity-50" />
                      <p className="text-slate-500 text-sm">No security incidents recorded. System operating securely.</p>
                      <p className="text-xs text-slate-600">
                        Incidents are auto-created when the Security Gateway issues a BLOCK or REVIEW decision.
                        Use the Security tab to test payloads.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredIncidents.map((inc) => {
                  const sev = SEVERITY_STYLES[inc.severity] || SEVERITY_STYLES.LOW;
                  return (
                    <tr key={inc.id} className="hover:bg-white/[0.02] transition-colors cursor-pointer"
                      onClick={() => handleOpenIncident(inc)}>
                      <td className="p-4">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded"
                          style={{ background: sev.bg, border: `1px solid ${sev.border}`, color: sev.color }}>
                          {inc.severity}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-xs text-blue-300 font-semibold max-w-[120px] truncate">
                        {inc.id.substring(0, 16)}…
                      </td>
                      <td className="p-4">
                        <div className="text-sm text-slate-300 font-medium">{inc.agent_id}</div>
                        {inc.role && <div className="text-[10px] font-mono text-slate-600">{inc.role}</div>}
                      </td>
                      <td className="p-4 font-mono text-xs text-slate-500">{inc.tool_name || 'blocked_tool'}</td>
                      <td className="p-4 font-mono text-sm font-bold text-red-400">
                        {inc.risk_score ? inc.risk_score.toFixed(4) : '0.0000'}
                      </td>
                      <td className="p-4">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                          inc.decision === 'BLOCK' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                          inc.decision === 'REVIEW' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        }`}>
                          {inc.decision}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${STATUS_STYLES[inc.status] || STATUS_STYLES.OPEN}`}>
                          {inc.status}
                        </span>
                      </td>
                      <td className="p-4 text-xs text-slate-600 font-mono">
                        {new Date(inc.created_at).toLocaleTimeString()}
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleOpenIncident(inc); }}
                          className="btn-ghost"
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                        >
                          Inspect <ChevronRight className="w-3 h-3 inline" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(12px)' }}>
          <div className="rounded-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden"
            style={{
              background: 'rgba(8, 13, 25, 0.99)',
              border: '1px solid rgba(99,148,255,0.2)',
              boxShadow: '0 25px 80px rgba(0,0,0,0.9), 0 0 80px rgba(248,113,113,0.04)',
            }}>

            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 shrink-0"
              style={{ borderBottom: '1px solid rgba(99,148,255,0.1)' }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(248,113,113,0.12)', border: '1px solid rgba(248,113,113,0.25)' }}>
                  <ShieldAlert className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    INCIDENT #{selectedIncident.id.substring(0, 8).toUpperCase()}
                  </h3>
                  <p className="text-xs text-slate-500 font-mono">
                    Session: {selectedIncident.session_id?.substring(0, 20)}… · {new Date(selectedIncident.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="w-8 h-8 rounded-lg flex items-center justify-center transition"
                style={{ color: '#64748b', background: 'rgba(255,255,255,0.04)' }}
                onMouseEnter={e => (e.currentTarget.style.color = '#e2e8f0')}
                onMouseLeave={e => (e.currentTarget.style.color = '#64748b')}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5">

              {/* Risk Score Grid */}
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                {[
                  { label: 'Risk Score',    val: selectedIncident.risk_score?.toFixed(4),       color: '#f87171', icon: TrendingUp },
                  { label: 'Threat (ML)',   val: selectedIncident.threat_score?.toFixed(4) || '—', color: '#f97316', icon: Brain },
                  { label: 'Permission',   val: selectedIncident.permission_score?.toFixed(4) || '—', color: '#fbbf24', icon: Lock },
                  { label: 'Behavioral',   val: selectedIncident.behavioral_score?.toFixed(4) || '—', color: '#818cf8', icon: Activity },
                  { label: 'Sensitivity',  val: selectedIncident.sensitivity_score?.toFixed(4) || '—', color: '#34d399', icon: Eye },
                  { label: 'Criticality',  val: selectedIncident.criticality_score?.toFixed(4) || '—', color: '#4f8ef7', icon: Target },
                ].map((s, i) => {
                  const Icon = s.icon;
                  return (
                    <div key={i} className="p-3 rounded-xl text-center"
                      style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                      <Icon className="w-3 h-3 mx-auto mb-1" style={{ color: s.color }} />
                      <span className="text-[9px] text-slate-500 block mb-1 uppercase tracking-wider">{s.label}</span>
                      <span className="font-mono font-bold text-xs block" style={{ color: s.color }}>{s.val}</span>
                    </div>
                  );
                })}
              </div>

              {/* Agent + Decision + Tool Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Agent ID',    val: selectedIncident.agent_id,         color: '#4f8ef7' },
                  { label: 'Role',        val: selectedIncident.role || 'UNKNOWN', color: '#818cf8' },
                  { label: 'Target Tool', val: selectedIncident.tool_name || '—',  color: '#94a3b8', mono: true },
                  { label: 'Decision',    val: selectedIncident.decision,          color: selectedIncident.decision === 'BLOCK' ? '#f87171' : '#fbbf24' },
                ].map((s, i) => (
                  <div key={i} className="p-3 rounded-xl"
                    style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                    <span className="text-[10px] text-slate-500 block mb-1">{s.label}</span>
                    <span className={`font-bold text-sm block truncate ${s.mono ? 'font-mono' : ''}`} style={{ color: s.color }}>
                      {s.val}
                    </span>
                  </div>
                ))}
              </div>

              {/* Circuit Breaker badge */}
              {selectedIncident.circuit_breaker_triggered && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl"
                  style={{ background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.3)' }}>
                  <Zap className="w-4 h-4 text-red-400 shrink-0" />
                  <span className="text-xs font-bold text-red-400 uppercase tracking-wider">
                    ⚡ Circuit Breaker TRIGGERED — Agent session quarantined
                  </span>
                </div>
              )}

              {/* Block Justification */}
              {selectedIncident.reasons && selectedIncident.reasons.length > 0 && (
                <div className="p-4 rounded-xl"
                  style={{ background: 'rgba(248,113,113,0.06)', border: '1px solid rgba(248,113,113,0.2)' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    <strong className="text-xs font-bold text-red-400 uppercase tracking-wider">
                      {selectedIncident.decision} Justification
                    </strong>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono">
                    {selectedIncident.reasons.join(' | ')}
                  </p>
                </div>
              )}

              {/* Payload Preview */}
              {selectedIncident.payload_preview && (
                <div className="p-4 rounded-xl"
                  style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                  <span className="text-[10px] text-slate-500 block mb-1 uppercase tracking-wider">Intercepted Payload</span>
                  <p className="text-xs text-slate-400 font-mono leading-relaxed">{selectedIncident.payload_preview}</p>
                </div>
              )}

              {/* Gemini CISO Forensics Section */}
              <div className="p-5 rounded-xl space-y-4"
                style={{ background: 'rgba(79,142,247,0.04)', border: '1px solid rgba(79,142,247,0.2)' }}>
                <div className="flex items-center justify-between pb-3"
                  style={{ borderBottom: '1px solid rgba(79,142,247,0.12)' }}>
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-blue-400" />
                    <h4 className="font-bold text-white text-sm">Gemini CISO Automated Forensics</h4>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold"
                      style={{ background: 'rgba(79,142,247,0.1)', color: '#4f8ef7', border: '1px solid rgba(79,142,247,0.2)' }}>
                      7-SECTION ANALYSIS
                    </span>
                  </div>
                  {!forensicReport && !forensicLoading && (
                    <button
                      onClick={() => fetchForensics(selectedIncident.id)}
                      className="btn-primary"
                      style={{ padding: '6px 14px', fontSize: '12px' }}
                    >
                      ⚡ Run Gemini Forensics
                    </button>
                  )}
                </div>

                {forensicLoading ? (
                  <div className="py-6 text-center flex items-center justify-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                    <span className="text-sm text-slate-400">Gemini CISO compiling CVE post-mortem…</span>
                  </div>
                ) : forensicReport ? (
                  <div className="space-y-4">
                    {/* CWE + Vector + Confidence */}
                    <div className="grid grid-cols-3 gap-3 font-mono">
                      <div className="p-3 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(79,142,247,0.15)' }}>
                        <span className="text-[10px] text-slate-500 block mb-1">CWE Classification</span>
                        <span className="font-bold text-blue-400 text-sm">{forensicReport.cwe_id}</span>
                      </div>
                      <div className="p-3 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(79,142,247,0.15)' }}>
                        <span className="text-[10px] text-slate-500 block mb-1">Attack Vector</span>
                        <span className="font-bold text-white text-sm">{forensicReport.attack_vector}</span>
                      </div>
                      <div className="p-3 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(79,142,247,0.15)' }}>
                        <span className="text-[10px] text-slate-500 block mb-1">AI Confidence</span>
                        <span className="font-bold text-sm font-mono"
                          style={{ color: CONFIDENCE_COLOR(forensicReport.forensic_confidence) }}>
                          {(forensicReport.forensic_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Section 1: Incident Summary */}
                    {forensicReport.incident_summary && (
                      <Section label="1. Incident Summary" icon={AlertOctagon} color="#f87171">
                        <p className="text-xs text-slate-300 leading-relaxed">{forensicReport.incident_summary}</p>
                      </Section>
                    )}

                    {/* Section 2: Why suspicious */}
                    {forensicReport.suspicion_reasoning && (
                      <Section label="2. Why the Action Was Suspicious" icon={Eye} color="#fbbf24">
                        <p className="text-xs text-slate-300 leading-relaxed">{forensicReport.suspicion_reasoning}</p>
                      </Section>
                    )}

                    {/* Section 3: Threat Indicators */}
                    {forensicReport.threat_indicators && forensicReport.threat_indicators.length > 0 && (
                      <Section label="3. Attack / Threat Indicators" icon={Target} color="#f97316">
                        <ul className="space-y-1">
                          {forensicReport.threat_indicators.map((ind, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                              <span className="text-orange-400 mt-0.5 shrink-0">◆</span>
                              {ind}
                            </li>
                          ))}
                        </ul>
                      </Section>
                    )}

                    {/* Section 4: Behavioral Anomalies */}
                    {forensicReport.behavioral_anomalies && (
                      <Section label="4. Context & Behavioral Anomalies" icon={Activity} color="#818cf8">
                        <p className="text-xs text-slate-300 leading-relaxed">{forensicReport.behavioral_anomalies}</p>
                      </Section>
                    )}

                    {/* Section 5: Potential Impact */}
                    {forensicReport.potential_impact && (
                      <Section label="5. Potential Impact" icon={TrendingUp} color="#fb923c">
                        <p className="text-xs text-slate-300 leading-relaxed">{forensicReport.potential_impact}</p>
                      </Section>
                    )}

                    {/* Section 6: Recommended Response */}
                    {forensicReport.recommended_response && (
                      <Section label="6. Recommended Response" icon={ShieldAlert} color="#34d399">
                        <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                          {forensicReport.recommended_response}
                        </pre>
                      </Section>
                    )}

                    {/* Section 7: Confidence Notes */}
                    {forensicReport.confidence_notes && (
                      <Section label="7. Confidence & Uncertainty" icon={Brain} color="#94a3b8">
                        <p className="text-xs text-slate-400 leading-relaxed italic">{forensicReport.confidence_notes}</p>
                      </Section>
                    )}

                    {/* Fallback legacy display if new sections not populated */}
                    {!forensicReport.incident_summary && forensicReport.threat_summary && (
                      <div className="p-4 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(79,142,247,0.12)' }}>
                        <span className="text-xs font-bold text-slate-300 block mb-2">Threat Summary</span>
                        <p className="text-xs text-slate-400 leading-relaxed">{forensicReport.threat_summary}</p>
                      </div>
                    )}
                    {!forensicReport.recommended_response && forensicReport.suggested_patch && (
                      <div className="p-4 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(79,142,247,0.12)' }}>
                        <span className="text-xs font-bold text-slate-300 block mb-2">Recommended Patch & Mitigation</span>
                        <pre className="text-[11px] font-mono text-slate-400 whitespace-pre-wrap leading-relaxed">
                          {forensicReport.suggested_patch}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic py-4 text-center">
                    Click 'Run Gemini Forensics' to generate a full 7-section CVE post-mortem.
                  </p>
                )}
              </div>

              {error && (
                <div className="p-3 rounded text-xs text-red-400"
                  style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)' }}>
                  {error}
                </div>
              )}

              {/* Status Update Actions */}
              <div className="flex items-center justify-between pt-3"
                style={{ borderTop: '1px solid rgba(99,148,255,0.08)' }}>
                <span className="text-xs text-slate-500 font-medium">Update Status:</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleUpdateStatus('INVESTIGATING')}
                    disabled={statusUpdateLoading}
                    className="btn-ghost"
                    style={{ padding: '8px 14px', fontSize: '12px' }}
                  >
                    Investigate
                  </button>
                  <button
                    onClick={() => handleUpdateStatus('FALSE_POSITIVE')}
                    disabled={statusUpdateLoading}
                    className="btn-ghost"
                    style={{ padding: '8px 14px', fontSize: '12px' }}
                  >
                    False Positive
                  </button>
                  <button
                    onClick={() => handleUpdateStatus('RESOLVED')}
                    disabled={statusUpdateLoading}
                    className="btn-primary"
                    style={{ padding: '8px 14px', fontSize: '12px' }}
                  >
                    Mark Resolved
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper component for forensic sections
const Section: React.FC<{
  label: string;
  icon: React.FC<any>;
  color: string;
  children: React.ReactNode;
}> = ({ label, icon: Icon, color, children }) => (
  <div className="p-4 rounded-lg"
    style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
    <div className="flex items-center gap-2 mb-2">
      <Icon className="w-3.5 h-3.5 shrink-0" style={{ color }} />
      <span className="text-xs font-bold uppercase tracking-wider" style={{ color }}>{label}</span>
    </div>
    {children}
  </div>
);
