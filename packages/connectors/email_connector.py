"""Email connector — ingests memories from an email inbox via IMAP."""

from __future__ import annotations

import imaplib
import email as email_lib
from email.header import decode_header

from packages.shared.schemas.claim_schema import ClaimType


class EmailMemory:
    def __init__(self, subject: str, sender: str, body: str) -> None:
        self.subject = subject
        self.sender = sender
        self.body = body

    def to_ingest_payload(self) -> dict:
        return {
            "content": f"Subject: {self.subject}\n\n{self.body}",
            "source_type": "email",
            "source_id": self.sender,
            "actor": self.sender,
            "metadata": {"subject": self.subject},
        }


class EmailConnector:
    """Read unread emails from an IMAP mailbox and yield ingest payloads."""

    def __init__(self, host: str, username: str, password: str, mailbox: str = "INBOX") -> None:
        self.host = host
        self.username = username
        self.password = password
        self.mailbox = mailbox

    def fetch_unread(self, limit: int = 20) -> list[EmailMemory]:
        memories: list[EmailMemory] = []
        with imaplib.IMAP4_SSL(self.host) as imap:
            imap.login(self.username, self.password)
            imap.select(self.mailbox)
            _, msg_ids = imap.search(None, "UNSEEN")
            for uid in (msg_ids[0].split() or [])[:limit]:
                _, data = imap.fetch(uid, "(RFC822)")
                raw = data[0][1]  # type: ignore[index]
                msg = email_lib.message_from_bytes(raw)
                subject = self._decode_header(msg.get("Subject", ""))
                sender = msg.get("From", "unknown")
                body = self._get_body(msg)
                memories.append(EmailMemory(subject=subject, sender=sender, body=body))
        return memories

    @staticmethod
    def _decode_header(value: str) -> str:
        parts = decode_header(value)
        decoded = []
        for part, enc in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                decoded.append(part)
        return "".join(decoded)

    @staticmethod
    def _get_body(msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
        return msg.get_payload(decode=True).decode("utf-8", errors="replace")
