import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

with open("/openai/api_key.json") as f:
    config = json.load(f)

api_key = config["key"]


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

HUMAN_MESSAGE_BASE = HumanMessage(
    """
    From the following candidate list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection.      
    """
)

HUMAN_ERROR_ANALYSIS_MESSAGE = HumanMessage(
    """
    I am working on solving a word grouping puzzle where I need to select 4 words that fit into a specific category from a list of remaining words. The current recommended set of 4 words is incorrect, with one or more words being wrong. Please help me regenerate a new set of 4 words that better fits the category. Below is the relevant information:
    """
    # Remaining words: [list the remaining words]
    # Current recommended set (incorrect): [list the 4 words]
    """
    Please suggest an alternative set of 4 words based on the remaining options and correct the errors in the current set. 
    """
)


def ask_llm_for_solution(prompt, temperature=1.0, max_tokens=4096):
    """
    Asks the OpenAI LLM for a solution based on the provided prompt.

    Parameters:
    prompt (str): The input prompt to be sent to the LLM.
    temperature (float, optional): The sampling temperature to use. Defaults to 1.0.
    max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 4096.

    Returns:
    dict: The response from the LLM in JSON format.
    """
    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4o",
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Create a prompt by concatenating the system and human messages
    conversation = [SYSTEM_MESSAGE, prompt]

    # Invoke the LLM
    response = llm.invoke(conversation)

    return response
