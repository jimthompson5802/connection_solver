import json
import os
import sys
from typing import List


from workflow_manager import run_workflow, create_workflow_graph
from puzzle_solver import PuzzleState
from tools import read_file_to_word_list, extract_words_from_image

from flask import Flask, render_template, request, jsonify


app = Flask(__name__)

# get config from api_key.json and setup openai api key
with open("/openai/api_key.json") as f:
    config = json.load(f)
os.environ["OPENAI_API_KEY"] = config["key"]

# read in workflow instructions
with open("src/agent/embedvec_workflow_specification.md", "r") as f:
    workflow_instructions = f.read()

workflow_graph = create_workflow_graph()


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
    return jsonify({"status": "success", "puzzle_words": puzzle_words})


if __name__ == "__main__":

    app.run(debug=True)
