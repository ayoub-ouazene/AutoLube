"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/chat";
import { ChatProductCards } from "./ChatProductCards";

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`${
          isUser
            ? "bg-neutral-900 text-white self-end"
            : "bg-neutral-100 text-neutral-900 self-start"
        } rounded-lg px-3 py-2 max-w-[85%] text-sm`}
      >
        {isUser ? (
          <p>{message.text}</p>
        ) : (
          <div className="chat-md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.text}
            </ReactMarkdown>
            {message.products && message.products.length > 0 && (
              <ChatProductCards products={message.products} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
