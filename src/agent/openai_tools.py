from abc import ABC, abstractmethod
import asyncio
import logging
from typing import List, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


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
    async def choose_embedvec_item(self, candidates):
        """chooses an item from a list of candidates"""
        raise NotImplementedError()

    @abstractmethod
    async def ask_llm_for_solution(self, prompt):
        """asks the LLM for a solution to a prompt"""
        raise NotImplementedError()

    @abstractmethod
    async def extract_words_from_image(image_fp: str) -> List[str]:
        """extracts words from an image"""
        raise NotImplementedError()


VOCABULARY_SYSTEM_MESSAGE = """
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


class VocabularyResults(TypedDict):
    result: List[str]


LLM_RECOMMENDER_SYSTEM_MESSAGE = """
    You are a helpful assistant in solving the New York Times Connection Puzzle.

    The New York Times Connection Puzzle involves identifying groups of four related items from a grid of 16 words. Each word can belong to only one group, and there are generally 4 groups to identify. Your task is to examine the provided words, identify the possible groups based on thematic connections, and then suggest the groups one by one.

    # Steps

    1. **Review the candidate words**: Look at the words provided in the candidate list carefully.
    2. **Identify Themes**: Notice any apparent themes or categories (e.g., types of animals, names of colors, etc.).
    3. **Group Words**: Attempt to form groups of four words that share a common theme.
    4. **Avoid invalid groups**: Do not include word groups that are known to be invalid.
    5. **Verify Groups**: Ensure that each word belongs to only one group. If a word seems to fit into multiple categories, decide on the best fit based on the remaining options.
    6. **Order the groups**: Order your answers in terms of your confidence level, high confidence first.
    7. **Solution output**: Select only the highest confidence group.  Generate only a json response as shown in the **Output Format** section.

    # Output Format

    Provide the solution with the highest confidence group and their themes in a structured format. The JSON output should contain keys "words" that is the list of the connected words and "connection" describing the connection among the words.

    ```json
    {"words": ["Word1", "Word2", "Word3", "Word4"], "connection": "..."},
    ```

    No other text.

    # Examples

    **Example:**

    - **Input:** ["prime", "dud", "shot", "card", "flop", "turn", "charge", "rainforest", "time", "miss", "plastic", "kindle", "chance", "river", "bust", "credit"]
    
    - **Output:**
    {"words": [ "bust", "dud", "flop", "mist"], "connection": "clunker"}

    No other text.

    # Notes

    - Ensure all thematic connections make logical sense.
    - Consider edge cases where a word could potentially fit into more than one category.
    - Focus on clear and accurate thematic grouping to aid in solving the puzzle efficiently.
    """


class LLMRecommendation(TypedDict):
    words: List[str]
    connection: str


EMBEDVEC_SYSTEM_MESSAGE = """
    anaylyze the following set of "candidate group" of 4 words.
    
    For each  "candidate group"  determine if the 4 words are connected by a single theme or concept.

    eliminate "candidate group" where the 4 words are not connected by a single theme or concept.

    return the "candidate group" that is unlike the other word groups

    if there is no  "candidate group" connected by a single theme or concept, return the group with the highest group metric.

    return response in json with the
    * key "candidate_group" for the "candidate group" that is connected by a single theme or concept that is the most unique about the "candidate group".  This is a list of 4 words.
    * key "explanation" with a few word summary for the reason for the response.
    """


class EmbedVecGroup(TypedDict):
    candidate_group: List[str]
    explanation: str


class ExtractedWordsFromImage(TypedDict):
    words: List[str]


class LLMOpenAIInterface(LLMInterfaceBase):
    """class for OpenAI LLM Interface"""

    def __init__(self, model_name: str, temperature=0.7, max_tokens=4096, **kwargs):
        """setups up LLM Model"""
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    async def generate_vocabulary(self, words):

        vocabulary = {}
        system_message = SystemMessage(VOCABULARY_SYSTEM_MESSAGE)

        async def process_word(the_word):
            prompt = f"\n\ngiven word: {the_word}"
            prompt = HumanMessage(prompt)
            prompt = [system_message, prompt]
            structured_llm = self.llm.with_structured_output(VocabularyResults)
            result = await structured_llm.ainvoke(prompt)
            vocabulary[the_word] = result["result"]

        await asyncio.gather(*[process_word(word) for word in words])

        return vocabulary

    async def choose_embedvec_item(self, candidates):
        """
        Selects a response from a list of candidate messages generated by embedvec tool using a specified language model.

        Args:
            candidates (str): The input text containing candidate messages to be evaluated.

        Returns:
            dict: The selected response in JSON format.
        """

        prompt = HumanMessage(candidates)
        prompt = [SystemMessage(EMBEDVEC_SYSTEM_MESSAGE), prompt]

        structured_llm = self.llm.with_structured_output(EmbedVecGroup)
        result = await structured_llm.ainvoke(prompt)

        return result

    async def ask_llm_for_solution(self, prompt):
        """
        Asks the OpenAI LLM for a solution based on the provided prompt.

        Parameters:
        prompt (str): The input prompt to be sent to the LLM.

        Returns:
        dict: The response from the LLM in JSON format.
        """
        logger.info("Entering ask_llm_for_solution")
        logger.debug(f"Entering ask_llm_for_solution Prompt: {prompt.content}")

        # Create a prompt by concatenating the system and human messages
        conversation = [SystemMessage(LLM_RECOMMENDER_SYSTEM_MESSAGE), prompt]

        # Invoke the LLM
        structured_llm = self.llm.with_structured_output(LLMRecommendation)
        response = await structured_llm.ainvoke(conversation)

        logger.info("Exiting ask_llm_for_solution")
        logger.debug(f"exiting ask_llm_for_solution response {response}")

        return response

    async def extract_words_from_image(self, encoded_image: str):
        """extracts words from an image"""
        # Create a message with text and image
        message = HumanMessage(
            content=[
                {"type": "text", "text": "extract words from the image and return as a json list"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
            ]
        )

        structured_llm = self.llm.with_structured_output(ExtractedWordsFromImage)

        response = await structured_llm.ainvoke([message])

        return response
