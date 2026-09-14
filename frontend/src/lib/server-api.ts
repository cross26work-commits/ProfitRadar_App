import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

async function getServerSupabase() {
  const cookieStore = await cookies();

  const supabaseUrl =
    process.env.NEXT_PUBLIC_SUPABASE_URL;

  const supabaseKey =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      "Supabase environment variables are missing"
    );
  }

  return createServerClient(
    supabaseUrl,
    supabaseKey,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },

        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(
              ({
                name,
                value,
                options,
              }) => {
                cookieStore.set(
                  name,
                  value,
                  options
                );
              }
            );
          } catch {
            // Server Componentでは
            // Cookie書き込み不可の場合がある。
          }
        },
      },
    }
  );
}

export async function serverApiGet<T = unknown>(
  path: string
): Promise<T> {
  const supabase =
    await getServerSupabase();

  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    throw new Error(
      "Authentication temporarily unavailable"
    );
  }

  const accessToken =
    session?.access_token;

  if (!accessToken) {
    redirect("/login");
  }

  const response = await fetch(
    `${API_BASE}${path}`,
    {
      method: "GET",
      headers: {
        Authorization:
          `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    }
  ).catch(() => { throw new Error("Data temporarily unavailable"); });

  if (!response.ok) {
    if (response.status === 401) redirect("/login");
    if (response.status === 403 || response.status === 404) notFound();
    throw new Error("Data temporarily unavailable");
  }

  return response.json().catch(() => { throw new Error("Invalid data response"); }) as Promise<T>;
}
