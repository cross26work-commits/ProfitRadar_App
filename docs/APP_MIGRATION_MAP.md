# Profit Radar App 移植マップ

## 目的

Streamlit版 Profit Radar を、本格Webアプリ版へ移植する。

現在の資産は捨てない。
AI、Gmail、DB、返信検知、実利益保存、ログ機能を再利用する。

---

## 新構成

ProfitRadar_App/

frontend/
- Next.js
- React
- Tailwind
- 利用者画面

backend/
- Python
- FastAPI
- AI処理
- Gmail処理
- SMS処理
- DB処理

docs/
- 設計書
- API設計
- UI設計
- 移植マップ

migrations/
- SQLite → PostgreSQL 移行

---

## 既存Profit Radarから移すもの

### AI系

移植元：
~/ProfitRadar_RUDIA/

対象：
- ai_judge.py
- ai_roi_engine.py
- ai_decision_engine.py
- ai_sales_forecast.py
- ai_home_brief.py
- ai_self_eval_sync.py
- ai_self_eval_update.py
- learning_engine.py
- openai_advisor_engine.py
- openai_followup_engine.py

移植先：
backend/app/ai/

---

### DB系

移植元：
~/ProfitRadar_RUDIA/services/

対象：
- db_service.py
- schema_service.py

移植先：
backend/app/services/

---

### Utils

移植元：
~/ProfitRadar_RUDIA/utils/

対象：
- formatters.py

移植先：
backend/app/utils/

---

### Logging

移植元：
~/ProfitRadar_RUDIA/

対象：
- app_logger.py
- error_handler.py

移植先：
backend/app/core/

---

### Gmail

移植元：
~/ProfitRadar_RUDIA/

対象：
- Gmail OAuth
- Gmail解析
- Gmail送信
- Gmail返信検知
- gmail_connections
- profit_actions
- reply_detection_logs

移植先：
backend/app/integrations/gmail/

---

### UI

移植元：
~/ProfitRadar_RUDIA/modules/

対象：
- home_dashboard_ui.py
- customer_ui.py
- gmail_ui.py
- results_ui.py
- auth_ui.py

移植先：
frontend/app/

注意：
Streamlitコードはそのまま使わない。
表示ロジックだけNext.jsへ再設計する。

---

## Streamlitの扱い

Streamlit版は廃止しない。

役割：
- 開発者画面
- 管理者確認
- デバッグ
- AI挙動確認

利用者画面はNext.jsへ移行する。

---

## 追加予定

### SMS

方式：
Twilio API

流れ：
SMS受信
↓
Twilio Webhook
↓
FastAPI
↓
DB保存
↓
AI分析
↓
返信案生成
↓
SMS送信

---

## 最終判断

Profit Radar の中身は維持。
外側を本格アプリ化する。

