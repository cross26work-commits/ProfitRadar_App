import { supabase } from "@/lib/supabase/client";

export async function signInWithEmail(
  email: string,
  password: string
) {
  const { data, error } =
    await supabase.auth.signInWithPassword({
      email,
      password,
    });

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function signUpWithEmail(params: {
  email: string;
  password: string;
  companyName: string;
  name: string;
}) {
  const { data, error } = await supabase.auth.signUp({
    email: params.email,
    password: params.password,
    options: {
      data: {
        company_name: params.companyName,
        name: params.name,
      },
    },
  });

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function requestPasswordReset(
  email: string
) {
  const redirectTo =
    typeof window !== "undefined"
      ? `${window.location.origin}/reset-password`
      : undefined;

  const { data, error } =
    await supabase.auth.resetPasswordForEmail(
      email,
      {
        redirectTo,
      }
    );

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function updatePassword(
  password: string
) {
  const { data, error } =
    await supabase.auth.updateUser({
      password,
    });

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw new Error(error.message);
  }
}

export async function getCurrentSession() {
  const { data, error } =
    await supabase.auth.getSession();

  if (error) {
    throw new Error(error.message);
  }

  return data.session;
}
