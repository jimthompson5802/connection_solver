import base64
import hashlib
import json
import logging
import pprint as pp
from typing import List, TypedDict
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig


# temporary llm interface registry
# manually update this as other LLM interfaces are added
llm_interface_registry = {}

# with open("/openai/api_key.json") as f:
#     config = json.load(f)

# api_key = config["key"]

logger = logging.getLogger(__name__)

pp = pp.PrettyPrinter(indent=4)


class LLMInterfaceBase(ABC):
    """base class for LLM Interface"""

    @abstractmethod
    def __init__(self, model_name: str, **kwargs):
        """setups up LLM Model"""
        raise NotImplementedError()

    @abstractmethod
    async def generate_vocabulary(self, words):
        """creates definitions for all the words"""
        raise NotImplementedError()

    @abstractmethod
    def generate_embeddings(self, definitions: List[str]) -> List[List[float]]:
        """generates embeddings for the definitions"""
        raise NotImplementedError()

    @abstractmethod
    async def choose_embedvec_item(self, candidates):
        """chooses an item from a list of candidates"""
        raise NotImplementedError()

    @abstractmethod
    async def ask_llm_for_solution(self, prompt):
        """asks the LLM for a solution to a prompt"""
        raise NotImplementedError()

    @abstractmethod
    async def extract_words_from_image(encoded_image: str) -> List[str]:
        """extracts words from an image"""
        raise NotImplementedError()

    @abstractmethod
    async def analyze_anchor_words_group(self, anchor_words_group):
        """analyzes a group of anchor words"""
        raise NotImplementedError()

    @abstractmethod
    async def generate_one_away_recommendation(self, anchor_words_prompt: str):
        """generates a recommendation for a single word that is one away from the correct group"""
        raise NotImplementedError()

    @abstractmethod
    async def ask_llm_for_next_step(self, instructions: str, puzzle_state: str):
        """asks the LLM for the next step in the workflow"""
        raise NotImplementedError()


def compute_group_id(word_group: list) -> str:
    return hashlib.md5("".join(sorted(word_group)).encode()).hexdigest()


def read_file_to_word_list(file_location: str) -> List[str]:
    """
    Reads a file and returns a list of words separated by commas on the first line of the file.
    Remainder of the file contains the correct word groupings and is ignored.

    Prompts the user to enter the file location, reads the file, and splits its contents by commas.
    Strips any leading or trailing whitespace from each word.

    Returns:
    list: A list of words from the file. If the file is not found or an error occurs, returns an empty list.
    """

    logger.info(f"Reading words from file {file_location}")
    try:
        with open(file_location, "r") as file:
            contents = file.readline()
            words = contents.split(",")
            words = [word.strip() for word in words]
            return words
    except FileNotFoundError:
        print(f"File not found: {file_location}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


async def extract_words_from_image_file(image_fp: str, config: RunnableConfig) -> List[str]:
    """
    Encodes an image to base64 and sends it to the OpenAI LLM to extract words from the image.

    Parameters:
    image_path (str): The path to the image file to be processed.

    Returns:
    dict: The response from the LLM in JSON format.
    """

    logger.info("Entering extract_words_from_image")
    logger.debug(f"Entering extract_words_from_image image_path: {image_fp}")

    # Encode the image
    with open(image_fp, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Get the response from the model
    # response = await chat_with_llm([message])
    response = await config["configurable"]["llm_interface"].extract_words_from_image(base64_image)

    words = [w.lower() for w in response["words"]]

    logger.info("Exiting extract_words_from_image")
    logger.debug(f"Exiting extract_words_from_image response {words}")

    return words


async def manual_puzzle_setup_prompt(config: RunnableConfig) -> List[str]:

    # pompt user for puzzle source
    puzzle_source_type = input("Enter 'file' to read words from a file or 'image' to read words from an image: ")
    puzzle_source_fp = input("Please enter the file/image location: ")

    # get puzzle words from indicated source
    if puzzle_source_type == "file":
        words = read_file_to_word_list(puzzle_source_fp)
    elif puzzle_source_type == "image":
        words = await extract_words_from_image_file(puzzle_source_fp, config=config)
    else:
        raise ValueError("Invalid input source. Please enter 'file' or 'image'.")

    return words


def interact_with_user(gen_words, gen_reason, recommender) -> str:
    recommendation_message = f"\n{recommender.upper()}: RECOMMENDED WORDS {gen_words} with connection {gen_reason}"
    logger.info(recommendation_message)
    print(recommendation_message)

    user_instruction = "Is the recommendation accepted? (y/g/b/p/m/s/o/n): "
    logger.info(user_instruction)
    user_response = input(user_instruction)

    logger.info(f"User response: {user_response}")

    return user_response


def check_one_solution(solution, *, gen_words: List[str], gen_reason: str, recommender: str) -> str:
    recommendation_message = f"\n{recommender.upper()}: RECOMMENDED WORDS {gen_words} with connection {gen_reason}"
    logger.info(recommendation_message)
    print(recommendation_message)

    for sol_dict in solution["groups"]:
        sol_words = sol_dict["words"]
        sol_reason = sol_dict["reason"]
        if set(gen_words) == set(sol_words):
            print(f"{gen_reason} ~ {sol_reason}: {gen_words} == {sol_words}")
            return "correct"
        elif len(set(gen_words).intersection(set(sol_words))) == 3:
            return "o"
    else:
        return "n"
