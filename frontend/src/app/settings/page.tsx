import { ConnectionStatus } from "@/components/business/ConnectionStatus";
import { PageHeader } from "@/components/sections/PageHeader";
import { PageStack } from "@/components/sections/PageStack";
import { SettingsSection } from "@/components/sections/SettingsSection";
import { ActionBar } from "@/components/ui/ActionBar";
import { Button } from "@/components/ui/Button";
import { MiniPanel } from "@/components/ui/MiniPanel";
import { getSettingsDashboard } from "@/services/settingsService";

export default async function SettingsPage() {
  const settings = await getSettingsDashboard();

  return (
    <PageStack>
      <PageHeader
        title="設定"
        description="Gmail接続・通知・アプリ設定を管理します。"
      />

      <SettingsSection
        title="Gmail接続"
        description="FastAPIからOAuth状態を取得します。"
      >
        <ConnectionStatus
          label={settings.gmail.label}
          connected={settings.gmail.connected}
          description={settings.gmail.description}
        />

        <ActionBar>
          <Button>Gmailを接続する</Button>
        </ActionBar>
      </SettingsSection>

      <SettingsSection
        title="通知設定"
        description="メール・SMS通知の基本設定です。"
      >
        <ConnectionStatus
          label={settings.sms.label}
          connected={settings.sms.connected}
          description={settings.sms.description}
        />
        <MiniPanel title="高優先度通知" description="高利益案件を通知します。" />
        <MiniPanel title="返信遅延通知" description="一定日数以上放置された案件を通知します。" />
      </SettingsSection>

      <SettingsSection
        title="アプリ設定"
        description="販売版へ向けた基本設定項目です。"
      >
        <MiniPanel title="会社情報" description={settings.app.company} />
        <MiniPanel title="プラン管理" description={settings.app.plan} />
      </SettingsSection>
    </PageStack>
  );
}
