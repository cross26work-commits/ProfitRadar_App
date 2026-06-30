import { ConnectionStatus } from "../business/ConnectionStatus";
import { ActionBar } from "../ui/ActionBar";
import { Button } from "../ui/Button";
import { SettingsSection } from "./SettingsSection";

export function ConnectionSection() {
  return (
    <SettingsSection
      title="Gmail接続"
      description="現在はダミー表示です。FastAPI接続後にOAuth状態を表示します。"
    >
      <ConnectionStatus
        label="接続状態"
        connected={false}
        description="Gmail OAuthは未接続です。"
      />
      <ActionBar>
        <Button>Gmailを接続する</Button>
      </ActionBar>
    </SettingsSection>
  );
}
