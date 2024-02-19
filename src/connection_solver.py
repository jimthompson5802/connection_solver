import argparse
import json

from openai_module import OpenAIInterface

if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser()
    # Add argument for word file path, with default value "data/word_list.txt"
    parser.add_argument("word_fp", nargs="?", default="data/word_list.txt")
    # add keyword argument for temperature with default value of 0.1
    parser.add_argument("--temperature", type=float, default=0.1)

    # Parse the arguments
    args = parser.parse_args()

    # Get the word file path from the arguments
    word_fp = args.word_fp
    temperature = args.temperature

    # Open the word file and read the words
    with open(word_fp, "r") as f:
        words = f.read().splitlines()   
    
    # Create a prompt with the words
    prompt = "Word list: " + ", ".join(words)
    print(f"{prompt}")

    # Create an OpenAIInterface object
    # Load the API key from a JSON file
    with open("/openai/api_key.json") as f:
        api_key = json.load(f)
    openai_interface = OpenAIInterface(api_key["key"])

    # Use the OpenAIInterface to chat with the prompt and parse the response as JSON
    json_data = json.loads(openai_interface.chat(prompt, temperature=temperature))

    # Initialize an empty dictionary to store the results
    result = {}
    # Iterate over the JSON data
    for d in json_data:
        # Get the 'connection' value
        connection = d['connection']

        # If this 'connection' value is not in the result dictionary,
        # create a new set with the 'words' values
       
        if connection not in result:
            result[connection] = set(d['words'])
        # If this 'connection' value is already in the result dictionary,
        # add the 'words' values to the existing set
        else:
            result[connection] = result[connection].union(set(d['words']))

    # Print the results
    for k, v in result.items():
        print(f"\nconnection: {k}:  {v}")