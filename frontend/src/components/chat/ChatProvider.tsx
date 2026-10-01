"use client";

import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from "react";
import {
  ChatMessage,
  ChatProduct,
  SessionRecord,
  clearSession,
  loadSession,
  newMessageId,
  saveSession,
} from "@/lib/chat";

type ChatContextValue = {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  messages: ChatMessage[];
  isSending: boolean;
  error: string | null;
  sessionExpired: boolean;
  send: (text: string) => Promise<void>;
  startNewChat: () => Promise<void>;
  reset: () => void;
};

const ChatContext = createContext<ChatContextValue | null>(null);

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

async function createSession(): Promise<SessionRecord> {
  const res = await fetch(`${API_URL}/chat/session`, { method: "POST" });
  if (!res.ok) throw new Error(`Session creation failed: ${res.status}`);
  const data = await res.json();
  const rec: SessionRecord = {
    session_id: data.session_id,
    created_at: Date.now(),
  };
  saveSession(rec);
  return rec;
}

async function sendMessage(
  sessionId: string,
  text: string
): Promise<{ reply: string; products: ChatProduct[] }> {
  const res = await fetch(`${API_URL}/chat/session/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  if (res.status === 404) {
    throw new Error("SESSION_EXPIRED");
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Send failed: ${res.status} ${body}`);
  }
  return res.json();
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  // Text of the last user message that failed due to session expiry.
  // Used to auto-resend after the user starts a new chat.
  const pendingResendRef = useRef<string | null>(null);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  const reset = useCallback(() => {
    clearSession();
    setMessages([]);
    setError(null);
    setSessionExpired(false);
    pendingResendRef.current = null;
  }, []);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) return;

      // If session already marked expired, don't attempt to send.
      // Ask the user to start a new chat instead.
      if (sessionExpired) {
        pendingResendRef.current = trimmed;
        return;
      }

      const userMsg: ChatMessage = {
        id: newMessageId(),
        role: "user",
        text: trimmed,
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsSending(true);
      setError(null);

      try {
        let session = loadSession();
        if (!session) {
          session = await createSession();
        }

        const result = await sendMessage(session.session_id, trimmed);

        const assistantMsg: ChatMessage = {
          id: newMessageId(),
          role: "assistant",
          text: result.reply,
          products: result.products ?? [],
          createdAt: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        if (err instanceof Error && err.message === "SESSION_EXPIRED") {
          // Session died. Do NOT retry. Surface the state so the widget
          // can show the "start new chat" button.
          clearSession();
          setSessionExpired(true);
          pendingResendRef.current = trimmed;
        } else {
          console.error("Chat send error:", err);
          setError(
            "Le service est momentanément indisponible. Veuillez réessayer."
          );
        }
      } finally {
        setIsSending(false);
      }
    },
    [isSending, sessionExpired]
  );

  const startNewChat = useCallback(async () => {
    clearSession();
    setSessionExpired(false);
    setError(null);

    const toResend = pendingResendRef.current;
    pendingResendRef.current = null;

    try {
      await createSession();
    } catch (err) {
      console.error("New chat creation failed:", err);
      setError(
        "Impossible de démarrer une nouvelle conversation. Réessayez."
      );
      return;
    }

    if (toResend) {
      // Re-send the message the user already typed. Do NOT add a new
      // user bubble — the previous one is still visible and this is
      // the same message.
      setIsSending(true);
      try {
        const session = loadSession();
        if (!session) throw new Error("No session after creation");
        const result = await sendMessage(session.session_id, toResend);
        const assistantMsg: ChatMessage = {
          id: newMessageId(),
          role: "assistant",
          text: result.reply,
          products: result.products ?? [],
          createdAt: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        console.error("Resend after new chat failed:", err);
        setError("Le service est momentanément indisponible.");
      } finally {
        setIsSending(false);
      }
    }
  }, []);

  const value: ChatContextValue = {
    isOpen,
    open,
    close,
    messages,
    isSending,
    error,
    sessionExpired,
    send,
    startNewChat,
    reset,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used inside <ChatProvider>");
  return ctx;
}
