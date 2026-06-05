"""Tool-trace connector — converts LLM tool call traces into memories.

Ingests structured tool invocation records (e.g. from LangSmith, Langfuse,
or a custom trace log) so the firewall can audit what an agent did.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolTraceEvent:
    tool_name: str
    input_args: dict = field(default_factory=dict)
    output: str = ""
    actor: str = "agent"
    trace_id: str = ""
    occurred_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_ingest_payload(self) -> dict:
        summary = (
            f"Tool '{self.tool_name}' was called with args: "
            f"{json.dumps(self.input_args, ensure_ascii=False)[:200]}. "
            f"Output: {self.output[:300]}"
        )
        return {
            "content": summary,
            "source_type": "tool_trace",
            "source_id": self.trace_id or self.tool_name,
            "actor": self.actor,
            "metadata": {
                "tool_name": self.tool_name,
                "occurred_at": self.occurred_at,
            },
        }


class ToolTraceConnector:
    """Parse a JSONL tool-trace file and yield ingest payloads.

    Each line in the file should be a JSON object with keys:
      tool_name, input_args, output, actor, trace_id, occurred_at
    """

    def __init__(self, trace_file: str) -> None:
        self.trace_file = trace_file

    def read_events(self) -> list[ToolTraceEvent]:
        events: list[ToolTraceEvent] = []
        with open(self.trace_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                events.append(
                    ToolTraceEvent(
                        tool_name=data.get("tool_name", "unknown"),
                        input_args=data.get("input_args", {}),
                        output=str(data.get("output", "")),
                        actor=data.get("actor", "agent"),
                        trace_id=data.get("trace_id", ""),
                        occurred_at=data.get("occurred_at", ""),
                    )
                )
        return events
