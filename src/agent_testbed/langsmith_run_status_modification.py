import json
import os

from langsmith import Client
import datetime

with open("/openai/api_key.json") as f:
    config = json.load(f)
os.environ["LANGCHAIN_API_KEY"] = config["langsmith_key"]

# utility to mark a run in "pending" to be completed
# fill in the run_id for the pending run
run_id = "40f6ffd6-5658-4c82-a268-5654c7a7abd5"

client = Client()
client.update_run(run_id, end_time=datetime.datetime.now())
