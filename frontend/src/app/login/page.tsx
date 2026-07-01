import { PageStack } from "@/components/sections/PageStack";
import { PageHeader } from "@/components/sections/PageHeader";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  return (
    <PageStack>
      <PageHeader
        title="ログイン"
        description="Profit Radarへサインインします。"
      />

      <Card className="mx-auto w-full max-w-md p-6">
        <div className="space-y-4">
          <Input
            label="メールアドレス"
            type="email"
            placeholder="example@company.com"
          />

          <Input
            label="パスワード"
            type="password"
            placeholder="********"
          />

          <div className="grid gap-3">
            <Button>
              ログイン
            </Button>

            <Button variant="secondary">
              新規登録
            </Button>
          </div>
        </div>
      </Card>
    </PageStack>
  );
}
