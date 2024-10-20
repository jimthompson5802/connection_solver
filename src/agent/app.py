import pprint
import json
import numpy as np

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from tools import read_file_to_word_list, HUMAN_MESSAGE_BASE, ask_llm_for_solution
from utils import chunk_words, flatten_list

pp = pprint.PrettyPrinter(indent=4)

prompt_template = HUMAN_MESSAGE_BASE.content


class PuzzleState(TypedDict):
    words_remaining: List[str] = []
    invalid_connections: List[List[str]] = []
    recommended_words: List[str] = []
    recommended_connection: str = ""
    recommended_correct: bool = False
    found_yellow: bool = False
    found_greeen: bool = False
    found_blue: bool = False
    found_purple: bool = False
    mistake_count: int = 0
    recommendation_count: int = 0
    llm_temperature: float = 1.0


def read_words_from_file(state: PuzzleState) -> PuzzleState:
    words = read_file_to_word_list()
    state["words_remaining"] = words
    print("\nWords read from file:")
    pp.pprint(state)
    return state


def get_recommendation(state: PuzzleState) -> PuzzleState:
    print("\nEntering Recommendation:")
    pp.pprint(state)

    state["recommendation_count"] += 1

    # build prompt for llm
    prompt = prompt_template
    if len(state["invalid_connections"]) > 0:
        prompt += "\n\n"
        prompt += "Invalid word groups:\n"
        for invalid_connection in state["invalid_connections"]:
            prompt += f"{', '.join(invalid_connection)}\n"
    prompt += "\n\n"
    prompt += f"candidate list: {', '.join(state['words_remaining'])}\n"

    print(f"\nPrompt for llm: {prompt}")

    # get recommendation from llm
    llm_response = ask_llm_for_solution(prompt, temperature=state["llm_temperature"])

    llm_response_json = json.loads(llm_response.content)
    if isinstance(llm_response_json, list):
        print(f"\nLLM response is list")
        state["recommended_words"] = llm_response_json[0]["words"]
        state["recommended_connection"] = llm_response_json[0]["connection"]
    else:
        print(f"\nLLM response is dict")
        state["recommended_words"] = llm_response_json["words"]
        state["recommended_connection"] = llm_response_json["connection"]

    print("\nExiting recommendation:")
    pp.pprint(state)

    return state


def apply_recommendation(state: PuzzleState) -> PuzzleState:
    print("\nEntering apply_recommendation:")
    pp.pprint(state)

    print(f"\nRECOMMENDED WORDS {state['recommended_words']} with connection {state['recommended_connection']}")

    # update state with found words
    found_correct_group = input("Is the recommendation accepted? (y/g/b/p/n): ")
    match found_correct_group:
        case "y":
            state["found_yellow"] = True
        case "g":
            state["found_green"] = True
        case "b":
            state["found_blue"] = True
        case "p":
            state["found_purple"] = True
        case "n":
            state["mistake_count"] += 1

    # remove recommended words if we found a solution
    if found_correct_group != "n":
        # remove from remaining_words the words from recommended_words
        state["words_remaining"] = [word for word in state["words_remaining"] if word not in state["recommended_words"]]
        state["recommended_correct"] = True
    else:
        state["invalid_connections"].append(state["recommended_words"])
        state["recommended_correct"] = False

    print("\nExiting apply_recommendation:")
    pp.pprint(state)

    return state


def clear_recommendation(state: PuzzleState) -> PuzzleState:
    print("\nEntering clear_recommendation:")
    pp.pprint(state)

    state["recommended_words"] = []
    state["recommended_connection"] = ""
    state["recommended_correct"] = False

    print("\nExiting clear_recommendation:")
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
        return "clear_recommendation"


workflow = StateGraph(PuzzleState)

workflow.add_node("read_words_from_file", read_words_from_file)
workflow.add_node("get_recommendation", get_recommendation)
workflow.add_node("apply_recommendation", apply_recommendation)
workflow.add_node("clear_recommendation", clear_recommendation)

workflow.add_edge("read_words_from_file", "get_recommendation")
workflow.add_edge("get_recommendation", "apply_recommendation")
workflow.add_edge("clear_recommendation", "get_recommendation")
workflow.add_conditional_edges(
    "apply_recommendation", is_end, {END: END, "clear_recommendation": "clear_recommendation"}
)

workflow.set_entry_point("read_words_from_file")

app = workflow.compile()

initial_state = PuzzleState(
    words=[],
    invalid_connections=[],
    recommended_words=[],
    recommended_connection="",
    recommended_correct=False,
    found_blue=False,
    found_green=False,
    found_purple=False,
    found_yellow=False,
    mistake_count=0,
    recommendation_count=0,
    llm_temperature=1.0,
)

result = app.invoke(initial_state)

pp.pprint(result)
