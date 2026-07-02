from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProvider(ABC):
    @abstractmethod
    def judge_sales_opportunity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass


class RuleBasedAIProvider(AIProvider):
    def judge_sales_opportunity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        estimated_profit = int(payload.get("estimated_profit") or 0)
        score = 80 if estimated_profit >= 100000 else 60 if estimated_profit >= 30000 else 40

        return {
            "provider": "rule_based",
            "score": score,
            "priority": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "risk": "返信遅延・競合流出・機会損失",
            "next_action": "本日中に確認連絡を送る",
            "reason": "推定利益と未対応状態から優先度を算出",
        }


def get_ai_provider() -> AIProvider:
    return RuleBasedAIProvider()
