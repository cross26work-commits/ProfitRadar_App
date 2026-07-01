# Phase3 認証・ユーザー管理・会社管理 設計

## 目的

Profit Radarを単一ユーザー用アプリから、販売可能なSaaS構成へ移行する。

## Phase3の対象

- 認証
- ユーザー管理
- 会社管理
- 会社別データ分離
- セッション管理
- 将来のGmail OAuth分離
- 将来のStripe課金連携

## 採用候補

Supabase Auth
Supabase PostgreSQL

## 最小DB設計

### users

- id
- email
- name
- created_at

### companies

- id
- name
- owner_user_id
- created_at

### memberships

- id
- user_id
- company_id
- role
- created_at

### gmail_connections

- id
- user_id
- company_id
- provider
- connected
- token_json
- created_at
- updated_at

### sms_connections

- id
- user_id
- company_id
- provider
- connected
- config_json
- created_at
- updated_at

## データ分離ルール

すべての営業データに company_id を持たせる。

対象：

- leads
- customers
- results
- messages
- timelines
- actions
- learning_logs

## APIルール

Frontendはログイン中ユーザーの company_id を基準にAPI取得する。

Page直接fetchは禁止。

必ず以下を守る。

services/
↓
mapper/
↓
page/section

## Phase3実装順

1. Supabaseプロジェクト作成
2. 環境変数整理
3. users / companies / memberships 設計
4. Backendに auth API stub 追加
5. Frontendに login page 追加
6. Settingsへログイン状態表示
7. company_id をAPIレスポンスへ段階的に追加
8. Gmail OAuthを user_id / company_id 単位に接続
9. Stripe用 plan_status を会社に追加

## 注意

旧StreamlitのログインUIは移植しない。

販売品質のログイン画面をNext.js側で新規設計する。

## Phase3完了条件

- ログイン画面がある
- ユーザー作成導線がある
- 会社作成導線がある
- API側に現在ユーザー/会社の概念がある
- Settingsで接続状態を会社単位で表示できる
- 将来Gmail OAuthをユーザー別に保存できる構造になっている
