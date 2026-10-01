export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  products?: ChatProduct[];
  createdAt: number;
};

export type ChatProduct = {
  category: string;
  id: number;
  brand: string;
  name: string;
  specification: string;
  viscosity: string | null;
  size: string | null;
  price: number;
  in_stock: boolean;
  image_front_url: string | null;
  image_back_url: string | null;
};

export type SessionRecord = {
  session_id: string;
  created_at: number;
};

export const SESSION_STORAGE_KEY = "autolube_chat_session_v1";

export function loadSession(): SessionRecord | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (
      !parsed ||
      typeof parsed.session_id !== "string" ||
      typeof parsed.created_at !== "number"
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveSession(rec: SessionRecord): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(rec));
  } catch {
    // ignore
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function newMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
