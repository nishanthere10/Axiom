"use client";

import { Toaster, toast as sonnerToast } from "sonner";

type ToastType = "success" | "error" | "info";

export function ToastProvider({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <Toaster
        position="bottom-right"
        theme="dark"
        richColors
        closeButton
      />
    </>
  );
}

export function useToast() {
  const toast = (message: string, type: ToastType = "info") => {
    if (type === "success") sonnerToast.success(message);
    else if (type === "error") sonnerToast.error(message);
    else sonnerToast.info(message);
  };

  return { toast, sonner: sonnerToast };
}
