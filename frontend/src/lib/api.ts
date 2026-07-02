import { supabase } from "@/lib/supabase/client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function createHeaders() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }

  return headers;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: await createHeaders(),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API GET failed: ${path} ${response.status} ${errorText}`);
  }

  return response.json() as Promise<T>;
}

export async function apiPost<T>(
  path: string,
  body: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: await createHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`API POST failed: ${path} ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function apiPut<T>(
  path: string,
  body: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: await createHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`API PUT failed: ${path} ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function apiDelete(
  path: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
    headers: await createHeaders(),
  });

  if (!response.ok) {
    throw new Error(`API DELETE failed: ${path} ${response.status}`);
  }
}
