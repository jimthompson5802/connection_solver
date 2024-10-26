import os
import json

from langchain.tools import BaseTool, StructuredTool, tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tracers.context import tracing_v2_enabled


with open("/openai/api_key.json") as f:
    config = json.load(f)


os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["OPENAI_API_KEY"] = config["key"]
os.environ["LANGCHAIN_API_KEY"] = config["langsmith_key"]
os.environ["LANGCHAIN_PROJECT"] = "Agent-With-Math-Tools"


@tool
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


@tool
def square(a: float) -> float:
    """Square a number"""
    return a * a


toolkit = [add, multiply, square]

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_openai_tools_agent(llm, toolkit, prompt)

agent_executor = AgentExecutor(agent=agent, tools=toolkit, verbose=True)

# Use the tracing context manager when invoking the agent
with tracing_v2_enabled():
    result = agent_executor.invoke({"input": "What is ((2 + 2) * 3) - 4?"})
    print(result["output"])

# with tracing_v2_enabled():
#     result = agent_executor.invoke(
#         {"input": "What is 2 + 2?"},
#         config={
#             "metadata": {
#                 "user_id": "12345",
#                 "session_id": "abcde",
#                 "query_type": "math_operation"
#             }
#         }
#     )
#     print(result['output'])
