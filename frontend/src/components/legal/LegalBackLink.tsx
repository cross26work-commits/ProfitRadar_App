"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import { useAuth } from "@/providers/AuthProvider";
import { resolveLegalReturn } from "@/lib/legalReturn";

function subscribeToLocation(onStoreChange: () => void) {
  window.addEventListener("popstate", onStoreChange);
  return () => window.removeEventListener("popstate", onStoreChange);
}

export function LegalBackLink() {
  const { session, loading } = useAuth();
  const locationSearch = useSyncExternalStore(
    subscribeToLocation,
    () => window.location.search,
    () => null,
  );

  if (loading || locationSearch === null) {
    return <span className="text-sm font-semibold text-slate-600">戻る先を確認中…</span>;
  }

  const returnTo = new URLSearchParams(locationSearch).get("returnTo");
  const target = resolveLegalReturn(returnTo, Boolean(session));
  return <Link href={target.href} className="text-sm font-semibold text-emerald-800 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-700">{target.label}</Link>;
}
