"use client";

import { MessageCircle } from "lucide-react";
import { useChat } from "@/components/chat/ChatProvider";

export function OpenChatButton({ className }: { className?: string }) {
  const { open } = useChat();
  return (
    <button type="button" onClick={open} className={className}>
      <MessageCircle size={17} aria-hidden="true" /> Demander conseil
    </button>
  );
}