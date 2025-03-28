import os
import json
import datetime

from typing import TypedDict, Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langchain_core.utils.function_calling import convert_to_openai_function

with open("/openai/api_key.json") as f:
    config = json.load(f)

# Set up environment variables
os.environ["LANGCHAIN_PROJECT"] = "Agent-With-LangGraph"
os.environ["OPENAI_API_KEY"] = config["key"]


# Define tools
def search(query: str) -> str:
    """Search the internet for the given query."""
    return f"Search results for: {query}"


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))


tools = [
    Tool.from_function(search, name="search", description="Search the internet"),
    Tool.from_function(calculator, name="calculator", description="Perform calculations"),
]

# Create the language model
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Create the agent
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful AI assistant."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_openai_functions_agent(llm, tools, prompt)


# Define the state
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], "The messages in the conversation"]
    next_step: Annotated[str, "The next step to take"]
    intermediate_steps: Annotated[str, "The intermediate steps to take"]


# Define the nodes
def human_input(state: AgentState) -> AgentState:
    human_input = input("Human: ")
    state["messages"].append(HumanMessage(content=human_input))
    return state


def agent_step(state: AgentState) -> AgentState:
    if "intermediate_steps" not in state:
        state["intermediate_steps"] = []

    result = agent.invoke(
        {
            "input": state["messages"][-1].content,
            "chat_history": state["messages"][:1],
            "intermediate_steps": state["intermediate_steps"],
        }
    )

    state["messages"].append(result.message_log[-1])

    if "intermediate_steps" in result:
        state["intermediate_steps"] = result["intermediate_steps"]

    # Determine next step based on agent's output
    if "calculation" in result.return_values["output"].lower():
        state["next_step"] = "calculate"
    elif "search" in result.return_values["output"].lower():
        state["next_step"] = "search"
    else:
        state["next_step"] = "end"

    return state


def calculate(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content
    result = calculator(last_message)
    state["messages"].append(AIMessage(content=f"Calculation result: {result}"))
    state["next_step"] = "agent"
    return state


def search_step(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content
    result = search(last_message)
    state["messages"].append(AIMessage(content=f"Search result: {result}"))
    state["next_step"] = "agent"
    return state


# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("human", human_input)
workflow.add_node("agent", agent_step)
workflow.add_node("calculate", calculate)
workflow.add_node("search", search_step)

# Add edges
workflow.add_edge("human", "agent")
workflow.add_conditional_edges(
    "agent",
    lambda x: x["next_step"],
    {
        "calculate": "calculate",
        "search": "search",
        "end": END,
    },
)
workflow.add_edge("calculate", "agent")
workflow.add_edge("search", "agent")

# Set entry point
workflow.set_entry_point("human")

# Compile the graph
app = workflow.compile()
app.get_graph().draw_png("src/agent_testbed/agent_langgraph_poc.png")


initial_state = AgentState(
    messages=[],
    next_step="",
    intermediate_steps="",
)


result = app.invoke(initial_state)

print("\n\nAgent Response:")
print(result)
