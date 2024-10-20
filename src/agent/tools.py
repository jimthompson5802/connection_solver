import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

with open("/openai/api_key.json") as f:
    config = json.load(f)

api_key = config["key"]


def read_file_to_word_list():
    # TODO: undo hard coding for testing
    file_location = "data/word_list3.txt"  # input("Please enter the file location: ")
    try:
        with open(file_location, "r") as file:
            contents = file.read()
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

    1. **Review the Grid**: Look at the 16 words provided in the grid carefully.
    2. **Identify Themes**: Notice any apparent themes or categories (e.g., types of animals, names of colors, etc.).
    3. **Group Words**: Attempt to form groups of four words that share a common theme.
    4. **Avoid invalid groups**: Avoid groups that are known to be invalid.
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
    From the following list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection.      
    """
)


def ask_llm_for_solution(prompt):
    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4o",
        temperature=1.0,
        max_tokens=4096,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Create a prompt by concatenating the system and human messages
    conversation = [SYSTEM_MESSAGE, prompt]

    # Invoke the LLM
    response = llm.invoke(conversation)

    return response
