"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type ConfirmOptions = {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
};

type ConfirmFn = (
  message: string,
  options?: ConfirmOptions
) => Promise<boolean>;

const ConfirmContext = createContext<ConfirmFn | null>(null);

export function useConfirm(): ConfirmFn {
  const ctx = useContext(ConfirmContext);
  if (!ctx) {
    throw new Error("useConfirm must be used inside ConfirmProvider");
  }
  return ctx;
}

type PendingConfirm = {
  message: string;
  options: ConfirmOptions;
  resolve: (value: boolean) => void;
};

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<PendingConfirm | null>(null);

  const confirm = useCallback<ConfirmFn>((message, options = {}) => {
    return new Promise<boolean>((resolve) => {
      setPending({ message, options, resolve });
    });
  }, []);

  const close = useCallback(
    (result: boolean) => {
      if (pending) {
        pending.resolve(result);
        setPending(null);
      }
    },
    [pending]
  );

  useEffect(() => {
    if (!pending) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        close(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [pending, close]);

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {pending && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => close(false)}
        >
          <div
            className="bg-white rounded-md shadow-xl max-w-md w-full p-6"
            onClick={(event) => event.stopPropagation()}
          >
            {pending.options.title && (
              <h2
                id="confirm-title"
                className="text-lg font-semibold text-neutral-900 mb-2"
              >
                {pending.options.title}
              </h2>
            )}
            <p className="text-sm text-neutral-700 mb-6">
              {pending.message}
            </p>
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => close(false)}
                autoFocus
                className="text-sm border border-neutral-300 px-4 py-2 rounded hover:bg-neutral-100"
              >
                {pending.options.cancelLabel ?? "Annuler"}
              </button>
              <button
                type="button"
                onClick={() => close(true)}
                className={
                  "text-sm font-medium px-4 py-2 rounded " +
                  (pending.options.danger
                    ? "bg-red-600 text-white hover:bg-red-700"
                    : "bg-neutral-900 text-white hover:bg-neutral-800")
                }
              >
                {pending.options.confirmLabel ?? "Confirmer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}
