import json

from langchain.tools import BaseTool, StructuredTool, tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor

with open("/openai/api_key.json") as f:
    config = json.load(f)

api_key = config["key"]


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


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)


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

result = agent_executor.invoke({"input": "What is (2 times 4) minus 7?"})
print(result["output"])
