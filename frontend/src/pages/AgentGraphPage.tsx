import React from 'react';
import { Search, Shield, Code, Box, Send, Activity, Lock, CheckCircle2, Zap } from 'lucide-react';
import { ResearchSessionRecord } from '../types';

interface AgentGraphPageProps {
  currentSession: ResearchSessionRecord | null;
}

export const AgentGraphPage: React.FC<AgentGraphPageProps> = ({ currentSession }) => {
  const status = currentSession?.status || 'IDLE';
  const decision = currentSession?.security?.decision || 'ALLOW';
  const isBlocked = decision === 'BLOCK';

  // Determine active states for nodes
  const researcherState = !currentSession ? 'WAITING' : status === 'RUNNING' || status === 'COMPLETED' ? 'COMPLETED' : 'BLOCKED';
  const gate1State = !currentSession ? 'WAITING' : isBlocked ? 'BLOCKED' : 'ALLOW';
  const coderState = !currentSession ? 'WAITING' : isBlocked ? 'SKIPPED' : 'ACTIVE';
  const deployerState = !currentSession ? 'WAITING' : isBlocked ? 'SKIPPED' : 'READY';

  const getNodeStyles = (state: string, isGate = false) => {
    if (state === 'COMPLETED' || state === 'ACTIVE' || state === 'ALLOW' || state === 'READY') {
      return {
        bg: isGate ? 'rgba(129,140,248,0.1)' : 'rgba(79,142,247,0.1)',
        border: isGate ? 'rgba(129,140,248,0.3)' : 'rgba(79,142,247,0.3)',
        color: isGate ? '#818cf8' : '#4f8ef7',
        shadow: isGate ? '0 0 20px rgba(129,140,248,0.1)' : '0 0 20px rgba(79,142,247,0.1)'
      };
    }
    if (state === 'BLOCKED') {
      return {
        bg: 'rgba(248,113,113,0.1)',
        border: 'rgba(248,113,113,0.3)',
        color: '#f87171',
        shadow: '0 0 20px rgba(248,113,113,0.1)'
      };
    }
    if (state === 'SKIPPED') {
      return {
        bg: 'rgba(255,255,255,0.02)',
        border: 'rgba(255,255,255,0.05)',
        color: '#475569',
        shadow: 'none'
      };
    }
    // WAITING
    return {
      bg: 'rgba(255,255,255,0.03)',
      border: 'rgba(255,255,255,0.08)',
      color: '#64748b',
      shadow: 'none'
    };
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(129,140,248,0.12)', border: '1px solid rgba(129,140,248,0.25)' }}>
            <Activity className="w-5 h-5" style={{ color: '#818cf8' }} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Multi-Agent Security Execution Graph</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Live visualization of LangGraph nodes & AGENTSHIELD gatekeeper boundaries for Session: <code className="font-bold text-slate-300 ml-1">{currentSession?.session_id || 'None'}</code>
            </p>
          </div>
        </div>
      </div>

      {/* Graph Flow Board */}
      <div className="glass-card p-8 space-y-10 relative overflow-hidden">
        {/* Background circuit pattern */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
            backgroundSize: '24px 24px'
          }}
        />
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-5 relative z-10">
          {/* Node 1: Researcher */}
          <div className="agent-node flex flex-col justify-between"
            style={{
              background: getNodeStyles(researcherState).bg,
              borderColor: getNodeStyles(researcherState).border,
              boxShadow: getNodeStyles(researcherState).shadow,
              opacity: researcherState === 'SKIPPED' ? 0.5 : 1
            }}>
            <div className="flex items-center justify-between mb-4">
              <Search className="w-5 h-5" style={{ color: getNodeStyles(researcherState).color }} />
              <span className="text-[9px] font-bold px-2 py-0.5 rounded tracking-widest"
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  color: getNodeStyles(researcherState).color,
                  border: `1px solid ${getNodeStyles(researcherState).border}`
                }}>
                {researcherState}
              </span>
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">1. Researcher</h3>
              <p className="text-[11px] mt-1" style={{ color: getNodeStyles(researcherState).color }}>Tavily Web Research</p>
            </div>
          </div>

          {/* Gate 1 */}
          <div className="agent-node flex flex-col justify-between relative overflow-hidden"
            style={{
              background: getNodeStyles(gate1State, true).bg,
              borderColor: getNodeStyles(gate1State, true).border,
              boxShadow: getNodeStyles(gate1State, true).shadow,
              opacity: gate1State === 'SKIPPED' ? 0.5 : 1
            }}>
            {gate1State === 'ALLOW' && (
              <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500 opacity-20 rounded-bl-full filter blur-xl" />
            )}
            <div className="flex items-center justify-between mb-4 relative z-10">
              <Shield className="w-5 h-5" style={{ color: getNodeStyles(gate1State, true).color }} />
              <span className="text-[9px] font-bold px-2 py-0.5 rounded tracking-widest"
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  color: getNodeStyles(gate1State, true).color,
                  border: `1px solid ${getNodeStyles(gate1State, true).border}`
                }}>
                {gate1State}
              </span>
            </div>
            <div className="relative z-10">
              <h3 className="font-bold text-sm text-white">Security Gate</h3>
              <p className="text-[11px] mt-1 flex items-center gap-1" style={{ color: getNodeStyles(gate1State, true).color }}>
                <Zap className="w-3 h-3" /> ONNX ML Proxy
              </p>
            </div>
          </div>

          {/* Node 2: Coder */}
          <div className="agent-node flex flex-col justify-between"
            style={{
              background: getNodeStyles(coderState).bg,
              borderColor: getNodeStyles(coderState).border,
              boxShadow: getNodeStyles(coderState).shadow,
              opacity: coderState === 'SKIPPED' ? 0.5 : 1
            }}>
            <div className="flex items-center justify-between mb-4">
              <Code className="w-5 h-5" style={{ color: getNodeStyles(coderState).color }} />
              <span className="text-[9px] font-bold px-2 py-0.5 rounded tracking-widest"
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  color: getNodeStyles(coderState).color,
                  border: `1px solid ${getNodeStyles(coderState).border}`
                }}>
                {coderState}
              </span>
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">2. Coder Node</h3>
              <p className="text-[11px] mt-1" style={{ color: getNodeStyles(coderState).color }}>Code Generation</p>
            </div>
          </div>

          {/* Node 3: Sandbox */}
          <div className="agent-node flex flex-col justify-between"
            style={{
              background: getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).bg,
              borderColor: getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).border,
              boxShadow: getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).shadow,
              opacity: coderState === 'SKIPPED' ? 0.5 : 1
            }}>
            <div className="flex items-center justify-between mb-4">
              <Box className="w-5 h-5" style={{ color: getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).color }} />
              <span className="text-[9px] font-bold px-2 py-0.5 rounded tracking-widest"
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  color: getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).color,
                  border: `1px solid ${getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).border}`
                }}>
                CONTAINED
              </span>
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">3. Sandbox</h3>
              <p className="text-[11px] mt-1 flex items-center gap-1" style={{ color: getNodeStyles(coderState === 'ACTIVE' ? 'ALLOW' : coderState).color }}>
                <Lock className="w-3 h-3" /> Process Isolation
              </p>
            </div>
          </div>

          {/* Node 4: Deployer */}
          <div className="agent-node flex flex-col justify-between"
            style={{
              background: getNodeStyles(deployerState).bg,
              borderColor: getNodeStyles(deployerState).border,
              boxShadow: getNodeStyles(deployerState).shadow,
              opacity: deployerState === 'SKIPPED' ? 0.5 : 1
            }}>
            <div className="flex items-center justify-between mb-4">
              <Send className="w-5 h-5" style={{ color: getNodeStyles(deployerState).color }} />
              <span className="text-[9px] font-bold px-2 py-0.5 rounded tracking-widest"
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  color: getNodeStyles(deployerState).color,
                  border: `1px solid ${getNodeStyles(deployerState).border}`
                }}>
                {deployerState}
              </span>
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">4. Deployer</h3>
              <p className="text-[11px] mt-1" style={{ color: getNodeStyles(deployerState).color }}>Staging Environment</p>
            </div>
          </div>
        </div>

        {/* Live Execution Telemetry log */}
        <div className="p-5 rounded-xl border relative z-10"
          style={{ background: 'rgba(13,21,38,0.8)', borderColor: 'rgba(99,148,255,0.1)' }}>
          <div className="flex items-center justify-between pb-3 mb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">LangGraph Runtime Telemetry</span>
            {currentSession && <span className="pulse-dot pulse-dot-blue" />}
          </div>

          <div className="font-mono space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-blue-500">→</span>
              <span className="text-slate-500">Session ID:</span>
              <span className="text-white">{currentSession?.session_id || 'IDLE'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-500">→</span>
              <span className="text-slate-500">Current Agent Role:</span>
              <span className="text-white">{currentSession?.agent_id || 'NONE'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-purple-500">→</span>
              <span className="text-slate-500">Gateway Envelope Token:</span>
              <span className="text-purple-300">{currentSession?.security?.envelope_token || 'NONE'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-purple-500">→</span>
              <span className="text-slate-500">Gateway Decision:</span>
              <span className={isBlocked ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'}>
                {currentSession?.security?.decision || 'NONE'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
