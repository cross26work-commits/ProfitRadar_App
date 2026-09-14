import { AppShell } from "@/components/layout/AppShell";
import { OnboardingGuard } from "@/components/auth/OnboardingGuard";
import { AuthGuard } from "@/providers/AuthGuard";


export default function ProtectedAppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <OnboardingGuard>
        <AppShell>
          {children}
        </AppShell>
      </OnboardingGuard>
    </AuthGuard>
  );
}
