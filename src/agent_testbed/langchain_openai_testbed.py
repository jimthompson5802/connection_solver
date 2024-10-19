import json

with open("/openai/api_key.json") as f:
    config = json.load(f)

api_key = config["key"]

def main():
    from langchain_openai import ChatOpenAI

    # Initialize the OpenAI LLM with your API key and specify the GPT-4o model
    llm = ChatOpenAI(
        api_key=api_key, 
        model="gpt-4o",
        max_tokens=4096,
        )

    # Define the prompt for translation
    # prompt = "Translate the following English text to Hawaiian Pidgin English: 'I am very hungry and I want to eat some delicious food that my grandma makes.'"
    prompt = "Tell the story of Little Red Riding Hood in the context of India."

    # Invoke the LLM
    response = llm.invoke(prompt)

    # Print the response
    print(response.content)

if __name__ == "__main__":
    main()