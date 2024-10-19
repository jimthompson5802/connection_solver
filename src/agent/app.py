import pprint

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from tools import read_file_to_word_list
from utils import chunk_words, flatten_list

pp = pprint.PrettyPrinter(indent=4)


class PuzzleState(TypedDict):
    words_remaining: List[str] = []
    recommended_words: List[str] = []
    recommeded_connection: str = ""
    found_yellow: bool = False
    found_greeen: bool = False
    found_blue: bool = False
    found_purple: bool = False
    mistake_count: int = 0
    recommendation_count: int = 0


def read_words_from_file(state: PuzzleState) -> PuzzleState:
    words = read_file_to_word_list()
    state["words_remaining"] = words
    print("\nWords read from file:")
    pp.pprint(state)
    return state


def get_recomendation(state: PuzzleState) -> PuzzleState:
    print("\nEntering Recommendation:")
    pp.pprint(state)

    state["recommendation_count"] += 1
    list_of_lists = chunk_words(state["words_remaining"])

    # remove first element
    state["recommended_words"] = list_of_lists[0]
    state["recommeded_connection"] = f"simulated connection {state['recommended_words']}"

    # update state with remaining words
    state["words_remaining"] = flatten_list(list_of_lists)

    print("\nExiting recomendation:")
    pp.pprint(state)

    return state


def apply_recomendation(state: PuzzleState) -> PuzzleState:
    print("\nEntering apply_recomendation:")
    pp.pprint(state)

    print(f"\nRECOMMENDED WORDS {state['recommended_words']} with connection {state['recommeded_connection']}")

    # update state with found words
    recommendation_ok = input("Is the recommendation accepted? (y/g/b/p/no): ")
    match recommendation_ok:
        case "y":
            state["found_yellow"] = True
        case "g":
            state["found_green"] = True
        case "b":
            state["found_blue"] = True
        case "p":
            state["found_purple"] = True
        case "no":
            state["mistake_count"] += 1

    # remove recommended words if we found a solution
    if recommendation_ok != "no":
        # remove from remaining_words the words from recommended_words
        state["words_remaining"] = [word for word in state["words_remaining"] if word not in state["recommended_words"]]

    print("\nExiting apply_recomendation:")
    pp.pprint(state)

    return state


def is_end(state: PuzzleState) -> str:
    if len(state["words_remaining"]) == 0:
        print("\nSOLVED THE CONNECTION PUZZLE!!!")
        return END
    elif state["mistake_count"] >= 4:
        print("\nFAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
        return END
    else:
        return "get_recomendation"


workflow = StateGraph(PuzzleState)

workflow.add_node("read_words_from_file", read_words_from_file)
workflow.add_node("get_recomendation", get_recomendation)
workflow.add_node("apply_recomendation", apply_recomendation)

workflow.add_edge("read_words_from_file", "get_recomendation")
workflow.add_edge("get_recomendation", "apply_recomendation")
workflow.add_conditional_edges("apply_recomendation", is_end, {END: END, "get_recomendation": "get_recomendation"})

workflow.set_entry_point("read_words_from_file")

app = workflow.compile()

initial_state = PuzzleState(
    words=[],
    recommended_words=[],
    recommeded_connection="",
    found_blue=False,
    found_green=False,
    found_purple=False,
    found_yellow=False,
    mistake_count=0,
    recommendation_count=0,
)

result = app.invoke(initial_state)

pp.pprint(result)
