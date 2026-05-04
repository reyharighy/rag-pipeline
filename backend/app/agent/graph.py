from langgraph.graph import StateGraph, START, END

from .nodes import first_node
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
            node="first_node",
            action=first_node,
        )

        self.graph_builder.add_edge(start_key=START, end_key="first_node")

        self.graph_builder.add_edge(
            start_key="first_node",
            end_key=END,
        )

        return self.graph_builder.compile()
