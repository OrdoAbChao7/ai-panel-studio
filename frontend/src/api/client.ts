import { Discussion, Participant, Turn, SummaryData } from '../types';

const BASE_URL = '/api';

export async function generateRoster(topic: string, participantCount: number = 4) {
  const res = await fetch(`${BASE_URL}/discussions/roster/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, participant_count: participantCount }),
  });
  if (!res.ok) throw new Error(`Failed to generate roster: ${res.statusText}`);
  return res.json();
}

export async function createDiscussion(
  topic: string,
  maxRounds: number,
  participants: Partial<Participant>[]
): Promise<Discussion> {
  const res = await fetch(`${BASE_URL}/discussions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, max_rounds: maxRounds, participants }),
  });
  if (!res.ok) throw new Error(`Failed to create discussion: ${res.statusText}`);
  return res.json();
}

export async function listDiscussions(): Promise<Discussion[]> {
  const res = await fetch(`${BASE_URL}/discussions`);
  if (!res.ok) throw new Error(`Failed to list discussions: ${res.statusText}`);
  return res.json();
}

export async function getDiscussion(id: string): Promise<Discussion> {
  const res = await fetch(`${BASE_URL}/discussions/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch discussion: ${res.statusText}`);
  return res.json();
}

export async function controlDiscussion(id: string, action: 'start' | 'pause' | 'resume' | 'terminate') {
  const res = await fetch(`${BASE_URL}/discussions/${id}/${action}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to ${action} discussion: ${res.statusText}`);
  return res.json();
}

export async function getTranscript(id: string): Promise<Turn[]> {
  const res = await fetch(`${BASE_URL}/discussions/${id}/transcript`);
  if (!res.ok) throw new Error(`Failed to fetch transcript: ${res.statusText}`);
  return res.json();
}

export async function getSummary(id: string): Promise<SummaryData> {
  const res = await fetch(`${BASE_URL}/discussions/${id}/summary`);
  if (!res.ok) throw new Error(`Failed to fetch summary: ${res.statusText}`);
  return res.json();
}
