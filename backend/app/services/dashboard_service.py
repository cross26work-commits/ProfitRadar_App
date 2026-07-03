from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository

    def get_summary(self, company_id: str):
        profit_events = self.repository.list_profit_events(company_id)
        customers = self.repository.list_customers(company_id)
        timeline = self.repository.list_recent_timeline(company_id)

        estimated_profit = sum(int(row.get("estimated_profit") or 0) for row in profit_events)
        actual_profit = sum(int(row.get("actual_profit") or 0) for row in profit_events)
        open_events = [row for row in profit_events if row.get("status") == "open"]
        hot_leads = [row for row in profit_events if row.get("hot_lead") is True]

        top_actions = sorted(
            open_events,
            key=lambda row: int(row.get("opportunity_score") or 0),
            reverse=True,
        )[:5]

        return {
            "company_id": company_id,
            "metrics": {
                "estimated_profit": estimated_profit,
                "actual_profit": actual_profit,
                "recoverable_profit": estimated_profit - actual_profit,
                "customer_count": len(customers),
                "open_event_count": len(open_events),
                "hot_lead_count": len(hot_leads),
            },
            "top_actions": top_actions,
            "recent_timeline": timeline,
        }
