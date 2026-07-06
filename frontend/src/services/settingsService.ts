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

export async function getSettingsDashboard(): Promise<SettingsDashboardData> {
  const [gmail, sms, app] = await Promise.all([
    apiGet<ConnectionSetting>("/settings/gmail"),
    apiGet<ConnectionSetting>("/settings/sms"),
    apiGet<AppSetting>("/settings/app"),
  ]);

  return { gmail, sms, app };
}
