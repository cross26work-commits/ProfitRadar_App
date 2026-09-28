"""Request-local counters only; never collect prompts, responses, keys or identifiers."""
from contextvars import ContextVar

usage_records = ContextVar("ai_usage_records", default=None)
cost_records = ContextVar("ai_cost_records", default=None)


def record_usage(response):
    records = usage_records.get()
    usage = getattr(response, "usage", None)
    if records is None or usage is None:
        return
    incoming = getattr(usage, "input_tokens", None)
    outgoing = getattr(usage, "output_tokens", None)
    if type(incoming) is int and type(outgoing) is int and incoming >= 0 and outgoing >= 0:
        records.append((incoming, outgoing))
