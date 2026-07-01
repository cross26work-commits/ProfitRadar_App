import { PageStack } from "@/components/sections/PageStack";
import { PageHeader } from "@/components/sections/PageHeader";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/ui/Button";

export default function RegisterPage() {
  return (
    <PageStack>
      <PageHeader
        title="新規登録"
        description="Profit Radarのアカウントを作成します。"
      />

      <Card className="mx-auto w-full max-w-md p-6">
        <div className="space-y-4">
          <Input
            label="会社名"
            placeholder="株式会社サンプル"
          />

          <Input
            label="お名前"
            placeholder="山田 太郎"
          />

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

          <Input
            label="パスワード（確認）"
            type="password"
            placeholder="********"
          />

          <div className="grid gap-3">
            <Button>
              アカウントを作成
            </Button>

            <Button variant="secondary">
              ログインへ戻る
            </Button>
          </div>
        </div>
      </Card>
    </PageStack>
  );
}
