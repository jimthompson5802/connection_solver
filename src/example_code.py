from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
  model="gpt-4",
  messages=[
    {
      "role": "system",
      "content": "You are a helpful assistant with knowledge about words and how words relate to each other.\n\nThis relationshps can be anything.  Here are some examples:\n* common characteristics\n* used in combination with the same word not in the list\n* Shares a common prefix or suffix.\n* parts of a larger whole.\n* synomyns\n\nWhat connections are possible between all pairs of words in the list.\n\nDescribe the connection in 1 to 5 words.\n\ngenerate json list containing all the pairs formed.  For each word pair there is the key \"connection\" that contains the 1 to 5 word connection and \"words\" that list the word pair.\n"
    },
    {
      "role": "user",
      "content": "Word list:  spoil, bumble,  fluff, blow"
    },
    {
      "role": "assistant",
      "content": "[\n  {\n    \"connection\": \"Synonyms for making mistakes\",\n    \"words\": [\"spoil\", \"bumble\"]\n  },\n  {\n    \"connection\": \"Synonyms for making mistakes\",\n    \"words\": [\"spoil\", \"fluff\"]\n  },\n  {\n    \"connection\": \"Spoil and blow: negative outcomes\",\n    \"words\": [\"spoil\", \"blow\"]\n  },\n  {\n    \"connection\": \"Bumble and fluff: clumsy actions\",\n    \"words\": [\"bumble\", \"fluff\"]\n  },\n  {\n    \"connection\": \"Bumble and blow: verbs with 'b'\",\n    \"words\": [\"bumble\", \"blow\"]\n  },\n  {\n    \"connection\": \"Fluff and blow: air-related actions\",\n    \"words\": [\"fluff\", \"blow\"]\n  }\n]"
    },
    {
      "role": "user",
      "content": "Consolidate common or similar connections found.  Ignore \"unrelated\" connections.\n\nOutput the summarization in a json list where each element contains \"connection\" for the common connection and \"words\" that is a list of the words.\n"
    },
    {
      "role": "assistant",
      "content": "[\n  {\n    \"connection\": \"Synonyms for making mistakes\",\n    \"words\": [\"spoil\", \"bumble\", \"fluff\"]\n  },\n  {\n    \"connection\": \"Verbs starting with 'b'\",\n    \"words\": [\"bumble\", \"blow\"]\n  },\n  {\n    \"connection\": \"Actions related to air\",\n    \"words\": [\"fluff\", \"blow\"]\n  }\n]"
    }
  ],
  temperature=0.1,
  max_tokens=6400,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)