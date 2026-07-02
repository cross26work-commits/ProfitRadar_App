# Supabase Schema Notes

## 最重要
全テーブルは company_id で会社分離する。

## 主要データ流れ
messages
↓
profit_events
↓
ai_judgements
↓
timeline
↓
reply_logs
↓
learning_logs

## 利用者に見せる
- customers
- profit_events
- timeline
- ai_judgements の要約

## 利用者に見せない
- learning_logs
- provider内部情報
- RUDIA同期情報
