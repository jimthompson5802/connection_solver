import json
import os
import sys
from typing import List
import tempfile
import uuid
import pprint as pp
import logging
import aiosqlite
import asyncio

import pandas as pd

from workflow_manager import create_webui_workflow_graph
from puzzle_solver import PuzzleState
from tools import read_file_to_word_list, extract_words_from_image_file
from openai_tools import LLMOpenAIInterface

from langchain_core.runnables import RunnableConfig

from src.agent import __version__

from quart import Quart, render_template, request, jsonify

pp = pp.PrettyPrinter(indent=4)
logger = logging.getLogger(__name__)

print(f"Running AVA {__version__}")

db_lock = asyncio.Lock()

# get config from api_key.json and setup openai api key
with open("/openai/api_key.json") as f:
    config = json.load(f)
os.environ["OPENAI_API_KEY"] = config["key"]

# read in workflow instructions
with open("src/agent/embedvec_webui_workflow_specification.md", "r") as f:
    workflow_instructions = f.read()

workflow_graph = create_webui_workflow_graph()


async def webui_puzzle_setup_function(puzzle_setup_fp: str, config: RunnableConfig) -> List[str]:
    # get suffix of the file path
    suffix = puzzle_setup_fp.split(".")[-1]
    if suffix == "txt":
        words = read_file_to_word_list(puzzle_setup_fp)
    elif suffix == "png":
        words = await extract_words_from_image_file(puzzle_setup_fp, config)
    else:
        ValueError(f"Unsupported file type: {suffix}")

    return words


# setup interace to LLM
llm_interface = LLMOpenAIInterface()

# setup runtime config
runtime_config = {
    "configurable": {
        "thread_id": str(uuid.uuid4()),
        "workflow_instructions": workflow_instructions,
        "llm_interface": llm_interface,
    },
    "recursion_limit": 50,
}

app = Quart(__name__)


@app.route("/")
async def index():
    print("app.route('/')")
    return await render_template("index.html")


@app.route("/setup-puzzle", methods=["POST"])
async def setup_puzzle():
    print("app.route('/setup-puzzle')")
    puzzle_setup_fp = (await request.json).get("setup")
    puzzle_words = await webui_puzzle_setup_function(puzzle_setup_fp, runtime_config)

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp_db:
        initial_state = PuzzleState(
            puzzle_status="initialized",
            current_tool="setup_puzzle",
            tool_status="initialized",
            workflow_instructions=workflow_instructions,
            llm_temperature=0.7,
            vocabulary_db_fp=tmp_db.name,
            recommendation_answer_status="",
            recommendation_correct_groups=[],
            found_count=0,
            mistake_count=0,
            recommendation_count=0,
            llm_retry_count=0,
            invalid_connections=[],
            words_remaining=puzzle_words,
        )

        print("\nGenerating vocabulary and embeddings for the words...this may take several seconds ")
        vocabulary = await llm_interface.generate_vocabulary(puzzle_words)
        # Convert dictionary to DataFrame
        rows = []
        for word, definitions in vocabulary.items():
            for definition in definitions:
                rows.append({"word": word, "definition": definition})
        df = pd.DataFrame(rows)

    # Generate embeddings
    print("\nGenerating embeddings for the definitions")
    embeddings = llm_interface.generate_embeddings(df["definition"].tolist())
    # convert embeddings to json strings for storage
    df["embedding"] = [json.dumps(v) for v in embeddings]

    # store the vocabulary in external database
    print("\nStoring vocabulary and embeddings in external database")

    async with aiosqlite.connect(tmp_db.name) as conn:
        async with db_lock:
            cursor = await conn.cursor()
            # create the table
            await cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT,
                    definition TEXT,
                    embedding TEXT
                )
                """
            )
            await conn.executemany(
                "INSERT INTO vocabulary (word, definition, embedding) VALUES (?, ?, ?)",
                df.values.tolist(),
            )
            await conn.commit()

    # run workflow until the next human-in-the-loop input needed
    async for chunk in workflow_graph.astream(initial_state, runtime_config, stream_mode="values"):
        pass

    return jsonify({"status": "success in getting puzzle words", "puzzle_words": puzzle_words})


@app.route("/update-solution", methods=["POST"])
async def update_solution():
    print("app.route('/update-solution')")
    data = await request.json
    user_response = data.get("user_response")

    if user_response in ["y", "g", "b", "p"]:
        logger.info(f"User response: {user_response}")
        status_message = "Correct recommendation"
    elif user_response in ["n", "o"]:
        logger.info(f"User response: {user_response}")
        status_message = "Incorrect recommendation"

    current_state = workflow_graph.get_state(runtime_config)
    logger.debug(f"\nCurrent state: {current_state}")
    logger.info(f"\nNext action: {current_state.next}")

    if current_state.next[0] == "apply_recommendation":

        workflow_graph.update_state(
            runtime_config,
            {
                "recommendation_answer_status": user_response,
            },
        )
    else:
        raise RuntimeError(f"Unexpected next action: {current_state.next[0]}")

    # run rest of workflow untile the next human-in-the-loop input required for puzzle answer
    async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
        logger.debug(f"\nstate: {workflow_graph.get_state(runtime_config)}")
        pass

    # get current state after applying the user response
    current_state = workflow_graph.get_state(runtime_config)

    response_dict = {
        "words_remaining": current_state.values["words_remaining"],
        "connection_reason": "",
        "recommeded_words": "",
        "found_count": current_state.values["found_count"],
        "mistake_count": current_state.values["mistake_count"],
        "found_groups": current_state.values["recommendation_correct_groups"],
        "invalid_groups": [x[1] for x in current_state.values["invalid_connections"]],
    }

    if current_state.values["found_count"] == 4:
        response_dict["status"] = "PUZZLE SOLVED!!!"
    elif current_state.values["mistake_count"] == 4:
        response_dict["status"] = "FAILED TO SOLVE PUZZLE!!!"

    return jsonify(response_dict)


@app.route("/generate-next", methods=["POST"])
async def generate_next():
    print("app.route('/generate-next')")
    current_state = workflow_graph.get_state(runtime_config)

    return jsonify(
        {
            "status": "Next recommendation will be generated here",
            "recommended_words": sorted(current_state.values["recommended_words"]),
            "connection_reason": current_state.values["recommended_connection"],
            "active_recommender": current_state.values["current_tool"],
        }
    )


@app.route("/manual-override", methods=["POST"])
async def manual_override():
    print("app.route('/manual-override')")
    current_state = workflow_graph.get_state(runtime_config)
    workflow_graph.update_state(
        runtime_config,
        {
            "puzzle_status": "manual_override",
        },
    )
    return jsonify({"status": "success"})


@app.route("/confirm-manual-override", methods=["POST"])
async def confirm_manual_override():
    print("app.route('/confirm-manual-override')")
    data = await request.json
    words = data.get("words", [])

    current_state = workflow_graph.get_state(runtime_config)

    if set(words).issubset(set(current_state.values["words_remaining"])):
        workflow_graph.update_state(
            runtime_config,
            {"recommended_words": words},
        )
        status_message = "success"
    else:
        status_message = "error"

    return jsonify({"status": status_message})


@app.route("/terminate", methods=["POST"])
async def terminate():
    print("app.route('/terminate')")
    # Schedule the shutdown after sending response
    asyncio.get_event_loop().call_later(1, lambda: os._exit(0))
    return jsonify({"status": "terminating"})


if __name__ == "__main__":
    app.run(debug=True)
