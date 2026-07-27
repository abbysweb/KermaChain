"use client";

import { useEffect, useRef, useState } from "react";
import type { WsMessage } from "./types";

const WS_BASE =
  (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3001") + "/ws/live";

export function useWebSocket(onMessage: (msg: WsMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_BASE);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data);
          onMessage(msg);
        } catch {}
      };
    };

    connect();
    return () => wsRef.current?.close();
  }, [onMessage]);

  return { connected };
}
