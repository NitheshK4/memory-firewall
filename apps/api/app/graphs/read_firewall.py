from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from apps.api.app.models.api import RetrievalRequest, RetrievalResponse
from apps.api.app.services.retrieval_service import RetrievalService


class ReadState(TypedDict, total=False):
    request: RetrievalRequest
    response: RetrievalResponse


class ReadFirewall:
    def __init__(self, retrieval_service: RetrievalService) -> None:
        self.retrieval_service = retrieval_service
        self.graph = self._compile()

    def run(self, request: RetrievalRequest) -> RetrievalResponse:
        result = self.graph.invoke({"request": request})
        return result["response"]

    def _compile(self):
        graph = StateGraph(ReadState)
        graph.add_node("retrieve", self.retrieve)
        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", END)
        return graph.compile()

    def retrieve(self, state: ReadState) -> ReadState:
        return {"response": self.retrieval_service.retrieve(state["request"])}

