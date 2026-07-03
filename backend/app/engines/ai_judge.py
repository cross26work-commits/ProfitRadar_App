import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def fallback_judge(subject: str, body: str) -> dict[str, Any]:
    text = f"{subject or ''} {body or ''}"

    keywords = [
        "見積", "請求", "契約", "提案", "発注", "案件", "紹介", "採用",
        "面談", "依頼", "支払い", "入金", "契約書", "正式", "進めたい",
    ]

    hot_keywords = ["契約", "発注", "入金", "請求", "正式", "進めたい"]
    risk_keywords = ["至急", "本日", "期限", "未入金", "遅延", "確認お願いします"]

    is_lead = any(k in text for k in keywords)
    hot = any(k in text for k in hot_keywords)
    risky = any(k in text for k in risk_keywords)

    if hot and risky:
        risk_level = "高"
    elif hot or risky:
        risk_level = "中"
    else:
        risk_level = "低" if not is_lead else "中"

    return {
        "is_lead": is_lead,
        "customer": "",
        "estimated_profit": 100000 if is_lead else 0,
        "risk_level": risk_level,
        "neglected_days": 7,
        "next_action": "本日中に確認フォロー" if is_lead else "保存不要",
        "reason": "Fallback AI Judge: 売上関連キーワードを判定",
        "provider": "fallback",
    }


def judge_email(subject: str, sender: str = "", body: str = "") -> dict[str, Any]:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "ここにGeminiAPIキー":
        return fallback_judge(subject, body)

    try:
        from google import genai
    except Exception:
        data = fallback_judge(subject, body)
        data["reason"] = "google-genai未導入のためFallback判定"
        return data

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
あなたはProfit RadarのAI Revenue Judgeです。
以下のメールが売上・案件・請求・営業フォローに関係するか判定してください。

必ずJSONだけで返してください。

形式：
{{
  "is_lead": true,
  "customer": "相手名または会社名",
  "estimated_profit": 100000,
  "risk_level": "低/中/高",
  "neglected_days": 7,
  "next_action": "次にやるべき行動",
  "reason": "判定理由",
  "provider": "gemini"
}}

From:
{sender}

Subject:
{subject}

Body:
{body[:3000]}
"""

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = res.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        data["provider"] = "gemini"
        return data
    except Exception as exc:
        data = fallback_judge(subject, body)
        data["reason"] = f"Gemini判定失敗のためFallback判定: {exc}"
        return data
