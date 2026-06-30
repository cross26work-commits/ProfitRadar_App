# Profit Radar App API設計

## Backend

Python / FastAPI

---

## 基本API

### Health

GET /health

目的：
サーバー稼働確認

---

### Auth

POST /auth/login
POST /auth/register
POST /auth/logout
GET /auth/me

目的：
ログイン、新規登録、現在ユーザー確認

---

### Leads

GET /leads
GET /leads/{lead_id}
PATCH /leads/{lead_id}

目的：
案件一覧、案件詳細、ステータス更新、実利益更新

---

### Customers

GET /customers
GET /customers/{customer_id}
GET /customers/{customer_id}/timeline

目的：
顧客一覧、顧客詳細、タイムライン取得

---

### Results

GET /results/summary
GET /results/monthly
GET /results/customers

目的：
実績、売上、回収利益、ランキング表示

---

### Gmail

GET /gmail/status
GET /gmail/connect
POST /gmail/analyze
POST /gmail/send
POST /gmail/replies/detect

目的：
Gmail接続、解析、送信、返信検知

---

### SMS

GET /sms/status
POST /sms/send
POST /sms/inbound
GET /sms/threads

目的：
SMS送信、SMS受信、履歴表示

---

### AI

POST /ai/judge
POST /ai/reply
POST /ai/roi
POST /ai/home-brief

目的：
AI案件判断、返信文生成、ROI分析、ホーム助言

---

## API設計方針

- Frontendは直接DBを触らない
- FrontendはBackend APIのみ呼ぶ
- AI処理はBackendに集約
- Gmail TokenはBackendで管理
- SMS TokenはBackendで管理
- ユーザーごとにuser_id/company_idで分離
