import pytest

from scripts.run_isolated_ai_restart import validate_isolated_env


def valid():
    return {
        "APP_ENV":"test", "STRIPE_MODE":"test", "SUPABASE_URL":"http://127.0.0.1:54321",
        "FRONTEND_URL":"http://localhost:3190", "OPENAI_API_KEY":"fixture",
        "AI_MODEL_MAX_RATES_JSON":"{}", "AI_COMPANY_MONTHLY_TOKENS":"1",
        "AI_COMPANY_MONTHLY_USD":"1", "AI_MONTHLY_GENERATION_LIMIT":"1",
        "OPENAI_MODEL_PRIMARY":"a", "OPENAI_MODEL_ESCALATION":"b", "OPENAI_MODEL_STANDARD":"c",
    }


@pytest.mark.parametrize("name,value", [
    ("SUPABASE_URL","https://project.supabase.co"),
    ("FRONTEND_URL","https://app.example.com"),
    ("STRIPE_MODE","live"),
    ("STRIPE_SECRET_KEY","sk_live_forbidden"),
])
def test_isolated_ai_guard_rejects_production_or_live(name,value):
    values=valid();values[name]=value
    with pytest.raises(RuntimeError):validate_isolated_env(values)


def test_isolated_ai_guard_accepts_loopback_and_optional_test_key():
    values=valid();values["STRIPE_SECRET_KEY"]="sk_test_fixture"
    validate_isolated_env(values)
