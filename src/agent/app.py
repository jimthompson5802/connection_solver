import argparse
import copy
import logging
import pprint
import json
import os
import random


import numpy as np

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from langchain_core.tracers.context import tracing_v2_enabled

from tools import (
    PuzzleState,
    setup_puzzle,
    ask_llm_for_solution,
    interact_with_user,
    ask_llm_for_next_step,
)
from utils import chunk_words, flatten_list

pp = pprint.PrettyPrinter(indent=4)

MAX_ERRORS = 4


def run_planner(state: PuzzleState) -> PuzzleState:
    logger.info("Entering run_planner:")
    logger.debug(f"\nEntering run_planner State: {pp.pformat(state)}")

    # convert state to json string
    puzzle_state = "\npuzzle state:\n" + json.dumps(state)

    # wrap the state in a human message
    puzzle_state = HumanMessage(puzzle_state)
    logger.info(f"\nState for lmm: {puzzle_state.content}")

    # get next action from llm
    next_action = ask_llm_for_next_step(puzzle_state, model="gpt-3.5-turbo", temperature=0)

    logger.info(f"\nNext action from llm: {next_action.content}")

    state["tool_to_use"] = json.loads(next_action.content)["tool"]

    logger.info("Exiting run_planner:")
    logger.debug(f"\nExiting run_planner State: {pp.pformat(state)}")
    return state


def determine_next_action(state: PuzzleState) -> str:
    logger.info("Entering determine_next_action:")
    logger.debug(f"\nEntering determine_next_action State: {pp.pformat(state)}")

    tool_to_use = state["tool_to_use"]

    if tool_to_use == "abort":
        raise ValueError("LLM returned abort")
    elif tool_to_use == "END":
        return END
    else:
        return tool_to_use


HUMAN_MESSAGE_BASE = """
    From the following candidate list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection.      
    """


def get_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_recommendation")
    logger.debug(f"Entering get_recommendation State: {pp.pformat(state)}")

    # build prompt for llm
    prompt = HUMAN_MESSAGE_BASE
    if len(state["invalid_connections"]) > 0:
        prompt += " Do not include word groups that are known to be invalid."
        prompt += "\n\n"
        prompt += "Invalid word groups:\n"
        for invalid_connection in state["invalid_connections"]:
            prompt += f"{', '.join(invalid_connection)}\n"
    prompt += "\n\n"
    # scramble the remaining words for more robust group selection
    random.shuffle(state["words_remaining"])
    prompt += f"candidate list: {', '.join(state['words_remaining'])}\n"

    prompt = HumanMessage(prompt)

    logger.info(f"\nPrompt for llm: {prompt.content}")

    # get recommendation from llm
    llm_response = ask_llm_for_solution(prompt, temperature=state["llm_temperature"])

    llm_response_json = json.loads(llm_response.content)
    if isinstance(llm_response_json, list):
        logger.debug(f"\nLLM response is list")
        state["recommended_words"] = sorted(llm_response_json[0]["words"])
        state["recommended_connection"] = llm_response_json[0]["connection"]
    else:
        logger.debug(f"\nLLM response is dict")
        state["recommended_words"] = sorted(llm_response_json["words"])
        state["recommended_connection"] = llm_response_json["connection"]

    logger.info("Exiting get_recommendation")
    logger.debug(f"Exiting get_recommendation State: {pp.pformat(state)}")

    return state


REGENERATE_MESSAGE_PART1 = """
    I am working on solving a word grouping puzzle where I need to select 4 words that fit into a specific category from a list of remaining words. The current recommended set of 4 words is incorrect, with one or more words being wrong. Please help me regenerate a new set of 4 words that better fits the category. Below is the relevant information:\n
    """
# Remaining words: [list the remaining words]
# Current recommended set (incorrect): [list the 4 words]
REGNERTE_MESSAGE_PART2 = """
    Please suggest a completely new set of 4 words based on the remaining words and correct the errors in the current set and do not use any know invalid groups. 
    """


def regenerate_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering regenerate recommendation:")
    logger.debug(f"\nEntering regenerate recommendation State: {pp.pformat(state)}")

    # build prompt for llm
    prompt = REGENERATE_MESSAGE_PART1
    # scramble the remaining words for more robust group selection
    random.shuffle(state["words_remaining"])
    prompt += f"\nRemaining words: {', '.join(state['words_remaining'])}\n"
    prompt += f"\nCurrent recommended set (incorrect): {', '.join(state['recommended_words'])}\n"
    if len(state["invalid_connections"]) > 0:
        prompt += "\n\nDo not include word groups that are known to be invalid."
        prompt += "\n"
        prompt += "Invalid word groups:\n"
        for invalid_connection in state["invalid_connections"]:
            prompt += f"{', '.join(invalid_connection)}\n"

    prompt += REGNERTE_MESSAGE_PART2

    prompt = HumanMessage(prompt)

    logger.info(f"\nPrompt for llm: {prompt.content}")

    # get recommendation from llm
    llm_response = ask_llm_for_solution(prompt, temperature=state["llm_temperature"])

    llm_response_json = json.loads(llm_response.content)
    if isinstance(llm_response_json, list):
        logger.debug(f"\nLLM response is list")
        state["recommended_words"] = sorted(llm_response_json[0]["words"])
        state["recommended_connection"] = llm_response_json[0]["connection"]
    else:
        logger.debug(f"\nLLM response is dict")
        state["recommended_words"] = sorted(llm_response_json["words"])
        state["recommended_connection"] = llm_response_json["connection"]

    logger.info("Exiting regenerate recommendation:")
    logger.debug(f"\nExiting regenerate recommendation State: {pp.pformat(state)}")

    return state


def apply_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering apply_recommendation:")
    logger.debug(f"\nEntering apply_recommendation State: {pp.pformat(state)}")

    state["recommendation_count"] += 1

    # display recommended words to user and get user response
    found_correct_group = interact_with_user(state["recommended_words"], state["recommended_connection"])

    # process user response
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
            pass
        case _:
            raise ValueError(f"Invalid user response {found_correct_group}")

    # remove recommended words if we found a solution
    if found_correct_group != "n":
        print(f"Recommendation {state['recommended_words']} is correct")
        # remove from remaining_words the words from recommended_words
        state["words_remaining"] = [word for word in state["words_remaining"] if word not in state["recommended_words"]]
        state["recommended_correct"] = True
        state["found_count"] += 1
    else:
        print(f"Recommendation {state['recommended_words']} is incorrect")
        state["invalid_connections"].append(copy.deepcopy(state["recommended_words"]))
        state["recommended_correct"] = False
        state["mistake_count"] += 1

    logger.info("Exiting apply_recommendation:")
    logger.debug(f"\nExiting apply_recommendation State: {pp.pformat(state)}")

    return state


def clear_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering clear_recommendation:")
    logger.debug(f"\nEntering clear_recommendation State: {pp.pformat(state)}")

    state["recommended_words"] = []
    state["recommended_connection"] = ""
    state["recommended_correct"] = False

    logger.info("Exiting clear_recommendation:")
    logger.debug(f"\nExiting clear_recommendation State: {pp.pformat(state)}")

    return state


def is_end(state: PuzzleState) -> str:
    logger.info("Entering is_end:")
    logger.debug(f"\nEntering is_end State: {pp.pformat(state)}")

    if len(state["words_remaining"]) == 0:
        logger.info("SOLVED THE CONNECTION PUZZLE!!!")
        print("SOLVED THE CONNECTION PUZZLE!!!")
        return "run_planner"
    elif state["mistake_count"] >= MAX_ERRORS:
        logger.info("FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
        print("FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
        return "run_planner"
    elif state["recommended_correct"]:
        logger.info("Recommendation accepted, Going to clear_recommendation")
        return "clear_recommendation"
    else:
        logger.info("Recommendation not accepted, Going to regenerate_recommendation")
        return "regenerate_recommendation"


def configure_logging(log_level):
    # get numeric value of log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Configure the logging settings
    logging.basicConfig(
        level=numeric_level,  # Set the logging level
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the log format
        handlers=[
            logging.FileHandler("app.log"),  # Log to a file
            # logging.StreamHandler(),  # Optional: Log to the console as well
        ],
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Set logging level for the application.")
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    parser.add_argument(
        "--trace", action="store_true", default=False, help="Enable langsmith tracing for the application."
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    configure_logging(args.log_level)

    # setup for tracing if specified
    if args.trace:
        with open("/openai/api_key.json") as f:
            config = json.load(f)
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        # os.environ["LANGCHAIN_PROJECT"] = "Agent-With-LangGraph"
        os.environ["LANGCHAIN_API_KEY"] = config["langsmith_key"]
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    # Create a logger instance
    logger = logging.getLogger(__name__)

    workflow = StateGraph(PuzzleState)

    workflow.add_node("run_planner", run_planner)
    workflow.add_node("setup_puzzle", setup_puzzle)
    workflow.add_node("get_recommendation", get_recommendation)
    workflow.add_node("regenerate_recommendation", regenerate_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)
    workflow.add_node("clear_recommendation", clear_recommendation)

    workflow.add_conditional_edges(
        "run_planner",
        determine_next_action,
        {
            "setup_puzzle": "setup_puzzle",
            "get_recommendation": "get_recommendation",
            END: END,
        },
    )

    workflow.add_edge("setup_puzzle", "run_planner")
    workflow.add_edge("get_recommendation", "apply_recommendation")
    workflow.add_edge("clear_recommendation", "run_planner")
    workflow.add_edge("regenerate_recommendation", "apply_recommendation")

    workflow.add_conditional_edges(
        "apply_recommendation",
        is_end,
        {
            "run_planner": "run_planner",
            "clear_recommendation": "clear_recommendation",
            "regenerate_recommendation": "regenerate_recommendation",
        },
    )

    workflow.set_entry_point("run_planner")

    app = workflow.compile()
    app.get_graph().draw_png("images/connection_solver_graph.png")

    initial_state = PuzzleState(
        status="",
        tool_to_use="",
        words_remaining=[],
        invalid_connections=[],
        recommended_words=[],
        recommended_connection="",
        recommended_correct=False,
        found_blue=False,
        found_green=False,
        found_purple=False,
        found_yellow=False,
        mistake_count=0,
        found_count=0,
        recommendation_count=0,
        llm_temperature=0.7,
    )

    with tracing_v2_enabled("Connection_Solver_Agent"):
        result = app.invoke(initial_state, {"recursion_limit": 50})

    print("\n\nFINAL PUZZLE STATE:")
    pp.pprint(result)
