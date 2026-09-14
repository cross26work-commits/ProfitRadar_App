import base64
from email.utils import parseaddr
from typing import Any


def _header(
    headers: list[dict],
    name: str,
) -> str:
    for header in headers:
        if (
            str(
                header.get("name") or ""
            ).lower()
            == name.lower()
        ):
            return str(
                header.get("value") or ""
            )

    return ""


def _decode(data: str) -> str:
    if not data:
        return ""

    try:
        raw = base64.urlsafe_b64decode(
            data + "==="
        )

        return raw.decode(
            "utf-8",
            errors="ignore",
        )
    except Exception:
        return ""


def _extract_text(
    payload: dict,
) -> str:
    body_data = (
        payload
        .get("body", {})
        .get("data")
    )

    if body_data:
        return _decode(
            body_data
        )

    plain_parts: list[str] = []

    def walk(
        part: dict,
    ) -> None:
        mime_type = (
            part.get("mimeType")
            or ""
        )

        data = (
            part
            .get("body", {})
            .get("data")
        )

        if (
            mime_type == "text/plain"
            and data
        ):
            plain_parts.append(
                _decode(data)
            )

        for child in (
            part.get("parts", [])
            or []
        ):
            walk(child)

    walk(payload)

    return "\n".join(
        text
        for text in plain_parts
        if text.strip()
    )


def strip_quoted_text(
    text: str,
) -> str:
    """
    1通の本文に含まれる過去メール引用を除外する。

    Gmail thread自体から過去メッセージを
    個別取得するため、引用文を重複してAIへ渡さない。
    """

    if not text:
        return ""

    markers = [
        "\nOn ",
        "\r\nOn ",
        "\nFrom:",
        "\r\nFrom:",
        "\n-----Original Message-----",
        "\n----- Forwarded message -----",
    ]

    cleaned = text

    for marker in markers:
        index = cleaned.find(
            marker
        )

        if index != -1:
            cleaned = cleaned[:index]

    lines = []

    for line in cleaned.splitlines():
        if (
            line.strip()
            .startswith(">")
        ):
            continue

        lines.append(line)

    return (
        "\n".join(lines)
        .strip()
    )


def build_conversation_history(
    *,
    thread: dict[str, Any],
    own_email: str,
) -> dict[str, Any]:
    own_email_normalized = (
        parseaddr(
            own_email or ""
        )[1]
        .lower()
    )

    messages = (
        thread.get(
            "messages",
            [],
        )
        or []
    )

    normalized: list[
        dict[str, Any]
    ] = []

    for message in messages:
        payload = (
            message.get(
                "payload",
                {},
            )
            or {}
        )

        headers = (
            payload.get(
                "headers",
                [],
            )
            or []
        )

        from_raw = _header(
            headers,
            "From",
        )

        from_email = (
            parseaddr(
                from_raw
            )[1]
            .lower()
        )

        to_raw = _header(
            headers,
            "To",
        )

        subject = _header(
            headers,
            "Subject",
        )

        date = _header(
            headers,
            "Date",
        )

        body = strip_quoted_text(
            _extract_text(
                payload
            )
        )

        if not body:
            continue

        is_own = bool(
            own_email_normalized
            and from_email
            == own_email_normalized
        )

        role = (
            "こちら"
            if is_own
            else "顧客"
        )

        normalized.append({
            "message_id": (
                message.get("id")
            ),
            "thread_id": (
                message.get(
                    "threadId"
                )
            ),
            "role": role,
            "from": from_raw,
            "from_email": (
                from_email
            ),
            "to": to_raw,
            "subject": subject,
            "date": date,
            "body": body,
        })

    transcript_parts = []

    for index, item in enumerate(
        normalized,
        start=1,
    ):
        transcript_parts.append(
            (
                f"--- メッセージ {index} ---\n"
                f"送信者: {item['role']}\n"
                f"日時: {item['date']}\n"
                f"件名: {item['subject']}\n"
                f"本文:\n{item['body']}"
            )
        )

    return {
        "thread_id": (
            thread.get("id")
        ),
        "message_count": len(
            normalized
        ),
        "messages": normalized,
        "transcript": (
            "\n\n".join(
                transcript_parts
            )
        ),
    }
