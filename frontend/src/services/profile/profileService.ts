import { supabase } from "@/lib/supabase/client";

export type AppProfile = {
  userId: string;
  email: string;
  name: string;
  role: string;
  companyId: string;
  companyName: string;
  plan: string;
};

export async function createCompanyAndProfile(params: {
  userId: string;
  companyName: string;
  name: string;
}) {
  const { data: company, error: companyError } = await supabase
    .from("companies")
    .insert({
      name: params.companyName,
      plan: "free",
    })
    .select("id, name, plan")
    .single();

  if (companyError) {
    throw new Error(companyError.message);
  }

  const { error: profileError } = await supabase
    .from("profiles")
    .insert({
      user_id: params.userId,
      company_id: company.id,
      name: params.name,
      role: "owner",
    });

  if (profileError) {
    throw new Error(profileError.message);
  }

  return company;
}

export async function getCurrentAppProfile(): Promise<AppProfile | null> {
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError) {
    if (userError.message.includes("User from sub claim in JWT does not exist")) {
      await supabase.auth.signOut();
      return null;
    }

    throw new Error(userError.message);
  }

  if (!user) {
    return null;
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select(`
      user_id,
      name,
      role,
      company_id,
      companies (
        name,
        plan
      )
    `)
    .eq("user_id", user.id)
    .single();

  if (profileError) {
    return {
      userId: user.id,
      email: user.email ?? "",
      name: user.email ?? "未設定",
      role: "owner",
      companyId: "",
      companyName: "未設定",
      plan: "free",
    };
  }

  const company = Array.isArray(profile.companies)
    ? profile.companies[0]
    : profile.companies;

  return {
    userId: profile.user_id,
    email: user.email ?? "",
    name: profile.name,
    role: profile.role,
    companyId: profile.company_id,
    companyName: company?.name ?? "未設定",
    plan: company?.plan ?? "free",
  };
}
