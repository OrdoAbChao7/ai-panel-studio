import { useEffect, useRef, useState } from 'react';

export interface SSEEvent {
  id?: string;
  event: string;
  data: any;
}

export function useSSE(discussionId: string | null, onEvent?: (event: SSEEvent) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const lastEventIdRef = useRef<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!discussionId) return;

    let url = `/api/discussions/${discussionId}/events`;
    if (lastEventIdRef.current) {
      url += `?last_event_id=${lastEventIdRef.current}`;
    }

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setError(new Error('SSE connection error'));
    };

    const handleGenericEvent = (type: string) => (e: MessageEvent) => {
      if (e.lastEventId) {
        lastEventIdRef.current = e.lastEventId;
      }
      try {
        const parsed = JSON.parse(e.data);
        onEvent?.({ id: e.lastEventId, event: type, data: parsed });
      } catch {
        onEvent?.({ id: e.lastEventId, event: type, data: e.data });
      }
    };

    const eventTypes = [
      'session_status_changed',
      'hand_raising',
      'speaker_selected',
      'speech_chunk',
      'speech_completed',
      'moderator_intervention',
      'consensus_updated',
      'divergence_updated',
      'session_concluded',
      'sync_required',
    ];

    eventTypes.forEach((type) => {
      eventSource.addEventListener(type, handleGenericEvent(type));
    });

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [discussionId, onEvent]);

  return { isConnected, error };
}
