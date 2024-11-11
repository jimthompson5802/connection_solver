import json
import logging
import pprint as pp
from typing import List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from tools import extract_words_from_image, read_file_to_word_list


logger = logging.getLogger(__name__)
pp = pp.PrettyPrinter(indent=4)


# define the state of the puzzle
class PuzzleState(TypedDict):
    puzzle_status: str = ""
    puzzle_step: str = ""
    puzzle_recommender: str = ""
    workflow_instructions: str = ""
    tool_to_use: str = ""
    words_remaining: List[str] = []
    invalid_connections: List[List[str]] = []
    recommended_words: List[str] = []
    recommended_connection: str = ""
    recommended_correct: bool = False
    found_yellow: bool = False
    found_greeen: bool = False
    found_blue: bool = False
    found_purple: bool = False
    mistake_count: int = 0
    found_count: int = 0
    recommendation_count: int = 0
    llm_temperature: float = 1.0


def setup_puzzle(state: PuzzleState) -> PuzzleState:
    logger.info("Entering setup_puzzle:")
    logger.debug(f"\nEntering setup_puzzle State: {pp.pformat(state)}")

    # prompt user for input source
    input_source = input("Enter 'file' to read words from a file or 'image' to read words from an image: ")

    if input_source == "file":
        puzzle_word_fp = input("Please enter the word file location: ")
        words = read_file_to_word_list(puzzle_word_fp)
    elif input_source == "image":
        puzzle_word_fp = input("Please enter the image file location: ")
        words = extract_words_from_image(puzzle_word_fp)
    else:
        raise ValueError("Invalid input source. Please enter 'file' or 'image'.")

    print(f"Puzzle Words: {words}")
    state["words_remaining"] = words
    state["puzzle_status"] = "initialized"
    state["puzzle_step"] = "next_recommendation"
    state["puzzle_recommender"] = "fallback_recommender"
    state["invalid_connections"] = []
    state["mistake_count"] = 0
    state["found_count"] = 0
    state["recommendation_count"] = 0
    state["recommended_words"] = []

    # read in the workflow specification
    # TODO: support specifying the workflow specification file path in config
    workflow_spec_fp = "src/agent/rag_workflow_specification.md"
    with open(workflow_spec_fp, "r") as f:
        state["workflow_instructions"] = f.read()

    logger.debug(f"Workflow Specification: {state['workflow_instructions']}")

    logger.info("Exiting setup_puzzle:")
    logger.debug(f"\nExiting setup_puzzle State: {pp.pformat(state)}")

    return state


SYSTEM_MESSAGE = SystemMessage(
    """
You are an expert in language and knowledgeable on how words are used.

Your task is to generate as many diverse definitions as possible for the given word.  Follow these steps:

1. come up with a list of all possible parts of speech that the given word can be,e.g., noun, verb, adjective, etc.
2. for each part of speech, generate one or more examples of the given word for that parts of speech.  preappend the part of speech to the examples, e.g., "noun: example1", "verb: example2", etc.
3. combine all examples into a single list.

Return your response as a JSON object with the word as the key and the connotations as a list of strings.

example:

{
  "word": [
    "noun: example1", 
    "noun: example2", 
    "adjective: example3",]
}
"""
)


def generate_vocabulary(words, model="gpt-4o", temperature=0.7, max_tokens=4096):

    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    vocabulary = {}

    for the_word in words:
        prompt = f"\n\ngiven word: {the_word}"
        prompt = HumanMessage(prompt)
        prompt = [SYSTEM_MESSAGE, prompt]
        result = llm.invoke(prompt)
        vocabulary[the_word] = json.loads(result.content)[the_word]

    return vocabulary


def generate_embeddings(definitions, model="text-embedding-3-small"):

    # setup embedding model
    embed_model = OpenAIEmbeddings(model=model)

    embeddings = embed_model.embed_documents(definitions)

    return embeddings


VALIDATOR_SYSTEM_MESSAGE = SystemMessage(
    """
    anaylyze the following set of "candidate group" of 4 words.
    
    For each  "candidate group"  determine if the 4 words are connected by a single theme or concept.

    eliminate "candidate group" where the 4 words are not connected by a single theme or concept.

    return the "candidate group" that is unlike the other word groups

    if there is no  "candidate group" connected by a single theme or concept, return the group with the highest group metric.

    return response in json with the
    * key "candidate_group" for the "candidate group" that is connected by a single theme or concept that is the most unique about the "candidate group".  This is a list of 4 words.
    * key "explanation" with the reason for the response.
    """
)


def choose_rag_item(candidates, model="gpt-4o", temperature=0.7, max_tokens=4096):
    """
    Selects a response from a list of candidate messages generated by RAG tool using a specified language model.

    Args:
        candidates (str): The input text containing candidate messages to be evaluated.
        model (str, optional): The model name to be used for the language model. Defaults to "gpt-4o".
        temperature (float, optional): The sampling temperature to use. Higher values mean the model will take more risks. Defaults to 0.7.
        max_tokens (int, optional): The maximum number of tokens to generate in the response. Defaults to 4096.

    Returns:
        dict: The selected response in JSON format.
    """

    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    prompt = HumanMessage(candidates)
    prompt = [VALIDATOR_SYSTEM_MESSAGE, prompt]
    result = llm.invoke(prompt)

    return json.loads(result.content)


PLANNER_SYSTEM_MESSAGE = """
    You are an expert in managing the sequence of a workflow. Your task is to
    determine the next tool to use given the current state of the workflow.

    the eligible tools to use are: ["setup_puzzle", "get_recommendation", "apply_recommendation", "get_rag_recommendation", "END"]

    The important information for the workflow state is to consider are: "puzzle_status", "puzzle_step", and "puzzle_recommender".

    Using the provided instructions, you will need to determine the next tool to use.

    output response in json format with key word "tool" and the value as the output string.
    
"""

# TODO: clean up the instructions message
# INSTRUCTIONS_MESSAGE = """
# **Instructions**

# use "setup_puzzle" tool to initialize the puzzle if the "puzzle_status" is not initialized.

# if "puzzle_step" is "puzzle_completed" then use "END" tool.

# Based use the table to select the appropriate tool.

# |puzzle_recommender| puzzle_step | tool |
# | --- | --- | --- |
# |rag_recommender| next_recommendation | get_rag_recommendation |
# |rag_recommender| have_recommendation | apply_recommendation |
# |fallback_recommender| next_recommendation | get_recommendation |
# |fallback_recommender| have_recommendation | apply_recommendation |

# If no tool is selected, use "ABORT" tool.

# """

#  puzzle step state:
#  have_rag_recommendation
#  have_fallback_recommendation
#  recommendation_applied
#  puzzle_completed

# If "puzzle_step" is "have_recommendation" use "apply_recommendation" tool.

# If "puzzle_step" is "next_recommendation", use "get_recommendation" tool.

# if "puzzle_step" is "puzzle_completed" use "END" tool.

# used for testing int playground
# puzzle_state: {
#     "puzzle_status": "initialized",
#     "puzzle_step": "",
# }


def ask_llm_for_next_step(instructions, puzzle_state, model="gpt-3.5-turbo", temperature=0, max_tokens=4096):
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
    response = llm.invoke(conversation)

    logger.debug(f"response: {pp.pformat(response)}")

    logger.info("Exiting ask_llm_for_next_step")
    logger.info(f"exiting ask_llm_for_next_step response {response.content}")

    return response
