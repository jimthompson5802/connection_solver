import json
import os
import sys
from typing import List
import tempfile
import uuid


from workflow_manager import run_workflow, create_webui_workflow_graph
from puzzle_solver import PuzzleState
from tools import read_file_to_word_list, extract_words_from_image

from flask import Flask, render_template, request, jsonify


app = Flask(__name__)

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setup-puzzle", methods=["POST"])
async def setup_puzzle():
    puzzle_setup_fp = request.json.get("setup")
    puzzle_words = await webui_puzzle_setup_function(puzzle_setup_fp)

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

        # result = await run_webui_workflow(
        #     workflow_graph,
        #     initial_state,
        #     runtime_config,
        #     puzzle_setup_function=manual_puzzle_setup_prompt,
        #     puzzle_response_function=interact_with_user,
        # )

    return jsonify({"status": "success", "puzzle_words": puzzle_words})


@app.route("/update-solution", methods=["POST"])
def update_solution():
    return jsonify({"status": "success"})


if __name__ == "__main__":

    app.run(debug=True)
