"use client";

import { useEffect, useRef, useState } from "react";
import { MessageCircle, X, Send, RotateCcw } from "lucide-react";
import { useChat } from "./ChatProvider";
import { ChatMessageBubble } from "./ChatMessage";

const EXAMPLES = [
  "Huile moteur",
  "Huile de boîte",
  "Filtre à huile",
];

export function ChatWidget() {
  const {
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
  } = useChat();

  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isSending]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || isSending || sessionExpired) return;
    setInput("");
    await send(text);
  }

  return (
    <>
      {/* Floating button */}
      <button
        type="button"
        onClick={isOpen ? close : open}
        aria-label={isOpen ? "Fermer le chat" : "Ouvrir le chat"}
        className="fixed bottom-5 right-5 z-40 w-14 h-14 rounded-full bg-neutral-900 text-white shadow-lg hover:bg-neutral-800 flex items-center justify-center transition-colors"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* Panel */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={close}
        >
          <div
            className="relative bg-white border border-neutral-200 rounded-lg shadow-xl w-full max-w-3xl h-[85vh] max-h-[720px] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
          {/* Header */}
          <div className="border-b border-neutral-200 px-4 py-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-900">
                Assistant AutoLube
              </p>
              <p className="text-xs text-neutral-500">Posez votre question</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={reset}
                aria-label="Nouvelle conversation"
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-100 text-neutral-500"
              >
                <RotateCcw size={16} />
              </button>
              <button
                type="button"
                onClick={close}
                aria-label="Fermer"
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-neutral-100 text-neutral-500"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center gap-4">
                <p className="text-sm text-neutral-600">
                  Bonjour. Posez-moi une question sur votre véhicule, je vous recommande les huiles adaptées.
                </p>
                <div className="flex flex-col gap-2 w-full">
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex}
                      type="button"
                      onClick={() => send(ex)}
                      className="w-full text-left text-xs text-neutral-700 border border-neutral-200 rounded-md px-3 py-2 hover:bg-neutral-50 transition-colors"
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((m) => (
                  <ChatMessageBubble key={m.id} message={m} />
                ))}
                {isSending && (
                  <p className="text-xs text-neutral-400 animate-pulse">
                    L&apos;assistant écrit…
                  </p>
                )}
                {sessionExpired && (
                  <div className="border border-amber-300 bg-amber-50 text-amber-900 text-xs p-3 rounded-md">
                    <p>La conversation a expiré.</p>
                    <button
                      type="button"
                      onClick={startNewChat}
                      className="mt-2 w-full text-center text-xs font-medium text-amber-900 border border-amber-300 rounded-md py-1.5 hover:bg-amber-100 transition-colors"
                    >
                      Démarrer une nouvelle conversation
                    </button>
                  </div>
                )}
                {error && (
                  <p className="text-red-600 text-xs">{error}</p>
                )}
              </>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-neutral-200 p-3 flex gap-2 items-end">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSending || sessionExpired}
              placeholder="Écrivez votre message…"
              className="flex-1 resize-none border border-neutral-300 rounded-md px-3 py-2 text-sm focus:border-neutral-900 focus:outline-none focus:ring-0 disabled:opacity-50"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={!input.trim() || isSending || sessionExpired}
              aria-label="Envoyer"
              className="w-10 h-10 bg-neutral-900 text-white rounded-md flex items-center justify-center disabled:bg-neutral-300 disabled:cursor-not-allowed shrink-0"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
        </div>
      )}
    </>
  );
}
