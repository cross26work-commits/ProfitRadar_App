import { apiGet } from "@/lib/api";

export type ConnectionSetting = {
  connected: boolean;
  label: string;
  description: string;
  provider: string;
};

export type AppSetting = {
  company: string;
  plan: string;
  message: string;
};

export type SettingsDashboardData = {
  gmail: ConnectionSetting;
  sms: ConnectionSetting;
  app: AppSetting;
};

const fallbackSettings: SettingsDashboardData = {
  gmail: {
    connected: false,
    label: "接続状態",
    description: "Gmail OAuthは未接続です。",
    provider: "gmail",
  },
  sms: {
    connected: false,
    label: "SMS状態",
    description: "Twilio SMSは未接続です。",
    provider: "twilio",
  },
  app: {
    company: "未設定",
    plan: "未契約",
    message: "settings fallback",
  },
};

export async function getSettingsDashboard(): Promise<SettingsDashboardData> {
  try {
    const [gmail, sms, app] = await Promise.all([
      apiGet<ConnectionSetting>("/settings/gmail"),
      apiGet<ConnectionSetting>("/settings/sms"),
      apiGet<AppSetting>("/settings/app"),
    ]);

    return { gmail, sms, app };
  } catch {
    return fallbackSettings;
  }
}
