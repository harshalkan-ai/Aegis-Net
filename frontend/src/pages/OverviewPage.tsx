import React from 'react';
import { Shield, Search, FolderTree, Box, GitFork, AlertOctagon, CheckCircle2, ArrowRight, Cpu, Activity, Zap, Lock, TrendingUp } from 'lucide-react';
import { MLStatusInfo, IncidentRecord } from '../types';

interface OverviewPageProps {
  mlStatus: MLStatusInfo | null;
  activeSessionId: string | null;
  incidents: IncidentRecord[];
  onNavigate: (tab: any) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ mlStatus, activeSessionId, incidents, onNavigate }) => {
  const openIncidents = incidents.filter((i) => i.status === 'OPEN' || i.status === 'INVESTIGATING');
  const isMlActive = mlStatus?.status === 'MODEL ACTIVE';

  const MetricCard = ({ label, value, sub, icon: Icon, accent = '#4f8ef7', onClick }: any) => (
    <div
      onClick={onClick}
      className={`metric-card hover-lift ${onClick ? 'cursor-pointer' : ''}`}
      style={{ borderColor: `${accent}20` }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold uppercase tracking-widest" style={{ color: accent + '99', letterSpacing: '0.1em' }}>
          {label}
        </span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: accent + '15' }}>
          <Icon className="w-4 h-4" style={{ color: accent }} />
        </div>
      </div>
      <div className="metric-value" style={{ color: accent === '#f87171' && (value as number) > 0 ? '#f87171' : 'white' }}>
        {value}
      </div>
      {sub && <p className="text-xs mt-2" style={{ color: '#4f6884' }}>{sub}</p>}
    </div>
  );

  return (
    <div className="space-y-6 fade-in">
      {/* Hero Header */}
      <div className="glass-card p-8 relative overflow-hidden">
        {/* Decorative glow */}
        <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #4f8ef7, transparent)', filter: 'blur(40px)' }}
        />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, rgba(79,142,247,0.2), rgba(99,102,241,0.1))', border: '1px solid rgba(79,142,247,0.3)' }}>
                <Shield className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-white tracking-tight">
                  AGENTSHIELD Control Plane
                </h1>
                <p className="text-sm text-slate-400 mt-0.5">
                  Zero-Trust Runtime Protection for Multi-Agent Autonomous Workflows
                </p>
              </div>
            </div>

            {/* Status line */}
            <div className="flex flex-wrap items-center gap-3 mt-4">
              <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full"
                style={{ background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.2)' }}>
                <span className="pulse-dot pulse-dot-green" />
                <span className="text-emerald-400 font-semibold">System Online</span>
              </div>
              <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full"
                style={{ background: 'rgba(79,142,247,0.08)', border: '1px solid rgba(79,142,247,0.2)' }}>
                <Zap className="w-3 h-3 text-blue-400" />
                <span className="text-blue-400 font-semibold">ONNX Runtime Active</span>
              </div>
              <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(99,148,255,0.12)' }}>
                <Lock className="w-3 h-3 text-slate-400" />
                <span className="text-slate-400 font-semibold">Zero-Trust Enforcing</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('research')}
              className="btn-primary"
            >
              <Search className="w-4 h-4" />
              Launch Research
            </button>
            <button
              onClick={() => onNavigate('incidents')}
              className="btn-ghost"
            >
              <AlertOctagon className="w-4 h-4" />
              <span>Incidents</span>
              {openIncidents.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                  style={{ background: 'rgba(248,113,113,0.15)', border: '1px solid rgba(248,113,113,0.3)', color: '#f87171' }}>
                  {openIncidents.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Real-time Status Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="ML Threat Engine"
          value={isMlActive ? 'ACTIVE' : 'ERROR'}
          icon={Cpu}
          accent={isMlActive ? '#34d399' : '#f87171'}
          sub={`DeBERTa-v3 ONNX · ${mlStatus?.last_latency_ms?.toFixed(1) || '0.0'}ms · ${mlStatus?.total_predictions || 0} predictions`}
          onClick={() => onNavigate('security')}
        />
        <MetricCard
          label="Security Gateway"
          value="100%"
          icon={Shield}
          accent="#4f8ef7"
          sub="Risk < 0.30 ALLOW · ≥ 0.60 BLOCK · Tri-State threshold"
        />
        <MetricCard
          label="Open Incidents"
          value={openIncidents.length}
          icon={AlertOctagon}
          accent={openIncidents.length > 0 ? '#f87171' : '#34d399'}
          sub={openIncidents.length > 0 ? 'Requires CISO review & Gemini forensics' : 'Zero open security violations'}
          onClick={() => onNavigate('incidents')}
        />
        <MetricCard
          label="Active Session"
          value={activeSessionId ? '1' : '0'}
          icon={Activity}
          accent="#818cf8"
          sub={activeSessionId ? `ID: ${activeSessionId.substring(0, 12)}…` : 'Click Research to start'}
        />
      </div>

      {/* Pipeline Architecture */}
      <div className="glass-card p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Zero-Trust Multi-Agent Runtime Pipeline</h2>
            <p className="text-xs text-slate-500 mt-0.5">Click any node to navigate to that section</p>
          </div>
          <TrendingUp className="w-4 h-4 text-blue-400 opacity-60" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {[
            { step: 'STEP 1', title: 'Researcher', sub: 'Tavily Web Research', icon: Search, tab: 'research', accent: '#4f8ef7', state: activeSessionId ? 'done' : 'idle' },
            { step: 'GATE 1', title: 'ONNX ML Proxy', sub: 'DeBERTa Threat Scorer', icon: Shield, tab: 'security', accent: '#818cf8', isGate: true, state: activeSessionId ? 'done' : 'idle' },
            { step: 'STEP 2', title: 'Coder Agent', sub: 'Workspace File Creation', icon: FolderTree, tab: 'workspace', accent: '#4f8ef7', state: 'idle' },
            { step: 'STEP 3', title: 'Sandbox', sub: 'Isolated Execution', icon: Box, tab: 'sandbox', accent: '#4f8ef7', state: 'idle' },
            { step: 'STEP 4', title: 'Deployer', sub: 'Staging Build', icon: GitFork, tab: 'graph', accent: '#4f8ef7', state: 'idle' },
          ].map((item, idx) => {
            const Icon = item.icon;
            const isGate = item.isGate;
            return (
              <div
                key={idx}
                onClick={() => onNavigate(item.tab)}
                className="cursor-pointer p-4 rounded-xl transition-all duration-200 hover-lift"
                style={{
                  background: isGate ? 'rgba(129,140,248,0.07)' : 'rgba(255,255,255,0.02)',
                  border: isGate ? '1px solid rgba(129,140,248,0.25)' : '1px solid rgba(99,148,255,0.1)',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = `${item.accent}50`;
                  (e.currentTarget as HTMLDivElement).style.background = `${item.accent}0D`;
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = isGate ? 'rgba(129,140,248,0.25)' : 'rgba(99,148,255,0.1)';
                  (e.currentTarget as HTMLDivElement).style.background = isGate ? 'rgba(129,140,248,0.07)' : 'rgba(255,255,255,0.02)';
                }}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: item.accent + '90' }}>
                    {item.step}
                  </span>
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: item.accent + '15' }}>
                    <Icon className="w-3.5 h-3.5" style={{ color: item.accent }} />
                  </div>
                </div>
                <h3 className="font-bold text-white text-sm">{item.title}</h3>
                <p className="text-xs text-slate-500 mt-1">{item.sub}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Incidents Summary */}
      {incidents.length > 0 && (
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-red-400" />
              Recent Security Incidents
            </h2>
            <button
              onClick={() => onNavigate('incidents')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2">
            {incidents.slice(0, 3).map((inc) => (
              <div key={inc.id} className="flex items-center justify-between p-3 rounded-lg"
                style={{ background: 'rgba(248,113,113,0.04)', border: '1px solid rgba(248,113,113,0.1)' }}>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded"
                    style={{
                      background: inc.severity === 'CRITICAL' ? 'rgba(248,113,113,0.15)' : 'rgba(251,191,36,0.12)',
                      border: `1px solid ${inc.severity === 'CRITICAL' ? 'rgba(248,113,113,0.3)' : 'rgba(251,191,36,0.25)'}`,
                      color: inc.severity === 'CRITICAL' ? '#f87171' : '#fbbf24',
                    }}>
                    {inc.severity}
                  </span>
                  <span className="font-mono text-xs text-slate-400">{inc.agent_id}</span>
                  <span className="text-xs text-slate-600">·</span>
                  <span className="font-mono text-xs text-slate-500">{inc.tool_name || 'blocked_tool'}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-red-400">{inc.risk_score?.toFixed(4)}</span>
                  <span className="badge-block">{inc.decision}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
