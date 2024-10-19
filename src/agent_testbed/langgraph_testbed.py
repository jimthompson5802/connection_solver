from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class State(TypedDict):
    number: Annotated[int, operator.add]
    limit: int

def create_number(state: State) -> State:
    print(f"entering create_number with state: {state}")
    return {"number": 1}

def increment_number(state: State) -> State:
    print(f"entering increment_number with state: {state}")
    current_number = state["number"]
    print(f"current_number: {current_number}")
    return {"number": 1}

def should_continue(state: State) -> str:
    print(f"entering should_continue with state: {state}")
    if state["number"] > state["limit"]:
        return END
    return "increment_number"

graph = StateGraph(State)

graph.add_node("create_number", create_number)
graph.add_node("increment_number", increment_number)

graph.set_entry_point("create_number")

graph.add_edge("create_number", "increment_number")
graph.add_conditional_edges(
    "increment_number",
    should_continue,
    {
        END: END,
        "increment_number": "increment_number"
    }
)

app = graph.compile()

result = app.invoke({"number": 0, "limit": 10})
print(result)