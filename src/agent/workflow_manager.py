from dataclasses import dataclass, field
import json
import logging
import pprint as pp
from typing import List, TypedDict, Optional, Tuple

import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from puzzle_solver import (
    setup_puzzle,
    get_embedvec_recommendation,
    get_llm_recommendation,
    get_manual_recommendation,
    apply_recommendation,
)


from puzzle_solver import PuzzleState


logger = logging.getLogger(__name__)


KEY_PUZZLE_STATE_FIELDS = ["puzzle_status", "tool_status", "current_tool"]

PLANNER_SYSTEM_MESSAGE = """
    You are an expert in managing the sequence of a workflow. Your task is to
    determine the next tool to use given the current state of the workflow.

    the eligible tools to use are: ["setup_puzzle", "get_llm_recommendation", "apply_recommendation", "get_embedvec_recommendation", "get_manual_recommendation", "END"]

    The important information for the workflow state is to consider are: "puzzle_status", "tool_status", and "current_tool".

    Using the provided instructions, you will need to determine the next tool to use.

    output response in json format with key word "tool" and the value as the output string.
    
"""


async def ask_llm_for_next_step(instructions, puzzle_state, model="gpt-3.5-turbo", temperature=0, max_tokens=4096):
    """
    Asks the language model (LLM) for the next step based on the provided prompt.

    Args:
        prompt (AIMessage): The prompt containing the content to be sent to the LLM.
        model (str, optional): The model to be used by the LLM. Defaults to "gpt-3.5-turbo".
        temperature (float, optional): The temperature setting for the LLM, controlling the randomness of the output. Defaults to 0.
        max_tokens (int, optional): The maximum number of tokens for the LLM response. Defaults to 4096.

    Returns:
        AIMessage: The response from the LLM containing the next step.
    """
    logger.info("Entering ask_llm_for_next_step")
    logger.debug(f"Entering ask_llm_for_next_step Instructions: {instructions.content}")
    logger.debug(f"Entering ask_llm_for_next_step Prompt: {puzzle_state.content}")

    # Initialize the OpenAI LLM for next steps
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Create a prompt by concatenating the system and human messages
    conversation = [PLANNER_SYSTEM_MESSAGE, instructions, puzzle_state]

    logger.debug(f"conversation: {pp.pformat(conversation)}")

    # Invoke the LLM
    response = await llm.ainvoke(conversation)

    logger.debug(f"response: {pp.pformat(response)}")

    logger.info("Exiting ask_llm_for_next_step")
    logger.info(f"exiting ask_llm_for_next_step response {response.content}")

    return response


async def run_planner(state: PuzzleState, config: RunnableConfig) -> PuzzleState:
    logger.info("Entering run_planner:")
    logger.debug(f"\nEntering run_planner State: {pp.pformat(state)}")

    # workflow instructions
    instructions = HumanMessage(config["configurable"]["workflow_instructions"])
    logger.debug(f"\nWorkflow instructions:\n{instructions.content}")

    # convert state to json string
    relevant_state = {k: state[k] for k in KEY_PUZZLE_STATE_FIELDS}
    puzzle_state = "\npuzzle state:\n" + json.dumps(relevant_state)

    # wrap the state in a human message
    puzzle_state = HumanMessage(puzzle_state)
    logger.info(f"\nState for lmm: {puzzle_state.content}")

    # get next action from llm
    next_action = await ask_llm_for_next_step(instructions, puzzle_state, model="gpt-3.5-turbo", temperature=0)

    logger.info(f"\nNext action from llm: {next_action.content}")

    state["tool_to_use"] = json.loads(next_action.content)["tool"]

    logger.info("Exiting run_planner:")
    logger.debug(f"\nExiting run_planner State: {pp.pformat(state)}")
    return state


def determine_next_action(state: PuzzleState) -> str:
    logger.info("Entering determine_next_action:")
    logger.debug(f"\nEntering determine_next_action State: {pp.pformat(state)}")

    tool_to_use = state["tool_to_use"]

    if tool_to_use == "ABORT":
        raise ValueError("LLM returned abort")
    elif tool_to_use == "END":
        return END
    else:
        return tool_to_use


async def run_workflow(
    workflow_graph,
    initial_state: PuzzleState,
    runtime_config: dict,
    *,
    puzzle_setup_function: callable = None,
    puzzle_response_function: callable = None,
) -> None:

    # run workflow until first human-in-the-loop input required for setup
    async for chunk in workflow_graph.astream(initial_state, runtime_config, stream_mode="values"):
        pass

    # continue workflow until the next human-in-the-loop input required for puzzle answer
    while chunk["tool_status"] != "puzzle_completed":
        current_state = workflow_graph.get_state(runtime_config)
        logger.debug(f"\nCurrent state: {current_state}")
        logger.info(f"\nNext action: {current_state.next}")
        if current_state.next[0] == "setup_puzzle":
            words = puzzle_setup_function()

            print(f"Setting up Puzzle Words: {words}")

            workflow_graph.update_state(
                runtime_config,
                {"words_remaining": words},
            )
        elif current_state.next[0] == "apply_recommendation":
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

    print("\n\nFINAL PUZZLE STATE:")
    pp.pprint(chunk)

    return chunk["recommendation_correct_groups"]


def create_workflow_graph() -> StateGraph:
    workflow = StateGraph(PuzzleState)

    workflow.add_node("run_planner", run_planner)
    workflow.add_node("setup_puzzle", setup_puzzle)
    workflow.add_node("get_embedvec_recommendation", get_embedvec_recommendation)
    workflow.add_node("get_llm_recommendation", get_llm_recommendation)
    workflow.add_node("get_manual_recommendation", get_manual_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)

    workflow.add_conditional_edges(
        "run_planner",
        determine_next_action,
        {
            "setup_puzzle": "setup_puzzle",
            "get_embedvec_recommendation": "get_embedvec_recommendation",
            "get_llm_recommendation": "get_llm_recommendation",
            "get_manual_recommendation": "get_manual_recommendation",
            "apply_recommendation": "apply_recommendation",
            END: END,
        },
    )

    workflow.add_edge("setup_puzzle", "run_planner")
    workflow.add_edge("get_llm_recommendation", "run_planner")
    workflow.add_edge("get_embedvec_recommendation", "run_planner")
    workflow.add_edge("get_manual_recommendation", "run_planner")
    workflow.add_edge("apply_recommendation", "run_planner")

    workflow.set_entry_point("run_planner")

    memory_checkpoint = MemorySaver()

    workflow_graph = workflow.compile(
        checkpointer=memory_checkpoint,
        interrupt_before=["setup_puzzle", "apply_recommendation"],
    )

    return workflow_graph


def create_webui_workflow_graph() -> StateGraph:
    workflow = StateGraph(PuzzleState)

    workflow.add_node("run_planner", run_planner)
    workflow.add_node("get_embedvec_recommendation", get_embedvec_recommendation)
    workflow.add_node("get_llm_recommendation", get_llm_recommendation)
    workflow.add_node("get_manual_recommendation", get_manual_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)

    workflow.add_conditional_edges(
        "run_planner",
        determine_next_action,
        {
            "get_embedvec_recommendation": "get_embedvec_recommendation",
            "get_llm_recommendation": "get_llm_recommendation",
            "get_manual_recommendation": "get_manual_recommendation",
            "apply_recommendation": "apply_recommendation",
            END: END,
        },
    )

    workflow.add_edge("get_llm_recommendation", "run_planner")
    workflow.add_edge("get_embedvec_recommendation", "run_planner")
    workflow.add_edge("get_manual_recommendation", "run_planner")
    workflow.add_edge("apply_recommendation", "run_planner")

    workflow.set_entry_point("run_planner")

    memory_checkpoint = MemorySaver()

    workflow_graph = workflow.compile(
        checkpointer=memory_checkpoint,
        interrupt_before=["apply_recommendation"],
    )

    return workflow_graph
