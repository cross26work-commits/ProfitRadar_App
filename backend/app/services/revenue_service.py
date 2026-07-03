from app.engines.revenue_engine import analyze_email


class RevenueService:
    def analyze(self, company_id: str, payload: dict):
        if not company_id:
            raise ValueError("company_id is required")

        subject = payload.get("subject", "")
        body = payload.get("body", "") or payload.get("content", "")
        neglected_days = int(payload.get("neglected_days") or 7)

        result = analyze_email(
            subject=subject,
            body=body,
            neglected_days=neglected_days,
        )

        return {
            "company_id": company_id,
            "engine": "revenue_engine",
            "input": {
                "subject": subject,
                "body": body,
                "neglected_days": neglected_days,
            },
            "result": result,
        }
