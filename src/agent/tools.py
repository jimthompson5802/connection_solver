import base64
import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

with open("/openai/api_key.json") as f:
    config = json.load(f)

api_key = config["key"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def read_file_to_word_list():
    """
    Reads a file and returns a list of words separated by commas on the first line of the file.
    Remainder of the file contains the correct word groupings and is ignored.

    Prompts the user to enter the file location, reads the file, and splits its contents by commas.
    Strips any leading or trailing whitespace from each word.

    Returns:
    list: A list of words from the file. If the file is not found or an error occurs, returns an empty list.
    """
    file_location = input("Please enter the file location: ")
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


def extract_words_from_image():
    """
    Encodes an image to base64 and sends it to the OpenAI LLM to extract words from the image.

    Parameters:
    image_path (str): The path to the image file to be processed.

    Returns:
    dict: The response from the LLM in JSON format.
    """
    image_fp = input("Please enter the image file location: ")

    logger.info("Entering extract_words_from_image")
    logger.debug(f"Entering extract_words_from_image image_path: {image_fp}")

    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4o",
        temperature=1.0,
        max_tokens=4096,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Encode the image
    with open(image_fp, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Create a message with text and image
    message = HumanMessage(
        content=[
            {"type": "text", "text": "extract words from the image and return as a json list"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
        ]
    )

    # Get the response from the model
    response = llm.invoke([message])

    words = [w.lower() for w in json.loads(response.content)["words"]]

    logger.info("Exiting extract_words_from_image")
    logger.debug(f"Exiting extract_words_from_image response {words}")

    return words


def interact_with_user(words, connection) -> str:
    recommendation_message = f"\nRECOMMENDED WORDS {words} with connection {connection}"
    logger.info(recommendation_message)
    print(recommendation_message)

    user_instruction = "Is the recommendation accepted? (y/g/b/p/n): "
    logger.info(user_instruction)
    user_response = input(user_instruction)

    logger.info(f"User response: {user_response}")

    return user_response


# Used ChatGPT to get an initial system message with this prompt:
# "What is a good system prompt to solve the NYT Connection Puzzle that returns a JSON output?"
# Revised the system message to be based on development experience.
SYSTEM_MESSAGE = SystemMessage(
    """
    You are a helpful assistant in solving the New York Times Connection Puzzle.

    The New York Times Connection Puzzle involves identifying groups of four related items from a grid of 16 words. Each word can belong to only one group, and there are generally 4 groups to identify. Your task is to examine the provided words, identify the possible groups based on thematic connections, and then suggest the groups one by one.

    # Steps

    1. **Review the candidate words**: Look at thewords provided in the candidate list carefully.
    2. **Identify Themes**: Notice any apparent themes or categories (e.g., types of animals, names of colors, etc.).
    3. **Group Words**: Attempt to form groups of four words that share a common theme.
    4. **Avoid invalid groups**: Do not include word groups that are known to be invalid.
    5. **Verify Groups**: Ensure that each word belongs to only one group. If a word seems to fit into multiple categories, decide on the best fit based on the remaining options.
    6. **Order the groups**: Order your answers in terms of your confidence level, high confidence first.
    7. **Solution output**: Generate only a json response as shown in the **Output Format** section.

    # Output Format

    Provide the solution with the identified groups and their themes in a structured format. Each group should be output as a JSON list object.  Each list item is dictionary with keys "words" list of the connected words and "connection" describing the connection among the words.

    ```json
    [
    {"words": ["Word1", "Word2", "Word3", "Word4"], "connection": "..."},
    {"words": ["Word5", "Word6", "Word7", "Word8"], "connection": "..."},
    {"words": ["Word9", "Word10", "Word11", "Word12"], "connection": "..."},
    {"words": ["Word13", "Word14", "Word15", "Word16"], "connection": "..."}
    ]
    ```

    # Examples

    **Example:**

    - **Input:** ["prime", "dud", "shot", "card", "flop", "turn", "charge", "rainforest", "time", "miss", "plastic", "kindle", "chance", "river", "bust", "credit"]
    
    - **Output:**
    [
    {"words": [ "bust", "dud", "flop", "mist"], "connection": "clunker"},
    {"words": ["chance", "shot", "time", "turn"], "connection": "opportunity"},
    {"words": ["card", "charge", "credit", "plastic"], "connection": "Non-Cash Way to Pay"},
    {"words": ["kindle", "prime", "rainforest", "river"], "connection": "Amazon ___"}
    ]

    No other text.

    # Notes

    - Ensure all thematic connections make logical sense.
    - Consider edge cases where a word could potentially fit into more than one category.
    - Focus on clear and accurate thematic grouping to aid in solving the puzzle efficiently.
    """
)


def ask_llm_for_solution(prompt, model="gpt-4o", temperature=1.0, max_tokens=4096):
    """
    Asks the OpenAI LLM for a solution based on the provided prompt.

    Parameters:
    prompt (str): The input prompt to be sent to the LLM.
    temperature (float, optional): The sampling temperature to use. Defaults to 1.0.
    max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 4096.

    Returns:
    dict: The response from the LLM in JSON format.
    """
    logger.info("Entering ask_llm_for_solution")
    logger.debug(f"Entering ask_llm_for_solution Prompt: {prompt.content}")
    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Create a prompt by concatenating the system and human messages
    conversation = [SYSTEM_MESSAGE, prompt]

    # Invoke the LLM
    response = llm.invoke(conversation)

    logger.info("Exiting ask_llm_for_solution")
    logger.debug(f"exiting ask_llm_for_solution response {response.content}")

    return response


PLANNER_SYSTEM_MESSAGE = """
    select one and only of the following actions based on the puzzle state:

    Actions:
    * puzzle_phase is "uninitalized" output  "get_input_source"
    * puzzle_phase is "setup_complete" output "get_recommendation"
    * puzzle_phase is "solve_puzzle" and (remaining_words is empty list  or mistake_count is 4 or greater) output "END" otherwise "get_recommendation"
    * if none of the above output "abort"

    output response in json format with key word "action" and the value as the output string.
"""


def ask_llm_for_next_step(prompt, model="gpt-4o", temperature=1.0, max_tokens=4096):
    """
    Asks the OpenAI LLM for a solution based on the provided prompt.

    Parameters:
    prompt (str): The input prompt to be sent to the LLM.
    temperature (float, optional): The sampling temperature to use. Defaults to 1.0.
    max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 4096.

    Returns:
    dict: The response from the LLM in JSON format.
    """
    logger.info("Entering ask_llm_for_solution")
    logger.debug(f"Entering ask_llm_for_solution Prompt: {prompt.content}")
    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Create a prompt by concatenating the system and human messages
    conversation = [PLANNER_SYSTEM_MESSAGE, prompt]

    # Invoke the LLM
    response = llm.invoke(conversation)

    logger.info("Exiting ask_llm_for_solution")
    logger.debug(f"exiting ask_llm_for_solution response {response.content}")

    return response
