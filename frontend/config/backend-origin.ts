type Environment = Record<string, string | undefined>;

function origin(value: string | undefined, production: boolean): string {
  try {
    const url = new URL(value ?? "");
    if (url.username || url.password || url.search || url.hash ||
        !["", "/"].includes(url.pathname) ||
        (production ? url.protocol !== "https:" : !["http:", "https:"].includes(url.protocol))) {
      throw new Error();
    }
    if (production && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) throw new Error();
    return url.origin;
  } catch {
    // Never include a misconfigured URL (which may contain credentials) in logs.
    throw new Error("Backend origin configuration is invalid; production requires an explicit HTTPS origin");
  }
}

export function backendOrigin(env: Environment): string {
  const production = env.NODE_ENV === "production";
  if (production) origin(env.NEXT_PUBLIC_API_BASE_URL, true);
  return origin(env.BACKEND_ORIGIN ?? (production ? undefined : "http://127.0.0.1:8000"), production);
}
