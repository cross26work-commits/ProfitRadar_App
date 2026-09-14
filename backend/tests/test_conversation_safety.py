from app.engines.conversation_intelligence import validate_price_basis
from app.engines.conversation_reply import _contains_forbidden_calculation
from app.engines.conversation_intelligence import grounded_number


def test_price_basis_requires_verbatim_evidence():
    text = "1ヶ月、一人当たり480,000円です。"
    assert validate_price_basis(price_basis="per_person_period", evidence="1ヶ月、一人当たり480,000円", conversation_text=text) == "per_person_period"
    assert validate_price_basis(price_basis="per_person_per_day", evidence="480,000円", conversation_text=text) == "unknown"


def test_unconfirmed_hallucinated_amount_is_rejected():
    facts = {"unit_price": 480000, "people_count": 3, "work_days": None, "stated_period_amount": 480000, "calculated_total": 1440000}
    assert _contains_forbidden_calculation(reply="Total 1,500,000 confirmed.", facts=facts)
    assert not _contains_forbidden_calculation(reply="Total 1,440,000 confirmed.", facts=facts)


def test_price_basis_needs_person_and_time_not_either():
    for text in ["月額48万円", "1名あたり48万円", "日額48万円"]:
        assert validate_price_basis(price_basis="per_person_period",evidence=text,conversation_text=text)=="unknown"
    assert validate_price_basis(price_basis="per_person_per_day",evidence="日額48万円",conversation_text="日額48万円")=="unknown"


def test_numeric_units_cannot_be_swapped_or_invented():
    text="３名、24日、48万円です。"
    assert grounded_number(480000,text,"円")==480000
    assert grounded_number(3,text,"人|名")==3
    assert grounded_number(24,text,"日")==24
    assert grounded_number(24,text,"人|名") is None
    assert grounded_number(500000,text,"円") is None
    assert grounded_number(True,text,"人|名") is None
    assert grounded_number("480000",text,"円") is None
