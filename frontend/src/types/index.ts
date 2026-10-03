export type Decision = 'ALLOW' | 'REVIEW' | 'BLOCK';
export type IncidentStatus = 'OPEN' | 'RESOLVED' | 'FALSE_POSITIVE' | 'INVESTIGATING';
export type IncidentSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface MLStatusInfo {
  model_name: string;
  runtime: string;
  status: 'MODEL ACTIVE' | 'MODEL ERROR' | 'INITIALIZING';
  model_path: string;
  last_latency_ms: number;
  last_prediction: number;
  total_predictions: number;
  errors: number;
  last_error: string | null;
}

export interface MLPredictResponse {
  threat_score: number;
  status: string;
  latency_ms: number;
  model_name: string;
  error?: string;
}

export interface RiskFactors {
  threat: number;
  permission_violation: number;
  behavioral_dev: number;
  resource_sens: number;
  action_crit: number;
}

export interface RiskAssessment {
  threat_score: number;
  total_risk: number;
  decision: Decision;
  factors: RiskFactors;
}

export interface SecurityEvaluation {
  decision: Decision;
  reason: string;
  latency_ms: number;
  envelope_token: string;
  risk_assessment: RiskAssessment;
}

export interface TavilySource {
  title: string;
  url: string;
  content: string;
  score: number;
}

export interface ResearchSessionRecord {
  session_id: string;
  agent_id: string;
  query: string;
  status: string;
  research_notes: string | null;
  tavily_sources: TavilySource[];
  cancellation_token: string | null;
  cancellation_reason: string | null;
  security: SecurityEvaluation;
}

export interface FileEntry {
  name: string;
  path: string;
  type: 'file' | 'dir';
  size?: number;
  modified_at?: string;
  children?: FileEntry[];
}

export interface WorkspaceTreeResponse {
  session_id?: string;
  path: string;
  entries: FileEntry[];
  error?: string;
}

export interface FileContentResponse {
  content: string;
  path: string;
  bytes: number;
  created_at?: string;
  modified_at?: string;
  error?: string;
}

export interface SandboxStatusResponse {
  session_id: string;
  agent_role: string;
  workspace_root: string;
  status: string;
  isolation_status: string;
  circuit_breaker_state: string;
  allowed_tools: string[];
  blocked_tools: string[];
  active_session?: any;
}

export interface CoderRunResponse {
  session_id: string;
  status: string;
  generated_code?: string;
  cancellation_token?: string;
  cancellation_reason?: string;
  gateway_results?: any;
}

export interface DeployerRunResponse {
  session_id: string;
  status: string;
  deployment_receipt?: string;
  cancellation_token?: string;
  cancellation_reason?: string;
  gateway_results?: any;
}

export interface ForensicReport {
  cwe_id: string;
  attack_vector: string;
  // 7-section structured report
  incident_summary?: string;
  suspicion_reasoning?: string;
  threat_indicators?: string[];
  behavioral_anomalies?: string;
  potential_impact?: string;
  recommended_response?: string;
  forensic_confidence: number;
  confidence_notes?: string;
  // Legacy fields
  threat_summary: string;
  affected_components: string[];
  suggested_patch: string;
}

export interface IncidentRecord {
  id: string;
  agent_id: string;
  session_id: string;
  tool_call_id?: string;
  risk_score: number;
  threat_score?: number;
  permission_score?: number;
  behavioral_score?: number;
  sensitivity_score?: number;
  criticality_score?: number;
  decision: Decision;
  severity: IncidentSeverity;
  status: IncidentStatus;
  created_at: string;
  resolved_at?: string | null;
  tool_name?: string;
  role?: string;
  reasons?: string[];
  payload_preview?: string;
  circuit_breaker_triggered?: boolean;
  prior_tool_calls?: number;
}

export interface AuditLogEntry {
  id?: string;
  event_name: string;
  actor: string;
  payload: any;
  created_at: string;
}
