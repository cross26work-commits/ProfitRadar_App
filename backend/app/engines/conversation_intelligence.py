import json
import os
import re
import unicodedata
from decimal import Decimal
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from app.services.ai_metrics import record_usage
from app.services.ai_budget import create_response

load_dotenv()


@dataclass
class ConversationFacts:
    intent: str
    unit_price: int | None
    price_unit: str | None
    price_basis: str
    price_basis_evidence: str | None
    people_count: int | None
    work_days: int | None
    stated_period_amount: int | None
    calculated_total: int | None
    confirmed_facts: list[str]
    uncertain_facts: list[str]
    required_questions: list[str]
    confidence: float
    provider: str
    model: str


def calculate_total(
    *,
    unit_price: int | None,
    people_count: int | None,
    work_days: int | None,
    price_unit: str | None,
) -> int | None:
    if (
        unit_price is None
        or people_count is None
        or work_days is None
        or not price_unit
    ):
        return None

    if (
        unit_price < 0
        or people_count <= 0
        or work_days <= 0
    ):
        return None

    normalized = price_unit.lower()

    per_person_per_day = (
        "人日" in normalized
        or "1名1日" in normalized
        or "1人1日" in normalized
        or "円/人日" in normalized
    )

    if not per_person_per_day:
        return None

    return (
        unit_price
        * people_count
        * work_days
    )


def calculate_period_amount(
    *,
    unit_price: int | None,
    work_days: int | None,
) -> int | None:
    if (
        unit_price is None
        or work_days is None
    ):
        return None

    if (
        unit_price < 0
        or work_days <= 0
    ):
        return None

    return unit_price * work_days


def validate_price_basis(*, price_basis: str, evidence: str | None, conversation_text: str) -> str:
    """Accept a price basis only when its stated evidence appears in the conversation."""
    evidence = (evidence or "").strip()
    if not evidence or evidence not in conversation_text:
        return "unknown"
    normalized = evidence.lower()
    person = any(term in normalized for term in ("一人当たり", "一人あたり", "1名あたり", "1人あたり", "1名分", "1人分"))
    period = any(term in normalized for term in ("一ヶ月", "1ヶ月", "1か月", "月額", "期間", "日分"))
    if price_basis == "per_person_per_day" and (any(term in normalized for term in ("人日", "1名1日", "1人1日", "一人あたり1日")) or (person and "日額" in normalized)):
        return price_basis
    if price_basis == "per_person_period" and person and period:
        return price_basis
    if price_basis == "total_period" and any(term in normalized for term in ("合計", "総額", "全体")):
        return price_basis
    return "unknown"


def grounded_number(value, text, unit):
    """Conservative literal-unit check. Unsupported notation remains unknown, not zero."""
    if type(value) is not int or value < 0 or (unit != "円" and value == 0):
        return None
    normalized=unicodedata.normalize("NFKC",text)
    for match in re.finditer(r"(?<![\d.])([\d,]+(?:\.\d+)?)\s*(万|億)?\s*("+unit+r")",normalized):
        number=Decimal(match[1].replace(",",""))*{"万":10000,"億":100000000,None:1}[match[2]]
        if number==value:
            return value
    return None


def validate_questions(
    *,
    questions: list[str],
    conversation_text: str,
) -> list[str]:
    """
    AIが不要な確認事項を増やしすぎないようにする。

    現段階では、
    ・税抜/税込
    ・支払条件
    ・契約書
    など、会話に一度も出ていない一般的な論点は
    自動質問として採用しない。
    """

    blocked_topics = [
        ("税抜", ["税抜", "税込", "消費税"]),
        ("税込", ["税抜", "税込", "消費税"]),
        ("支払", ["支払", "入金", "締め", "請求"]),
        ("契約書", ["契約書", "契約"]),
    ]

    result: list[str] = []

    for question in questions:
        if not question:
            continue

        blocked = False

        for trigger, source_terms in blocked_topics:
            if trigger not in question:
                continue

            if not any(
                term in conversation_text
                for term in source_terms
            ):
                blocked = True
                break

        if not blocked:
            result.append(question)

    return result


class ConversationIntelligenceEngine:
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
        important: bool,
    ) -> str:
        return self.primary_model

    def analyze(
        self,
        *,
        conversation_text: str,
        important: bool = False,
    ) -> ConversationFacts:
        model = self._choose_model(
            important=important
        )

        instructions = """
あなたはProfit Radarの営業会話理解エンジンです。

メールスレッド全体を読み、
最新メッセージだけではなく、
過去の質問・回答・条件変更を含めて理解してください。

目的:
1. 営業上の意図を特定する
2. 金額・人数・日数・単価を構造化する
3. 確定済みと未確定を分離する
4. すでに回答済みの質問を繰り返さない
5. 会話を進めるために必須の質問だけ挙げる

価格分類:
price_basis は必ず次のどれかにする:
- unknown
- per_person_per_day
- per_person_period
- total_period

重要:
- 「1名あたり」としか書いていない場合、日額とは限らないので unknown
- 「1名1日あたり」「人日単価」まで明示されて初めて per_person_per_day
- 「1名の1ヶ月分」「1名24日分」なら per_person_period
- 「3名合計」「全体総額」なら total_period
- 文面が矛盾・曖昧なら必ず unknown
- required_questions は中立な質問にする
- 未確定な選択肢の片方を「〜という認識でよいですか」と先に決めつけない

禁止:
- 会話にない数字を推測しない
- 税抜/税込など、一般論を勝手に質問しない
- 契約条件を勝手に追加しない
- 計算結果を確定事実として扱わない
- 同じ質問を繰り返さない

JSONだけ返してください。

{
  "intent": "",
  "unit_price": null,
  "price_unit": null,
  "price_basis": "unknown",
  "price_basis_evidence": null,
  "people_count": null,
  "work_days": null,
  "stated_period_amount": null,
  "confirmed_facts": [],
  "uncertain_facts": [],
  "required_questions": [],
  "confidence": 0.0
}
"""

        response = create_response(self.client,
            model=model,
            instructions=instructions,
            input=conversation_text,
            store=False,
            max_output_tokens=2048,
        )

        record_usage(response)
        raw = (
            response.output_text
            or ""
        ).strip()

        raw = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        data = json.loads(raw)

        unit_price = data.get(
            "unit_price"
        )

        people_count = data.get(
            "people_count"
        )

        work_days = data.get(
            "work_days"
        )

        stated_period_amount = data.get(
            "stated_period_amount"
        )
        unit_price=grounded_number(unit_price,conversation_text,"円")
        stated_period_amount=grounded_number(stated_period_amount,conversation_text,"円")
        people_count=grounded_number(people_count,conversation_text,"人|名")
        work_days=grounded_number(work_days,conversation_text,"日")

        price_basis = str(
            data.get("price_basis")
            or "unknown"
        )
        price_basis_evidence = data.get("price_basis_evidence")

        allowed_price_basis = {
            "unknown",
            "per_person_per_day",
            "per_person_period",
            "total_period",
        }

        if price_basis not in allowed_price_basis:
            price_basis = "unknown"
        price_basis = validate_price_basis(
            price_basis=price_basis,
            evidence=price_basis_evidence,
            conversation_text=conversation_text,
        )

        if price_basis == "per_person_per_day":
            calculated_total = calculate_total(
                unit_price=unit_price,
                people_count=people_count,
                work_days=work_days,
                price_unit="円/人日",
            )

        elif (
            price_basis == "per_person_period"
            and stated_period_amount is not None
            and people_count is not None
        ):
            calculated_total = (
                stated_period_amount
                * people_count
            )

        elif (
            price_basis == "total_period"
            and stated_period_amount is not None
        ):
            calculated_total = (
                stated_period_amount
            )

        else:
            calculated_total = None

        calculated_period_amount = (
            calculate_period_amount(
                unit_price=unit_price,
                work_days=work_days,
            )
            if price_basis == "per_person_per_day"
            else None
        )

        uncertain_facts = list(
            data.get(
                "uncertain_facts"
            )
            or []
        )

        if (
            stated_period_amount is not None
            and calculated_period_amount is not None
            and stated_period_amount
            != calculated_period_amount
        ):
            uncertain_facts.append(
                "相手が提示した期間金額と、単価×稼働日数の計算結果が一致していません。"
            )

        required_questions = (
            validate_questions(
                questions=list(
                    data.get(
                        "required_questions"
                    )
                    or []
                ),
                conversation_text=conversation_text,
            )
        )

        return ConversationFacts(
            intent=str(
                data.get("intent")
                or ""
            ),
            unit_price=unit_price,
            price_unit=(
                data.get("price_unit")
                or None
            ),
            price_basis=price_basis,
            price_basis_evidence=price_basis_evidence if price_basis != "unknown" else None,
            people_count=people_count,
            work_days=work_days,
            stated_period_amount=(
                stated_period_amount
            ),
            calculated_total=(
                calculated_total
            ),
            confirmed_facts=list(
                data.get(
                    "confirmed_facts"
                )
                or []
            ),
            uncertain_facts=(
                uncertain_facts
            ),
            required_questions=(
                required_questions
            ),
            confidence=float(
                data.get("confidence")
                or 0.0
            ),
            provider="openai",
            model=model,
        )


def facts_to_dict(
    facts: ConversationFacts,
) -> dict[str, Any]:
    return {
        "intent": facts.intent,
        "unit_price": facts.unit_price,
        "price_unit": facts.price_unit,
        "price_basis": facts.price_basis,
        "price_basis_evidence": facts.price_basis_evidence,
        "people_count": facts.people_count,
        "work_days": facts.work_days,
        "stated_period_amount": (
            facts.stated_period_amount
        ),
        "calculated_total": (
            facts.calculated_total
        ),
        "confirmed_facts": (
            facts.confirmed_facts
        ),
        "uncertain_facts": (
            facts.uncertain_facts
        ),
        "required_questions": (
            facts.required_questions
        ),
        "confidence": facts.confidence,
        "provider": facts.provider,
        "model": facts.model,
    }
