import argparse
import copy
import logging
import pprint
import json
import os
import random
import uuid
import sqlite3


import numpy as np
import pandas as pd

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
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
__version__ = "0.7.1"

pp = pprint.PrettyPrinter(indent=4)

MAX_ERRORS = 4
RETRY_LIMIT = 8


KEY_PUZZLE_STATE_FIELDS = ["puzzle_status", "tool_status", "current_tool"]


def run_planner(state: PuzzleState) -> PuzzleState:
    logger.info("Entering run_planner:")
    logger.debug(f"\nEntering run_planner State: {pp.pformat(state)}")

    if state["workflow_instructions"] is None:
        # read in the workflow specification
        # TODO: support specifying the workflow specification file path in config
        workflow_spec_fp = "src/agent/embedvec_workflow_specification.md"
        with open(workflow_spec_fp, "r") as f:
            state["workflow_instructions"] = f.read()

        logger.debug(f"Workflow Specification: {state['workflow_instructions']}")

    # workflow instructions
    instructions = HumanMessage(state["workflow_instructions"])
    logger.debug(f"\nWorkflow instructions:\n{instructions.content}")

    # convert state to json string
    relevant_state = {k: state[k] for k in KEY_PUZZLE_STATE_FIELDS}
    puzzle_state = "\npuzzle state:\n" + json.dumps(relevant_state)

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


def get_llm_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_recommendation")
    logger.debug(f"Entering get_recommendation State: {pp.pformat(state)}")

    state["current_tool"] = "llm_recommender"
    print(f"\nENTERED {state['current_tool'].upper()}")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    # build prompt for llm
    prompt = HUMAN_MESSAGE_BASE

    attempt_count = 0
    while True:
        attempt_count += 1
        if attempt_count > RETRY_LIMIT:
            break
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

        if compute_group_id(recommended_words) not in set(x[0] for x in state["invalid_connections"]):
            break
        else:
            print(
                f"\nrepeat invalid group detected: group_id {compute_group_id(recommended_words)}, recommendation: {sorted(recommended_words)}"
            )

    state["recommended_words"] = sorted(recommended_words)
    state["recommended_connection"] = recommended_connection

    if attempt_count <= RETRY_LIMIT:
        state["tool_status"] = "have_recommendation"
    else:
        print(f"Failed to get a valid recommendation after {RETRY_LIMIT} attempts")
        print("Changing to manual_recommender, last attempt to solve the puzzle")
        print(f"last recommendation: {state['recommended_words']} with {state['recommended_connection']}")
        state["tool_status"] = "manual_recommendation"

    logger.info("Exiting get_recommendation")
    logger.debug(f"Exiting get_recommendation State: {pp.pformat(state)}")

    return state


def get_embedvec_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_embedvec_recommendation")
    logger.debug(f"Entering get_embedvec_recommendation State: {pp.pformat(state)}")

    state["current_tool"] = "embedvec_recommender"
    print(f"\nENTERED {state['current_tool'].upper()}")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    # get candidate list of words from database
    conn = sqlite3.connect(state["vocabulary_db_fp"])
    sql_query = "SELECT * FROM vocabulary"
    df = pd.read_sql_query(sql_query, conn)
    conn.close()

    # convert embedding string representation to numpy array
    df["embedding"] = df["embedding"].apply(lambda x: np.array(json.loads(x)))

    # get candidate list of words based on embedding vectors
    candidate_list = get_candidate_words(df)
    print(f"candidate_lists size: {len(candidate_list)}")

    # validate the top 5 candidate list with LLM
    list_to_validate = "\n".join([str(x) for x in candidate_list[:5]])
    recommended_group = choose_embedvec_item(list_to_validate)
    logger.info(f"Recommended group: {recommended_group}")

    state["recommended_words"] = recommended_group["candidate_group"]
    state["recommended_connection"] = recommended_group["explanation"]
    state["tool_status"] = "have_recommendation"

    # build prompt for llm

    logger.info("Exiting get_embedvec_recommendation")
    logger.debug(f"Exiting get_embedvec_recommendation State: {pp.pformat(state)}")

    return state


def get_manual_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_manual_recommendation")
    logger.debug(f"Entering get_manual_recommendation State: {pp.pformat(state)}")

    state["current_tool"] = "manual_recommender"
    print(f"\nENTERED {state['current_tool'].upper()}")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    # display current recommendation and words remaining
    print(f"\nCurrent recommendation: {sorted(state['recommended_words'])}")
    print(f"Words remaining: {state['words_remaining']}")

    # get user input for manual recommendation
    response = "n"
    while response != "y":
        manual_recommendation = [
            x.strip() for x in input("Enter manual recommendation as comma separated words: ").split(",")
        ]
        print(f"Manual recommendation: {manual_recommendation}")

        if not set(manual_recommendation).issubset(set(state["words_remaining"])) or len(manual_recommendation) != 4:
            print("Manual recommendation is not a subset of words remaining or not 4 words")
            print("try again")
        else:
            response = input("Is the manual recommendation correct? (y/n): ")

    # get user defined connection
    response = "n"
    while response != "y":
        manual_connection = input("Enter manual connection: ")
        print(f"Manual connection: {manual_connection}")
        response = input("Is the manual connection correct? (y/n): ")

    state["recommended_words"] = manual_recommendation
    state["recommended_connection"] = manual_connection
    state["tool_status"] = "have_recommendation"

    logger.info("Exiting get_manual_recommendation")
    logger.debug(f"Exiting get_manual_recommendation State: {pp.pformat(state)}")

    return state


def apply_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering apply_recommendation:")
    logger.debug(f"\nEntering apply_recommendation State: {pp.pformat(state)}")

    state["recommendation_count"] += 1

    # get user response from human input
    found_correct_group = state["recommendation_answer_status"]

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

        # for embedvec_recommender, remove the words from the vocabulary database
        if state["current_tool"] == "embedvec_recommender":
            # remove accepted words from vocabulary.db
            conn = sqlite3.connect(state["vocabulary_db_fp"])
            # for each word in recommended_words, remove the word from the vocabulary table
            for word in state["recommended_words"]:
                sql_query = f"DELETE FROM vocabulary WHERE word = '{word}'"
                conn.execute(sql_query)
            conn.commit()
            conn.close()

        # remove the words from words_remaining
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
                    one_away_group_recommendation = one_away_analyzer(state, invalid_group, state["words_remaining"])

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
                    if state["current_tool"] == "embedvec_recommender":
                        print("Changing the recommender from 'embedvec_recommender' to 'llm_recommender'")
                        state["current_tool"] = "llm_recommender"
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

        state["tool_status"] = "puzzle_completed"
    elif found_correct_group == "o":
        if one_away_group_recommendation:
            print(f"using one_away_group_recommendation")
            state["recommended_words"] = one_away_group_recommendation.words
            state["recommended_connection"] = one_away_group_recommendation.connection_description
            state["tool_status"] = "have_recommendation"
        else:
            print(f"no one_away_group_recommendation, let llm_recommender try again")
            state["recommended_words"] = []
            state["recommended_connection"] = ""
            state["tool_status"] = "next_recommendation"
    elif found_correct_group == "m":
        print("Changing to manual_recommender")
        state["tool_status"] = "manual_recommendation"

    else:
        logger.info("Going to next get_recommendation")
        state["tool_status"] = "next_recommendation"

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


def run_workflow(workflow_graph, initial_state: PuzzleState, runtime_config: dict) -> None:
    # result = workflow_graph.invoke(initial_state, runtime_config)

    # run workflow until first human-in-the-loop input required for setup
    for chunk in workflow_graph.stream(initial_state, runtime_config, stream_mode="values"):
        pass

    # continue workflow until the next human-in-the-loop input required for puzzle answer
    while chunk["tool_status"] != "puzzle_completed":
        current_state = workflow_graph.get_state(runtime_config)
        logger.debug(f"\nCurrent state: {current_state}")
        logger.info(f"\nNext action: {current_state.next}")
        if current_state.next[0] == "setup_puzzle":
            puzzle_source_type = input("Enter 'file' to read words from a file or 'image' to read words from an image: ")
            puzzle_source_fp = input("Please enter the file/image location: ")

            # specify location of puzzle data for setup
            workflow_graph.update_state(
                runtime_config,
                {
                    "puzzle_source_type": puzzle_source_type,
                    "puzzle_source_fp": puzzle_source_fp,
                },
            )
        elif current_state.next[0] == "apply_recommendation":
            found_correct_group = interact_with_user(
                sorted(current_state.values["recommended_words"]), 
                current_state.values["recommended_connection"],    
                current_state.values["current_tool"]
            )

            workflow_graph.update_state(
                runtime_config,
                {
                    "recommendation_answer_status": found_correct_group,
                },
            )
        else:
            raise RuntimeError(f"Unexpected next action: {current_state.next[0]}")

        # run rest of workflow untile the next human-in-the-loop input required for puzzle answer
        for chunk in workflow_graph.stream(None, runtime_config, stream_mode="values"):
            logger.debug(f"\nstate: {workflow_graph.get_state(runtime_config)}")
            pass


    print("\n\nFINAL PUZZLE STATE:")
    pp.pprint(chunk)

    return None


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
    workflow.add_node("get_llm_recommendation", get_llm_recommendation)
    workflow.add_node("get_manual_recommendation", get_manual_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)

    workflow.add_conditional_edges(
        "run_planner",
        determine_next_action,
        {
            "setup_puzzle": "setup_puzzle",
            "get_embedvec_recommendation": "get_embedvec_recommendation",
            "get_llm_recommendation": "get_llm_recommendation",
            "get_manual_recommendation": "get_manual_recommendation",
            "apply_recommendation": "apply_recommendation",
            END: END,
        },
    )

    workflow.add_edge("setup_puzzle", "run_planner")
    workflow.add_edge("get_llm_recommendation", "run_planner")
    workflow.add_edge("get_embedvec_recommendation", "run_planner")
    workflow.add_edge("get_manual_recommendation", "run_planner")
    workflow.add_edge("apply_recommendation", "run_planner")

    workflow.set_entry_point("run_planner")

    memory_checkpoint = MemorySaver()

    workflow_graph = workflow.compile(
        checkpointer=memory_checkpoint,
        interrupt_before=["setup_puzzle", "apply_recommendation"],
    )
    workflow_graph.get_graph().draw_png("images/connection_solver_embedvec_graph.png")

    initial_state = PuzzleState(
        puzzle_status="",
        current_tool="",
        tool_status="",
        workflow_instructions=None,
        llm_temperature=0.7,
        vocabulary_db_fp="/tmp/vocabulary.db",
    )

    runtime_config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 50,
    }

    if args.trace:
        with tracing_v2_enabled("Connection_Solver_Agent"):
            result = run_workflow(workflow_graph, initial_state, runtime_config)
    else:
        result = run_workflow(workflow_graph, initial_state, runtime_config)
