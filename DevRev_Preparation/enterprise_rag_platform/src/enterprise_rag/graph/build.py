# -*- coding: utf-8 -*-
"""Assemble and run the LangGraph pipeline.

    START -> authorize -> plan -> retrieve -> enforce -> grade -+-> generate -> verify -> END
                                                                +-> refuse -------------> END

The security-critical ordering (authorize first, enforce before the model sees
anything) is encoded in the graph's edges, not in a comment someone can ignore.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph

from ..config import SETTINGS
from ..llm.client import LLMClient, Usage
from ..models import Answer, Principal
from ..observability.trace import RunTrace
from . import nodes
from .state import RAGState

_COMPILED = None


def build_graph():
    """Compile the graph once and reuse it - compilation is not free."""
    global _COMPILED
    if _COMPILED is not None:
        return _COMPILED

    g = StateGraph(RAGState)

    g.add_node("authorize", nodes.authorize)
    g.add_node("plan", nodes.plan)
    g.add_node("retrieve", nodes.retrieve)
    g.add_node("enforce", nodes.enforce)
    g.add_node("grade", nodes.grade)
    g.add_node("generate", nodes.generate)
    g.add_node("verify", nodes.verify)
    g.add_node("refuse", nodes.refuse)

    g.add_edge(START, "authorize")
    g.add_edge("authorize", "plan")
    g.add_edge("plan", "retrieve")
    g.add_edge("retrieve", "enforce")
    g.add_edge("enforce", "grade")
    g.add_conditional_edges("grade", nodes.route_after_grade,
                            {"generate": "generate", "refuse": "refuse"})
    # `generate` can itself decide the run must be refused (model unavailable), so
    # it routes conditionally too rather than assuming success.
    g.add_conditional_edges("generate",
                            lambda s: "refuse" if not s.get("draft") else "verify",
                            {"verify": "verify", "refuse": "refuse"})
    g.add_edge("verify", END)
    g.add_edge("refuse", END)

    _COMPILED = g.compile()
    return _COMPILED


class RAGPlatform:
    """The public entry point. One object, one method you actually call."""

    def __init__(self, settings=SETTINGS):
        self.settings = settings
        self.graph = build_graph()

    def ask(self,
            question: str,
            principal: Principal,
            strategy: str = "enterprise",
            as_of: Optional[str] = None,
            write_trace: bool = True) -> Dict[str, Any]:
        """Answer one question as one principal. Returns the answer plus its trace."""
        usage = Usage()
        llm = LLMClient(self.settings, usage=usage)
        trace = RunTrace(question=question, strategy=strategy)

        state: RAGState = {
            "question": question,
            "principal": principal,
            "strategy": strategy,
            "as_of": as_of,
            "llm": llm,
            "usage": usage,
            "trace": trace,
        }

        final = self.graph.invoke(state)
        trace.finish(usage)
        if write_trace:
            trace.write(self.settings)

        answer: Answer = final.get("answer") or Answer(
            text="No answer was produced.", refused=True,
            refusal_reason="pipeline produced no answer")

        return {"answer": answer, "trace": trace, "state": final}
