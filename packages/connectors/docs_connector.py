"""Google Docs connector — ingests document content as memories via the Drive API."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DocsMemory:
    doc_id: str
    title: str
    content: str

    def to_ingest_payload(self) -> dict:
        return {
            "content": f"{self.title}\n\n{self.content}",
            "source_type": "docs",
            "source_id": self.doc_id,
            "actor": "docs_connector",
            "metadata": {"doc_id": self.doc_id, "title": self.title},
        }


class DocsConnector:
    """Read content from Google Docs and yield ingest payloads.

    Requires ``google-api-python-client`` and a service account or OAuth
    credential with ``https://www.googleapis.com/auth/documents.readonly`` scope.
    """

    def __init__(self, credentials_path: str | None = None) -> None:
        try:
            from google.oauth2 import service_account  # type: ignore[import]
            from googleapiclient.discovery import build  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Install google-api-python-client and google-auth: "
                "pip install google-api-python-client google-auth"
            ) from exc

        creds_file = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
        scopes = ["https://www.googleapis.com/auth/documents.readonly"]
        credentials = service_account.Credentials.from_service_account_file(creds_file, scopes=scopes)
        self._service = build("docs", "v1", credentials=credentials)

    def fetch_document(self, document_id: str) -> DocsMemory:
        doc = self._service.documents().get(documentId=document_id).execute()
        title = doc.get("title", "Untitled")
        content = self._extract_text(doc)
        return DocsMemory(doc_id=document_id, title=title, content=content)

    @staticmethod
    def _extract_text(doc: dict) -> str:
        texts: list[str] = []
        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun")
                if text_run:
                    texts.append(text_run.get("content", ""))
        return "".join(texts).strip()
