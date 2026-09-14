import { supabase } from "@/lib/supabase/client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function deleteCurrentAccount(params: {
  password: string;
  confirmation: string;
}) {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("ログイン情報を確認できません。");
  }

  const response = await fetch(`${API_BASE_URL}/account`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
    },
    body: JSON.stringify({
      password: params.password,
      confirmation: params.confirmation,
    }),
  });

  if (!response.ok) {
    let message = "アカウント削除に失敗しました。";

    try {
      const body = await response.json();

      if (body?.detail) {
        message = body.detail;
      }
    } catch {}

    throw new Error(message);
  }

  const result = await response.json();
  if (result.success !== true || result.status !== "completed") {
    throw new Error("削除処理は未完了です。運営者へ状態を確認してください。");
  }
  return result;
}
