"""In-memory repository regression tests, NOT real RLS/Auth evidence."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services import reply_drafts


class Database:
    def __init__(self):
        self.rows = {"profit_events": [{"id": "a-event", "company_id": "a"}, {"id": "b-event", "company_id": "b"}], "reply_drafts": []}

    def table(self, name):
        return Query(self.rows[name])


class Query:
    def __init__(self, rows):
        self.rows, self.filters = rows, {}
    def select(self, _): return self
    def eq(self, key, value):
        self.filters[key] = value
        return self
    def limit(self, _): return self
    def upsert(self, payload, on_conflict):
        assert on_conflict == "company_id,profit_event_id"
        self.rows[:] = [r for r in self.rows if (r["company_id"], r["profit_event_id"]) != (payload["company_id"], payload["profit_event_id"])]
        self.rows.append(payload.copy())
        return self
    def execute(self):
        return SimpleNamespace(data=[r.copy() for r in self.rows if all(r.get(k) == v for k, v in self.filters.items())])


def test_save_reload_update_and_tenant_denial():
    db = Database()
    for text in ("first", "edited"):
        assert reply_drafts.save(db, "a", "a-event", reply_drafts.DraftInput(body=text, subject="Test")) == {"saved": True}
        assert reply_drafts.load(db, "a", "a-event")["body"] == text
    assert len(db.rows["reply_drafts"]) == 1
    assert reply_drafts.load(db, "b", "a-event") is None
    with pytest.raises(HTTPException) as error:
        reply_drafts.save(db, "a", "b-event", reply_drafts.DraftInput(body="forbidden", subject="Test"))
    assert error.value.status_code == 404
    assert len(db.rows["reply_drafts"]) == 1


def test_subject_header_injection_denied():
    db = Database()
    with pytest.raises(HTTPException) as error:
        reply_drafts.save(db, "a", "a-event", reply_drafts.DraftInput(body="test", subject="Test\r\nBcc: forbidden"))
    assert error.value.status_code == 422
    assert db.rows["reply_drafts"] == []
