"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ChatMessage,
  ChatProduct,
  SessionRecord,
  clearMessages,
  clearSession,
  loadMessages,
  loadSession,
  newMessageId,
  saveMessages,
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

  useEffect(() => {
    const persisted = loadMessages();
    if (persisted && persisted.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time hydration from localStorage
      setMessages(persisted);
    }
  }, []);

  useEffect(() => {
    // Skip the initial empty run to avoid clobbering persisted messages
    // before loadMessages fires.
    if (messages.length === 0) return;
    saveMessages(messages);
  }, [messages]);

  // Text of the last user message that failed due to session expiry.
  // Used to auto-resend after the user starts a new chat.
  const pendingResendRef = useRef<string | null>(null);

  const open = useCallback(() => {
    setIsOpen(true);

    // If we have a stored session but no visible messages, and the
    // stored session is past the TTL, silently forget it. Next send
    // will recreate. Prevents a stale ID from triggering the popup on
    // an otherwise-empty chat.
    const rec = loadSession();
    if (rec && messages.length === 0) {
      // Mirrors backend values in chat_service.py:
      //   _SESSION_MAX_SECONDS = 30 * 60
      //   _SESSION_IDLE_SECONDS = 10 * 60
      const TTL_HARD_MS = 30 * 60 * 1000;
      const TTL_IDLE_MS = 10 * 60 * 1000;
      const now = Date.now();
      const createdAgo = now - rec.created_at;
      const idleAgo = rec.last_activity
        ? now - rec.last_activity
        : createdAgo;
      if (createdAgo > TTL_HARD_MS || idleAgo > TTL_IDLE_MS) {
        clearSession();
      }
    }
  }, [messages.length]);
  const close = useCallback(() => setIsOpen(false), []);

  const reset = useCallback(() => {
    const rec = loadSession();
    if (rec) {
      // Fire-and-forget. Do not block UI on the delete.
      const url = `${API_URL}/chat/session/${rec.session_id}`;
      fetch(url, { method: "DELETE" }).catch(() => {
        // ignore — the session will expire on its own
      });
    }
    clearSession();
    clearMessages();
    setMessages([]);
    setError(null);
    setSessionExpired(false);
    pendingResendRef.current = null;
  }, []);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isSending || sessionExpired) {
      if (sessionExpired) pendingResendRef.current = trimmed;
      return;
    }

    // Append the user bubble first (matches current behavior).
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
      if (!session) session = await createSession();

      const result = await sendMessage(session.session_id, trimmed);

      // Update last_activity on success.
      const rec = loadSession();
      if (rec) saveSession({ ...rec, last_activity: Date.now() });

      const replyText =
        result.reply && result.reply.trim().length > 0
          ? result.reply
          : result.products && result.products.length > 0
            ? ""
            : "Je n'ai pas de réponse à vous proposer pour le moment.";

      const assistantMsg: ChatMessage = {
        id: newMessageId(),
        role: "assistant",
        text: replyText,
        products: result.products ?? [],
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      if (err instanceof Error && err.message === "SESSION_EXPIRED") {
        // If there has never been an assistant reply in this visible
        // conversation, this is a "first message" scenario: silently
        // recreate the session and retry, no popup.
        //
        // NOTE: `messages` here reflects state BEFORE the user bubble
        // was appended (closure snapshot). If the chat was empty prior
        // to this send, `messages` is [] and hasAssistantReply is false.
        const hasAssistantReply = messages.some((m) => m.role === "assistant");

        if (!hasAssistantReply) {
          clearSession();
          try {
            const fresh = await createSession();
            const retry = await sendMessage(fresh.session_id, trimmed);
            const rec = loadSession();
            if (rec) saveSession({ ...rec, last_activity: Date.now() });

            const replyText =
              retry.reply && retry.reply.trim().length > 0
                ? retry.reply
                : retry.products && retry.products.length > 0
                  ? ""
                  : "Je n'ai pas de réponse à vous proposer pour le moment.";

            const assistantMsg: ChatMessage = {
              id: newMessageId(),
              role: "assistant",
              text: replyText,
              products: retry.products ?? [],
              createdAt: Date.now(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
            return;
          } catch {
            // Silent retry also failed — fall through to popup.
          }
        }

        // Non-empty history, or silent retry failed: show popup.
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
  }

  const startNewChat = useCallback(async () => {
    clearSession();
    clearMessages();
    setMessages([]);
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
        const rec = loadSession();
        if (rec) saveSession({ ...rec, last_activity: Date.now() });
        const replyText =
          result.reply && result.reply.trim().length > 0
            ? result.reply
            : result.products && result.products.length > 0
              ? ""
              : "Je n'ai pas de réponse à vous proposer pour le moment.";
        const assistantMsg: ChatMessage = {
          id: newMessageId(),
          role: "assistant",
          text: replyText,
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
