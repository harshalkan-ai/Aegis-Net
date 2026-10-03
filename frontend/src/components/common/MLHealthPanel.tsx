import React from 'react';
import { Cpu, RefreshCw, Zap } from 'lucide-react';
import { MLStatusInfo } from '../../types';

interface MLHealthPanelProps {
  mlStatus: MLStatusInfo | null;
  onRefresh?: () => void;
}

export const MLHealthPanel: React.FC<MLHealthPanelProps> = ({ mlStatus, onRefresh }) => {
  if (!mlStatus) {
    return (
      <div className="glass-card p-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <Cpu className="w-4 h-4 animate-spin text-blue-400" />
          <span>Connecting to backend ONNX ML Engine...</span>
        </div>
      </div>
    );
  }

  const isActive = mlStatus.status === 'MODEL ACTIVE';

  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-4"
        style={{ borderBottom: '1px solid rgba(99,148,255,0.08)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(79,142,247,0.12)', border: '1px solid rgba(79,142,247,0.25)' }}>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-bold text-white">ONNX ML Threat Engine</h3>
            <span className={`flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold rounded uppercase tracking-wider border ${
                isActive ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'
              }`}>
              <span className={`pulse-dot w-2 h-2 ${isActive ? 'pulse-dot-green' : 'pulse-dot-red'}`} />
              {isActive ? 'Active' : 'Error'}
            </span>
          </div>
        </div>

        {onRefresh && (
          <button onClick={onRefresh} className="btn-ghost" style={{ padding: '6px' }} title="Refresh ML Telemetry">
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 text-xs">
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1">Model</span>
          <span className="font-bold text-white truncate block">DeBERTa-v3</span>
        </div>
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1">Runtime</span>
          <span className="font-bold text-white block">{mlStatus.runtime}</span>
        </div>
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1 flex items-center gap-1"><Zap className="w-3 h-3 text-blue-400"/> Latency</span>
          <span className="font-mono font-bold text-blue-400 block">
            {mlStatus.total_predictions ? `${mlStatus.last_latency_ms?.toFixed(1) || '0.0'} ms` : '—'}
          </span>
        </div>
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1">Last Score</span>
          <span className="font-mono font-bold text-white block">
            {mlStatus.total_predictions ? (mlStatus.last_prediction?.toFixed(4) || '0.0000') : '—'}
          </span>
        </div>
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1">Predictions</span>
          <span className="font-bold text-white block">{mlStatus.total_predictions}</span>
        </div>
        <div className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1">Errors</span>
          <span className={`font-bold block ${mlStatus.errors > 0 ? 'text-red-400' : 'text-white'}`}>
            {mlStatus.errors}
          </span>
        </div>
        <div className="col-span-2 sm:col-span-4 lg:col-span-1 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1">Model File</span>
          <span className="font-mono text-slate-400 truncate block text-[11px]" title={mlStatus.model_path}>
            model.onnx
          </span>
        </div>
      </div>

      {mlStatus.last_error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400 font-mono">
          <strong>ML Exception Log:</strong> {mlStatus.last_error}
        </div>
      )}
    </div>
  );
};
