#!/usr/bin/env python3

import argparse
import asyncio
import logging
import pprint
import json
import os
import uuid
import tempfile
from functools import partial

import pandas as pd

from langchain_core.runnables import RunnableConfig

from langchain_core.tracers.context import tracing_v2_enabled

from workflow_manager import run_workflow, create_workflow_graph
from puzzle_solver import PuzzleState
from tools import check_one_solution, llm_interface_registry


from src.agent import __version__


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
    print(f"Running Connection Solver Agent Tester {__version__}")

    parser = argparse.ArgumentParser(description="Set logging level for the application.")

    parser.add_argument(
        "--llm_interface",
        type=str,
        default="openai",
        help="Set the LLM interface to use (e.g., openai, other_llm), default is 'openai'",
    )

    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    parser.add_argument(
        "--trace", action="store_true", default=False, help="Enable langsmith tracing for the application."
    )

    # parameter for jsonl file path for data to set up the puzzle
    parser.add_argument(
        "--puzzle_setup_fp",
        type=str,
        default=None,
        help="File path to setup Connections Puzzle data",
    )

    # parameter to enable or disable concurrency, set default to 'true'
    parser.add_argument(
        "--concurrent",
        type=str,
        choices=["true", "false"],
        default="true",
        help="Enable or disable concurrency for the application (true or false)",
    )

    # Parse arguments
    args = parser.parse_args()

    if args.concurrent == "true":
        concurrent_flag = True
    else:
        concurrent_flag = False

    # configure the logger
    configure_logging(args.log_level)

    # setup for tracing if specified
    if args.trace:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        # os.environ["LANGCHAIN_PROJECT"] = "Agent-With-LangGraph"
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    workflow_graph = create_workflow_graph()

    workflow_graph.get_graph().draw_png("images/connection_solver_embedvec_graph.png")

    # read in puzzle data
    puzzle_data = []
    if args.puzzle_setup_fp:
        with open(args.puzzle_setup_fp, "r") as f:
            for line in f:
                puzzle_data.append(json.loads(line))

    # read in workflow instructions
    with open("src/agent/embedvec_tester_workflow_specification.md", "r") as f:
        workflow_instructions = f.read()

    async def solve_a_puzzle(i, solution, workflow_instructions):
        print(f"\n>>>>SOLVING PUZZLE {i+1}")

        llm_interface = llm_interface_registry.get(args.llm_interface)()

        runtime_config = RunnableConfig(
            configurable={
                "thread_id": str(uuid.uuid4()),
                "workflow_instructions": workflow_instructions,
                "llm_interface": llm_interface,
            },
            recursion_limit=50,
        )

        async def setup_this_puzzle(solution):
            return solution

        setup_this_puzzle = partial(setup_this_puzzle, solution["words"])

        check_this_puzzle = partial(puzzle_response_function, solution["solution"])

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
                        puzzle_setup_function=setup_this_puzzle,
                        puzzle_response_function=check_this_puzzle,
                    )
            else:
                result = await run_workflow(
                    workflow_graph,
                    initial_state,
                    runtime_config,
                    puzzle_setup_function=setup_this_puzzle,
                    puzzle_response_function=check_this_puzzle,
                )

        print("\nFOUND SOLUTIONS")
        pp.pprint(result)

        return result

    if concurrent_flag:
        found_solutions = await asyncio.gather(
            *[solve_a_puzzle(i, solution, workflow_instructions) for i, solution in enumerate(puzzle_data)]
        )
    else:
        found_solutions = []
        for i, solution in enumerate(puzzle_data):
            found_solutions.append(await solve_a_puzzle(i, solution, workflow_instructions))

    return found_solutions


if __name__ == "__main__":
    results = asyncio.run(main(None, check_one_solution))

    print("ALL GROUPS FOUND")
    pp.pprint(results)

    solved_puzzle = [len(x) == 4 for x in results]
    number_found = [len(x) for x in results]
    groups_found = [x for x in results]

    df = pd.DataFrame(
        {
            "solved_puzzle": solved_puzzle,
            "number_found": number_found,
            "groups_found": groups_found,
        }
    )

    print(df)

    # save dataframe to pickle file
    df.to_pickle("results/automated_test_results.pkl")
