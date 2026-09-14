import "server-only";

import { createSupabaseServerClient } from "@/lib/supabase/server";
import { notFound, redirect } from "next/navigation";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function createServerHeaders(): Promise<HeadersInit> {
  const supabase = await createSupabaseServerClient();

  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    throw new Error("Authentication temporarily unavailable");
  }

  if (!session?.access_token) {
    redirect("/login");
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session.access_token}`,
  };
}

export async function apiGetServer<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: await createServerHeaders(),
    cache: "no-store",
  }).catch(() => { throw new Error("Data temporarily unavailable"); });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    if (response.status === 403 || response.status === 404) notFound();
    throw new Error("Data temporarily unavailable");
  }

  return response.json().catch(() => { throw new Error("Invalid data response"); }) as Promise<T>;
}
