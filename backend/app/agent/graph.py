from langgraph.graph import StateGraph, START, END

from .nodes import get_relevant_docs, response
from .runtime import Context
from .state import State


class Graph:
    def __init__(self):
        self.graph_builder = StateGraph(
            state_schema=State,
            context_schema=Context,
        )

    def build_graph(self):
        self.graph_builder.add_node(
            node="get_relevant_docs",
            action=get_relevant_docs,
        )

        self.graph_builder.add_node(
            node="response",
            action=response,
        )

        self.graph_builder.add_edge(start_key=START, end_key="get_relevant_docs")
        self.graph_builder.add_edge(start_key="get_relevant_docs", end_key="response")

        self.graph_builder.add_edge(
            start_key="response",
            end_key=END,
        )

        return self.graph_builder.compile()
