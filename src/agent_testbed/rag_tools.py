import json
import os
import pickle

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


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


def validate_recommendations(candidates, model="gpt-4o", temperature=0.7, max_tokens=4096):

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
