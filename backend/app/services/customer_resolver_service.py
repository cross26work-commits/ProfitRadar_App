import re
from app.repositories.customer_repository import CustomerRepository


EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def extract_email(payload: dict) -> str:
    candidates = [
        payload.get("sender"),
        payload.get("from_email"),
        payload.get("email"),
        payload.get("from"),
    ]

    for value in candidates:
        if not value:
            continue

        text = str(value)
        match = EMAIL_RE.search(text)
        if match:
            return match.group(0).lower()

    body = str(payload.get("body") or payload.get("content") or "")
    match = EMAIL_RE.search(body)
    if match:
        return match.group(0).lower()

    return ""


def extract_customer_name(payload: dict, email: str = "") -> str:
    for key in ["customer_name", "customer", "company_name", "sender_name", "name"]:
        value = payload.get(key)
        if value:
            return str(value).strip()

    if email:
        return email.split("@")[0]

    return "顧客未設定"


class CustomerResolverService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository

    def resolve(self, company_id: str, payload: dict) -> dict | None:
        email = extract_email(payload)
        name = extract_customer_name(payload, email=email)

        if email:
            return self.repository.find_or_create_by_email(
                company_id=company_id,
                email=email,
                name=name,
            )

        return None
