import argparse
import asyncio
import logging
import pprint
import json
import os
import random
import uuid
import sqlite3
import tempfile


import numpy as np
import pandas as pd

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from langchain_core.tracers.context import tracing_v2_enabled

from tools import (
    interact_with_user,
)

from embedvec_tools import (
    PuzzleState,
    setup_puzzle,
    get_embedvec_recommendation,
    get_llm_recommendation,
    get_manual_recommendation,
    apply_recommendation,
    run_planner,
    determine_next_action,
)

# specify the version of the agent
__version__ = "0.8.0"

# create logger
logger = logging.getLogger(__name__)


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


pp = pprint.PrettyPrinter(indent=4)


async def run_workflow(workflow_graph, initial_state: PuzzleState, runtime_config: dict) -> None:
    # result = workflow_graph.invoke(initial_state, runtime_config)

    # run workflow until first human-in-the-loop input required for setup
    async for chunk in workflow_graph.astream(initial_state, runtime_config, stream_mode="values"):
        pass

    # continue workflow until the next human-in-the-loop input required for puzzle answer
    while chunk["tool_status"] != "puzzle_completed":
        current_state = workflow_graph.get_state(runtime_config)
        logger.debug(f"\nCurrent state: {current_state}")
        logger.info(f"\nNext action: {current_state.next}")
        if current_state.next[0] == "setup_puzzle":
            puzzle_source_type = input(
                "Enter 'file' to read words from a file or 'image' to read words from an image: "
            )
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
                current_state.values["current_tool"],
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
        async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
            logger.debug(f"\nstate: {workflow_graph.get_state(runtime_config)}")
            pass

    print("\n\nFINAL PUZZLE STATE:")
    pp.pprint(chunk)

    return None


async def main():
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

    # configure the logger
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

    runtime_config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 50,
    }

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp_db:
        initial_state = PuzzleState(
            puzzle_status="",
            current_tool="",
            tool_status="",
            workflow_instructions=None,
            llm_temperature=0.7,
            vocabulary_db_fp=tmp_db.name,
        )

        if args.trace:
            with tracing_v2_enabled("Connection_Solver_Agent"):
                result = run_workflow(workflow_graph, initial_state, runtime_config)
        else:
            result = await run_workflow(workflow_graph, initial_state, runtime_config)


if __name__ == "__main__":
    asyncio.run(main())
