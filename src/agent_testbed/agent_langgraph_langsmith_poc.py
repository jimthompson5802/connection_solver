import os
import json

from langchain_openai import ChatOpenAI
from langchain.tools import Tool, tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.context import tracing_v2_enabled

with open("/openai/api_key.json") as f:
    config = json.load(f)

# Set up environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = config["langsmith_key"]
os.environ["LANGCHAIN_PROJECT"] = "Agent-With-LangGraph"
os.environ["OPENAI_API_KEY"] = config["key"]


# Define tools
@tool
def search(query: str) -> str:
    """Search the internet for the given query."""
    return f"Search results for: {query}"


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))


tools = [search, calculator]

# Create the language model
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Create the agent using LangGraph
agent_executor = create_react_agent(llm, tools)

# Set up memory
memory = MemorySaver()
agent_executor = create_react_agent(llm, tools, checkpointer=memory)

# Set up LangSmith tracing
tracer = LangChainTracer(project_name="Agent-With-LangGraph")

# Use the agent with tracing
config = {"configurable": {"thread_id": "abc123"}}

with tracing_v2_enabled("Agent-With_LangGraph"):  # tracer.trace("Agent Execution"):
    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content="What is (2 + 2) * 3 + 4 and who invented the telephone?")]},
        config,
        # include_run_info=True,
    ):
        print(chunk)
        print("----")
