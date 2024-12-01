import pprint
import uuid

import queue

from typing import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# setup pprint
pp = pprint.PrettyPrinter(indent=4)


class WorkflowState(TypedDict):
    counter: int = 0
    message: str = "this message"
    next_updater: str = "update_counter1"


# function to update the counter
def update_counter1(state: WorkflowState) -> WorkflowState:
    state["counter"] += 1
    print(f"\ncounter1: {state['counter']}")
    return state


def update_counter2(state: WorkflowState) -> WorkflowState:
    state["counter"] += 2
    print(f"\ncounter2: {state['counter']}")
    return state


def update_counter3(state: WorkflowState) -> WorkflowState:
    state["counter"] += 3
    print(f"\ncounter3: {state['counter']}")
    return state


def human_input(state: WorkflowState) -> WorkflowState:
    print(f"----human input-----: counter: {state['counter']}")
    return state


def decider(state: WorkflowState) -> WorkflowState:
    if state["counter"] < 20:
        state["next_updater"] = "update_counter1"
    else:
        state["next_updater"] = "END"
    return state


def determine_next_action(state: WorkflowState) -> str:
    if state["next_updater"] == "END":
        return END
    else:
        return state["next_updater"]


# define workflow graph
workflow_graph = StateGraph(WorkflowState)

workflow_graph.add_node("update_counter1", update_counter1)
workflow_graph.add_node("update_counter2", update_counter2)
workflow_graph.add_node("human_input", human_input)
workflow_graph.add_node("update_counter3", update_counter3)
workflow_graph.add_node("decider", decider)

workflow_graph.add_edge("update_counter1", "update_counter2")
workflow_graph.add_edge("update_counter2", "human_input")
workflow_graph.add_edge("human_input", "update_counter3")
workflow_graph.add_edge("update_counter3", "decider")

workflow_graph.add_conditional_edges(
    "decider",
    determine_next_action,
    {
        "update_counter1": "update_counter1",
        END: END,
    },
)

workflow_graph.set_entry_point("update_counter1")

memory_checkpoint = MemorySaver()

workflow = workflow_graph.compile(checkpointer=memory_checkpoint, interrupt_before=["human_input"])


initial_state = WorkflowState(counter=0, message="this message")
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

num_updates = 0

# run workflow until human_input
for chunk in workflow.stream(initial_state, config=config, stream_mode="values"):
    print(f"\nchunk0: {chunk}")
print(f"state at first human_input:\n{workflow.get_state(config=config)}")

# breakpoint at human_input
while True:
    # run workflow until end condtion
    num_updates += 1
    # emulating getting external input from the user
    workflow.update_state(
        config,
        {"counter": 2 * num_updates, "message": f"num_updates: {num_updates}"},
        # as_node="human_input",  #if specified, the code in the node is not executed
    )

    # continue workflow until the next human_input breakpoint
    for chunk in workflow.stream(None, config=config, stream_mode="values"):
        print(f"\nchunk1: {chunk}")

    print(f"state at human_input:\n{workflow.get_state(config=config)}")

    # check to see if workflow is done or should be terminated
    if num_updates > 15 or chunk["next_updater"] == "END":
        break
