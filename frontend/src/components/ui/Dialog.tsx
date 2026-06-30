import { Button } from "./Button";
import { Card } from "./Card";

type DialogProps = {
  open: boolean;
  title: string;
  description?: string;
  children?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
};

export function Dialog({
  open,
  title,
  description,
  children,
  confirmLabel = "保存",
  cancelLabel = "閉じる",
}: DialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 p-4">
      <Card className="w-full max-w-lg p-6">
        <h2 className="text-lg font-black text-slate-900">{title}</h2>
        {description && (
          <p className="mt-2 text-sm font-medium leading-6 text-slate-500">
            {description}
          </p>
        )}
        {children && <div className="mt-5">{children}</div>}
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary">{cancelLabel}</Button>
          <Button>{confirmLabel}</Button>
        </div>
      </Card>
    </div>
  );
}
