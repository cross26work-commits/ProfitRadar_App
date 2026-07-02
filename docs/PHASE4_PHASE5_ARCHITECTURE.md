# Profit Radar Phase4-5 Architecture

Profit Radar = AI Sales OS
利用者表示は「AI」のみ。RUDIA / Learning DB / 営業経験収集は内部概念として非表示。

## 移植元
ProfitRadar_RUDIA

## 移植対象
- Revenue Engine
- Opportunity Score Engine
- AI Judge
- Reply Detection
- Hot Lead判定
- Timeline生成
- ROI Engine
- Follow-up Engine
- Learning DB
- AI Self Evaluation
- Sales Forecast
- Home Brief
- Action Engine
- Profit Pipeline

## API
現行:
- /auth
- /dashboard
- /customers
- /reply
- /results
- /settings

追加予定:
- /gmail
- /outlook
- /calendar
- /learning
- /timeline
- /revenue
- /ai

## DB
- companies
- profiles
- customers
- messages
- timeline
- profit_events
- reply_logs
- learning_logs
- ai_judgements
- calendar_events
- gmail_connections

## 層構造
DB
↓
Repository
↓
Service
↓
Mapper
↓
React Component

## 禁止事項
- 旧ロジックを理解せず作り直すこと
- Mockを増やすこと
- Atomic Designを崩すこと
- Repositoryを飛ばしてSQLを書くこと
- Serviceを飛ばしてAPIを書くこと
- Mapperへビジネスロジックを書くこと
- OpenAIへ直接依存すること
- company_idを無視すること
- UIだけ先行実装すること
