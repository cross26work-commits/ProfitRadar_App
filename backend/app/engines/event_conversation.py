from datetime import datetime
from typing import Any


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.min

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except Exception:
        return datetime.min


def build_event_conversation(
    *,
    timeline_rows: list[dict[str, Any]],
    reply_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []

    for row in timeline_rows:
        event_type = row.get("event_type")

        if event_type == "reply_sent_gmail":
            items.append({
                "role": "こちら",
                "type": "outgoing",
                "body": row.get("description") or "",
                "created_at": row.get("created_at"),
                "metadata": row.get("metadata") or {},
            })

    for row in reply_rows:
        items.append({
            "role": "顧客",
            "type": "incoming",
            "body": row.get("reply_body") or "",
            "created_at": row.get("created_at"),
            "metadata": {
                "gmail_message_id": row.get("gmail_message_id"),
                "gmail_thread_id": row.get("gmail_thread_id"),
            },
        })

    items.sort(
        key=lambda item: _parse_time(
            item.get("created_at")
        )
    )

    transcript_parts = []

    for index, item in enumerate(
        items,
        start=1,
    ):
        transcript_parts.append(
            (
                f"--- メッセージ {index} ---\n"
                f"送信者: {item['role']}\n"
                f"種別: {item['type']}\n"
                f"日時: {item['created_at']}\n"
                f"本文:\n{item['body']}"
            )
        )

    return {
        "message_count": len(items),
        "messages": items,
        "transcript": "\n\n".join(
            transcript_parts
        ),
    }
