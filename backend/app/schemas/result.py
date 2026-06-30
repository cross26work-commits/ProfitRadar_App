from pydantic import BaseModel


class ResultSummaryResponse(BaseModel):
    actual_profit: int
    estimated_profit: int
    action_count: int
    recovery_rate: float
    message: str = "results summary loaded"
