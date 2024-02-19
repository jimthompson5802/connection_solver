# Connection Solver Virtual Assistant Testbed

Experimental project to determine how to use GPT4 to solve the NYT Connection puzzles

## Instructions for use
* Create a new line separate file with the "Connection" puzzle words.  By default, the software assumes
the file is in `data/word_list.txt`, e.g.,
```
hinge
spoil
drill
match
lock
tinder
handle
bumble
grinder
frame
saw
log
fluff
kindling
blow 
router
```

* Run the `src/connection_solver.py` script to generate possible solutions for the NYT `Connection` puzzles. It uses the OpenAI API to generate the solutions.  Example output:

```
Word list: hinge, spoil, drill, match, lock, tinder, handle, bumble, grinder, frame, saw, log, fluff, kindling, blow , router

connection: door parts:  {'handle', 'lock', 'hinge'}

connection: woodworking tools:  {'router', 'drill', 'saw'}

connection: fire starting materials:  {'kindling', 'match', 'tinder'}

connection: dating apps:  {'bumble', 'tinder', 'grinder'}

connection: wood related:  {'router', 'drill', 'log', 'saw'}

connection: picture related:  {'match', 'frame'}

connection: soft materials:  {'kindling', 'fluff'}

connection: action verbs:  {'spoil', 'blow'}

```

* The user can use the above output to determine a group of four words that can be submitted as a solution to the NYT `Connection` puzzle.

* After a group of 4 words is selected and submitted, the user is expected to update the word list and remove the 4 words that were submitted.  The script can then be run again to generate the next set of possible solutions.


### Example run for 19Feb2024 puzzle

Lines that start with `>>>` are the user's action.

```
$ python src/connection_solver.py

Word list: hinge, spoil, drill, match, lock, tinder, handle, bumble, grinder, frame, saw, log, fluff, kindling, blow , router

connection: door parts:  {'handle', 'lock', 'hinge'}

connection: woodworking tools:  {'router', 'drill', 'saw'}

connection: fire starting materials:  {'kindling', 'match', 'tinder'}

connection: dating apps:  {'bumble', 'tinder', 'grinder'}

connection: wood related:  {'router', 'drill', 'log', 'saw'}

connection: picture related:  {'match', 'frame'}

connection: soft materials:  {'kindling', 'fluff'}

connection: action verbs:  {'spoil', 'blow'}

>>>Submitted: "door parts" + "frame"  THIS WORKED, removed words from list

$ python src/connection_solver.py

Word list: spoil, drill, match, tinder, bumble, grinder, saw, log, fluff, kindling, blow , router

connection: Dating apps:  {'bumble', 'tinder', 'grinder'}

connection: Fire starting materials:  {'match', 'kindling', 'tinder'}

connection: Woodworking tools:  {'saw', 'drill', 'router'}

connection: Wood related:  {'saw', 'log'}

connection: Starts with 'b':  {'bumble', 'blow'}

connection: Ends with 'l':  {'spoil', 'drill'}

connection: Fire related:  {'blow', 'kindling'}

connection: Soft materials:  {'kindling', 'fluff'}

>>>Submitted: "Woodworking tools:  + "grinder" THIS WORKED, removed words from list

$ python src/connection_solver.py
Word list: spoil, match, tinder, bumble, log, fluff, kindling, blow 

connection: fire starting materials:  {'tinder', 'log', 'kindling', 'match'}

connection: dating apps:  {'tinder', 'bumble'}

connection: verb, ruin something:  {'blow', 'spoil'}

connection: light, fluffy materials:  {'kindling', 'fluff'}

>>>Submitted: "fire starting materials" THIS WORKED

```

At this point only 4 words remain in the list, so the puzzle is solved.


## Core Modules

### src/connection_solver.py

This module generates possible solutions for the NYT `Connection` puzzles. It uses the OpenAI API to generate the solutions.

Here's a step-by-step breakdown:

1. The script starts by importing necessary modules: `argparse` for command-line argument parsing, `json` for handling JSON data, and `OpenAIInterface` from a custom module named `openai_module`.

2. The `argparse.ArgumentParser()` is initialized to handle command-line arguments. An argument for the word file path is added with a default value of "data/word_list.txt".

3. The arguments are parsed and the word file path is extracted.

4. The script then opens the word file, reads the words, and stores them in a list.

5. A prompt is created with the words and printed to the console.

6. The script opens a JSON file containing the OpenAI API key, loads the key, and initializes an `OpenAIInterface` object with it.

7. The `OpenAIInterface` object is used to chat with the prompt and the response is parsed as JSON.

8. An empty dictionary is initialized to store the results.

9. The script iterates over the JSON data. For each item, it extracts a 'connection' value and a list of 'words'. If the 'connection' value is not already in the result dictionary, it adds a new set with the 'words' values. If the 'connection' value is already in the result dictionary, it adds the 'words' values to the existing set.

10. Finally, the script prints the results.

Here is sample output from the script:

```
$ python src/connection_solver.py

Word list: hinge, spoil, drill, match, lock, tinder, handle, bumble, grinder, frame, saw, log, fluff, kindling, blow , router

connection: door parts:  {'handle', 'lock', 'hinge'}

connection: woodworking tools:  {'router', 'drill', 'saw'}

connection: fire starting materials:  {'kindling', 'match', 'tinder'}

connection: dating apps:  {'bumble', 'tinder', 'grinder'}

connection: wood related:  {'router', 'drill', 'log', 'saw'}

connection: picture related:  {'match', 'frame'}

connection: soft materials:  {'kindling', 'fluff'}

connection: action verbs:  {'spoil', 'blow'}
```

The user can use the above output to determine a group of four words that can be submitted as a solution to the NYT `Connection` puzzle.

In the above example, "door parts" with the addition of "frame" can be submitted as a solution to the puzzle.

### src/openai_module.py

The selected code is a Python class named [`OpenAIInterface`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22OpenAIInterface%22%5D "src/openai_module.py") that is used to interact with the OpenAI API. This class is defined in a module named [`openai_module.py`](command:_github.copilot.openRelativePath?%5B%22src%2Fopenai_module.py%22%5D "src/openai_module.py").

Here's a step-by-step breakdown:

1. The `openai` module is imported, which provides the functionality to interact with the OpenAI API.

2. The [`OpenAIInterface`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22OpenAIInterface%22%5D "src/openai_module.py") class is defined with a docstring that describes its purpose and attributes.

3. A class attribute [`system_prompt`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22system_prompt%22%5D "src/openai_module.py") is defined. This is a multi-line string that seems to be used as a prompt for the OpenAI API.

4. The [`__init__`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22__init__%22%5D "src/openai_module.py") method is defined. This method is called when an instance of the [`OpenAIInterface`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22OpenAIInterface%22%5D "src/openai_module.py") class is created. It takes an API key and a model name as arguments, with the model defaulting to "gpt-4". The method initializes an `OpenAI` client with the provided API key and sets the model.

5. The [`chat`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22chat%22%5D "src/openai_module.py") method is defined. This method takes a prompt as an argument and uses it to make a request to the OpenAI API. The method constructs a list of messages, with the [`system_prompt`](command:_github.copilot.openSymbolInFile?%5B%22src%2Fopenai_module.py%22%2C%22system_prompt%22%5D "src/openai_module.py") as the system message and the provided prompt as the user message. It then makes a request to the OpenAI API's chat completions endpoint with these messages and some additional parameters. The response from the API is returned.

6. If an error occurs during the API request, it is caught and printed, and then re-raised.

This class provides a convenient way to interact with the OpenAI API, encapsulating the details of making the API request and handling the response. It can be used in other parts of your project to generate responses from the OpenAI API based on a given prompt.

