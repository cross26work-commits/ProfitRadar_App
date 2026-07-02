import { AppShell } from "@/components/layout/AppShell";
import { AuthGuard } from "@/providers/AuthGuard";

export default function ProtectedAppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
