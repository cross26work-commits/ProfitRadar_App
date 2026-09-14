import { supabase } from "@/lib/supabase/client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public readonly status: number) {
    super(({401:"ログインし直してください。",402:"試用・契約期間をご確認ください。",409:"別の処理が進行中です。",413:"入力が長すぎます。",429:"利用上限に達しました。",503:"一時的に利用できません。"} as Record<number,string>)[status] || "操作を完了できませんでした。");
    this.name = "ApiError";
  }
}


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


async function handleSpecialResponse(response: Response) {
  if (
    response.status === 428 &&
    typeof window !== "undefined"
  ) {
    window.location.replace("/onboarding");

    await new Promise(() => {});
  }
}


async function parseError(
  response: Response,
  method: string,
  path: string
): Promise<never> {
  await handleSpecialResponse(response);

  void method; void path;
  throw new ApiError(response.status);
}


export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: await createHeaders(),
    cache: "no-store",
  });

  if (!response.ok) {
    return parseError(response, "GET", path);
  }

  return response.json() as Promise<T>;
}


export async function apiPost<T>(
  path: string,
  body?: unknown
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: await createHeaders(),
    body: body === undefined
      ? undefined
      : JSON.stringify(body),
  });

  if (!response.ok) {
    return parseError(response, "POST", path);
  }

  return response.json() as Promise<T>;
}


export async function apiPatch<T>(
  path: string,
  body?: unknown
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: await createHeaders(),
    body: body === undefined
      ? undefined
      : JSON.stringify(body),
  });

  if (!response.ok) {
    return parseError(response, "PATCH", path);
  }

  return response.json() as Promise<T>;
}


export async function apiPut<T>(
  path: string,
  body?: unknown
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: await createHeaders(),
    body: body === undefined
      ? undefined
      : JSON.stringify(body),
  });

  if (!response.ok) {
    return parseError(response, "PUT", path);
  }

  return response.json() as Promise<T>;
}


export async function apiDelete<T>(
  path: string
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
    headers: await createHeaders(),
  });

  if (!response.ok) {
    return parseError(response, "DELETE", path);
  }

  return response.json() as Promise<T>;
}
