# Connection Solver Virtual Assistant Testbed

Experimental project to solve the [NYT Connection puzzles](https://www.nytimes.com/games/connections) using agentic workflow based on the [`langchain` ecosystem](https://python.langchain.com/v0.2/docs/introduction/).  In particular used:
* [`langchain`'s OpenAI LLM abstraction layer](https://python.langchain.com/v0.2/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html#chatopenai) to interact with OpenAI's `gpt-4o` and `gpt-3.5-turbo` models
* [`langgraph`'s stateful orchestration framework](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/#multi-agent-network) to manage the agent's workflow
* [`langsmith`'s tracing tool](https://www.langchain.com/langsmith) to trace the agent's workflow

The agentic approach was inspired by these talks:
* [What's next for AI agentic workflows ft. Andrew Ng of AI Fund](https://youtu.be/sal78ACtGTc)
* [How Clearwater Analytics Builds AI Agents with Small Language Models (SLMs)](https://youtu.be/Z-k8Wm2uQmw?t=72)


## Connection Puzzle Description
Connections is a word game that challenges players to find themes between words. The user is presented with 16 words and must create groups of four items that share something in common. For example: **Tropical fruit**: banana, mango, pineapple, guava.

## Features of the Connection Solver Virtual Assistant Agent `app_embedvec.py`
* Extract puzzle words from text file to setup the puzzle
* LLM based tools to:
  * Extract words from an image to seutp the puzzle 

    ![](./images/example_puzzle_image.png)
  * LLM generator to create embedding vectors
  * Embedding vector based puzzle recommendation generator  
  * LLM puzzle recommendation generator
  * Natural Language Puzzle Planner workflow using markdown in an external file
* Two phase solver process
    * Phase 1: Use Embedding Vecotor recommendation generation
    * Phase 2: Use LLM puzzle recommendation generation if Phase 1 encounters a mistake
* Use of multiple LLMs:
    * `gpt-3.5-turbo` for the agent's planner
    * `gpt-4o` for generating puzzle recommendations and extract words from image
* LLM tracing with `langsmith`


## Solution Strategy

The agent uses a two-phase solver process.  The first phase uses an Embedding Vector-based recommendation generator.  If the agent encounters a mistake, the second phase uses an LLM-based recommendation generator.  

**Note**: See [here](./docs/README_LLM.md) for a description of the original LLM-based solver.

The agent uses the `PuzzleState` class to manage the agent's state and controls the agent's workflow. 
```python
# define the state of the puzzle
class PuzzleState(TypedDict):
    puzzle_status: str = ""
    puzzle_step: str = ""
    puzzle_recommender: str = ""
    workflow_instructions: str = ""
    vocabulary_df: pd.DataFrame = None
    tool_to_use: str = ""
    words_remaining: List[str] = []
    invalid_connections: List[List[str]] = []
    recommended_words: List[str] = []
    recommended_connection: str = ""
    recommended_correct: bool = False
    found_yellow: bool = False
    found_greeen: bool = False
    found_blue: bool = False
    found_purple: bool = False
    mistake_count: int = 0
    found_count: int = 0
    recommendation_count: int = 0
    llm_temperature: float = 1.0
```

Key workflow attributes:
* `puzzle_status`: indicates if puzzle is initialized
* `puzzle_step`: indicates the results of the current step and is used to determine next tool to use
* `puzzle_recommender`: indicates current active recommender tool:  `embedvec_recommender` or `llm_recommender`.
* `workflow_instructions`: contains the workflow instructions
* `vocabulary_df`: contains the vocabulary and embedding vectors for the puzzle words


Overall control is performed by the `run_planner()` function.  The agent's workflow is defined by the `StateGraph` class from `langgraph`.  The agent's workflow is defined by a series of nodes and edges.  The nodes are the agent's processing steps and the edges are the transitions between the processing steps.  This function determines the next step in the agent's workflow based on the attributes described above.

Agent's workflow defintion:
```python
    workflow = StateGraph(PuzzleState)


    workflow.add_node("run_planner", run_planner)
    workflow.add_node("setup_puzzle", setup_puzzle)
    workflow.add_node("get_embedvec_recommendation", get_embedvec_recommendation)
    workflow.add_node("get_recommendation", get_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)


    workflow.add_conditional_edges(
        "run_planner",
        determine_next_action,
        {
            "setup_puzzle": "setup_puzzle",
            "get_embedvec_recommendation": "get_embedvec_recommendation",
            "get_recommendation": "get_recommendation",
            "apply_recommendation": "apply_recommendation",
            END: END,
        },
    )


    workflow.add_edge("setup_puzzle", "run_planner")
    workflow.add_edge("get_recommendation", "run_planner")
    workflow.add_edge("get_embedvec_recommendation", "run_planner")
    workflow.add_edge("apply_recommendation", "run_planner")


    workflow.set_entry_point("run_planner")


    app = workflow.compile()
    app.get_graph().draw_png("images/connection_solver_embedvec_graph.png")
```

Diagram of the agent's workflow:
![Connection Solver Workflow](./images/connection_solver_embedvec_graph.png)

The agent's planner function uses the LLM and current `PuzzleState` to determine the next step in the workflow.  The Planner's prompt consists of three parts.  First is the "system prompt":
```python
PLANNER_SYSTEM_MESSAGE = """
    You are an expert in managing the sequence of a workflow. Your task is to
    determine the next tool to use given the current state of the workflow.


    the eligible tools to use are: ["setup_puzzle", "get_recommendation", "apply_recommendation", "get_embedvec_recommendation", "END"]


    The important information for the workflow state is to consider are: "puzzle_status", "puzzle_step", and "puzzle_recommender".


    Using the provided instructions, you will need to determine the next tool to use.


    output response in json format with key word "tool" and the value as the output string.
    
"""
```

The second part is this markdown description of the workflow.

Markdown description of the workflow instructions:
---
**Instructions**

use "setup_puzzle" tool to initialize the puzzle if the "puzzle_status" is not initialized.

if "puzzle_step" is "puzzle_completed" then use "END" tool.

Use the table to select the appropriate tool.

|puzzle_recommender| puzzle_step | tool |
| --- | --- | --- |
|embedvec_recommender| next_recommendation | get_embedvec_recommendation |
|embedvec_recommender| have_recommendation | apply_recommendation |
|llm_recommender| next_recommendation | get_recommendation |
|llm_recommender| have_recommendation | apply_recommendation |

If no tool is selected, use "ABORT" tool.

---


The final part is the current state of the game.  The following subset of `PuzzleState` is extracted as a string and passed to the LLM in the prompt to determine the next step in the agent's workflow.  The LLM's response determines the next tool to use.
```python
'{
    "puzzle_status": "initialized", 
    "puzzle_step": "next_recommendation",
    "puzzle_recommender": "embedvec_recommender",
}'
```

## Repo Contents
Major contents of the repo:
| File/Folder | Description |
| --- | --- |
| `src/agent/app.py` | Main entry point for the agent.  Define workflow processing steps (aka graph nodes), workflow transitions (aka graph edges) and `PuzzleState` data structure.  The original LLM-based solver|
| `src/agent/app_embedvec.py` | Main entry point for the agent.  Define workflow processing steps (aka graph nodes), workflow transitions (aka graph edges) and `PuzzleState` data structure.  The Embedding Vector-based solver.|
| `src/agent/tools.py` | Tools used by the agent: retrieve puzzle setup, interact with user and interface to OpenAI LLM|
| `src/agent/embedvec_tools.py` | Tools used by the agent: created embedding vectors, retrieve puzzle setup, interact with user and interface to OpenAI LLM|
| `src/agent/utils.py` | Utilities to be used by the agent. |
| `src/agent/tests/` | Unit tests for the agent. |
| `src/agent_testbed/` | Directory containing technical proof-of-concept code. |
| `data/` | Directory containing past NYT Connection Puzzles for testing. |
| `prompt_testbed/` | Directory containing sample prompts used in testing with the OpenAI Playground. |

## Some Lessons Learned
While prompt engineering is a critical component to the agent's success, an equally critical function is setting up the right data structures to be used by the LLM.  Speficially, randomizing the order of the words in `words_remaining` seemed to allow the LLM to get unstuck from invalid groupings. 

Automated testing is needed.  Right now the agent is tested manually.  This can be tedious as more test cases are needed.  Automated testing would allow for more rapid development and testing of the agent.

Experiment tracking is needed.  As different designs of the workflow and changes in functionality at different steps in the process, the results from testing should be automatically recorded.  For this body of work, all of this was done either in hand-written notes or tracked via memory.

From a Virtual Coding Assistant perspective, perplexity.ai seemed to generate more useful code for `langchain` and `langgraph`.  Github Copilot generated code for these libraries generated code that was not compatible with the current version of the libraries.  This is probably due to GH Copilot is trained on code in public repos vs perplexity.ai uses a RAG based approach on current content in the web.  perplexity.ai appears to support better at code generation for new and quickly evolving packages.  However, once I have some code in the Visual Studio Code IDE, then GH Copilot reduced the effort to refactor and revise the code.  For long standing packages, e.g, `pandas`, `numpy`, `matplotlib`, GH Copilot generates useful code snippets.

## Sample Runs

Historical NYT Connection Puzzles were used in testing the agent.  Past puzzles can be found [here](https://word.tips/todays-nyt-connections-answers/).

### How to Run the Agent
```bash
# run agent with default logging level
$ python src/agent/app_embedvec.py

# run agent with DEBUG logging level
$ python src/agent/app_embedvec.py --log-level DEBUG
```
Command line options:
```text
usage: app_embedvec.py [-h] [--log-level LOG_LEVEL] [--trace]

Set logging level for the application.

options:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  --trace               Enable langsmith tracing for the application.
```

Note: Due to the random nature of the LLM, the results vary from run to run.  For example, running the same puzzle multiple times may result in different recommendations from the LLM.  As a result, the puzzle may get solved in one run and not in another.

### Solved Connection Puzzle 1
**Expected Solution**
```text
🟡 MAKE GOOD ON, AS A PROMISE: FULFILL ,HONOR ,KEEP ,UPHOLD

🟢 BEDDING: BLANKET ,SHAM ,SHEET ,THROW

🔵 ACTIONS IN CARD GAMES: DISCARD ,DRAW ,PASS ,PLAY

🟣 CABINET DEPARTMENTS: ENERGY ,JUSTICE ,LABOR ,STATE
```
**Example Run**
```text
python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: file
Please enter the word file location: data/word_list5.txt
Puzzle Words: ['uphold', 'discard', 'honor', 'energy', 'state', 'play', 'justice', 'labor', 'pass', 'fulfill', 'draw', 'keep', 'blanket', 'sham', 'sheet', 'throw']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(133, 133)
(133, 133)
candidate_lists size: 86

RECOMMENDED WORDS ['fulfill', 'honor', 'keep', 'uphold'] with connection These words are all connected by the theme of fulfilling obligations or commitments.
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['fulfill', 'honor', 'keep', 'uphold'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(107, 107)
(107, 107)
candidate_lists size: 54

RECOMMENDED WORDS ['blanket', 'sham', 'sheet', 'throw'] with connection All words are related to household fabric items used for covering or decoration.
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['blanket', 'sham', 'sheet', 'throw'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(78, 78)
(78, 78)
candidate_lists size: 25

RECOMMENDED WORDS ['discard', 'draw', 'pass', 'play'] with connection This group uniquely centers around actions commonly associated with games or sports.
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['discard', 'draw', 'pass', 'play'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(29, 29)
(29, 29)
candidate_lists size: 1

RECOMMENDED WORDS ['energy', 'justice', 'labor', 'state'] with connection The words relate to different societal and functional aspects but do not share a single theme.
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['energy', 'justice', 'labor', 'state'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_count': 4,
    'found_purple': True,
    'found_yellow': True,
    'invalid_connections': [],
    'llm_temperature': 0.7,
    'mistake_count': 0,
    'puzzle_recommender': 'embedvec_recommender',
    'puzzle_status': 'initialized',
    'puzzle_step': 'puzzle_completed',
    'recommendation_count': 4,
    'recommended_connection': '',
    'recommended_correct': False,
    'recommended_words': [],
    'tool_to_use': 'END',
    'vocabulary_df': Empty DataFrame
Columns: [word, definition, embedding]
Index: [],
    'words_remaining': [],
    'workflow_instructions': '**Instructions**\n'
                             '\n'
                             'use "setup_puzzle" tool to initialize the puzzle '
                             'if the "puzzle_status" is not initialized.\n'
                             '\n'
                             'if "puzzle_step" is "puzzle_completed" then use '
                             '"END" tool.\n'
                             '\n'
                             'Use the table to select the appropriate tool.\n'
                             '\n'
                             '|puzzle_recommender| puzzle_step | tool |\n'
                             '| --- | --- | --- |\n'
                             '|embedvec_recommender| next_recommendation | '
                             'get_embedvec_recommendation |\n'
                             '|embedvec_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '|llm_recommender| next_recommendation | '
                             'get_recommendation |\n'
                             '|llm_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '\n'
                             'If no tool is selected, use "ABORT" tool.\n'}
``` 

### Solved Connection Puzzle 2
**Expected Solution**
```text
🟡 BRING ABOUT: GENERATE ,INSPIRE ,PROMPT ,PROVOKE

🟢 THINGS THAT ARE OFTEN SCENTED: CANDLE ,INCENSE ,LOTION ,SOAP

🔵 THINGS THAT MIGHT STING: INSULT ,JELLYFISH ,NETTLE ,WASP

🟣 VIDEO GAME FRANCHISES: CIVILIZATION ,HALO ,MADDEN ,METROID
```
**Example Run**
```text
$ python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: file
Please enter the word file location: data/word_list2.txt
Puzzle Words: ['inspire', 'madden', 'jellyfish', 'metroid', 'insult', 'candle', 'halo', 'provoke', 'soap', 'generate', 'incense', 'civilization', 'lotion', 'wasp', 'prompt', 'nettle']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(86, 86)
(86, 86)
candidate_lists size: 58

RECOMMENDED WORDS ['incense', 'madden', 'nettle', 'provoke'] with connection All words are connected by the theme of making someone angry or annoyed.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['incense', 'madden', 'nettle', 'provoke'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['insult', 'jellyfish', 'nettle', 'wasp'] with connection Things that sting or irritate
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['nettle', 'wasp', 'jellyfish', 'insult'] is correct

RECOMMENDED WORDS ['civilization', 'halo', 'incense', 'metroid'] with connection Video Game Titles
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['metroid', 'halo', 'civilization', 'incense'] is incorrect

RECOMMENDED WORDS ['candle', 'incense', 'lotion', 'soap'] with connection Items used for fragrance or hygiene
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['soap', 'candle', 'incense', 'lotion'] is correct

RECOMMENDED WORDS ['generate', 'inspire', 'prompt', 'provoke'] with connection Words related to eliciting a response or action
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['inspire', 'provoke', 'generate', 'prompt'] is correct

RECOMMENDED WORDS ['civilization', 'halo', 'madden', 'metroid'] with connection Video Game Titles
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['halo', 'metroid', 'civilization', 'madden'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_count': 4,
    'found_purple': True,
    'found_yellow': True,
    'invalid_connections': [   ['incense', 'madden', 'nettle', 'provoke'],
                               ['metroid', 'halo', 'civilization', 'incense']],
    'llm_temperature': 0.7,
    'mistake_count': 2,
    'puzzle_recommender': 'llm_recommender',
    'puzzle_status': 'initialized',
    'puzzle_step': 'puzzle_completed',
    'recommendation_count': 6,
    'recommended_connection': '',
    'recommended_correct': False,
    'recommended_words': [],
    'tool_to_use': 'END',
    'vocabulary_df':        word  ...                                          embedding
0   inspire  ...  [0.05667409673333168, -0.02952421084046364, -0...
1   inspire  ...  [0.011845439672470093, 0.008845405653119087, -...
2   inspire  ...  [0.0391249917447567, -0.0660882368683815, -0.1...
3   inspire  ...  [0.0076184929348528385, -0.0359916090965271, -...
4   inspire  ...  [0.04250592365860939, -0.03686268627643585, -0...
..      ...  ...                                                ...
81   prompt  ...  [-0.014272868633270264, 0.023768790066242218, ...
82   nettle  ...  [-0.02215682715177536, -0.00010512269363971427...
83   nettle  ...  [-0.005328505765646696, -0.00879666954278946, ...
84   nettle  ...  [0.01180578675121069, -0.04750848188996315, -0...
85   nettle  ...  [0.02716865763068199, -0.03534795343875885, -0...

[86 rows x 3 columns],
    'words_remaining': [],
    'workflow_instructions': '**Instructions**\n'
                             '\n'
                             'use "setup_puzzle" tool to initialize the puzzle '
                             'if the "puzzle_status" is not initialized.\n'
                             '\n'
                             'if "puzzle_step" is "puzzle_completed" then use '
                             '"END" tool.\n'
                             '\n'
                             'Use the table to select the appropriate tool.\n'
                             '\n'
                             '|puzzle_recommender| puzzle_step | tool |\n'
                             '| --- | --- | --- |\n'
                             '|embedvec_recommender| next_recommendation | '
                             'get_embedvec_recommendation |\n'
                             '|embedvec_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '|llm_recommender| next_recommendation | '
                             'get_recommendation |\n'
                             '|llm_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '\n'
                             'If no tool is selected, use "ABORT" tool.\n'}
```

### Solved Connection Puzzle 3
**Expected Solution**
```text
🟡 RUMMAGE: COMB ,DIG ,ROOT ,SIFT

🟢 SOUNDS OF THUNDER: CLAP ,PEAL ,ROLL ,RUMBLE

🔵 WAYS TO WEAR YOUR HAIR UP: BUN ,BRAID ,PONY ,TWIST

🟣 THINGS THAT CAN HAVE LEAVES: BOOK ,SALAD ,TABLE ,TREE
```

**Example Run**
```text
$ python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: file
Please enter the word file location: data/word_list4.txt
Puzzle Words: ['rumble', 'table', 'pony', 'sift', 'roll', 'bun', 'tree', 'twist', 'salad', 'clap', 'comb', 'peal', 'dig', 'braid', 'root', 'book']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(120, 120)
(120, 120)
candidate_lists size: 74

RECOMMENDED WORDS ['comb', 'dig', 'root', 'sift'] with connection All words are connected by the theme of searching or examining thoroughly.
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['comb', 'dig', 'root', 'sift'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(93, 93)
(93, 93)
candidate_lists size: 38

RECOMMENDED WORDS ['braid', 'bun', 'roll', 'twist'] with connection The group is connected by the theme of hairstyles, as all words can describe different hair arrangements or styles.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['braid', 'bun', 'roll', 'twist'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['clap', 'peal', 'roll', 'rumble'] with connection types of sounds
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['peal', 'clap', 'rumble', 'roll'] is correct

RECOMMENDED WORDS ['book', 'salad', 'table', 'tree'] with connection Types of leaves (tree leaf, salad leaf, table leaf, and book leaf)
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['tree', 'salad', 'table', 'book'] is correct

RECOMMENDED WORDS ['braid', 'bun', 'pony', 'twist'] with connection types of hairstyles
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['pony', 'braid', 'bun', 'twist'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_count': 4,
    'found_purple': True,
    'found_yellow': True,
    'invalid_connections': [['braid', 'bun', 'roll', 'twist']],
    'llm_temperature': 0.7,
    'mistake_count': 1,
    'puzzle_recommender': 'llm_recommender',
    'puzzle_status': 'initialized',
    'puzzle_step': 'puzzle_completed',
    'recommendation_count': 5,
    'recommended_connection': '',
    'recommended_correct': False,
    'recommended_words': [],
    'tool_to_use': 'END',
    'vocabulary_df':        word  ...                                          embedding
0    rumble  ...  [0.007194223813712597, -0.03427945449948311, -...
1    rumble  ...  [-0.012329446151852608, -0.012000261805951595,...
2    rumble  ...  [0.0026637613773345947, -0.020794421434402466,...
3    rumble  ...  [0.006952341180294752, -0.049337465316057205, ...
4    rumble  ...  [0.047436319291591644, 0.011532682925462723, -...
..      ...  ...                                                ...
115    book  ...  [-0.023059912025928497, -0.04290644824504852, ...
116    book  ...  [-0.017393656075000763, -0.04099489748477936, ...
117    book  ...  [-0.009654626250267029, -0.027533341199159622,...
118    book  ...  [0.013451640494167805, -0.033327944576740265, ...
119    book  ...  [0.011979937553405762, -0.0443277433514595, -0...

[93 rows x 3 columns],
    'words_remaining': [],
    'workflow_instructions': '**Instructions**\n'
                             '\n'
                             'use "setup_puzzle" tool to initialize the puzzle '
                             'if the "puzzle_status" is not initialized.\n'
                             '\n'
                             'if "puzzle_step" is "puzzle_completed" then use '
                             '"END" tool.\n'
                             '\n'
                             'Use the table to select the appropriate tool.\n'
                             '\n'
                             '|puzzle_recommender| puzzle_step | tool |\n'
                             '| --- | --- | --- |\n'
                             '|embedvec_recommender| next_recommendation | '
                             'get_embedvec_recommendation |\n'
                             '|embedvec_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '|llm_recommender| next_recommendation | '
                             'get_recommendation |\n'
                             '|llm_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '\n'
                             'If no tool is selected, use "ABORT" tool.\n'}
```

### Solved Connection Puzzle 4
This puzzle is defined by the image from the NYT Connection Puzzle grid for October 20, 2024.  A screenshot of the NYT online Connection Puzzle is saved to disk.  The agent reads the words from the image and solves the puzzle.

**Puzzle Grid Screenshot**

![Connection Puzzle Grid](src/agent_testbed/connection_puzzle_image.png)

**Expected Solution**

![Connection Puzzle Solution](src/agent_testbed/connection_puzzle_solution.png)

**Example Run**
```text
/usr/local/bin/python /workspaces/connection_solver/src/agent/app.py
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: src/agent_testbed/connection_puzzle_image.png

Words read from image: ['paddle', 'sew', 'row', 'story', 'oar', 'fore', 'column', 'racket', 'net', 'butt', 'feature', 'ball', 'clatter', 'table', 'ruckus', 'article']

RECOMMENDED WORDS ['oar', 'paddle', 'fore', 'row'] with connection Rowing-related terms
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['oar', 'paddle', 'fore', 'row'] is incorrect

RECOMMENDED WORDS ['oar', 'paddle', 'butt', 'ball'] with connection Parts of a Rowing Boat
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['oar', 'paddle', 'butt', 'ball'] is incorrect

RECOMMENDED WORDS ['story', 'feature', 'article', 'column'] with connection Parts of a newspaper or magazine
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['story', 'feature', 'article', 'column'] is correct

RECOMMENDED WORDS ['racket', 'ruckus', 'clatter', 'row'] with connection Noise or commotion
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['racket', 'ruckus', 'clatter', 'row'] is correct

RECOMMENDED WORDS ['net', 'table', 'ball', 'paddle'] with connection Table Tennis Terms
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['net', 'table', 'ball', 'paddle'] is correct

RECOMMENDED WORDS ['fore', 'sew', 'butt', 'oar'] with connection Homophones of numbers (four, so, but, or)
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['fore', 'sew', 'butt', 'oar'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_purple': True,
    'found_yellow': True,
    'input_source_type': 'image',
    'invalid_connections': [   ['oar', 'paddle', 'fore', 'row'],
                               ['oar', 'paddle', 'butt', 'ball']],
    'llm_temperature': 0.7,
    'mistake_count': 2,
    'recommendation_count': 6,
    'recommended_connection': 'Homophones of numbers (four, so, but, or)',
    'recommended_correct': True,
    'recommended_words': ['fore', 'sew', 'butt', 'oar'],
    'words_remaining': []}
```


### Failed to Solve Connection Puzzle 1
**Expected Solution**
```text
🟡 FOOTBALL POSITIONS: CENTER ,GUARD ,QUARTERBACK ,SAFETY

🟢 CABLE CHANNELS: DISCOVERY ,HISTORY ,NICKELODEON ,OXYGEN

🔵 FICTIONAL CLOWNS: HOMEY ,JOKER ,PENNYWISE ,RONALD

🟣 WHAT “D” MIGHT STAND FOR: DEFENSE ,DEMOCRAT ,DIMENSIONAL ,DRIVE
```

**Example Run**
```text 
$ python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: file
Please enter the word file location: data/word_list3.txt
Puzzle Words: ['center', 'pennywise', 'democrat', 'safety', 'oxygen', 'history', 'guard', 'homey', 'joker', 'quarterback', 'ronald', 'defense', 'discovery', 'drive', 'nickelodeon', 'dimensional']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(97, 97)
(97, 97)
candidate_lists size: 64

RECOMMENDED WORDS ['defense', 'drive', 'guard', 'safety'] with connection This group is unique as it relates to general safety and protection concepts, rather than being strictly tied to sports roles.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['defense', 'drive', 'guard', 'safety'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['discovery', 'drive', 'history', 'nickelodeon'] with connection TV Channels
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['nickelodeon', 'drive', 'discovery', 'history'] is incorrect

RECOMMENDED WORDS ['joker', 'nickelodeon', 'pennywise', 'ronald'] with connection Clowns or clown-related characters
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['joker', 'pennywise', 'ronald', 'nickelodeon'] is incorrect

RECOMMENDED WORDS ['center', 'guard', 'quarterback', 'safety'] with connection positions in American football
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['quarterback', 'center', 'guard', 'safety'] is correct

RECOMMENDED WORDS ['homey', 'joker', 'pennywise', 'ronald'] with connection Clowns
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['joker', 'pennywise', 'ronald', 'homey'] is correct

RECOMMENDED WORDS ['democrat', 'dimensional', 'discovery', 'oxygen'] with connection Words beginning with 'D'
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['oxygen', 'democrat', 'dimensional', 'discovery'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_count': 2,
    'found_yellow': True,
    'invalid_connections': [   ['defense', 'drive', 'guard', 'safety'],
                               ['nickelodeon', 'drive', 'discovery', 'history'],
                               ['joker', 'pennywise', 'ronald', 'nickelodeon'],
                               [   'oxygen',
                                   'democrat',
                                   'dimensional',
                                   'discovery']],
    'llm_temperature': 0.7,
    'mistake_count': 4,
    'puzzle_recommender': 'llm_recommender',
    'puzzle_status': 'initialized',
    'puzzle_step': 'puzzle_completed',
    'recommendation_count': 6,
    'recommended_connection': '',
    'recommended_correct': False,
    'recommended_words': [],
    'tool_to_use': 'END',
    'vocabulary_df':            word  ...                                          embedding
0        center  ...  [0.02066771127283573, -0.031914301216602325, 0...
1        center  ...  [0.005799443461000919, -0.020684584975242615, ...
2        center  ...  [0.005490818060934544, -0.012460795231163502, ...
3        center  ...  [-0.00505771953612566, 1.8607530364533886e-05,...
4        center  ...  [-0.0031464514322578907, 0.01062652189284563, ...
..          ...  ...                                                ...
92  dimensional  ...  [0.011221064254641533, -0.022305285558104515, ...
93  dimensional  ...  [0.022211303934454918, 0.007923364639282227, -...
94  dimensional  ...  [-0.02473333291709423, -0.017410408705472946, ...
95  dimensional  ...  [0.02035861276090145, 0.01731749251484871, -0....
96  dimensional  ...  [-0.005879412870854139, -0.019015125930309296,...

[97 rows x 3 columns],
    'words_remaining': [   'oxygen',
                           'democrat',
                           'dimensional',
                           'drive',
                           'defense',
                           'history',
                           'discovery',
                           'nickelodeon'],
    'workflow_instructions': '**Instructions**\n'
                             '\n'
                             'use "setup_puzzle" tool to initialize the puzzle '
                             'if the "puzzle_status" is not initialized.\n'
                             '\n'
                             'if "puzzle_step" is "puzzle_completed" then use '
                             '"END" tool.\n'
                             '\n'
                             'Use the table to select the appropriate tool.\n'
                             '\n'
                             '|puzzle_recommender| puzzle_step | tool |\n'
                             '| --- | --- | --- |\n'
                             '|embedvec_recommender| next_recommendation | '
                             'get_embedvec_recommendation |\n'
                             '|embedvec_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '|llm_recommender| next_recommendation | '
                             'get_recommendation |\n'
                             '|llm_recommender| have_recommendation | '
                             'apply_recommendation |\n'
                             '\n'
                             'If no tool is selected, use "ABORT" tool.\n'}
```

### Failed to Solve Connection Puzzle 2
**Expected Solution**
```text
🟡 GRASSY AREA: GREEN ,LAWN ,PARK ,YARD

🟢 DEAL WITH: ADDRESS ,ANSWER ,FIELD ,HANDLE

🔵 MOVIES WITH “S” REMOVED: CAR ,GOODFELLA ,JAW ,SWINGER

🟣 ___ LAW: CRIMINAL ,HARVARD ,LEMON ,NATURAL
```

**Example Run**
```text
/usr/local/bin/python /workspaces/connection_solver/src/agent/app.py
Please enter the file location: data/word_list1.txt

Words read from file: ['goodfella', 'jaw', 'answer', 'handle', 'park', 'lemon', 'yard', 'field', 'natural', 'car', 'harvard', 'swinger', 'green', 'criminal', 'address', 'lawn']

RECOMMENDED WORDS ['park', 'lawn', 'field', 'yard'] with connection Outdoor spaces
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['park', 'lawn', 'field', 'yard'] is incorrect

RECOMMENDED WORDS ['lawn', 'yard', 'handle', 'jaw'] with connection Parts of a Tool
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['lawn', 'yard', 'handle', 'jaw'] is incorrect

RECOMMENDED WORDS ['answer', 'address', 'field', 'park'] with connection Things related to location or response
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['answer', 'address', 'field', 'park'] is incorrect

RECOMMENDED WORDS ['lawn', 'green', 'lemon', 'natural'] with connection Things that are green
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['lawn', 'green', 'lemon', 'natural'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!


FINAL PUZZLE STATE:
{   'found_blue': False,
    'found_purple': False,
    'found_yellow': False,
    'invalid_connections': [   ['park', 'lawn', 'field', 'yard'],
                               ['lawn', 'yard', 'handle', 'jaw'],
                               ['answer', 'address', 'field', 'park'],
                               ['lawn', 'green', 'lemon', 'natural']],
    'llm_temperature': 0.7,
    'mistake_count': 4,
    'recommendation_count': 4,
    'recommended_connection': 'Things that are green',
    'recommended_correct': False,
    'recommended_words': ['lawn', 'green', 'lemon', 'natural'],
    'words_remaining': [   'lawn',
                           'park',
                           'address',
                           'swinger',
                           'answer',
                           'field',
                           'lemon',
                           'yard',
                           'jaw',
                           'handle',
                           'goodfella',
                           'car',
                           'criminal',
                           'green',
                           'harvard',
                           'natural']}
```

## `langsmith` tracing

The `langsmith` tracing tool was used to trace the agent's workflow.  Here is an example trace of the agent solving a Connection Puzzle.:

![](./images/example_langsmith_trace.png)

## Future Work
* Implement automated testing
* Implement experiment tracking
* Experiment...experiment...experiment
  * alternative prompts (color code?), LLM settings, e.g., temperature, top-k, top-p
  * Handle "one away" responses, where 3 of the 4 words are correct
  * RAG-based approach
* Enhance Planner, rationalize workflow design
* Incorporate more `langchain` concepts around "tools"

## Academic References

* Merino, et al, _Making New Connections: LLMs as Puzzle Generators for The New York Times' Connections Word Game_, 2024, https://arxiv.org/abs/2407.11240