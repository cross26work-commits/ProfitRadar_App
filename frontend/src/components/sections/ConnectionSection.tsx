import { ConnectionStatus } from "../business/ConnectionStatus";
import { SettingsSection } from "./SettingsSection";

export function ConnectionSection() {
  return (
    <SettingsSection
      title="メール連携"
      description="営業メールの接続状態を管理します。"
    >
      <ConnectionStatus
        label="Google"
        connected={false}
        description="接続状態はメール連携設定画面から確認できます。"
      />
    </SettingsSection>
  );
}
