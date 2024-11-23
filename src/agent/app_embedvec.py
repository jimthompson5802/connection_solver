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
    ask_llm_for_solution,
    interact_with_user,
)

from embedvec_tools import (
    ask_llm_for_next_step,
    PuzzleState,
    setup_puzzle,
    choose_embedvec_item,
    get_candidate_words,
    compute_group_id,
    one_away_analyzer,
)

# specify the version of the agent
__version__ = "0.6.2"

pp = pprint.PrettyPrinter(indent=4)

MAX_ERRORS = 4


KEY_PUZZLE_STATE_FIELDS = ["puzzle_status", "puzzle_step", "puzzle_recommender"]


def run_planner(state: PuzzleState) -> PuzzleState:
    logger.info("Entering run_planner:")
    logger.debug(f"\nEntering run_planner State: {pp.pformat(state)}")

    # workflow instructions
    instructions = HumanMessage(state["workflow_instructions"])
    logger.debug(f"\nWorkflow instructions:\n{instructions.content}")

    # convert state to json string
    relevanat_state = {k: state[k] for k in KEY_PUZZLE_STATE_FIELDS}
    puzzle_state = "\npuzzle state:\n" + json.dumps(relevanat_state)

    # wrap the state in a human message
    puzzle_state = HumanMessage(puzzle_state)
    logger.info(f"\nState for lmm: {puzzle_state.content}")

    # get next action from llm
    next_action = ask_llm_for_next_step(instructions, puzzle_state, model="gpt-3.5-turbo", temperature=0)

    logger.info(f"\nNext action from llm: {next_action.content}")

    state["tool_to_use"] = json.loads(next_action.content)["tool"]

    logger.info("Exiting run_planner:")
    logger.debug(f"\nExiting run_planner State: {pp.pformat(state)}")
    return state


def determine_next_action(state: PuzzleState) -> str:
    logger.info("Entering determine_next_action:")
    logger.debug(f"\nEntering determine_next_action State: {pp.pformat(state)}")

    tool_to_use = state["tool_to_use"]

    if tool_to_use == "ABORT":
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

    print(f"\nENTERED {state['puzzle_recommender'].upper()}")

    # build prompt for llm
    prompt = HUMAN_MESSAGE_BASE

    # TODO: Clean up the code below
    # if len(state["invalid_connections"]) > 0:
    #     prompt += " Do not include word groups that are known to be invalid."
    #     prompt += "\n\n"
    #     prompt += "Invalid word groups:\n"
    #     for invalid_connection in state["invalid_connections"]:
    #         prompt += f"{', '.join(invalid_connection)}\n"
    # prompt += "\n\n"
    attempt_count = 0
    while True:
        attempt_count += 1
        print(f"attempt_count: {attempt_count}")
        prompt = HUMAN_MESSAGE_BASE
        # scramble the remaining words for more robust group selection
        if np.random.uniform() < 0.5:
            random.shuffle(state["words_remaining"])
        else:
            state["words_remaining"].reverse()
        print(f"words_remaining: {state['words_remaining']}")
        prompt += f"candidate list: {', '.join(state['words_remaining'])}\n"

        prompt = HumanMessage(prompt)

        logger.info(f"\nPrompt for llm: {prompt.content}")

        # get recommendation from llm
        llm_response = ask_llm_for_solution(prompt, temperature=state["llm_temperature"])

        llm_response_json = json.loads(llm_response.content)
        if isinstance(llm_response_json, list):
            logger.debug(f"\nLLM response is list")
            recommended_words = llm_response_json[0]["words"]
            recommended_connection = llm_response_json[0]["connection"]
        else:
            logger.debug(f"\nLLM response is dict")
            recommended_words = llm_response_json["words"]
            recommended_connection = llm_response_json["connection"]

        if (
            compute_group_id(recommended_words) not in set(x[0] for x in state["invalid_connections"])
        ) or attempt_count > 10:
            break
        else:
            print(
                f"\nrepeat invalid group detected: group_id {compute_group_id(recommended_words)}, recommendation: {recommended_words}"
            )

    state["recommended_words"] = recommended_words
    state["recommended_connection"] = recommended_connection

    state["puzzle_step"] = "have_recommendation"

    logger.info("Exiting get_recommendation")
    logger.debug(f"Exiting get_recommendation State: {pp.pformat(state)}")

    return state


def get_embedvec_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_embedvec_recommendation")
    logger.debug(f"Entering get_embedvec_recommendation State: {pp.pformat(state)}")

    print(f"\nENTERED {state['puzzle_recommender'].upper()}")

    # get candidate list of words
    candidate_list = get_candidate_words(state["vocabulary_df"])
    print(f"candidate_lists size: {len(candidate_list)}")

    # validate the top 5 candidate list with LLM
    list_to_validate = "\n".join([str(x) for x in candidate_list[:5]])
    recommended_group = choose_embedvec_item(list_to_validate)
    logger.info(f"Recommended group: {recommended_group}")

    state["recommended_words"] = recommended_group["candidate_group"]
    state["recommended_connection"] = recommended_group["explanation"]
    state["puzzle_step"] = "have_recommendation"

    # build prompt for llm

    logger.info("Exiting get_embedvec_recommendation")
    logger.debug(f"Exiting get_embedvec_recommendation State: {pp.pformat(state)}")

    return state


def apply_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering apply_recommendation:")
    logger.debug(f"\nEntering apply_recommendation State: {pp.pformat(state)}")

    state["recommendation_count"] += 1

    # display recommended words to user and get user response
    found_correct_group = interact_with_user(
        sorted(state["recommended_words"]), state["recommended_connection"], state["puzzle_recommender"]
    )

    # process result of user response
    if found_correct_group in ["y", "g", "b", "p"]:
        print(f"Recommendation {sorted(state['recommended_words'])} is correct")
        match found_correct_group:
            case "y":
                state["found_yellow"] = True
            case "g":
                state["found_green"] = True
            case "b":
                state["found_blue"] = True
            case "p":
                state["found_purple"] = True

        # for embedvec_recommender, remove the words from the vocabulary_df
        if state["puzzle_recommender"] == "embedvec_recommender":
            # remove from remaining_words the words from recommended_words
            state["vocabulary_df"] = state["vocabulary_df"][
                ~state["vocabulary_df"]["word"].isin(state["recommended_words"])
            ]

        state["words_remaining"] = [word for word in state["words_remaining"] if word not in state["recommended_words"]]
        state["recommended_correct"] = True
        state["found_count"] += 1
    elif found_correct_group in ["n", "o"]:
        invalid_group = state["recommended_words"]
        invalid_group_id = compute_group_id(invalid_group)
        state["invalid_connections"].append((invalid_group_id, invalid_group))
        state["recommended_correct"] = False
        state["mistake_count"] += 1

        if state["mistake_count"] < MAX_ERRORS:
            match found_correct_group:
                case "o":
                    print(f"Recommendation {sorted(state['recommended_words'])} is incorrect, one away from correct")

                    # perform one-away analysis
                    one_away_group_recommendation = one_away_analyzer(invalid_group, state["words_remaining"])

                    # check if one_away_group_recommendation is a prior mistake
                    if one_away_group_recommendation:
                        one_away_group_id = compute_group_id(one_away_group_recommendation.words)
                        if one_away_group_id in set(x[0] for x in state["invalid_connections"]):
                            print(f"one_away_group_recommendation is a prior mistake")
                            one_away_group_recommendation = None
                        else:
                            print(f"one_away_group_recommendation is a new recommendation")

                case "n":
                    print(f"Recommendation {sorted(state['recommended_words'])} is incorrect")
                    if state["puzzle_recommender"] == "embedvec_recommender":
                        print("Changing the recommender from 'embedvec_recommender' to 'llm_recommender'")
                        state["puzzle_recommender"] = "llm_recommender"
        else:
            state["recommended_words"] = []
            state["recommended_connection"] = ""
            state["recommended_correct"] = False

    if len(state["words_remaining"]) == 0 or state["mistake_count"] >= MAX_ERRORS:
        if state["mistake_count"] >= MAX_ERRORS:
            logger.info("FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
            print("FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
        else:
            logger.info("SOLVED THE CONNECTION PUZZLE!!!")
            print("SOLVED THE CONNECTION PUZZLE!!!")

        state["puzzle_step"] = "puzzle_completed"
    elif found_correct_group == "o":
        if one_away_group_recommendation:
            print(f"using one_away_group_recommendation")
            state["recommended_words"] = one_away_group_recommendation.words
            state["recommended_connection"] = one_away_group_recommendation.connection_description
            state["puzzle_step"] = "have_recommendation"
        else:
            print(f"no one_away_group_recommendation, let llm_recommender try again")
            state["recommended_words"] = []
            state["recommended_connection"] = ""
            state["puzzle_step"] = "next_recommendation"
    else:
        logger.info("Going to next get_recommendation")
        state["puzzle_step"] = "next_recommendation"

    logger.info("Exiting apply_recommendation:")
    logger.debug(f"\nExiting apply_recommendation State: {pp.pformat(state)}")

    return state


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

    print(f"Running Connection Solver Agent with EmbedVec Recommender {__version__}")

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

    # get config from api_key.json and setup openai api key
    with open("/openai/api_key.json") as f:
        config = json.load(f)
    os.environ["OPENAI_API_KEY"] = config["key"]

    # setup for tracing if specified
    if args.trace:
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
    workflow.add_node("get_embedvec_recommendation", get_embedvec_recommendation)
    workflow.add_node("get_recommendation", get_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)

    workflow.add_conditional_edges(
        "run_planner",
        determine_next_action,
        {
            "setup_puzzle": "setup_puzzle",
            "get_embedvec_recommendation": "get_embedvec_recommendation",
            "get_recommendation": "get_recommendation",
            "apply_recommendation": "apply_recommendation",
            END: END,
        },
    )

    workflow.add_edge("setup_puzzle", "run_planner")
    workflow.add_edge("get_recommendation", "run_planner")
    workflow.add_edge("get_embedvec_recommendation", "run_planner")
    workflow.add_edge("apply_recommendation", "run_planner")

    workflow.set_entry_point("run_planner")

    app = workflow.compile()
    app.get_graph().draw_png("images/connection_solver_embedvec_graph.png")

    initial_state = PuzzleState(
        puzzle_status="",
        puzzle_step="",
        puzzle_recommender="",
        workflow_instructions="",
        llm_temperature=0.7,
    )

    if args.trace:
        with tracing_v2_enabled("Connection_Solver_Agent"):
            result = app.invoke(initial_state, {"recursion_limit": 50})
    else:
        result = app.invoke(initial_state, {"recursion_limit": 50})

    print("\n\nFINAL PUZZLE STATE:")
    pp.pprint(result)
