import React from 'react';
import { X, Calculator } from 'lucide-react';
import { RiskAssessment } from '../../types';

interface RiskBreakdownModalProps {
  assessment: RiskAssessment | null;
  isOpen: boolean;
  onClose: () => void;
}

export const RiskBreakdownModal: React.FC<RiskBreakdownModalProps> = ({ assessment, isOpen, onClose }) => {
  if (!isOpen || !assessment) return null;

  const f = assessment.factors || {
    threat: assessment.threat_score || 0,
    permission_violation: 0,
    behavioral_dev: 0,
    resource_sens: 0,
    action_crit: 0,
  };

  const threatContrib = 0.30 * f.threat;
  const permContrib = 0.20 * f.permission_violation;
  const behaviorContrib = 0.20 * f.behavioral_dev;
  const resourceContrib = 0.15 * f.resource_sens;
  const actionContrib = 0.15 * f.action_crit;

  const decision = assessment.decision || 'ALLOW';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 fade-in"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(12px)' }}>
      <div className="rounded-2xl max-w-lg w-full overflow-hidden"
        style={{
          background: 'rgba(10, 16, 30, 0.98)',
          border: '1px solid rgba(99,148,255,0.2)',
          boxShadow: '0 25px 80px rgba(0,0,0,0.8), 0 0 80px rgba(79,142,247,0.05)',
        }}>
        {/* Header */}
        <div className="flex items-center justify-between p-5"
          style={{ borderBottom: '1px solid rgba(99,148,255,0.1)' }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(79,142,247,0.12)', border: '1px solid rgba(79,142,247,0.25)' }}>
              <Calculator className="w-4 h-4 text-blue-400" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">Backend Risk Engine Audit</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between p-4 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.1)' }}>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block mb-1">
                Composite Risk Score
              </span>
              <div className="text-3xl font-bold font-mono text-white">
                {assessment.total_risk.toFixed(4)}
              </div>
            </div>
            <div className={decision === 'ALLOW' ? 'badge-allow' : decision === 'REVIEW' ? 'badge-review' : 'badge-block'}
              style={{ fontSize: '14px', padding: '6px 12px' }}>
              {decision}
            </div>
          </div>

          <div>
            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">
              Zero-Trust Weight Factor Breakdown
            </div>

            <div className="space-y-2 text-xs">
              {[
                { label: '0.30 × Threat Score (T)', sub: 'ONNX Prompt Injection model probability', val: threatContrib, raw: f.threat, color: '#f87171' },
                { label: '0.20 × Permission Violation (P)', sub: 'RBAC role tool authorization penalty', val: permContrib, raw: f.permission_violation, color: '#fbbf24' },
                { label: '0.20 × Behavioral Deviation (B)', sub: 'Telemetry anomaly deviation metric', val: behaviorContrib, raw: f.behavioral_dev, color: '#fbbf24' },
                { label: '0.15 × Resource Sensitivity (S)', sub: 'Data classification & system target sensitivity', val: resourceContrib, raw: f.resource_sens, color: '#a78bfa' },
                { label: '0.15 × Action Criticality (C)', sub: 'Irreversibility of runtime execution', val: actionContrib, raw: f.action_crit, color: '#a78bfa' },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg"
                  style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(99,148,255,0.05)' }}>
                  <div>
                    <span className="font-bold text-white">{item.label}</span>
                    <p className="text-slate-500 text-[10px] mt-0.5">{item.sub}</p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-sm block" style={{ color: item.color }}>{item.val.toFixed(4)}</span>
                    <span className="text-slate-500 block text-[9px] font-mono mt-0.5">Raw: {item.raw.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg text-xs"
            style={{ background: 'rgba(79,142,247,0.05)', border: '1px solid rgba(79,142,247,0.2)', color: '#94a3b8' }}>
            <strong className="text-blue-400">Tri-State Decision Policy:</strong> Risk &lt; 0.30 &rarr; <code className="text-emerald-400 bg-emerald-400/10 px-1 rounded">ALLOW</code> | 0.30 &le; Risk &lt; 0.60 &rarr; <code className="text-yellow-400 bg-yellow-400/10 px-1 rounded">REVIEW</code> | Risk &ge; 0.60 &rarr; <code className="text-red-400 bg-red-400/10 px-1 rounded">BLOCK</code>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex justify-end"
          style={{ borderTop: '1px solid rgba(99,148,255,0.1)', background: 'rgba(255,255,255,0.02)' }}>
          <button onClick={onClose} className="btn-ghost" style={{ padding: '8px 16px', fontSize: '12px' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
