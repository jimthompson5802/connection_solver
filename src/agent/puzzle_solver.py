import asyncio
import aiosqlite
from dataclasses import dataclass, field
import json
import logging
import pprint as pp
import random
from typing import List, TypedDict, Optional, Tuple
import itertools


import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from tools import compute_group_id, chat_with_llm

logger = logging.getLogger(__name__)


MAX_ERRORS = 4
RETRY_LIMIT = 8

db_lock = asyncio.Lock()


# used by the embedvec tool to store the candidate groups
@dataclass
class ConnectionGroup:
    group_metric: float = field(
        default=0.0, metadata={"help": "Average cosine similarity of all combinations of words in the group"}
    )
    root_word: str = field(default="", metadata={"help": "Root word of the group"})
    candidate_pairs: list = field(default_factory=list, metadata={"help": "List of candidate word with definition"})
    group_id: Optional[str] = field(default=None, metadata={"help": "Checksum identifer for the group"})

    def add_entry(self, word, connection):
        if len(self.candidate_pairs) < 4:
            self.candidate_pairs.append((word, connection))
            if len(self.candidate_pairs) == 4:
                self.group_id = compute_group_id(self.get_candidate_words())
        else:
            raise ValueError("Group is full, cannot add more entries")

    def get_candidate_words(self):
        sorted_pairs = sorted(self.candidate_pairs, key=lambda x: x[0])
        return [x[0] for x in sorted_pairs]

    def get_candidate_connections(self):
        sorted_pairs = sorted(self.candidate_pairs, key=lambda x: x[0])

        # strip the part of speech tag at the beginning of the connection, which looks like "noun:" or "verb:" etc.
        # find the first colon and take the substring after it
        stripped_connections = [x[1].split(":", 1)[1].strip() if ":" in x[1] else x[1] for x in sorted_pairs]

        return stripped_connections

    def __repr__(self):
        return_string = f"group metric: {self.group_metric}, "
        return_string += f"root word: {self.root_word}, group id: {self.group_id}\n"
        return_string += f"candidate group: {self.get_candidate_words()}\n"
        for connection in self.get_candidate_connections():
            return_string += f"\t{connection}\n"

        return return_string

    # method to determine if the group is equal to another group
    def __eq__(self, other):
        return set(self.get_candidate_words()) == set(other.get_candidate_words())


@dataclass
class RecommendedGroup:
    words: List[str]
    connection_description: str

    def __repr__(self):
        return f"Recommended Group: {self.words}\nConnection Description: {self.connection_description}"


# TODO: remove the color boolean indicators, these have not been used solution logic,
#       if needed can re-introduce
# define the state of the puzzle
class PuzzleState(TypedDict):
    puzzle_status: str = ""
    tool_status: str = ""
    current_tool: str = ""
    vocabulary_db_fp: Optional[str] = None
    tool_to_use: str = ""
    words_remaining: List[str] = []
    invalid_connections: List[Tuple[str, List[str]]] = []
    recommended_words: List[str] = []
    recommended_connection: str = ""
    recommended_correct: bool = False
    recommendation_answer_status: Optional[str] = None
    recommendation_correct_groups: Optional[List[List[str]]] = []
    found_yellow: bool = False
    found_greeen: bool = False
    found_blue: bool = False
    found_purple: bool = False
    mistake_count: int = 0
    llm_retry_count: int = 0
    found_count: int = 0
    recommendation_count: int = 0
    llm_temperature: float = 1.0
    puzzle_checker_response: Optional[str] = None


async def setup_puzzle(state: PuzzleState) -> PuzzleState:
    logger.info("Entering setup_puzzle:")
    logger.debug(f"\nEntering setup_puzzle State: {pp.pformat(state)}")

    state["current_tool"] = "setup_puzzle"
    print(f"\nENTERED {state['current_tool'].upper()}")

    # initialize the state
    state["puzzle_status"] = "initialized"
    state["tool_status"] = "initialized"
    state["invalid_connections"] = []
    state["mistake_count"] = 0
    state["found_count"] = 0
    state["recommendation_count"] = 0
    state["llm_retry_count"] = 0
    state["recommended_words"] = []

    # read in pre-built vocabulary for testing
    # state["vocabulary_df"] = pd.read_pickle("src/agent_testbed/word_list1.pkl")

    # generate vocabulary for the words
    print("\nGenerating vocabulary and embeddings for the words...this may take several seconds ")
    vocabulary = await generate_vocabulary(state["words_remaining"])

    # Convert dictionary to DataFrame
    rows = []
    for word, definitions in vocabulary.items():
        for definition in definitions:
            rows.append({"word": word, "definition": definition})
    df = pd.DataFrame(rows)

    # Generate embeddings
    print("\nGenerating embeddings for the definitions")
    embeddings = generate_embeddings(df["definition"].tolist())
    # convert embeddings to json strings for storage
    df["embedding"] = [json.dumps(v) for v in embeddings]

    # store the vocabulary in external database
    print("\nStoring vocabulary and embeddings in external database")

    async with aiosqlite.connect(state["vocabulary_db_fp"]) as conn:
        async with db_lock:
            cursor = await conn.cursor()
            # create the table
            await cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT,
                    definition TEXT,
                    embedding TEXT
                )
                """
            )
            await conn.executemany(
                "INSERT INTO vocabulary (word, definition, embedding) VALUES (?, ?, ?)",
                df.values.tolist(),
            )
            await conn.commit()

    logger.info("Exiting setup_puzzle:")
    logger.debug(f"\nExiting setup_puzzle State: {pp.pformat(state)}")

    return state


VOCABULARY_SYSTEM_MESSAGE = SystemMessage(
    """
You are an expert in language and knowledgeable on how words are used.

Your task is to generate as many diverse definitions as possible for the given word.  Follow these steps:

1. come up with a list of all possible parts of speech that the given word can be,e.g., noun, verb, adjective, etc.
2. for each part of speech, generate one or more examples of the given word for that parts of speech.  preappend the part of speech to the examples, e.g., "noun: example1", "verb: example2", etc.
3. combine all examples into a single list.

Return your response as a JSON object with the key "result" and the examples as a list of strings.

example:
{
    "result": [
    "noun: example1", 
    "noun: example2", 
    "adjective: example3",
    "verb: example4"
    ]
}

"""
)


async def generate_vocabulary(words, model="gpt-4o", temperature=0.7, max_tokens=4096):

    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    vocabulary = {}

    async def process_word(the_word):
        prompt = f"\n\ngiven word: {the_word}"
        prompt = HumanMessage(prompt)
        prompt = [VOCABULARY_SYSTEM_MESSAGE, prompt]
        result = await llm.ainvoke(prompt)
        vocabulary[the_word] = json.loads(result.content)["result"]

    await asyncio.gather(*[process_word(word) for word in words])

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
    * key "explanation" with a few word summary for the reason for the response.
    """
)


async def choose_embedvec_item(candidates, model="gpt-4o", temperature=0.7, max_tokens=4096):
    """
    Selects a response from a list of candidate messages generated by embedvec tool using a specified language model.

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
    result = await llm.ainvoke(prompt)

    return json.loads(result.content)


def get_candidate_words(df: pd.DataFrame) -> list:
    """
    Generate a list of candidate word groups based on cosine similarity of their embeddings.

    Args:
        df (pd.DataFrame): DataFrame containing words and their corresponding embeddings. Dataframe should have two columns: 'word', 'definition' and 'embedding', in that order.

    Returns:
        list: A list of unique candidate word groups sorted by their group metric in descending order.
    """

    candidate_list = []

    # create cosine similarity matrix for all pairs of the vectors
    cosine_similarities = cosine_similarity(df["embedding"].tolist())
    print(cosine_similarities.shape)

    # for each row in the cosine similarity matrix, sort by the cosine similarity
    sorted_cosine_similarites = np.argsort(cosine_similarities, axis=1)
    print(sorted_cosine_similarites.shape)

    # group of words that are most similar to each other
    for r in range(df.shape[0]):

        # get the top 3 closest words that are not the same as the current word and are not already connected
        connected_words = set()
        top3 = []
        for i in range(sorted_cosine_similarites.shape[1] - 2, 0, -1):
            c = sorted_cosine_similarites[r, i]

            # make sure the word is not already connected and not the current word
            if df.iloc[c, 0] not in connected_words and df.iloc[c, 0] != df.iloc[r, 0]:
                connected_words.add(df.iloc[c, 0])
                top3.append(c)
            if len(connected_words) == 3:
                break

        # create candidate group for the current word and the top 3 closest words
        if df.iloc[r, 0] not in connected_words and len(connected_words) == 3:
            candidate_group = ConnectionGroup()
            candidate_group.group_metric = cosine_similarities[r, top3].mean()
            candidate_group.root_word = df.iloc[r, 0]
            candidate_group.add_entry(df.iloc[r, 0], df.iloc[r, 1])

            for c in top3:
                candidate_group.add_entry(df.iloc[c, 0], df.iloc[c, 1])

            combinations = list(itertools.combinations([r] + top3, 2))
            candidate_group.group_metric = np.array([cosine_similarities[r, c] for r, c in combinations]).mean()

            candidate_list.append(candidate_group)

    # sort the candidate list by the group metric in descending order
    candidate_list.sort(key=lambda x: x.group_metric, reverse=True)

    # remove duplicate groups
    found_groups = set()
    unique_candidate_list = []
    for candidate in candidate_list:
        if candidate.group_id not in found_groups:
            unique_candidate_list.append(candidate)
            found_groups.add(candidate.group_id)

    return unique_candidate_list


# Used ChatGPT to get an initial system message with this prompt:
# "What is a good system prompt to solve the NYT Connection Puzzle that returns a JSON output?"
# Revised the system message to be based on development experience.
LLM_RECOMMENDER_SYSTEM_MESSAGE = SystemMessage(
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
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    # Create a prompt by concatenating the system and human messages
    conversation = [LLM_RECOMMENDER_SYSTEM_MESSAGE, prompt]

    # Invoke the LLM
    response = llm.invoke(conversation)

    logger.info("Exiting ask_llm_for_solution")
    logger.debug(f"exiting ask_llm_for_solution response {response.content}")

    return response


ANCHOR_WORDS_SYSTEM_PROMPT = (
    "you are an expert in the nuance of the english language.\n\n"
    "You will be given three words. you must determine if the three words can be related to a single topic.\n\n"
    "To make that determination, do the following:\n"
    "* Determine common contexts for each word. \n"
    "* Determine if there is a context that is shared by all three words.\n"
    "* respond 'single' if a single topic can be found that applies to all three words, otherwise 'multiple'.\n"
    "* Provide an explanation for the response.\n\n"
    "return response in json with the key 'response' with the value 'single' or 'multiple' and the key 'explanation' with the reason for the response."
)

CREATE_GROUP_SYSTEM_PROMPT = """
you will be given a list called the "anchor_words".

You will be given list of "candidate_words", select the one word that is most higly connected to the "anchor_words".

Steps:
1. First identify the common connection that is present in all the "anchor_words".  If each word has multiple meanings, consider the meaning that is most common among the "anchor_words".

2. Now test each word from the "candidate_words" and decide which one has the highest degree of connection to the "anchor_words".    

3. Return the word that is most connected to the "anchor_words" and the reason for its selection in json structure.  The word should have the key "word" and the explanation should have the key "explanation".
"""


async def one_away_analyzer(
    state: PuzzleState, one_away_group: List[str], words_remaining: List[str]
) -> List[Tuple[str, List[str]]]:
    print("\nENTERED ONE-AWAY ANALYZER")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    single_topic_groups = []
    possible_anchor_words_list = list(itertools.combinations(one_away_group, 3))

    async def process_anchor_words(anchor_list: List[str]) -> List[str]:
        anchor_words = "\n\n" + ", ".join(anchor_list)
        prompt = [SystemMessage(ANCHOR_WORDS_SYSTEM_PROMPT), HumanMessage(anchor_words)]
        response = await chat_with_llm(prompt)
        return anchor_list, response

    single_topic_groups = await asyncio.gather(
        *[process_anchor_words(anchor_list) for anchor_list in possible_anchor_words_list]
    )

    single_topic_groups = [
        RecommendedGroup(
            words=x[0],
            connection_description=x[1]["explanation"],
        )
        for x in single_topic_groups
        if x[1]["response"] == "single"
    ]

    print(f"\n>>>Number of single topic groups: {len(single_topic_groups)}")
    if len(single_topic_groups) > 1:
        # if more than one single topic group is found, select one at random
        print(f"More than one single-topic group recommendations, selecting one at random.")
        selected_word_group = random.choice(single_topic_groups)
    elif len(single_topic_groups) == 1:
        # if only one single topic group is found, select that one
        print(f"Only one single-topic group recommendation found.")
        selected_word_group = single_topic_groups[0]
    else:
        # if no single topic groups are found, select None
        print(f"No single-topic group recommendations found.")
        selected_word_group = None

    if selected_word_group:
        print(f"\n>>>Selected single-topic group:\n{selected_word_group}")
        # remove original one-away invalid group from the remaining word list
        words_to_test = [x for x in words_remaining if x not in one_away_group]
        user_prompt = "\n\nanchor_words: " + ",".join(selected_word_group.words)
        user_prompt += "\n\n" + "candidate_words: " + ", ".join(words_to_test)
        logger.info(f"single-topic user prompt:\n {user_prompt}")

        prompt = [SystemMessage(CREATE_GROUP_SYSTEM_PROMPT), HumanMessage(user_prompt)]

        response = await chat_with_llm(prompt)
        logger.info(response)
        new_group = list(selected_word_group.words) + [response["word"]]
        one_away_group_recommendation = RecommendedGroup(
            words=new_group, connection_description=response["explanation"]
        )
        print(f"\n>>>One-away group recommendations:")
        logger.info(one_away_group_recommendation)
    else:
        # if no single topic groups are found, single None
        one_away_group_recommendation = None

    return one_away_group_recommendation


def get_manual_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_manual_recommendation")
    logger.debug(f"Entering get_manual_recommendation State: {pp.pformat(state)}")

    state["current_tool"] = "manual_recommender"
    print(f"\nENTERED {state['current_tool'].upper()}")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    # display current recommendation and words remaining
    print(f"\nCurrent recommendation: {sorted(state['recommended_words'])}")
    print(f"Words remaining: {state['words_remaining']}")

    # get user input for manual recommendation
    response = "n"
    while response != "y":
        manual_recommendation = [
            x.strip() for x in input("Enter manual recommendation as comma separated words: ").split(",")
        ]
        print(f"Manual recommendation: {manual_recommendation}")

        if not set(manual_recommendation).issubset(set(state["words_remaining"])) or len(manual_recommendation) != 4:
            print("Manual recommendation is not a subset of words remaining or not 4 words")
            print("try again")
        else:
            response = input("Is the manual recommendation correct? (y/n): ")

    # get user defined connection
    response = "n"
    while response != "y":
        manual_connection = input("Enter manual connection: ")
        print(f"Manual connection: {manual_connection}")
        response = input("Is the manual connection correct? (y/n): ")

    state["recommended_words"] = manual_recommendation
    state["recommended_connection"] = manual_connection
    state["tool_status"] = "have_recommendation"

    logger.info("Exiting get_manual_recommendation")
    logger.debug(f"Exiting get_manual_recommendation State: {pp.pformat(state)}")

    return state


async def get_embedvec_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_embedvec_recommendation")
    logger.debug(f"Entering get_embedvec_recommendation State: {pp.pformat(state)}")

    state["current_tool"] = "embedvec_recommender"
    print(f"\nENTERED {state['current_tool'].upper()}")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    # get candidate list of words from database
    async with aiosqlite.connect(state["vocabulary_db_fp"]) as conn:
        async with db_lock:
            # get candidate list of words from database
            sql_query = "SELECT word, definition, embedding FROM vocabulary"
            async with conn.execute(sql_query) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                df = pd.DataFrame(rows, columns=columns)

    # convert embedding string representation to numpy array
    df["embedding"] = df["embedding"].apply(lambda x: np.array(json.loads(x)))

    # get candidate list of words based on embedding vectors
    candidate_list = get_candidate_words(df)
    print(f"candidate_lists size: {len(candidate_list)}")

    # validate the top 5 candidate list with LLM
    list_to_validate = "\n".join([str(x) for x in candidate_list[:5]])
    recommended_group = await choose_embedvec_item(list_to_validate)
    logger.info(f"Recommended group: {recommended_group}")

    state["recommended_words"] = recommended_group["candidate_group"]
    state["recommended_connection"] = recommended_group["explanation"]
    state["tool_status"] = "have_recommendation"

    # build prompt for llm

    logger.info("Exiting get_embedvec_recommendation")
    logger.debug(f"Exiting get_embedvec_recommendation State: {pp.pformat(state)}")

    return state


HUMAN_MESSAGE_BASE = """
    From the following candidate list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection.      
    """


def get_llm_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering get_recommendation")
    logger.debug(f"Entering get_recommendation State: {pp.pformat(state)}")

    state["current_tool"] = "llm_recommender"
    print(f"\nENTERED {state['current_tool'].upper()}")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    # build prompt for llm
    prompt = HUMAN_MESSAGE_BASE

    attempt_count = 0
    while True:
        attempt_count += 1
        if attempt_count > RETRY_LIMIT:
            break
        print(f"attempt_count: {attempt_count}")
        prompt = HUMAN_MESSAGE_BASE
        # scramble the remaining words for more robust group selection
        if np.random.uniform() < 0.5:
            random.shuffle(state["words_remaining"])
        else:
            state["words_remaining"].reverse()
        print(f"words_remaining: {state['words_remaining']}")
        prompt += f"candidate list: {', '.join(state['words_remaining'])}\n"

        prompt = HumanMessage(prompt)

        logger.info(f"\nPrompt for llm: {prompt.content}")

        # get recommendation from llm
        llm_response = ask_llm_for_solution(prompt, temperature=state["llm_temperature"])

        llm_response_json = json.loads(llm_response.content)
        if isinstance(llm_response_json, list):
            logger.debug(f"\nLLM response is list")
            recommended_words = llm_response_json[0]["words"]
            recommended_connection = llm_response_json[0]["connection"]
        else:
            logger.debug(f"\nLLM response is dict")
            recommended_words = llm_response_json["words"]
            recommended_connection = llm_response_json["connection"]

        if compute_group_id(recommended_words) not in set(x[0] for x in state["invalid_connections"]):
            break
        else:
            print(
                f"\nrepeat invalid group detected: group_id {compute_group_id(recommended_words)}, recommendation: {sorted(recommended_words)}"
            )

    state["recommended_words"] = sorted(recommended_words)
    state["recommended_connection"] = recommended_connection

    if attempt_count <= RETRY_LIMIT:
        state["tool_status"] = "have_recommendation"
    else:
        print(f"Failed to get a valid recommendation after {RETRY_LIMIT} attempts")
        print("Changing to manual_recommender, last attempt to solve the puzzle")
        print(f"last recommendation: {state['recommended_words']} with {state['recommended_connection']}")
        state["tool_status"] = "manual_recommendation"

    logger.info("Exiting get_recommendation")
    logger.debug(f"Exiting get_recommendation State: {pp.pformat(state)}")

    return state


async def apply_recommendation(state: PuzzleState) -> PuzzleState:
    logger.info("Entering apply_recommendation:")
    logger.debug(f"\nEntering apply_recommendation State: {pp.pformat(state)}")

    state["recommendation_count"] += 1

    # get user response from human input
    found_correct_group = state["recommendation_answer_status"]

    # process result of user response
    if found_correct_group in ["y", "g", "b", "p", "correct"]:
        print(f"Recommendation {sorted(state['recommended_words'])} is correct")
        match found_correct_group:
            case "y":
                state["found_yellow"] = True
            case "g":
                state["found_green"] = True
            case "b":
                state["found_blue"] = True
            case "p":
                state["found_purple"] = True
            case "correct":
                pass

        state["recommendation_correct_groups"].append(state["recommended_words"])

        # for embedvec_recommender, remove the words from the vocabulary database
        if state["current_tool"] == "embedvec_recommender":
            # remove accepted words from vocabulary.db
            async with aiosqlite.connect(state["vocabulary_db_fp"]) as conn:
                async with db_lock:
                    # remove accepted words from vocabulary.db
                    # for each word in recommended_words, remove the word from the vocabulary table
                    for word in state["recommended_words"]:
                        sql_query = f"DELETE FROM vocabulary WHERE word = '{word}'"
                        await conn.execute(sql_query)
                    await conn.commit()

        # remove the words from words_remaining
        state["words_remaining"] = [word for word in state["words_remaining"] if word not in state["recommended_words"]]
        state["recommended_correct"] = True
        state["found_count"] += 1
    elif found_correct_group in ["n", "o"]:
        invalid_group = state["recommended_words"]
        invalid_group_id = compute_group_id(invalid_group)
        state["invalid_connections"].append((invalid_group_id, invalid_group))
        state["recommended_correct"] = False
        state["mistake_count"] += 1

        if state["mistake_count"] < MAX_ERRORS:
            match found_correct_group:
                case "o":
                    print(f"Recommendation {sorted(state['recommended_words'])} is incorrect, one away from correct")

                    # perform one-away analysis
                    one_away_group_recommendation = await one_away_analyzer(
                        state, invalid_group, state["words_remaining"]
                    )

                    # check if one_away_group_recommendation is a prior mistake
                    if one_away_group_recommendation:
                        one_away_group_id = compute_group_id(one_away_group_recommendation.words)
                        if one_away_group_id in set(x[0] for x in state["invalid_connections"]):
                            print(f"one_away_group_recommendation is a prior mistake")
                            one_away_group_recommendation = None
                        else:
                            print(f"one_away_group_recommendation is a new recommendation")

                case "n":
                    print(f"Recommendation {sorted(state['recommended_words'])} is incorrect")
                    if state["current_tool"] == "embedvec_recommender":
                        print("Changing the recommender from 'embedvec_recommender' to 'llm_recommender'")
                        state["current_tool"] = "llm_recommender"
        else:
            state["recommended_words"] = []
            state["recommended_connection"] = ""
            state["recommended_correct"] = False

    if len(state["words_remaining"]) == 0 or state["mistake_count"] >= MAX_ERRORS:
        if state["mistake_count"] >= MAX_ERRORS:
            logger.info("FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
            print("FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!")
        else:
            logger.info("SOLVED THE CONNECTION PUZZLE!!!")
            print("SOLVED THE CONNECTION PUZZLE!!!")

        state["tool_status"] = "puzzle_completed"
    elif found_correct_group == "o":
        if one_away_group_recommendation:
            print(f"using one_away_group_recommendation")
            state["recommended_words"] = one_away_group_recommendation.words
            state["recommended_connection"] = one_away_group_recommendation.connection_description
            state["tool_status"] = "have_recommendation"
        else:
            print(f"no one_away_group_recommendation, let llm_recommender try again")
            state["recommended_words"] = []
            state["recommended_connection"] = ""
            state["tool_status"] = "next_recommendation"
    elif found_correct_group == "m":
        print("Changing to manual_recommender")
        state["tool_status"] = "manual_recommendation"

    else:
        logger.info("Going to next get_recommendation")
        state["tool_status"] = "next_recommendation"

    logger.info("Exiting apply_recommendation:")
    logger.debug(f"\nExiting apply_recommendation State: {pp.pformat(state)}")

    return state
