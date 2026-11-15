export type SessionStatus = 'created' | 'running' | 'paused' | 'completed' | 'terminated';

export type ActionType =
  | 'statement'
  | 'rebuttal'
  | 'supplement'
  | 'question'
  | 'clarification'
  | 'consensus_proposal'
  | 'concession'
  | 'none';

export interface Participant {
  id: string;
  name: string;
  occupation: string;
  stance: string;
  perspective: string;
  color_hex: string;
  role: 'expert' | 'moderator';
  total_turns_spoken: number;
}

export interface Turn {
  id: string;
  turn_number: number;
  round_number: number;
  speaker_id: string;
  speaker_name: string;
  action_type: ActionType;
  content: string;
  rationale?: string;
  priority_score: number;
  target_speaker_id?: string | null;
  timestamp: string;
}

export interface ConsensusItem {
  id: string;
  statement: string;
  supporting_agents: string[];
  confidence: number;
  resolved_turn?: number;
}

export interface DivergenceItem {
  id: string;
  tension: string;
  opposing_stances: Record<string, string>;
  intensity: number;
  is_active: boolean;
}

export interface Discussion {
  id: string;
  topic: string;
  status: SessionStatus;
  current_round: number;
  max_rounds: number;
  participants: Participant[];
  summary?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface HandRaisingItem {
  agent_id: string;
  agent_name: string;
  action_type: ActionType;
  priority_score: number;
  target_speaker_id?: string | null;
  rationale: string;
}

export interface SpeakerSelectedData {
  speaker_id: string;
  speaker_name: string;
  score: number;
  score_breakdown: Record<string, number>;
}

export interface SpeechChunkData {
  turn_id: string;
  speaker_id: string;
  chunk: string;
  is_first: boolean;
}

export interface SpeechCompletedData {
  turn_id: string;
  speaker_id: string;
  turn_number: number;
  round_number?: number;
  content: string;
  action_type: ActionType;
}

export interface ModeratorInterventionData {
  type: string;
  content: string;
  target_agent_id?: string | null;
}

export interface SessionConcludedData {
  summary: string;
  final_stances: Record<string, string>;
}

export interface StanceAuditItem {
  participant_id: string;
  name: string;
  initial_stance: string;
  final_stance: string;
  shifted: boolean;
  turns_spoken: number;
}

export interface SummaryData {
  discussion_id: string;
  topic: string;
  status: SessionStatus;
  summary: string;
  consensus_items: ConsensusItem[];
  divergence_items: DivergenceItem[];
  stance_audit: StanceAuditItem[];
}
