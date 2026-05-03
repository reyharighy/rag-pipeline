import json
from langgraph.graph.state import CompiledStateGraph
from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent import get_initial_state, State, Context

router = APIRouter()

class ChatAgentRequest(BaseModel):
    chat_input: str

def event_generator(graph: CompiledStateGraph[State], state: State, context: Context):
    for event in graph.stream(state, context=context, stream_mode="updates"): # type: ignore[arg-type]
        print("Event:", event)
        encoded_event = jsonable_encoder(event)
        print("Encoded Event:", encoded_event)

        payload = json.dumps({
            "type": "update",
            "data": encoded_event
        })

        print("Payload:", payload)

        yield f"{payload}\n\n"

@router.post("/chat")
def chat_agent(request: Request, chat_agent: ChatAgentRequest):
    graph: CompiledStateGraph[State] = request.app.state.graph
    graph_state = get_initial_state(chat_agent.chat_input)
    graph_context = Context()

    generator = event_generator(
        graph,
        state=graph_state,
        context=graph_context,
    )

    return StreamingResponse(generator, media_type="text/event-stream")
