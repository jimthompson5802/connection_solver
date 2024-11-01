import json
import os

from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

import re
from typing import Union
from langchain.schema import AgentAction, AgentFinish


with open("/openai/api_key.json") as f:
    config = json.load(f)

os.environ["OPENAI_API_KEY"] = config["key"]


# Define the compute_expression tool
def compute_expression(expression: str) -> str:
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error computing expression: {e}"


# Define the get_weather tool
def get_weather(city: str) -> str:
    weather_data = {"Hilo, Hawaii": "Sunny, 85°F", "Reston, VA": "Cloudy, 75°F", "San Francisco, CA": "Foggy, 65°F"}
    if city in weather_data:
        return f"The weather in {city} is {weather_data[city]}."
    else:
        return f"Weather data for {city} is not available."


# Define the tools
tools = [
    Tool(
        name="Arithmetic Evaluator",
        func=compute_expression,
        description="Computes the value of simple arithmetic expressions.",
    ),
    Tool(name="Weather Checker", func=get_weather, description="Provides simulated weather data for specified cities."),
]

# Define the prompt template
template = """Answer the following question as best you can. You have access to the following tools:

{tool_descriptions}

Use the following format:

Question: {input}
Thought: think about what tools to use and the steps to take
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (you can repeat Thought/Action/Action Input/Observation multiple times)
Thought: conclude with the final answer
Final Answer: the answer to the original question

Begin!

Question: {input}
{agent_scratchpad}"""

prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "tool_descriptions", "tool_names"],
    template=template,
)

print(template)


# Implement the custom output parser
class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Parse the LLM output for action and input
        action_match = re.search(r"Action: (.*)", llm_output)
        action_input_match = re.search(r"Action Input: (.*)", llm_output)
        final_answer_match = re.search(r"Final Answer: (.*)", llm_output)

        if final_answer_match:
            return AgentFinish(
                return_values={"output": final_answer_match.group(1).strip()},
                log=llm_output,
            )
        elif action_match and action_input_match:
            return AgentAction(
                tool=action_match.group(1).strip(),
                tool_input=action_input_match.group(1).strip(),
                log=llm_output,
            )
        else:
            raise ValueError(f"Could not parse LLM output: {llm_output}")


# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Set up the LLM chain
llm_chain = LLMChain(llm=llm, prompt=prompt)

# Create the agent
agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=CustomOutputParser(),
    stop=["\nObservation:"],
    allowed_tools=[tool.name for tool in tools],
)

# Create the agent executor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
)


# Function to get the agent's response
def agent_response(user_input: str) -> str:
    tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    tool_names = ", ".join([tool.name for tool in tools])
    inputs = {
        "input": user_input,
        "tool_names": tool_names,
        "tool_descriptions": tool_descriptions,
        "agent_scratchpad": "",
    }
    result = agent_executor.invoke(inputs)
    return result


# Example usage
if __name__ == "__main__":
    user_input = "What is 6 + 9 "  # and what's the weather like in Reston, VA?"
    print(agent_response(user_input))
