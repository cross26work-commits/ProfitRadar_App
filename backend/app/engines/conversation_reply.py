import json
import os
import re
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from app.services.ai_metrics import record_usage
from app.services.ai_budget import create_response
from fastapi import HTTPException

load_dotenv()


@dataclass
class ConversationReplyResult:
    body: str
    provider: str
    model: str
    used_fallback: bool


def _fallback_reply(
    facts: dict[str, Any],
) -> str:
    questions = (
        facts.get("required_questions")
        or []
    )

    lines = [
        "お疲れ様です。",
        "ご説明ありがとうございます。",
        "",
    ]

    if questions:
        lines.append(
            str(questions[0])
        )
    else:
        lines.append(
            "内容を確認いたしました。"
        )

        lines.append(
            "確認のうえ、改めてご連絡いたします。"
        )

    lines.extend([
        "",
        "よろしくお願いいたします。",
    ])

    return "\n".join(lines)


def _contains_forbidden_calculation(
    *,
    reply: str,
    facts: dict[str, Any],
) -> bool:
    """
    calculated_total が未確定なのに、
    AIが勝手に総額を断定していないかを防ぐ。
    """

    allowed = {
        int(value)
        for value in (
            facts.get("unit_price"), facts.get("people_count"), facts.get("work_days"),
            facts.get("stated_period_amount"), facts.get("calculated_total")
        )
        if value is not None
    }
    for token in re.findall(r"(?<!\d)(\d[\d,]{2,})(?!\d)", reply):
        if int(token.replace(",", "")) not in allowed:
            return True
    return False


class ConversationReplyGenerator:
    def __init__(self):
        self.api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        self.primary_model = os.getenv(
            "OPENAI_MODEL_PRIMARY",
            "gpt-5.6-terra",
        )

        self.escalation_model = os.getenv(
            "OPENAI_MODEL_ESCALATION",
            "gpt-5.6-sol",
        )

        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured"
            )

        self.client = OpenAI(
            api_key=self.api_key, timeout=30.0, max_retries=0
        )

    def _choose_model(
        self,
        *,
        facts: dict[str, Any],
        important: bool,
    ) -> str:
        confidence = float(
            facts.get("confidence")
            or 0.0
        )

        uncertain = bool(
            facts.get("uncertain_facts")
        )

        if (
            important
            or confidence < 0.90
            or uncertain
        ):
            return self.escalation_model

        return self.primary_model

    def generate(
        self,
        *,
        conversation_text: str,
        facts: dict[str, Any],
        important: bool = False,
    ) -> ConversationReplyResult:
        model = self._choose_model(
            facts=facts,
            important=important,
        )

        fallback = _fallback_reply(
            facts
        )

        instructions = """
あなたはProfit Radarの営業返信AIです。

あなたの仕事は、
メールスレッド全体と構造化された確定情報を読んで、
最新の顧客メッセージに対する自然な日本語返信を作ることです。

最重要ルール:

- 最新メールだけでなく会話全体を理解する
- 相手がすでに回答した質問を繰り返さない
- 会話を必ず一段前に進める
- confirmed_facts は確定情報として扱う
- uncertain_facts は未確定として扱う
- required_questions がある場合は、必要なものだけ自然に質問する
- price_basis が unknown の場合、価格の意味を絶対に一方へ決めつけない
- 「3名合計という認識でよいですか」のように一方を前提にせず、「1名分か3名合計か」のように中立に確認する
- calculated_total が null の場合、総額を勝手に計算・断定しない
- unit_price の単位が未確定なら、日額などと勝手に決めない
- 税込・税抜、支払条件、契約条件など、会話にない論点を勝手に追加しない
- 対応可能か未確認なのに「対応できます」と約束しない
- 数字を捏造しない
- 同じ確認を何度も繰り返さない
- 顧客の文章を不自然に復唱しすぎない
- 簡潔で自然なビジネス日本語にする
- 件名、説明、箇条書き、JSONは返さない
- メール本文だけ返す
"""

        input_text = f"""
=== 会話履歴 ===

{conversation_text}

=== Profit Radar 検証済み情報 ===

{json.dumps(
    facts,
    ensure_ascii=False,
    indent=2,
)}

この情報だけを根拠に、
最新の顧客メッセージへの返信本文を作成してください。
"""

        try:
            response = create_response(self.client,
                model=model,
                instructions=instructions,
                input=input_text,
                store=False,
                max_output_tokens=2048,
            )

            record_usage(response)
            body = (
                response.output_text
                or ""
            ).strip()

            if not body:
                raise ValueError(
                    "empty reply"
                )

            if _contains_forbidden_calculation(
                reply=body,
                facts=facts,
            ):
                return ConversationReplyResult(
                    body=fallback,
                    provider="validator_fallback",
                    model=model,
                    used_fallback=True,
                )

            return ConversationReplyResult(
                body=body,
                provider="openai",
                model=model,
                used_fallback=False,
            )

        except HTTPException:
            raise
        except Exception:
            return ConversationReplyResult(
                body=fallback,
                provider="fallback",
                model=model,
                used_fallback=True,
            )


def reply_result_to_dict(
    result: ConversationReplyResult,
) -> dict[str, Any]:
    return {
        "body": result.body,
        "provider": result.provider,
        "model": result.model,
        "used_fallback": (
            result.used_fallback
        ),
    }
