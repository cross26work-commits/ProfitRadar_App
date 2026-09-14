"use client";

import { ReactNode, useEffect } from "react";
import { Button } from "./Button";
import { Card } from "./Card";

type DialogProps = {
  open: boolean;
  title: string;
  description?: string;
  children?: ReactNode;

  confirmLabel?: string;
  cancelLabel?: string;

  variant?: "default" | "danger";
  loading?: boolean;

  onConfirm?: () => void;
  onCancel?: () => void;
};

export function Dialog({
  open,
  title,
  description,
  children,
  confirmLabel = "確認",
  cancelLabel = "キャンセル",
  variant = "default",
  loading = false,
  onConfirm,
  onCancel,
}: DialogProps) {
  useEffect(() => {
    if (!open) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !loading) {
        onCancel?.();
      }
    }

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, [open, loading, onCancel]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !loading) {
          onCancel?.();
        }
      }}
    >
      <Card className="max-h-[90dvh] w-full max-w-lg overflow-y-auto p-6 shadow-xl">
        <h2 className="text-xl font-bold text-slate-900">
          {title}
        </h2>

        {description ? (
          <p className="mt-3 text-sm leading-6 text-slate-600">
            {description}
          </p>
        ) : null}

        {children ? (
          <div className="mt-6">
            {children}
          </div>
        ) : null}

        <div className="mt-7 flex justify-end gap-3">
          <Button
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelLabel}
          </Button>

          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            onClick={onConfirm}
            loading={loading}
          >
            {confirmLabel}
          </Button>
        </div>
      </Card>
    </div>
  );
}
