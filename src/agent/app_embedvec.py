#!/usr/bin/env python3

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
import pprint


import numpy as np
import pandas as pd

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_core.runnables import ConfigurableField

from langchain_core.tracers.context import tracing_v2_enabled

from workflow_manager import run_workflow, create_workflow_graph
from puzzle_solver import PuzzleState
from tools import interact_with_user, manual_puzzle_setup_prompt


# specify the version of the agent
__version__ = "0.9.2"

# create logger
logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=4)


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


async def main(puzzle_setup_function: callable = None, puzzle_response_function: callable = None):
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

    # read in workflow instructions
    with open("src/agent/embedvec_workflow_specification.md", "r") as f:
        workflow_instructions = f.read()

    # TODO: determine how this is used
    # workflow_instructions_config = ConfigurableField(
    #     id="workflow_instructions",
    #     name="Workflow Instructions",
    #     description="Workflow Instructions for the Connection Solver",
    # )

    workflow_graph = create_workflow_graph()

    workflow_graph.get_graph().draw_png("images/connection_solver_embedvec_graph.png")

    runtime_config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "workflow_instructions": workflow_instructions,
        },
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
            recommendation_correct_groups=[],
        )

        if args.trace:
            with tracing_v2_enabled("Connection_Solver_Agent"):
                result = await run_workflow(
                    workflow_graph,
                    initial_state,
                    runtime_config,
                    puzzle_setup_function=puzzle_setup_function,
                    puzzle_response_function=puzzle_response_function,
                )
        else:
            result = await run_workflow(
                workflow_graph,
                initial_state,
                runtime_config,
                puzzle_setup_function=manual_puzzle_setup_prompt,
                puzzle_response_function=interact_with_user,
            )

    print("\nFOUND SOLUTIONS")
    pp.pprint(result)


if __name__ == "__main__":
    asyncio.run(main(manual_puzzle_setup_prompt, interact_with_user))
