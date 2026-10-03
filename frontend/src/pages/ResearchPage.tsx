import React, { useState } from 'react';
import { Search, Globe, Shield, ArrowRight, CheckCircle2, AlertTriangle, Cpu, Code, ExternalLink, Loader2, Zap, Lock } from 'lucide-react';
import { researchApi } from '../api/researchApi';
import { workspaceApi } from '../api/workspaceApi';
import { ResearchSessionRecord } from '../types';

interface ResearchPageProps {
  currentSession: ResearchSessionRecord | null;
  setCurrentSession: (session: ResearchSessionRecord | null) => void;
  onNavigateToWorkspace: () => void;
  onShowRiskModal: (assessment: any) => void;
  demoQuery?: string;
}

export const ResearchPage: React.FC<ResearchPageProps> = ({
  currentSession,
  setCurrentSession,
  onNavigateToWorkspace,
  onShowRiskModal,
  demoQuery = '',
}) => {
  const [query, setQuery] = useState(demoQuery || 'Research Python authentication best practices and prepare an implementation specification.');
  const [loading, setLoading] = useState(false);
  const [coderLoading, setCoderLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tavilyTesting, setTavilyTesting] = useState(false);
  const [tavilyStatus, setTavilyStatus] = useState<{ success: boolean; message: string; result_count: number } | null>(null);

  // Sync state if demoQuery changes
  React.useEffect(() => {
    if (demoQuery) {
      setQuery(demoQuery);
    }
  }, [demoQuery]);

  const handleTestTavily = async () => {
    setTavilyTesting(true);
    setTavilyStatus(null);
    try {
      const res = await researchApi.testTavily();
      setTavilyStatus(res);
    } catch (err: any) {
      setTavilyStatus({
        success: false,
        message: err.message || 'Tavily connection test failed',
        result_count: 0,
      });
    } finally {
      setTavilyTesting(false);
    }
  };

  const handleStartResearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const session = await researchApi.startResearch(query.trim());
      setCurrentSession(session);
    } catch (err: any) {
      setError(err.message || 'Failed to execute research query');
    } finally {
      setLoading(false);
    }
  };

  const handleSendToCoder = async () => {
    if (!currentSession) return;
    setCoderLoading(true);

    try {
      await workspaceApi.runCoder(
        currentSession.session_id,
        currentSession.query,
        currentSession.research_notes || ''
      );
      onNavigateToWorkspace();
    } catch (err: any) {
      setError(`Coder Execution Failed: ${err.message}`);
    } finally {
      setCoderLoading(false);
    }
  };

  const security = currentSession?.security;
  const riskAssessment = security?.risk_assessment;
  const decision = security?.decision || 'ALLOW';
  const isBlocked = decision === 'BLOCK';

  return (
    <div className="space-y-6 fade-in">
      {/* Title */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(79,142,247,0.15)', border: '1px solid rgba(79,142,247,0.3)' }}>
            <Search className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Research & Build</h1>
            <p className="text-xs text-slate-500">Researcher → Coder → Deployer secured by the AGENTSHIELD runtime</p>
          </div>
        </div>
      </div>

      {/* Input Section */}
      <div className="glass-card p-6 space-y-4">
        <label className="block text-xs font-bold uppercase tracking-widest text-slate-400">
          WHAT SHOULD THE AGENT RESEARCH?
        </label>
        <textarea
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Research Python authentication best practices and prepare an implementation specification."
          className="dark-input"
          style={{ resize: 'none', lineHeight: '1.6', fontFamily: 'Inter, sans-serif' }}
        />

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Globe className="w-3.5 h-3.5 text-blue-400" />
            <span>Tavily Web Research + DeBERTa ONNX Threat Interception via Backend Proxy</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleTestTavily}
              disabled={tavilyTesting}
              type="button"
              className="px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.15)',
                color: '#94a3b8',
              }}
            >
              {tavilyTesting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                  <span>Probing Tavily...</span>
                </>
              ) : (
                <>
                  <Globe className="w-3.5 h-3.5 text-blue-400" />
                  <span>TEST TAVILY API</span>
                </>
              )}
            </button>

            <button
              onClick={handleStartResearch}
              disabled={loading || !query.trim()}
              className="btn-primary"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Researching with Tavily & ONNX...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>START RESEARCH</span>
                </>
              )}
            </button>
          </div>
        </div>

        {tavilyStatus && (
          <div
            className="p-3 rounded-lg text-xs font-mono flex items-center justify-between"
            style={{
              background: tavilyStatus.success ? 'rgba(74,222,128,0.08)' : 'rgba(248,113,113,0.08)',
              border: `1px solid ${tavilyStatus.success ? 'rgba(74,222,128,0.3)' : 'rgba(248,113,113,0.3)'}`,
              color: tavilyStatus.success ? '#4ade80' : '#f87171',
            }}
          >
            <div className="flex items-center gap-2">
              {tavilyStatus.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
              <span>{tavilyStatus.message}</span>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-wider">
              {tavilyStatus.success ? 'ENDPOINT OK' : 'FAILED'}
            </span>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg text-xs font-medium flex items-start gap-2"
            style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.25)', color: '#f87171' }}>
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div><strong>Error:</strong> {error}</div>
          </div>
        )}
      </div>

      {/* Research Result Display */}
      {currentSession && (
        <div className="space-y-6">
          {/* Status & Security Summary Header */}
          <div className="glass-card p-6 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-5"
              style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">
                  Research Session ID
                </span>
                <div className="font-mono text-sm font-bold text-blue-300">{currentSession.session_id}</div>
              </div>

              <div className="flex items-center gap-4">
                <div>
                  <span className="text-[10px] text-slate-500 block mb-1">Status</span>
                  <span className="font-bold text-sm text-white uppercase">{currentSession.status}</span>
                </div>

                <div style={{ width: '1px', height: '32px', background: 'rgba(99,148,255,0.12)' }} />

                <div>
                  <span className="text-[10px] text-slate-500 block mb-1">Decision</span>
                  <span
                    onClick={() => riskAssessment && onShowRiskModal(riskAssessment)}
                    className={`cursor-pointer font-bold text-sm px-3 py-1 rounded-lg ${decision === 'ALLOW' ? 'badge-allow' : decision === 'REVIEW' ? 'badge-review' : 'badge-block'}`}
                    style={{ fontSize: '12px' }}
                    title="Click to view full Risk Scorer factor breakdown"
                  >
                    {decision}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-500 block mb-1">Latency</span>
                  <span className="font-mono text-sm font-bold text-slate-300">{security?.latency_ms?.toFixed(1)}ms</span>
                </div>
              </div>
            </div>

            {/* Security Telemetry Breakdown Grid */}
            {riskAssessment && (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {[
                  { label: 'ML Threat Score', val: riskAssessment.threat_score?.toFixed(4), accent: '#f87171' },
                  { label: 'Permission Risk', val: riskAssessment.factors?.permission_violation?.toFixed(4) || '0.0000', accent: '#fbbf24' },
                  { label: 'Behavior Dev.', val: riskAssessment.factors?.behavioral_dev?.toFixed(4) || '0.0000', accent: '#fbbf24' },
                  { label: 'Resource Sens.', val: riskAssessment.factors?.resource_sens?.toFixed(4) || '0.0000', accent: '#a78bfa' },
                  { label: 'Action Criticality', val: riskAssessment.factors?.action_crit?.toFixed(4) || '0.0000', accent: '#a78bfa' },
                  { label: 'Composite Risk', val: riskAssessment.total_risk?.toFixed(4), accent: '#4f8ef7', clickable: true },
                ].map((item, i) => (
                  <div key={i} className="p-3 rounded-lg space-y-1"
                    style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                    <span className="text-[10px] text-slate-500 block">{item.label}</span>
                    {item.clickable ? (
                      <button
                        onClick={() => onShowRiskModal(riskAssessment)}
                        className="font-mono font-bold text-sm block transition-colors"
                        style={{ color: item.accent }}
                      >
                        {item.val} →
                      </button>
                    ) : (
                      <span className="font-mono font-bold text-sm block" style={{ color: item.accent }}>
                        {item.val}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Block Warning Box */}
            {isBlocked && (
              <div className="p-4 rounded-xl flex items-start gap-3"
                style={{ background: 'rgba(248,113,113,0.07)', border: '1px solid rgba(248,113,113,0.25)' }}>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(248,113,113,0.15)' }}>
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                </div>
                <div>
                  <strong className="font-bold text-sm text-red-400 block mb-1">
                    RESEARCHER BLOCKED BY AGENTSHIELD GATEWAY
                  </strong>
                  <p className="text-xs text-slate-400">{security?.reason || 'The action exceeded security risk threshold (> 0.60).'}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Circuit breaker tripped and session quarantined. Check the Incidents tab for Gemini CISO forensic analysis.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Research Findings & Sources */}
          {!isBlocked && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left 2 Cols: Research Specification */}
              <div className="lg:col-span-2 glass-card p-6 space-y-4">
                <div className="flex items-center justify-between pb-3"
                  style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
                  <h3 className="text-base font-semibold text-white">Research Specification & Findings</h3>
                  <button
                    onClick={handleSendToCoder}
                    disabled={coderLoading}
                    className="btn-primary"
                    style={{ padding: '8px 16px', fontSize: '12px' }}
                  >
                    {coderLoading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Sending to Coder...</span>
                      </>
                    ) : (
                      <>
                        <Code className="w-3.5 h-3.5" />
                        <span>SEND TO CODER →</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="terminal-text text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[450px] overflow-y-auto"
                  style={{ fontSize: '11px' }}>
                  {currentSession.research_notes || 'No research findings returned.'}
                </div>
              </div>

              {/* Right Col: Verified Tavily Sources */}
              <div className="glass-card p-6 space-y-4">
                <div className="flex items-center justify-between pb-3"
                  style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
                  <h3 className="text-sm font-semibold text-white">Verified Sources</h3>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded"
                    style={{ background: 'rgba(79,142,247,0.1)', border: '1px solid rgba(79,142,247,0.2)', color: '#4f8ef7' }}>
                    {currentSession.tavily_sources?.length || 0}
                  </span>
                </div>

                {currentSession.tavily_sources && currentSession.tavily_sources.length > 0 ? (
                  <div className="space-y-3">
                    {currentSession.tavily_sources.map((source, idx) => (
                      <div key={idx} className="p-3 rounded-lg transition-all"
                        style={{
                          background: 'rgba(255,255,255,0.02)',
                          border: '1px solid rgba(99,148,255,0.1)',
                        }}
                        onMouseEnter={e => {
                          (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(79,142,247,0.3)';
                          (e.currentTarget as HTMLDivElement).style.background = 'rgba(79,142,247,0.04)';
                        }}
                        onMouseLeave={e => {
                          (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(99,148,255,0.1)';
                          (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.02)';
                        }}
                      >
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                        >
                          <span className="truncate">{source.title}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                        <p className="text-[11px] text-slate-500 mt-1.5 line-clamp-3 leading-relaxed">
                          {source.content}
                        </p>
                        {source.score && (
                          <div className="mt-2 text-[10px] font-mono text-slate-600">
                            Relevance: {(source.score * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-8 text-center">
                    <Globe className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-xs text-slate-500">No web sources retrieved.</p>
                    <p className="text-[11px] text-slate-600 mt-1">Add TAVILY_API_KEY to .env to enable web search.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
