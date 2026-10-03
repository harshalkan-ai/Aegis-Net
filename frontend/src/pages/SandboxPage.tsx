import React, { useEffect, useState } from 'react';
import { Box, Lock, ShieldCheck, AlertOctagon, RefreshCw, CheckCircle2, XCircle, Unlock, Power, Activity } from 'lucide-react';
import { sandboxApi } from '../api/sandboxApi';
import { SandboxStatusResponse } from '../types';

interface SandboxPageProps {
  activeSessionId: string | null;
}

export const SandboxPage: React.FC<SandboxPageProps> = ({ activeSessionId }) => {
  const [sandbox, setSandbox] = useState<SandboxStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchSandbox = async () => {
    if (!activeSessionId) return;
    setLoading(true);
    setError(null);

    try {
      const data = await sandboxApi.getSandbox(activeSessionId);
      setSandbox(data);
    } catch (err: any) {
      setError(`Sandbox fetch error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeSessionId) {
      fetchSandbox();
    }
  }, [activeSessionId]);

  const handleTripBreaker = async () => {
    if (!activeSessionId) return;
    setActionLoading(true);

    try {
      await sandboxApi.tripCircuitBreaker(activeSessionId, 'Manual admin trigger from Sandbox control plane');
      await fetchSandbox();
    } catch (err: any) {
      setError(`Trip breaker failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReleaseQuarantine = async () => {
    if (!activeSessionId) return;
    setActionLoading(true);

    try {
      await sandboxApi.releaseQuarantine(activeSessionId, sandbox?.agent_role || 'CODER');
      await fetchSandbox();
    } catch (err: any) {
      setError(`Release quarantine failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const isQuarantined = sandbox?.status === 'QUARANTINED' || sandbox?.isolation_status === 'QUARANTINED';

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="glass-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)' }}>
            <Box className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Sandbox Isolation & Containment</h1>
            <p className="text-xs text-slate-500">
              Confines all tool operations strictly within sandboxed session workspace boundary
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchSandbox}
            disabled={loading || !activeSessionId}
            className="btn-ghost"
            style={{ padding: '8px 14px', fontSize: '12px' }}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {isQuarantined ? (
            <button
              onClick={handleReleaseQuarantine}
              disabled={actionLoading}
              className="btn-primary"
              style={{ padding: '8px 14px', fontSize: '12px' }}
            >
              <Unlock className="w-3.5 h-3.5" />
              <span>Release Quarantine</span>
            </button>
          ) : (
            <button
              onClick={handleTripBreaker}
              disabled={actionLoading || !activeSessionId}
              className="btn-danger"
              style={{ padding: '8px 14px', fontSize: '12px' }}
            >
              <Power className="w-3.5 h-3.5" />
              <span>Trip Circuit Breaker</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl text-xs"
          style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)', color: '#f87171' }}>
          <strong>Sandbox Exception:</strong> {error}
        </div>
      )}

      {!activeSessionId ? (
        <div className="glass-card p-16 text-center space-y-3">
          <Box className="w-12 h-12 mx-auto" style={{ color: '#1e3a5f' }} />
          <p className="font-bold text-white">No active research session.</p>
          <p className="text-xs text-slate-500">Start a research session to view its dedicated sandbox status.</p>
        </div>
      ) : sandbox ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Telemetry Panel */}
          <div className="lg:col-span-2 glass-card p-6 space-y-6">
            <div className="flex items-center justify-between pb-4"
              style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ 
                    background: isQuarantined ? 'rgba(248,113,113,0.12)' : 'rgba(79,142,247,0.12)',
                    border: `1px solid ${isQuarantined ? 'rgba(248,113,113,0.3)' : 'rgba(79,142,247,0.3)'}`
                  }}>
                  <Lock className="w-5 h-5" style={{ color: isQuarantined ? '#f87171' : '#4f8ef7' }} />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">Sandbox Status</span>
                  <span className={`text-base font-bold uppercase ${isQuarantined ? 'text-red-400' : 'text-blue-400'}`}>
                    {sandbox.status}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <span className="text-[10px] text-slate-500 block mb-1 uppercase tracking-widest">Circuit Breaker State</span>
                <span className={`font-mono text-sm font-bold ${sandbox.circuit_breaker_state === 'CLOSED' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {sandbox.circuit_breaker_state}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl"
                style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block mb-2">Research Session ID</span>
                <span className="font-mono font-bold text-slate-300 block truncate">{sandbox.session_id}</span>
              </div>

              <div className="p-4 rounded-xl"
                style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block mb-2">Active Agent Role</span>
                <span className="font-bold text-white block">{sandbox.agent_role}</span>
              </div>

              <div className="p-4 rounded-xl sm:col-span-2"
                style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.08)' }}>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block mb-2">Sandboxed Workspace Root</span>
                <span className="font-mono text-slate-400 text-xs block truncate">{sandbox.workspace_root}</span>
              </div>
            </div>
            
            {isQuarantined && (
              <div className="p-4 rounded-xl flex items-start gap-3 mt-4"
                style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.25)' }}>
                <AlertOctagon className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-red-400 mb-1">CONTAINMENT BREACH MITIGATED</h4>
                  <p className="text-xs text-red-300/80 leading-relaxed">
                    The agent attempted to perform an action that violated security policies or exceeded the risk threshold.
                    The circuit breaker has tripped, instantly terminating the agent process and quarantining the workspace.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Tools Permission Guard */}
          <div className="glass-card p-6 space-y-5">
            <div className="flex items-center justify-between pb-3"
              style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Tool Permission Control
              </h3>
              <Activity className="w-4 h-4 text-slate-500" />
            </div>

            {/* Allowed Tools */}
            <div className="space-y-3">
              <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5 uppercase tracking-wider">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Allowed Tools ({sandbox.allowed_tools?.length || 0})</span>
              </span>
              <div className="space-y-1.5">
                {sandbox.allowed_tools?.map((tool) => (
                  <div key={tool} className="px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-between"
                    style={{ background: 'rgba(52,211,153,0.05)', border: '1px solid rgba(52,211,153,0.15)' }}>
                    <span className="text-emerald-300">{tool}</span>
                    <span className="text-[9px] text-emerald-500 font-bold uppercase tracking-wider">PERMITTED</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Blocked Tools */}
            <div className="space-y-3 pt-3" style={{ borderTop: '1px dashed rgba(255,255,255,0.05)' }}>
              <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5 uppercase tracking-wider">
                <XCircle className="w-3.5 h-3.5 text-red-500" />
                <span>Prohibited / Blocked Tools ({sandbox.blocked_tools?.length || 0})</span>
              </span>
              <div className="space-y-1.5">
                {sandbox.blocked_tools?.map((tool) => (
                  <div key={tool} className="px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-between"
                    style={{ background: 'rgba(248,113,113,0.05)', border: '1px solid rgba(248,113,113,0.15)' }}>
                    <span className="text-red-300">{tool}</span>
                    <span className="text-[9px] text-red-500 font-bold uppercase tracking-wider">BLOCKED</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
