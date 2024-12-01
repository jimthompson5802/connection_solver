from dataclasses import dataclass, field
import json
import logging
import pprint as pp
import random
from typing import List, TypedDict, Optional, Tuple
import hashlib
import itertools
import sqlite3
import os

import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from tools import extract_words_from_image, read_file_to_word_list


logger = logging.getLogger(__name__)
pp = pp.PrettyPrinter(indent=4)


def compute_group_id(word_group: list) -> str:
    return hashlib.md5("".join(sorted(word_group)).encode()).hexdigest()


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


# define the state of the puzzle
class PuzzleState(TypedDict):
    puzzle_status: str = ""
    tool_status: str = ""
    current_tool: str = ""
    workflow_instructions: Optional[str] = None
    vocabulary_db_fp: Optional[str] = None
    tool_to_use: str = ""
    words_remaining: List[str] = []
    invalid_connections: List[Tuple[str, List[str]]] = []
    recommended_words: List[str] = []
    recommended_connection: str = ""
    recommended_correct: bool = False
    found_yellow: bool = False
    found_greeen: bool = False
    found_blue: bool = False
    found_purple: bool = False
    mistake_count: int = 0
    llm_retry_count: int = 0
    found_count: int = 0
    recommendation_count: int = 0
    llm_temperature: float = 1.0
    puzzle_source_type: Optional[str] = None
    puzzle_source_fp: Optional[str] = None


def setup_puzzle(state: PuzzleState) -> PuzzleState:
    logger.info("Entering setup_puzzle:")
    logger.debug(f"\nEntering setup_puzzle State: {pp.pformat(state)}")

    state["current_tool"] = "setup_puzzle"
    print(f"\nENTERED {state['current_tool'].upper()}")

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

    # initialize the state
    state["words_remaining"] = words
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
    print("\nGenerating vocabulary for the words...this may take about a minute")
    vocabulary = generate_vocabulary(state["words_remaining"])

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
    print("\nStoring vocabulary in external database")
    # remove prior database file, ignore if it does not exist
    try:
        os.remove(state["vocabulary_db_fp"])
    except FileNotFoundError:
        pass

    conn = sqlite3.connect(state["vocabulary_db_fp"])
    cursor = conn.cursor()
    # create the table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            definition TEXT,
            embedding TEXT
        )
        """
    )
    df.to_sql("vocabulary", conn, if_exists="replace", index=False)
    conn.close()

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


PLANNER_SYSTEM_MESSAGE = """
    You are an expert in managing the sequence of a workflow. Your task is to
    determine the next tool to use given the current state of the workflow.

    the eligible tools to use are: ["setup_puzzle", "get_llm_recommendation", "apply_recommendation", "get_embedvec_recommendation", "get_manual_recommendation", "END"]

    The important information for the workflow state is to consider are: "puzzle_status", "tool_status", and "current_tool".

    Using the provided instructions, you will need to determine the next tool to use.

    output response in json format with key word "tool" and the value as the output string.
    
"""


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


def choose_embedvec_item(candidates, model="gpt-4o", temperature=0.7, max_tokens=4096):
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
    result = llm.invoke(prompt)

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


def chat_with_llm(prompt, model="gpt-4o", temperature=0.7, max_tokens=4096):

    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    result = llm.invoke(prompt)

    return json.loads(result.content)


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


def one_away_analyzer(state: PuzzleState, one_away_group: List[str], words_remaining: List[str]) -> List[Tuple[str, List[str]]]:
    print("\nENTERED ONE-AWAY ANALYZER")
    print(f"found count: {state['found_count']}, mistake_count: {state['mistake_count']}")

    single_topic_groups = []
    possible_anchor_words_list = list(itertools.combinations(one_away_group, 3))

    for anchor_list in possible_anchor_words_list:
        # determine if the anchor words can be related to a single topic
        anchor_words = "\n\n" + ", ".join(anchor_list)
        prompt = [SystemMessage(ANCHOR_WORDS_SYSTEM_PROMPT), HumanMessage(anchor_words)]
        response = chat_with_llm(prompt)

        logger.info(f"\n>>>Anchor Words: {anchor_list}")
        logger.info(response)

        if response["response"] == "single":

            single_topic_groups.append(
                RecommendedGroup(words=anchor_list, connection_description=response["explanation"])
            )

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
        user_prompt = "\n\nanchor_words: " + ", ".join(selected_word_group.words)
        user_prompt += "\n\n" + "candidate_words: " + ", ".join(words_to_test)
        logger.info(f"single-topic user prompt:\n {user_prompt}")

        prompt = [SystemMessage(CREATE_GROUP_SYSTEM_PROMPT), HumanMessage(user_prompt)]

        response = chat_with_llm(prompt)
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
