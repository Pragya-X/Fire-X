"use client";

import { useEffect, useRef, useState } from "react";
import { streamUrl } from "@/lib/api";

export interface SseEvent {
  type: string;
  data: unknown;
}

/**
 * Subscribes to the backend SSE stream. Returns the latest event and a rolling
 * list of recent events (used by the command-center live feed).
 */
export function useSSE(maxEvents = 50) {
  const [latest, setLatest] = useState<SseEvent | null>(null);
  const [events, setEvents] = useState<SseEvent[]>([]);
  const retryRef = useRef<number>(0);

  useEffect(() => {
    let es: EventSource | null = null;
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      es = new EventSource(streamUrl());
      es.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data) as SseEvent;
          if (!parsed || !parsed.type) return;
          setLatest(parsed);
          setEvents((prev) => [parsed, ...prev].slice(0, maxEvents));
        } catch {
          /* keepalive or malformed frame */
        }
      };
      es.onerror = () => {
        es?.close();
        retryRef.current = Math.min(retryRef.current + 1, 6);
        setTimeout(connect, 3000 * retryRef.current);
      };
      es.onopen = () => {
        retryRef.current = 0;
      };
    };

    connect();
    return () => {
      disposed = true;
      es?.close();
    };
  }, [maxEvents]);

  return { latest, events };
}