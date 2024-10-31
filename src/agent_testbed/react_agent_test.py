import json
import os

from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

with open("/openai/api_key.json") as f:
    openai_key = json.load(f)

os.environ["OPENAI_API_KEY"] = openai_key["key"]


# Define a simple tool
def get_current_time(x):
    from datetime import datetime

    return datetime.now().strftime("%H:%M:%S")


time_tool = Tool(
    name="CheckSystemTime", func=get_current_time, description="Useful for getting the current system time"
)

# Create the language model
llm = ChatOpenAI(temperature=0)

# Load the ReAct prompt
prompt = hub.pull("hwchase17/react")

# Create the ReAct agent
tools = [time_tool]
agent = create_react_agent(llm, tools, prompt)

# Create an agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Run the agent
result = agent_executor.invoke({"input": "What is the current time?"})
print(result["output"])
