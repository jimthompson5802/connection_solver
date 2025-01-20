import asyncio
import json
import logging
import pprint as pp
import textwrap
from typing import List, TypedDict, Dict

from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_aws.chat_models.bedrock import convert_messages_to_prompt_mistral
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from tools import LLMInterfaceBase

logger = logging.getLogger(__name__)


#
class LLMBedrockMistralAIInterface(LLMInterfaceBase):
    """class for OpenAI LLM Interface"""

    def __init__(
        self,
        word_analyzer_llm_name: str = "mistral.mistral-7b-instruct-v0:2",
        image_extraction_llm_name: str = NotImplementedError,
        workflow_llm_name: str = "gpt-4o-mini",
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

        self.word_analyzer_llm = ChatBedrock(
            model_id=self.word_analyzer_llm_name,
            model_kwargs={"temperature": self.temperature, "max_tokens": self.max_tokens},
        )

        self.image_extraction_llm = None

        self.workflow_llm = ChatOpenAI(
            model=self.workflow_llm_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        self.embedding_model = BedrockEmbeddings(model_id=self.embendding_model_name)

    async def _invoke_with_structured_output(self, in_prompt: List, ReponseStucture: Dict) -> Dict:
        """Invoke LLM with structured output"""

        retries = 4
        for attempt in range(retries):
            try:
                response = await self.word_analyzer_llm.ainvoke(in_prompt)
                response = json.loads(response.content)
                return response
            except json.JSONDecodeError as e:
                if attempt < retries - 1:
                    warning_message = f"JSONDecodeError encountered: {e}. Retrying {retries - attempt - 1} more times.\nprompt: {in_prompt}\nResponseStructure: {ReponseStucture}\nrespose: {response}"
                    logger.warning(warning_message)
                    print(warning_message)
                    await asyncio.sleep(1)  # Optional: wait a bit before retrying
                else:
                    error_message = f"Failed to decode JSON after {retries} attempts: {e}\nprompt: {in_prompt}\nResponseStructure: {ReponseStucture}\nrespose: {response}"
                    logger.error(error_message)
                    print(error_message)
                    raise

    async def llm_check(self):
        """
        Check if LLM is working
        """
        response = await self.word_analyzer_llm.ainvoke("what is capital of hawaii? only return the city's name")
        print(response.content)
        return response.content

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
            DO NOT INCLUDE ANY OTHER TEXT INCLUDING ANY COMMENTS.
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
            # print(f"Processing word: {the_word}")
            # prompt = self._convert_prompt_to_messages(given_word_template)
            prompt = given_word_template.invoke({"the_word": the_word})
            prompt = convert_messages_to_prompt_mistral(prompt.messages)
            result = await self._invoke_with_structured_output(prompt, VocabularyResults)

            vocabulary[the_word] = result["result"]

        await asyncio.gather(*[process_word(word) for word in words])

        # TODO Clean up
        # for word in words:
        #     await process_word(word)

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
            
            For each  "candidate group"  determine if the FOUR words are connected by a single theme or concept.

            eliminate "candidate group" where the 4 words are not connected by a single theme or concept.

            return the "candidate group" that is unlike the other word groups

            if there is no  "candidate group" connected by a single theme or concept, return the group with the highest group metric.

            return only a JSON object with following keys:
            "candidategroup" for the four word group that is connected by a single theme or concept, this must contain FOUR words.
            "explanation" with a few word summary for the reason.

            do not include any other text.
            """
        )

        # Define the structured output for the embedded vector item
        class EmbedVecGroup(TypedDict):
            candidate_group: List[str]
            explanation: str

        prompt = HumanMessage(candidates)
        prompt = [SystemMessage(EMBEDVEC_SYSTEM_MESSAGE), prompt]
        prompt = convert_messages_to_prompt_mistral(prompt)

        # TODO: clean up?
        # structured_llm = self.word_analyzer_llm.with_structured_output(EmbedVecGroup)
        # result = await structured_llm.ainvoke(prompt)

        result = await self._invoke_with_structured_output(prompt, EmbedVecGroup)

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
            You are a helpful assistant knowledgeable of the English language.

            From a canidate list of words, you must identify a group of four words that are connected by a common word association, theme, concept, or category.

            # Steps

            1. **Review the candidate words**: Look at the words provided in the candidate list carefully.
            2. **Identify Themes**: Notice any apparent themes or categories (e.g., types of animals, names of colors, etc.).
            3. **Group Words**: Attempt to form groups of four words that share a common theme.
            4. **Verify Groups**: Ensure that each word belongs to only one group. If a word seems to fit into multiple categories, decide on the best fit based on the remaining options.
            5. **Order the groups**: Order your answers in terms of your confidence level, high confidence first.
            6. **Solution output**: Select only the highest confidence group.  Generate only a JSON object response with the keys "words" and "connection".  Make sure the word group contains four words.

            Return only a "SINGLE" JSON object containing these keys:
            "words" that is the list of the connected 4 words.  MAKE SURE THE LIST CONTAINS 4 WORDS.
            "connection" describing the connection among the words.

            RETURN ONLY THE JSON OBJECT WITH THE KEYS "words" and "connection".
            DO NOT INCLUDE ANY OTHER TEXT.
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
        # structured_llm = self.word_analyzer_llm.with_structured_output(LLMRecommendation)
        # response = await structured_llm.ainvoke(prompt.to_messages())
        response = await self._invoke_with_structured_output(prompt, LLMRecommendation)

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

        response = await structured_llm.ainvoke([message])

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

        # structured_llm = self.word_analyzer_llm.with_structured_output(AnchorWordsAnalysis)
        # result = await structured_llm.ainvoke(prompt.to_messages())

        prompt = convert_messages_to_prompt_mistral(prompt.messages)
        result = await self._invoke_with_structured_output(prompt, AnchorWordsAnalysis)

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

        # structured_llm = self.word_analyzer_llm.with_structured_output(OneAwayRecommendation)
        # result = await structured_llm.ainvoke(prompt.to_messages())

        prompt = convert_messages_to_prompt_mistral(prompt.messages)
        result = await self._invoke_with_structured_output(prompt, OneAwayRecommendation)

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

        # Invoke the LLM
        llm_structured = self.workflow_llm.with_structured_output(NextAction)
        response = await llm_structured.ainvoke(prompt.to_messages())

        logger.debug(f"response: {pp.pformat(response)}")

        logger.info("Exiting ask_llm_for_next_step")
        logger.info(f"exiting ask_llm_for_next_step response {response}")

        return response
