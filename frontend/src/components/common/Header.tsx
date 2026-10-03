import React from 'react';
import { Shield, Cpu, Database, CheckCircle2, AlertTriangle, Zap } from 'lucide-react';
import { MLStatusInfo } from '../../types';

interface HeaderProps {
  mlStatus: MLStatusInfo | null;
  activeSessionId: string | null;
  onSelectScenario: (scenario: 'safe' | 'attack') => void;
}

export const Header: React.FC<HeaderProps> = ({ mlStatus, activeSessionId, onSelectScenario }) => {
  const isMlActive = mlStatus?.status === 'MODEL ACTIVE';

  return (
    <header className="sticky top-0 z-30" style={{
      background: 'rgba(5, 10, 20, 0.92)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(99, 148, 255, 0.12)',
    }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="relative w-10 h-10 flex items-center justify-center">
              {/* Glow ring */}
              <div className="absolute inset-0 rounded-xl opacity-30"
                style={{ background: 'radial-gradient(circle, rgba(79,142,247,0.6), transparent)', filter: 'blur(6px)' }}
              />
              <div className="relative w-10 h-10 rounded-xl flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, rgba(79,142,247,0.2), rgba(99,102,241,0.1))',
                  border: '1px solid rgba(79,142,247,0.3)',
                }}>
                <Shield className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white text-lg tracking-tight" style={{ letterSpacing: '-0.3px' }}>
                  AGENTSHIELD
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold"
                  style={{
                    background: 'rgba(79,142,247,0.12)',
                    border: '1px solid rgba(79,142,247,0.25)',
                    color: '#4f8ef7',
                    letterSpacing: '0.04em',
                  }}>
                  AEGIS-NET v1.0
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block mt-0.5">
                Zero-Trust Multi-Agent Runtime Security Platform
              </p>
            </div>
          </div>

          {/* Quick Security Demo Triggers & Telemetry Badges */}
          <div className="flex items-center space-x-2">
            {/* Quick Demo Selector */}
            <div className="hidden md:flex items-center space-x-1.5 p-1 rounded-lg text-xs"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(99,148,255,0.12)' }}>
              <span className="text-slate-500 font-medium px-2 text-[11px] uppercase tracking-wider">Demo</span>
              <button
                onClick={() => onSelectScenario('safe')}
                className="px-3 py-1.5 rounded-md font-medium transition"
                style={{
                  background: 'rgba(52,211,153,0.08)',
                  border: '1px solid rgba(52,211,153,0.2)',
                  color: '#34d399',
                  fontSize: '11px',
                }}
                onMouseEnter={e => {
                  (e.target as HTMLButtonElement).style.background = 'rgba(52,211,153,0.15)';
                }}
                onMouseLeave={e => {
                  (e.target as HTMLButtonElement).style.background = 'rgba(52,211,153,0.08)';
                }}
              >
                Safe Task
              </button>
              <button
                onClick={() => onSelectScenario('attack')}
                className="px-3 py-1.5 rounded-md font-medium transition"
                style={{
                  background: 'rgba(248,113,113,0.08)',
                  border: '1px solid rgba(248,113,113,0.2)',
                  color: '#f87171',
                  fontSize: '11px',
                }}
                onMouseEnter={e => {
                  (e.target as HTMLButtonElement).style.background = 'rgba(248,113,113,0.15)';
                }}
                onMouseLeave={e => {
                  (e.target as HTMLButtonElement).style.background = 'rgba(248,113,113,0.08)';
                }}
              >
                ⚡ Attack
              </button>
            </div>

            {/* ML Status Badge */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs"
              style={{
                background: isMlActive ? 'rgba(52,211,153,0.08)' : 'rgba(248,113,113,0.08)',
                border: isMlActive ? '1px solid rgba(52,211,153,0.2)' : '1px solid rgba(248,113,113,0.2)',
              }}>
              <span className={`pulse-dot ${isMlActive ? 'pulse-dot-green' : 'pulse-dot-red'}`} />
              <Cpu className="w-3.5 h-3.5" style={{ color: isMlActive ? '#34d399' : '#f87171' }} />
              <span className="font-semibold hidden sm:inline" style={{ color: isMlActive ? '#34d399' : '#f87171' }}>
                {isMlActive ? 'ONNX ACTIVE' : 'MODEL ERROR'}
              </span>
            </div>

            {/* Active Session Indicator */}
            {activeSessionId && (
              <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs"
                style={{
                  background: 'rgba(79,142,247,0.08)',
                  border: '1px solid rgba(79,142,247,0.2)',
                }}>
                <Database className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-mono text-blue-300 truncate max-w-[110px]">
                  {activeSessionId.substring(0, 12)}…
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
