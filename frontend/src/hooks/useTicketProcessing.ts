/**
 * Hook for WebSocket connection to track ticket processing in real-time
 *
 * Usage:
 * ```jsx
 * const { status, message, progress, error, logs } = useTicketProcessing(ticketId);
 * ```
 */

import { useState, useEffect, useCallback, useRef } from "react";

export interface ProcessingStatus {
  status: "idle" | "open" | "in_progress" | "pending_validation" | "closed" | "cancelled";
  message: string;
  step?: string;
  progress?: number;
  error?: string;
  data?: Record<string, unknown>;
}

export interface LogEntry {
  level: "INFO" | "WARNING" | "ERROR" | "DEBUG";
  message: string;
  timestamp: string;
}

export function useTicketProcessing(ticketId: string | null) {
  const [status, setStatus] = useState<ProcessingStatus>({
    status: "idle",
    message: "En attente...",
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!ticketId) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Create WebSocket connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/tickets/${ticketId}`;

    console.log("[WebSocket] Connecting to:", wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[WebSocket] Connected for ticket", ticketId);
      setIsConnected(true);

      // Send heartbeat every 30 seconds
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 30000);

      ws.addEventListener("close", () => clearInterval(heartbeat));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("[WebSocket] Message received:", data);

        if (data.type === "status_update") {
          setStatus({
            status: data.status,
            message: data.message,
            step: data.step,
            progress: data.progress,
            error: data.error,
            data: data.data,
          });
        } else if (data.type === "log") {
          const logEntry: LogEntry = {
            level: data.level,
            message: data.message,
            timestamp: data.timestamp || new Date().toISOString(),
          };
          setLogs((prev) => [...prev, logEntry]);
        } else if (data.type === "connected") {
          console.log("[WebSocket] Connection confirmed");
        } else if (data.type === "pong") {
          // Heartbeat response
        }
      } catch (error) {
        console.error("[WebSocket] Error parsing message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("[WebSocket] Error:", error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log("[WebSocket] Disconnected");
      setIsConnected(false);
    };

    wsRef.current = ws;
  }, [ticketId]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      console.log("[WebSocket] Disconnecting...");
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Auto-connect when ticketId changes
  useEffect(() => {
    if (ticketId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [ticketId, connect, disconnect]);

  return {
    status: status.status,
    message: status.message,
    step: status.step,
    progress: status.progress,
    error: status.error,
    data: status.data,
    logs,
    isConnected,
    connect,
    disconnect,
  };
}
