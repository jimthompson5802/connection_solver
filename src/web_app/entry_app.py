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


from workflow_manager import run_workflow, create_webui_workflow_graph
from puzzle_solver import PuzzleState, generate_vocabulary, generate_embeddings
from tools import read_file_to_word_list, extract_words_from_image

from flask import Flask, render_template, request, jsonify

pp = pp.PrettyPrinter(indent=4)
logger = logging.getLogger(__name__)

db_lock = asyncio.Lock()

# get config from api_key.json and setup openai api key
with open("/openai/api_key.json") as f:
    config = json.load(f)
os.environ["OPENAI_API_KEY"] = config["key"]

# read in workflow instructions
with open("src/agent/embedvec_webui_workflow_specification.md", "r") as f:
    workflow_instructions = f.read()

workflow_graph = create_webui_workflow_graph()


async def webui_puzzle_setup_function(puzzle_setup_fp: str) -> List[str]:
    # get suffix of the file path
    suffix = puzzle_setup_fp.split(".")[-1]
    if suffix == "txt":
        words = read_file_to_word_list(puzzle_setup_fp)
    elif suffix == "png":
        words = await extract_words_from_image(puzzle_setup_fp)
    else:
        ValueError(f"Unsupported file type: {suffix}")

    return words


async def run_webui_workflow(
    workflow_graph,
    initial_state: PuzzleState,
    runtime_config: dict,
    *,
    puzzle_response_function: callable = None,
) -> None:

    # run workflow until the next human-in-the-loop input needed
    async for chunk in workflow_graph.astream(initial_state, runtime_config, stream_mode="values"):
        pass

    # continue workflow until the next human-in-the-loop input required for puzzle answer
    while chunk["tool_status"] != "puzzle_completed":
        current_state = workflow_graph.get_state(runtime_config)
        logger.debug(f"\nCurrent state: {current_state}")
        logger.info(f"\nNext action: {current_state.next}")
        if current_state.next[0] == "apply_recommendation":
            puzzle_response = puzzle_response_function(
                gen_words=sorted(current_state.values["recommended_words"]),
                gen_reason=current_state.values["recommended_connection"],
                recommender=current_state.values["current_tool"],
            )

            workflow_graph.update_state(
                runtime_config,
                {
                    "recommendation_answer_status": puzzle_response,
                },
            )
        else:
            raise RuntimeError(f"Unexpected next action: {current_state.next[0]}")

        # run rest of workflow untile the next human-in-the-loop input required for puzzle answer
        async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
            logger.debug(f"\nstate: {workflow_graph.get_state(runtime_config)}")
            pass

    return chunk["recommendation_correct_groups"]


runtime_config = {
    "configurable": {
        "thread_id": str(uuid.uuid4()),
        "workflow_instructions": workflow_instructions,
    },
    "recursion_limit": 50,
}

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setup-puzzle", methods=["POST"])
async def setup_puzzle():
    puzzle_setup_fp = request.json.get("setup")
    puzzle_words = await webui_puzzle_setup_function(puzzle_setup_fp)

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp_db:
        initial_state = PuzzleState(
            puzzle_status="initalized",
            current_tool="setup_puzzle",
            tool_status="initialized",
            workflow_instructions=workflow_instructions,
            llm_temperature=0.7,
            vocabulary_db_fp=tmp_db.name,
            recommendation_correct_groups=[],
            found_count=0,
            mistake_count=0,
            recommendation_count=0,
            llm_retry_count=0,
            invalid_connections=[],
        )

        print("\nGenerating vocabulary and embeddings for the words...this may take several seconds ")
        vocabulary = await generate_vocabulary(puzzle_words)
        # Convert dictionary to DataFrame
        rows = []
        for word, definitions in vocabulary.items():
            for definition in definitions:
                rows.append({"word": word, "definition": definition})
        df = pd.DataFrame(rows)

    # Generate embeddings
    print("\nGenerating embeddings for the definitions")
    embeddings = generate_embeddings(df["definition"].tolist())
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
def update_solution():
    return jsonify({"status": "Correct recommendation"})


@app.route("/generate-next", methods=["POST"])
async def generate_next():
    current_state = workflow_graph.get_state(runtime_config)

    return jsonify(
        {
            "status": "Next recommendation will be generated here",
            "recommended_words": current_state.values["recommended_words"],
            "connection_reason": current_state.values["recommended_connection"],
        }
    )


if __name__ == "__main__":

    app.run(debug=True)