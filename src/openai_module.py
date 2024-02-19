from openai import OpenAI

class OpenAIInterface:
    """
    A class used to interface with the OpenAI API.

    This class provides a method to invoke the chat API with a given prompt and return the contents to the caller.

    Attributes:
        api_key_file (str): The location of a JSON file with the API key.
        model (str): The specific model to use.
    """
    system_prompt = """
        You are a helpful assistant with knowledge about words and how words relate to each other.

        This relationshps can be anything.  Here are some examples:
        * common characteristics
        * used in combination with the same word not in the list
        * Shares a common prefix or suffix.
        * parts of a larger whole.
        * synomyns

        What connections are possible between all pairs of words in the list.

        If there is no connection, do not include the pair in the list.

        Describe the connection in 1 to 5 words.

        Generate json list containing all the pairs formed.  
        For each word pair there is the key "connection" that contains the 1 to 5 word connection and "words" that list the word pair.

    """

    def __init__(self, api_key, model="gpt-4"):
        """
        Initializes the OpenAIInterface with the API key and the model.

        This method reads the API key from the provided JSON file and initializes an OpenAI client with the API key. 
        It also sets the model to use.

        Args:
            api_key (str): API key string
            model (str, optional): The specific model to use. Defaults to "gpt-4".
        """

        self.openai_client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, prompt):
        """
        Invokes the chat API with a given prompt and returns the contents to the caller.

        Args:
            prompt (str): The prompt to use.

        Returns:
            json string list: in the format of
            [
                {
                    "connection": "tools for woodworking",
                    "words": ["hinge", "drill"]
                },
                {
                    "connection": "could spoil food",
                    "words": ["spoil", "match"]
                },
                {
                    "connection": "parts of a door",
                    "words": ["hinge", "lock"]
                },
                {
                    "connection": "door hardware",
                    "words": ["hinge", "handle"]
                }
            ]

        """
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=6400, 
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            raise    

