import { useEffect, useRef, useState, useCallback } from "react";
import { ChatMessage, ToolActivity } from "../types";

export function useAegisWebSocket(
  sessionId: string,
  onStreamEnd?: (fullText: string) => void
) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeTools, setActiveTools] = useState<ToolActivity[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const onStreamEndRef = useRef(onStreamEnd);
  onStreamEndRef.current = onStreamEnd;
  const lastAssistantTextRef = useRef<string>("");

  useEffect(() => {
    const wsUrl = `ws://127.0.0.1:8420/ws/chat/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "stream_start") {
          setIsStreaming(true);
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              role: "assistant",
              content: "",
              timestamp: new Date().toLocaleTimeString(),
            },
          ]);
        } else if (data.type === "token") {
          lastAssistantTextRef.current += data.delta || "";
          setMessages((prev) => {
            if (prev.length === 0) return prev;
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
              last.content += data.delta;
              if (data.provider) last.provider = data.provider;
              if (data.model) last.model = data.model;
            }
            return updated;
          });
        } else if (data.type === "tool_start") {
          setActiveTools((prev) => [
            ...prev,
            {
              toolName: data.tool_name,
              arguments: data.arguments,
              status: "pending",
            },
          ]);
        } else if (data.type === "tool_result") {
          setActiveTools((prev) =>
            prev.map((t) =>
              t.toolName === data.tool_name
                ? {
                    ...t,
                    status: data.result.success ? "success" : "error",
                    result: data.result,
                  }
                : t
            )
          );
        } else if (data.type === "stream_end") {
          setIsStreaming(false);
          if (lastAssistantTextRef.current && onStreamEndRef.current) {
            onStreamEndRef.current(lastAssistantTextRef.current);
          }
          lastAssistantTextRef.current = "";
        }
      } catch (err) {
        console.error("Failed to parse websocket message:", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);

  const sendMessage = useCallback((content: string, confirmed = false) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    // Add user message to UI immediately
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    socketRef.current.send(
      JSON.stringify({
        type: "user_message",
        content,
        user_confirmed: confirmed,
      })
    );
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setActiveTools([]);
  }, []);

  return {
    messages,
    activeTools,
    isStreaming,
    isConnected,
    sendMessage,
    clearMessages,
  };
}

