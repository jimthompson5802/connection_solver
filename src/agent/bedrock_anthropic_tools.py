import asyncio
import logging
import pprint as pp
import textwrap
from typing import List, TypedDict, Coroutine, Any
from functools import wraps

from botocore.exceptions import ClientError

from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_aws.chat_models.bedrock import convert_messages_to_prompt_anthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.rate_limiters import InMemoryRateLimiter

from tools import LLMInterfaceBase, llm_interface_registry

logger = logging.getLogger(__name__)

import time
import random
import logging
import functools
import botocore
from typing import Any, Callable

logger = logging.getLogger(__name__)


def retry_when_error(max_retries=4, base_delay=1, jitter=0.1):
    """
    A decorator to retry an asynchronous function when an exception occurs.

    Parameters:
    max_retries (int): The maximum number of retries before giving up. Default is 4.
    base_delay (int or float): The base delay between retries in seconds. Default is 1 second.
    jitter (float): The maximum random jitter to add to the delay to avoid thundering herd problem. Default is 0.1 seconds.

    Returns:
    function: A wrapped function that will be retried upon failure.

    Example:
    @retry_when_error(max_retries=3, base_delay=2, jitter=0.5)
    async def my_function():
        # function implementation
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except ClientError as e:
                    # Retry on ThrottlingException
                    if e.response["Error"]["Code"] == "ThrottlingException":
                        if retries == max_retries - 1:
                            print(f"Failed after {retries + 1} retries")
                            raise
                        retries += 1
                        delay = (base_delay * 2**retries) + (random.random() * jitter)
                        print(f"Retrying {retries}/{max_retries} with delay {delay:.3f} after error: {e}")
                        await asyncio.sleep(delay)

                    # Raise other exceptions
                    else:
                        raise

            return await func(*args, **kwargs)

        return wrapper

    return decorator


@retry_when_error()
async def invoke_bedrock_model_async(llm_model, prompt):
    """
    Asynchronously invokes a Bedrock model with a given prompt and returns the result.

    Parameters:
    llm_model (ChatBedrock): The Bedrock model to be invoked.
    prompt (str): The prompt to be sent to the model.
    output_type (Any): The type of the output to be returned.

    Returns:
    Any: The result of the model invocation.
    """

    return await llm_model.ainvoke(prompt)


RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=(5 / 60.0),  # requests per minute in seconds
    check_every_n_seconds=0.1,  # check every 0.1 seconds
    max_bucket_size=5,  # allow up to 5 requests in a burst
)


@llm_interface_registry.register("bedrock_sonnet")
class LLMBedrockSonnetInterface(LLMInterfaceBase):

    def __init__(
        self,
        word_analyzer_llm_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        image_extraction_llm_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        workflow_llm_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        embedding_model_name: str = "amazon.titan-embed-text-v2:0",
        temperature: float = 0.7,
        max_tokens=4096,
        **kwargs,
    ):
        """setups up LLM Model"""

        print(f"{self.__class__.__name__} __init__")

        self.word_analyzer_llm_name = word_analyzer_llm_name
        self.workflow_llm_name = workflow_llm_name
        self.image_extraction_llm_name = image_extraction_llm_name
        self.embendding_model_name = embedding_model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        model_kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        self.word_analyzer_llm = ChatBedrock(
            model_id=self.word_analyzer_llm_name,
            model_kwargs=model_kwargs,
            rate_limiter=RATE_LIMITER,
        )

        self.image_extraction_llm = ChatBedrock(
            model=self.image_extraction_llm_name,
            model_kwargs=model_kwargs,
            rate_limiter=RATE_LIMITER,
        )

        self.workflow_llm = ChatBedrock(
            model_id=self.workflow_llm_name,
            model_kwargs={
                "temperature": 0,
                "max_tokens": self.max_tokens,
            },
            rate_limiter=RATE_LIMITER,
        )

        self.embedding_model = BedrockEmbeddings(model_id=self.embendding_model_name)

    async def generate_vocabulary(self, words: List[str]) -> dict:
        """
        Asynchronously generates a vocabulary dictionary for a given list of words.

        This method uses a language model to analyze each word and produce structured
        vocabulary results. The results are stored in a dictionary where the keys are
        the input words and the values are the analysis results.

        Args:
            words (list of str): A list of words to be analyzed.

        Returns:
            dict: A dictionary where the keys are the input words and the values are
                  the structured vocabulary results.
        """

        VOCABULARY_SYSTEM_MESSAGE = textwrap.dedent(
            """
            You are an expert in language and knowledgeable on how words are used.

            Your task is to generate as many diverse definitions as possible for the given word.  Follow these steps:

            1. come up with a list of all possible parts of speech that the given word can be,e.g., noun, verb, adjective, etc.
            2. for each part of speech, generate one or more examples of the given word for that parts of speech.  preappend the part of speech to the examples, e.g., "noun: example1", "verb: example2", etc.
            3. combine all examples into a single list.

            Return your response as a JSON object with the key "result" and the examples as a list of strings.

            example:
            {{
                "result": [
                "noun: example1", 
                "noun: example2", 
                "adjective: example3",
                "verb: example4"
                ]
            }}
            """
        )

        # Define the structured output for the vocabulary results
        class VocabularyResults(TypedDict):
            result: List[str]

        vocabulary = {}

        given_word_template = ChatPromptTemplate(
            [
                ("system", VOCABULARY_SYSTEM_MESSAGE),
                ("user", "\ngiven word: {the_word}"),
            ]
        )

        async def process_word(the_word: str) -> dict:
            """
            Asynchronously processes a given word using a language model to analyze its vocabulary.

            Args:
                the_word (str): The word to be processed.

            Returns:
                None: The result is stored in the vocabulary dictionary with the word as the key.
            """
            print(f"Processing word: {the_word}")
            prompt = given_word_template.invoke({"the_word": the_word})
            prompt = convert_messages_to_prompt_anthropic(prompt.messages)
            structured_llm = self.word_analyzer_llm.with_structured_output(VocabularyResults)
            result = await invoke_bedrock_model_async(structured_llm, prompt)
            print(f">>> generated vocabulary for {the_word}")
            vocabulary[the_word] = result["result"]

        await asyncio.gather(*[process_word(word) for word in words])

        return vocabulary

    def generate_embeddings(self, definitions: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of definitions.

        Args:
            definitions (List[str]): A list of strings where each string is a definition to be embedded.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """

        embeddings = self.embedding_model.embed_documents(definitions)

        return embeddings

    async def choose_embedvec_item(self, candidates: str) -> dict:
        """
        Asynchronously chooses an embedded vector item from a list of candidates.

        Args:
            candidates (str): A string representation of the candidate embedding vector word groups.

        Returns:
            dict: A dictionary containing the result of the chosen embedded vector item.

        """

        EMBEDVEC_SYSTEM_MESSAGE = textwrap.dedent(
            """
            anaylyze the following set of "candidate group" of 4 words.
            
            For each  "candidate group"  determine if the 4 words are connected by a single theme or concept.

            eliminate "candidate group" where the 4 words are not connected by a single theme or concept.

            return the "candidate group" that is unlike the other word groups

            if there is no  "candidate group" connected by a single theme or concept, return the group with the highest group metric.

            return response in json with the
            * key "candidategroup" for the "candidate group" that is connected by a single theme or concept that is the most unique about the "candidate group".  This is a list of 4 words.
            * key "explanation" with a few word summary for the reason for the response.
            """
        )

        # Define the structured output for the embedded vector item
        class EmbedVecGroup(TypedDict):
            candidategroup: List[str]
            explanation: str

        prompt = HumanMessage(candidates)
        prompt = [SystemMessage(EMBEDVEC_SYSTEM_MESSAGE), prompt]
        prompt = convert_messages_to_prompt_anthropic(prompt)

        structured_llm = self.word_analyzer_llm.with_structured_output(EmbedVecGroup)
        # await asyncio.sleep(8.0)
        # result = await structured_llm.ainvoke(prompt)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def ask_llm_for_solution(self, words_remaining: str) -> dict:
        """
        Asks the OpenAI LLM for a solution based on the provided prompt.

        Parameters:
        prompt (str): The input prompt containg the candidate words to be analyzed.

        Returns:
        dict: containing keys: "words" for the recommended word group and "connection" for the connection reason.
        """

        LLM_RECOMMENDER_SYSTEM_MESSAGE = textwrap.dedent(
            """
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
            {{"words": ["Word1", "Word2", "Word3", "Word4"], "connection": "..."}},
            ```

            No other text.

            # Examples

            **Example:**

            - **Input:** ["prime", "dud", "shot", "card", "flop", "turn", "charge", "rainforest", "time", "miss", "plastic", "kindle", "chance", "river", "bust", "credit"]
            
            - **Output:**
            {{"words": [ "bust", "dud", "flop", "mist"], "connection": "clunker"}}

            No other text.

            # Notes

            - Ensure all thematic connections make logical sense.
            - Consider edge cases where a word could potentially fit into more than one category.
            - Focus on clear and accurate thematic grouping to aid in solving the puzzle efficiently.
            """
        )

        HUMAN_MESSAGE_BASE = textwrap.dedent(
            """
            From the following candidate list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection. 

            candidate list: {candidate_list}     
            """
        )

        # Define the structured output for the LLM recommendation
        class LLMRecommendation(TypedDict):
            words: List[str]
            connection: str

        logger.info("Entering ask_llm_for_solution")
        logger.debug(f"Entering ask_llm_for_solution words remaining: {words_remaining}")

        prompt = ChatPromptTemplate(
            [
                ("system", LLM_RECOMMENDER_SYSTEM_MESSAGE),
                ("user", HUMAN_MESSAGE_BASE),
            ]
        ).invoke({"candidate_list": words_remaining})

        # Invoke the LLM
        structured_llm = self.word_analyzer_llm.with_structured_output(LLMRecommendation)
        response = await invoke_bedrock_model_async(structured_llm, prompt.to_messages())

        logger.info("Exiting ask_llm_for_solution")
        logger.debug(f"exiting ask_llm_for_solution response {response}")

        return response

    async def extract_words_from_image(self, encoded_image: str):
        """
        Extract words from a base64 encoded image and return them as list.

        Args:
            encoded_image (str): The base64 encoded string of the image.

        Returns:
            dict: A list of words extracted from the image under the key "words".
        """

        # Define the structured output for the image extraction
        class ExtractedWordsFromImage(TypedDict):
            words: List[str]

        # Create a message with text and image
        message = HumanMessage(
            content=[
                {"type": "text", "text": "extract words from the image and return as a json list"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
            ]
        )

        structured_llm = self.image_extraction_llm.with_structured_output(ExtractedWordsFromImage)
        response = await invoke_bedrock_model_async(structured_llm, [message])

        return response

    async def analyze_anchor_words_group(self, anchor_words_group: str) -> dict:
        """
        Analyzes a group of anchor words to determine if they are related to a single topic.

        Args:
            anchor_words_group (list): A list of three anchor words to be analyzed.

        Returns:
            dict: The analysis result in JSON format.
        """

        ANCHOR_WORDS_SYSTEM_PROMPT = textwrap.dedent(
            """
            You are an expert in the nuance of the english language.

            You will be given three words. you must determine if the three words can be related to a single topic.

            To make that determination, do the following:
            * Determine common contexts for each word. 
            * Determine if there is a context that is shared by all three words.
            * respond 'single' if a single topic can be found that applies to all three words, otherwise 'multiple'.
            * Provide an explanation for the response.

            Return response in json with the key 'response' with the value 'single' or 'multiple' and the key 'explanation' with the reason for the response.
            """
        )

        ANCHOR_LIST_PROMPT = "\n{anchor_words_group}"

        class AnchorWordsAnalysis(TypedDict):
            response: str
            explanation: str

        prompt = ChatPromptTemplate(
            [
                ("system", ANCHOR_WORDS_SYSTEM_PROMPT),
                ("user", ANCHOR_LIST_PROMPT),
            ]
        ).invoke({"anchor_words_group": anchor_words_group})
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        structured_llm = self.word_analyzer_llm.with_structured_output(AnchorWordsAnalysis)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def generate_one_away_recommendation(self, anchor_words: str, candidate_words_remaining: str) -> dict:
        """
        Generates a recommendation for a single word that is one letter away from the provided prompt.

        Args:
            anchor_words_prompt (str): The prompt containing the anchor words.

        Returns:
            dict: The recommendation in JSON format.
        """

        ONE_AWAY_RECOMMENDATION_SYSTEM_PROMPT = textwrap.dedent(
            """
        you will be given a list called the "anchor_words".

        You will be given list of "candidate_words", select the one word that is most higly connected to the "anchor_words".

        Steps:
        1. First identify the common connection that is present in all the "anchor_words".  If each word has multiple meanings, consider the meaning that is most common among the "anchor_words".

        2. Now test each word from the "candidate_words" and decide which one has the highest degree of connection to the "anchor_words".    

        3. Return the word that is most connected to the "anchor_words" and the reason for its selection in json structure.  The word should have the key "word" and the explanation should have the key "explanation".
        """
        )

        USER_PROMPT = "\nanchor_words: {anchor_words_prompt}\n\ncandidate_words: {candidate_words}"

        class OneAwayRecommendation(TypedDict):
            word: str
            explanation: str

        prompt = ChatPromptTemplate(
            [
                ("system", ONE_AWAY_RECOMMENDATION_SYSTEM_PROMPT),
                ("user", USER_PROMPT),
            ]
        ).invoke(
            {
                "anchor_words_prompt": anchor_words,
                "candidate_words": candidate_words_remaining,
            }
        )
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        structured_llm = self.word_analyzer_llm.with_structured_output(OneAwayRecommendation)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def ask_llm_for_next_step(self, instructions: str, puzzle_state: str) -> dict:
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

        PLANNER_SYSTEM_MESSAGE = textwrap.dedent(
            """
            You are an expert in managing the sequence of a workflow. Your task is to
            determine the next tool to use given the current state of the workflow.

            the eligible tools to use are: ["setup_puzzle", "get_llm_recommendation", "apply_recommendation", "get_embedvec_recommendation", "get_manual_recommendation", "END"]

            The important information for the workflow state is to consider are: "puzzle_status", "tool_status", and "current_tool".

            Using the provided instructions, you will need to determine the next tool to use.

            output response in json format with key word "tool" and the value as the output string.
            
            {instructions}
            """
        )

        PUZZLE_STATE_PROMPT = "\npuzzle state: {puzzle_state}"

        # Define the structured output for the next action to be taken by the workflow
        class NextAction(TypedDict):
            tool: str

        logger.info("Entering ask_llm_for_next_step")
        logger.debug(f"Entering ask_llm_for_next_step Instructions: {instructions}")
        logger.debug(f"Entering ask_llm_for_next_step Prompt: {puzzle_state}")

        # Create a prompt by concatenating the system and human messages
        prompt = ChatPromptTemplate(
            [
                ("system", PLANNER_SYSTEM_MESSAGE),
                ("user", PUZZLE_STATE_PROMPT),
            ]
        ).invoke({"instructions": instructions, "puzzle_state": puzzle_state})
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        # Invoke the LLM
        llm_structured = self.workflow_llm.with_structured_output(NextAction)
        response = await invoke_bedrock_model_async(llm_structured, prompt)

        logger.debug(f"response: {pp.pformat(response)}")

        logger.info("Exiting ask_llm_for_next_step")
        logger.info(f"exiting ask_llm_for_next_step response {response}")

        return response


@llm_interface_registry.register("bedrock_haiku")
class LLMBedrockHaikuInterface(LLMInterfaceBase):

    def __init__(
        self,
        word_analyzer_llm_name: str = "anthropic.claude-3-haiku-20240307-v1:0",
        image_extraction_llm_name: str = "anthropic.claude-3-haiku-20240307-v1:0",
        workflow_llm_name: str = "anthropic.claude-3-haiku-20240307-v1:0",
        embedding_model_name: str = "amazon.titan-embed-text-v2:0",
        temperature: float = 0.7,
        max_tokens=4096,
        **kwargs,
    ):
        """setups up LLM Model"""

        print(f"{self.__class__.__name__} __init__")

        self.word_analyzer_llm_name = word_analyzer_llm_name
        self.workflow_llm_name = workflow_llm_name
        self.image_extraction_llm_name = image_extraction_llm_name
        self.embendding_model_name = embedding_model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        model_kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        self.word_analyzer_llm = ChatBedrock(
            model_id=self.word_analyzer_llm_name,
            model_kwargs=model_kwargs,
        )

        self.image_extraction_llm = ChatBedrock(
            model=self.image_extraction_llm_name,
            model_kwargs=model_kwargs,
        )

        self.workflow_llm = ChatBedrock(
            model_id=self.workflow_llm_name,
            model_kwargs={
                "temperature": 0,
                "max_tokens": self.max_tokens,
            },
        )

        self.embedding_model = BedrockEmbeddings(model_id=self.embendding_model_name)

    async def generate_vocabulary(self, words: List[str]) -> dict:
        """
        Asynchronously generates a vocabulary dictionary for a given list of words.

        This method uses a language model to analyze each word and produce structured
        vocabulary results. The results are stored in a dictionary where the keys are
        the input words and the values are the analysis results.

        Args:
            words (list of str): A list of words to be analyzed.

        Returns:
            dict: A dictionary where the keys are the input words and the values are
                  the structured vocabulary results.
        """

        VOCABULARY_SYSTEM_MESSAGE = textwrap.dedent(
            """
            You are an expert in language and knowledgeable on how words are used.

            Your task is to generate as many diverse definitions as possible for the given word.  Follow these steps:

            1. come up with a list of all possible parts of speech that the given word can be,e.g., noun, verb, adjective, etc.
            2. for each part of speech, generate one or more examples of the given word for that parts of speech.  preappend the part of speech to the examples, e.g., "noun: example1", "verb: example2", etc.
            3. combine all examples into a single list.

            Return your response as a JSON object with the key "result" and the examples as a list of strings.

            example:
            {{
                "result": [
                "noun: example1", 
                "noun: example2", 
                "adjective: example3",
                "verb: example4"
                ]
            }}
            """
        )

        # Define the structured output for the vocabulary results
        class VocabularyResults(TypedDict):
            result: List[str]

        vocabulary = {}

        given_word_template = ChatPromptTemplate(
            [
                ("system", VOCABULARY_SYSTEM_MESSAGE),
                ("user", "\ngiven word: {the_word}"),
            ]
        )

        async def process_word(the_word: str) -> dict:
            """
            Asynchronously processes a given word using a language model to analyze its vocabulary.

            Args:
                the_word (str): The word to be processed.

            Returns:
                None: The result is stored in the vocabulary dictionary with the word as the key.
            """
            prompt = given_word_template.invoke({"the_word": the_word})
            prompt = convert_messages_to_prompt_anthropic(prompt.messages)
            structured_llm = self.word_analyzer_llm.with_structured_output(VocabularyResults)
            result = await invoke_bedrock_model_async(structured_llm, prompt)
            vocabulary[the_word] = result["result"]

        await asyncio.gather(*[process_word(word) for word in words])

        return vocabulary

    def generate_embeddings(self, definitions: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of definitions.

        Args:
            definitions (List[str]): A list of strings where each string is a definition to be embedded.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """

        embeddings = self.embedding_model.embed_documents(definitions)

        return embeddings

    async def choose_embedvec_item(self, candidates: str) -> dict:
        """
        Asynchronously chooses an embedded vector item from a list of candidates.

        Args:
            candidates (str): A string representation of the candidate embedding vector word groups.

        Returns:
            dict: A dictionary containing the result of the chosen embedded vector item.

        """

        EMBEDVEC_SYSTEM_MESSAGE = textwrap.dedent(
            """
            anaylyze the following set of "candidate group" of 4 words.
            
            For each  "candidate group"  determine if the 4 words are connected by a single theme or concept.

            eliminate "candidate group" where the 4 words are not connected by a single theme or concept.

            return the "candidate group" that is unlike the other word groups

            if there is no  "candidate group" connected by a single theme or concept, return the group with the highest group metric.

            return response in json with the
            * key "candidategroup" for the "candidate group" that is connected by a single theme or concept that is the most unique about the "candidate group".  This is a list of 4 words.
            * key "explanation" with a few word summary for the reason for the response.
            """
        )

        # Define the structured output for the embedded vector item
        class EmbedVecGroup(TypedDict):
            candidategroup: List[str]
            explanation: str

        prompt = HumanMessage(candidates)
        prompt = [SystemMessage(EMBEDVEC_SYSTEM_MESSAGE), prompt]
        prompt = convert_messages_to_prompt_anthropic(prompt)

        structured_llm = self.word_analyzer_llm.with_structured_output(EmbedVecGroup)
        # await asyncio.sleep(8.0)
        # result = await structured_llm.ainvoke(prompt)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def ask_llm_for_solution(self, words_remaining: str) -> dict:
        """
        Asks the OpenAI LLM for a solution based on the provided prompt.

        Parameters:
        prompt (str): The input prompt containg the candidate words to be analyzed.

        Returns:
        dict: containing keys: "words" for the recommended word group and "connection" for the connection reason.
        """

        LLM_RECOMMENDER_SYSTEM_MESSAGE = textwrap.dedent(
            """
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
            {{"words": ["Word1", "Word2", "Word3", "Word4"], "connection": "..."}},
            ```

            No other text.

            # Examples

            **Example:**

            - **Input:** ["prime", "dud", "shot", "card", "flop", "turn", "charge", "rainforest", "time", "miss", "plastic", "kindle", "chance", "river", "bust", "credit"]
            
            - **Output:**
            {{"words": [ "bust", "dud", "flop", "mist"], "connection": "clunker"}}

            No other text.

            # Notes

            - Ensure all thematic connections make logical sense.
            - Consider edge cases where a word could potentially fit into more than one category.
            - Focus on clear and accurate thematic grouping to aid in solving the puzzle efficiently.
            """
        )

        HUMAN_MESSAGE_BASE = textwrap.dedent(
            """
            From the following candidate list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection. 

            candidate list: {candidate_list}     
            """
        )

        # Define the structured output for the LLM recommendation
        class LLMRecommendation(TypedDict):
            words: List[str]
            connection: str

        logger.info("Entering ask_llm_for_solution")
        logger.debug(f"Entering ask_llm_for_solution words remaining: {words_remaining}")

        prompt = ChatPromptTemplate(
            [
                ("system", LLM_RECOMMENDER_SYSTEM_MESSAGE),
                ("user", HUMAN_MESSAGE_BASE),
            ]
        ).invoke({"candidate_list": words_remaining})

        # Invoke the LLM
        structured_llm = self.word_analyzer_llm.with_structured_output(LLMRecommendation)
        response = await invoke_bedrock_model_async(structured_llm, prompt.to_messages())

        logger.info("Exiting ask_llm_for_solution")
        logger.debug(f"exiting ask_llm_for_solution response {response}")

        return response

    async def extract_words_from_image(self, encoded_image: str):
        """
        Extract words from a base64 encoded image and return them as list.

        Args:
            encoded_image (str): The base64 encoded string of the image.

        Returns:
            dict: A list of words extracted from the image under the key "words".
        """

        # Define the structured output for the image extraction
        class ExtractedWordsFromImage(TypedDict):
            words: List[str]

        # Create a message with text and image
        message = HumanMessage(
            content=[
                {"type": "text", "text": "extract words from the image and return as a json list"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
            ]
        )

        structured_llm = self.image_extraction_llm.with_structured_output(ExtractedWordsFromImage)
        response = await invoke_bedrock_model_async(structured_llm, [message])

        return response

    async def analyze_anchor_words_group(self, anchor_words_group: str) -> dict:
        """
        Analyzes a group of anchor words to determine if they are related to a single topic.

        Args:
            anchor_words_group (list): A list of three anchor words to be analyzed.

        Returns:
            dict: The analysis result in JSON format.
        """

        ANCHOR_WORDS_SYSTEM_PROMPT = textwrap.dedent(
            """
            You are an expert in the nuance of the english language.

            You will be given three words. you must determine if the three words can be related to a single topic.

            To make that determination, do the following:
            * Determine common contexts for each word. 
            * Determine if there is a context that is shared by all three words.
            * respond 'single' if a single topic can be found that applies to all three words, otherwise 'multiple'.
            * Provide an explanation for the response.

            Return response in json with the key 'response' with the value 'single' or 'multiple' and the key 'explanation' with the reason for the response.
            """
        )

        ANCHOR_LIST_PROMPT = "\n{anchor_words_group}"

        class AnchorWordsAnalysis(TypedDict):
            response: str
            explanation: str

        prompt = ChatPromptTemplate(
            [
                ("system", ANCHOR_WORDS_SYSTEM_PROMPT),
                ("user", ANCHOR_LIST_PROMPT),
            ]
        ).invoke({"anchor_words_group": anchor_words_group})
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        structured_llm = self.word_analyzer_llm.with_structured_output(AnchorWordsAnalysis)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def generate_one_away_recommendation(self, anchor_words: str, candidate_words_remaining: str) -> dict:
        """
        Generates a recommendation for a single word that is one letter away from the provided prompt.

        Args:
            anchor_words_prompt (str): The prompt containing the anchor words.

        Returns:
            dict: The recommendation in JSON format.
        """

        ONE_AWAY_RECOMMENDATION_SYSTEM_PROMPT = textwrap.dedent(
            """
        you will be given a list called the "anchor_words".

        You will be given list of "candidate_words", select the one word that is most higly connected to the "anchor_words".

        Steps:
        1. First identify the common connection that is present in all the "anchor_words".  If each word has multiple meanings, consider the meaning that is most common among the "anchor_words".

        2. Now test each word from the "candidate_words" and decide which one has the highest degree of connection to the "anchor_words".    

        3. Return the word that is most connected to the "anchor_words" and the reason for its selection in json structure.  The word should have the key "word" and the explanation should have the key "explanation".
        """
        )

        USER_PROMPT = "\nanchor_words: {anchor_words_prompt}\n\ncandidate_words: {candidate_words}"

        class OneAwayRecommendation(TypedDict):
            word: str
            explanation: str

        prompt = ChatPromptTemplate(
            [
                ("system", ONE_AWAY_RECOMMENDATION_SYSTEM_PROMPT),
                ("user", USER_PROMPT),
            ]
        ).invoke(
            {
                "anchor_words_prompt": anchor_words,
                "candidate_words": candidate_words_remaining,
            }
        )
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        structured_llm = self.word_analyzer_llm.with_structured_output(OneAwayRecommendation)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def ask_llm_for_next_step(self, instructions: str, puzzle_state: str) -> dict:
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

        PLANNER_SYSTEM_MESSAGE = textwrap.dedent(
            """
            You are an expert in managing the sequence of a workflow. Your task is to
            determine the next tool to use given the current state of the workflow.

            the eligible tools to use are: ["setup_puzzle", "get_llm_recommendation", "apply_recommendation", "get_embedvec_recommendation", "get_manual_recommendation", "END"]

            The important information for the workflow state is to consider are: "puzzle_status", "tool_status", and "current_tool".

            Using the provided instructions, you will need to determine the next tool to use.

            output response in json format with key word "tool" and the value as the output string.
            
            {instructions}
            """
        )

        PUZZLE_STATE_PROMPT = "\npuzzle state: {puzzle_state}"

        # Define the structured output for the next action to be taken by the workflow
        class NextAction(TypedDict):
            tool: str

        logger.info("Entering ask_llm_for_next_step")
        logger.debug(f"Entering ask_llm_for_next_step Instructions: {instructions}")
        logger.debug(f"Entering ask_llm_for_next_step Prompt: {puzzle_state}")

        # Create a prompt by concatenating the system and human messages
        prompt = ChatPromptTemplate(
            [
                ("system", PLANNER_SYSTEM_MESSAGE),
                ("user", PUZZLE_STATE_PROMPT),
            ]
        ).invoke({"instructions": instructions, "puzzle_state": puzzle_state})
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        # Invoke the LLM
        llm_structured = self.workflow_llm.with_structured_output(NextAction)
        response = await invoke_bedrock_model_async(llm_structured, prompt)

        logger.debug(f"response: {pp.pformat(response)}")

        logger.info("Exiting ask_llm_for_next_step")
        logger.info(f"exiting ask_llm_for_next_step response {response}")

        return response


@llm_interface_registry.register("bedrock_hybrid")
class LLMBedrockHybridInterface(LLMInterfaceBase):

    def __init__(
        self,
        deep_word_analyzer_llm_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        word_analyzer_llm_name: str = "anthropic.claude-3-haiku-20240307-v1:0",
        image_extraction_llm_name: str = "anthropic.claude-3-haiku-20240307-v1:0",
        workflow_llm_name: str = "anthropic.claude-3-haiku-20240307-v1:0",
        embedding_model_name: str = "amazon.titan-embed-text-v2:0",
        temperature: float = 0.7,
        max_tokens=4096,
        **kwargs,
    ):
        """setups up LLM Model"""

        print(f"{self.__class__.__name__} __init__")

        self.word_analyzer_llm_name = word_analyzer_llm_name
        self.deep_word_analyzer_llm_name = deep_word_analyzer_llm_name
        self.workflow_llm_name = workflow_llm_name
        self.image_extraction_llm_name = image_extraction_llm_name
        self.embendding_model_name = embedding_model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        model_kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        self.word_analyzer_llm = ChatBedrock(
            model_id=self.word_analyzer_llm_name,
            model_kwargs=model_kwargs,
        )

        self.deep_word_analyzer_llm = ChatBedrock(
            model_id=self.deep_word_analyzer_llm_name,
            model_kwargs=model_kwargs,
            rate_limiter=RATE_LIMITER,
        )

        self.image_extraction_llm = ChatBedrock(
            model=self.image_extraction_llm_name,
            model_kwargs=model_kwargs,
        )

        self.workflow_llm = ChatBedrock(
            model_id=self.workflow_llm_name,
            model_kwargs={
                "temperature": 0,
                "max_tokens": self.max_tokens,
            },
        )

        self.embedding_model = BedrockEmbeddings(model_id=self.embendding_model_name)

    async def generate_vocabulary(self, words: List[str]) -> dict:
        """
        Asynchronously generates a vocabulary dictionary for a given list of words.

        This method uses a language model to analyze each word and produce structured
        vocabulary results. The results are stored in a dictionary where the keys are
        the input words and the values are the analysis results.

        Args:
            words (list of str): A list of words to be analyzed.

        Returns:
            dict: A dictionary where the keys are the input words and the values are
                  the structured vocabulary results.
        """

        VOCABULARY_SYSTEM_MESSAGE = textwrap.dedent(
            """
            You are an expert in language and knowledgeable on how words are used.

            Your task is to generate as many diverse definitions as possible for the given word.  Follow these steps:

            1. come up with a list of all possible parts of speech that the given word can be,e.g., noun, verb, adjective, etc.
            2. for each part of speech, generate one or more examples of the given word for that parts of speech.  preappend the part of speech to the examples, e.g., "noun: example1", "verb: example2", etc.
            3. combine all examples into a single list.

            Return your response as a JSON object with the key "result" and the examples as a list of strings.

            example:
            {{
                "result": [
                "noun: example1", 
                "noun: example2", 
                "adjective: example3",
                "verb: example4"
                ]
            }}
            """
        )

        # Define the structured output for the vocabulary results
        class VocabularyResults(TypedDict):
            result: List[str]

        vocabulary = {}

        given_word_template = ChatPromptTemplate(
            [
                ("system", VOCABULARY_SYSTEM_MESSAGE),
                ("user", "\ngiven word: {the_word}"),
            ]
        )

        async def process_word(the_word: str) -> dict:
            """
            Asynchronously processes a given word using a language model to analyze its vocabulary.

            Args:
                the_word (str): The word to be processed.

            Returns:
                None: The result is stored in the vocabulary dictionary with the word as the key.
            """
            prompt = given_word_template.invoke({"the_word": the_word})
            prompt = convert_messages_to_prompt_anthropic(prompt.messages)
            structured_llm = self.word_analyzer_llm.with_structured_output(VocabularyResults)
            result = await invoke_bedrock_model_async(structured_llm, prompt)
            vocabulary[the_word] = result["result"]

        await asyncio.gather(*[process_word(word) for word in words])

        return vocabulary

    def generate_embeddings(self, definitions: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of definitions.

        Args:
            definitions (List[str]): A list of strings where each string is a definition to be embedded.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """

        embeddings = self.embedding_model.embed_documents(definitions)

        return embeddings

    async def choose_embedvec_item(self, candidates: str) -> dict:
        """
        Asynchronously chooses an embedded vector item from a list of candidates.

        Args:
            candidates (str): A string representation of the candidate embedding vector word groups.

        Returns:
            dict: A dictionary containing the result of the chosen embedded vector item.

        """

        EMBEDVEC_SYSTEM_MESSAGE = textwrap.dedent(
            """
            anaylyze the following set of "candidate group" of 4 words.
            
            For each  "candidate group"  determine if the 4 words are connected by a single theme or concept.

            eliminate "candidate group" where the 4 words are not connected by a single theme or concept.

            return the "candidate group" that is unlike the other word groups

            if there is no  "candidate group" connected by a single theme or concept, return the group with the highest group metric.

            return response in json with the
            * key "candidategroup" for the "candidate group" that is connected by a single theme or concept that is the most unique about the "candidate group".  This is a list of 4 words.
            * key "explanation" with a few word summary for the reason for the response.
            """
        )

        # Define the structured output for the embedded vector item
        class EmbedVecGroup(TypedDict):
            candidategroup: List[str]
            explanation: str

        prompt = HumanMessage(candidates)
        prompt = [SystemMessage(EMBEDVEC_SYSTEM_MESSAGE), prompt]
        prompt = convert_messages_to_prompt_anthropic(prompt)

        structured_llm = self.deep_word_analyzer_llm.with_structured_output(EmbedVecGroup)
        # await asyncio.sleep(8.0)
        # result = await structured_llm.ainvoke(prompt)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def ask_llm_for_solution(self, words_remaining: str) -> dict:
        """
        Asks the OpenAI LLM for a solution based on the provided prompt.

        Parameters:
        prompt (str): The input prompt containg the candidate words to be analyzed.

        Returns:
        dict: containing keys: "words" for the recommended word group and "connection" for the connection reason.
        """

        LLM_RECOMMENDER_SYSTEM_MESSAGE = textwrap.dedent(
            """
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
            {{"words": ["Word1", "Word2", "Word3", "Word4"], "connection": "..."}},
            ```

            No other text.

            # Examples

            **Example:**

            - **Input:** ["prime", "dud", "shot", "card", "flop", "turn", "charge", "rainforest", "time", "miss", "plastic", "kindle", "chance", "river", "bust", "credit"]
            
            - **Output:**
            {{"words": [ "bust", "dud", "flop", "mist"], "connection": "clunker"}}

            No other text.

            # Notes

            - Ensure all thematic connections make logical sense.
            - Consider edge cases where a word could potentially fit into more than one category.
            - Focus on clear and accurate thematic grouping to aid in solving the puzzle efficiently.
            """
        )

        HUMAN_MESSAGE_BASE = textwrap.dedent(
            """
            From the following candidate list of words identify a group of four words that are connected by a common word association, theme, concept, or category, and describe the connection. 

            candidate list: {candidate_list}     
            """
        )

        # Define the structured output for the LLM recommendation
        class LLMRecommendation(TypedDict):
            words: List[str]
            connection: str

        logger.info("Entering ask_llm_for_solution")
        logger.debug(f"Entering ask_llm_for_solution words remaining: {words_remaining}")

        prompt = ChatPromptTemplate(
            [
                ("system", LLM_RECOMMENDER_SYSTEM_MESSAGE),
                ("user", HUMAN_MESSAGE_BASE),
            ]
        ).invoke({"candidate_list": words_remaining})

        # Invoke the LLM
        structured_llm = self.deep_word_analyzer_llm.with_structured_output(LLMRecommendation)
        response = await invoke_bedrock_model_async(structured_llm, prompt.to_messages())

        logger.info("Exiting ask_llm_for_solution")
        logger.debug(f"exiting ask_llm_for_solution response {response}")

        return response

    async def extract_words_from_image(self, encoded_image: str):
        """
        Extract words from a base64 encoded image and return them as list.

        Args:
            encoded_image (str): The base64 encoded string of the image.

        Returns:
            dict: A list of words extracted from the image under the key "words".
        """

        # Define the structured output for the image extraction
        class ExtractedWordsFromImage(TypedDict):
            words: List[str]

        # Create a message with text and image
        message = HumanMessage(
            content=[
                {"type": "text", "text": "extract words from the image and return as a json list"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
            ]
        )

        structured_llm = self.image_extraction_llm.with_structured_output(ExtractedWordsFromImage)
        response = await invoke_bedrock_model_async(structured_llm, [message])

        return response

    async def analyze_anchor_words_group(self, anchor_words_group: str) -> dict:
        """
        Analyzes a group of anchor words to determine if they are related to a single topic.

        Args:
            anchor_words_group (list): A list of three anchor words to be analyzed.

        Returns:
            dict: The analysis result in JSON format.
        """

        ANCHOR_WORDS_SYSTEM_PROMPT = textwrap.dedent(
            """
            You are an expert in the nuance of the english language.

            You will be given three words. you must determine if the three words can be related to a single topic.

            To make that determination, do the following:
            * Determine common contexts for each word. 
            * Determine if there is a context that is shared by all three words.
            * respond 'single' if a single topic can be found that applies to all three words, otherwise 'multiple'.
            * Provide an explanation for the response.

            Return response in json with the key 'response' with the value 'single' or 'multiple' and the key 'explanation' with the reason for the response.
            """
        )

        ANCHOR_LIST_PROMPT = "\n{anchor_words_group}"

        class AnchorWordsAnalysis(TypedDict):
            response: str
            explanation: str

        prompt = ChatPromptTemplate(
            [
                ("system", ANCHOR_WORDS_SYSTEM_PROMPT),
                ("user", ANCHOR_LIST_PROMPT),
            ]
        ).invoke({"anchor_words_group": anchor_words_group})
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        structured_llm = self.word_analyzer_llm.with_structured_output(AnchorWordsAnalysis)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def generate_one_away_recommendation(self, anchor_words: str, candidate_words_remaining: str) -> dict:
        """
        Generates a recommendation for a single word that is one letter away from the provided prompt.

        Args:
            anchor_words_prompt (str): The prompt containing the anchor words.

        Returns:
            dict: The recommendation in JSON format.
        """

        ONE_AWAY_RECOMMENDATION_SYSTEM_PROMPT = textwrap.dedent(
            """
        you will be given a list called the "anchor_words".

        You will be given list of "candidate_words", select the one word that is most higly connected to the "anchor_words".

        Steps:
        1. First identify the common connection that is present in all the "anchor_words".  If each word has multiple meanings, consider the meaning that is most common among the "anchor_words".

        2. Now test each word from the "candidate_words" and decide which one has the highest degree of connection to the "anchor_words".    

        3. Return the word that is most connected to the "anchor_words" and the reason for its selection in json structure.  The word should have the key "word" and the explanation should have the key "explanation".
        """
        )

        USER_PROMPT = "\nanchor_words: {anchor_words_prompt}\n\ncandidate_words: {candidate_words}"

        class OneAwayRecommendation(TypedDict):
            word: str
            explanation: str

        prompt = ChatPromptTemplate(
            [
                ("system", ONE_AWAY_RECOMMENDATION_SYSTEM_PROMPT),
                ("user", USER_PROMPT),
            ]
        ).invoke(
            {
                "anchor_words_prompt": anchor_words,
                "candidate_words": candidate_words_remaining,
            }
        )
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        structured_llm = self.deep_word_analyzer_llm.with_structured_output(OneAwayRecommendation)
        result = await invoke_bedrock_model_async(structured_llm, prompt)

        return result

    async def ask_llm_for_next_step(self, instructions: str, puzzle_state: str) -> dict:
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

        PLANNER_SYSTEM_MESSAGE = textwrap.dedent(
            """
            You are an expert in managing the sequence of a workflow. Your task is to
            determine the next tool to use given the current state of the workflow.

            the eligible tools to use are: ["setup_puzzle", "get_llm_recommendation", "apply_recommendation", "get_embedvec_recommendation", "get_manual_recommendation", "END"]

            The important information for the workflow state is to consider are: "puzzle_status", "tool_status", and "current_tool".

            Using the provided instructions, you will need to determine the next tool to use.

            output response in json format with key word "tool" and the value as the output string.
            
            {instructions}
            """
        )

        PUZZLE_STATE_PROMPT = "\npuzzle state: {puzzle_state}"

        # Define the structured output for the next action to be taken by the workflow
        class NextAction(TypedDict):
            tool: str

        logger.info("Entering ask_llm_for_next_step")
        logger.debug(f"Entering ask_llm_for_next_step Instructions: {instructions}")
        logger.debug(f"Entering ask_llm_for_next_step Prompt: {puzzle_state}")

        # Create a prompt by concatenating the system and human messages
        prompt = ChatPromptTemplate(
            [
                ("system", PLANNER_SYSTEM_MESSAGE),
                ("user", PUZZLE_STATE_PROMPT),
            ]
        ).invoke({"instructions": instructions, "puzzle_state": puzzle_state})
        prompt = convert_messages_to_prompt_anthropic(prompt.messages)

        # Invoke the LLM
        llm_structured = self.workflow_llm.with_structured_output(NextAction)
        response = await invoke_bedrock_model_async(llm_structured, prompt)

        logger.debug(f"response: {pp.pformat(response)}")

        logger.info("Exiting ask_llm_for_next_step")
        logger.info(f"exiting ask_llm_for_next_step response {response}")

        return response
