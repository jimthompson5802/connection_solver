import argparse
import json

from openai_module import OpenAIInterface

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("word_fp", nargs="?", default="data/word_list.txt")
    args = parser.parse_args()

    word_fp = args.word_fp

    with open(word_fp, "r") as f:
        words = f.read().splitlines()   
    
    prompt = "Word list: " + ", ".join(words)
    print(f"{prompt}")


    # Create an OpenAIInterface object
    with open("/openai/api_key.json") as f:
        api_key = json.load(f)
    openai_interface = OpenAIInterface(api_key["key"])

    json_data = json.loads(openai_interface.chat(prompt))

    result = {}
    for d in json_data:
        connection = d['connection']
        if connection not in result:
            result[connection] = set(d['words'])
        else:
            result[connection] = result[connection].union(set(d['words']))

    for k, v in result.items():
        print(f"\nconnection: {k}:  {v}")



