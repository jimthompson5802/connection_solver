# Connection Solver Virtual Assistant Testbed

Experimental project to solve the [NYT Connection puzzles](https://www.nytimes.com/games/connections) using agentic workflow based on the [`langchain` ecosystem](https://python.langchain.com/v0.2/docs/introduction/).  In particular used:
* [`langchain`'s OpenAI LLM abstraction layer](https://python.langchain.com/v0.2/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html#chatopenai) to interact with OpenAI's `gpt-4o` model
* [`langgraph`'s stateful orchestration framework](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/#multi-agent-network) to manage the agent's workflow

Historical NYT Connection Puzzles were used in testing the agent.  Past puzzles can be found [here](https://word.tips/todays-nyt-connections-answers/).

## Connection Puzzle Description
Connections is a word game that challenges players to find themes between words. The user is presented with 16 words and must create groups of four items that share something in common. For example: Tropical fruit: banana, mango, pineapple, guava.

## Solution Strategy
The agent uses the `PuzzleState` class to manage the agent's state and controls the agent's workflow. 
```python
class PuzzleState(TypedDict):
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
    recommendation_count: int = 0
    llm_temperature: float = 1.0
```
The attributes `words_remaining` and `mistake_count` are used to determine when to terminate the agent.  When a correct group of 4 words are found, these words are removed from `words_remaining`.  If a mistake is made, then `mistake_count` is incremented.  The agent is terminated when either `words_reamaining` becomes empty or  `mistake_count` exceeds a threshold.

Agent's workflow defintion:
```python
    workflow = StateGraph(PuzzleState)

    workflow.add_node("read_words_from_file", read_words_from_file)
    workflow.add_node("get_recommendation", get_recommendation)
    workflow.add_node("regenerate_recommendation", regenerate_recommendation)
    workflow.add_node("apply_recommendation", apply_recommendation)
    workflow.add_node("clear_recommendation", clear_recommendation)

    workflow.add_edge("read_words_from_file", "get_recommendation")
    workflow.add_edge("get_recommendation", "apply_recommendation")
    workflow.add_edge("clear_recommendation", "get_recommendation")
    workflow.add_edge("regenerate_recommendation", "apply_recommendation")
    workflow.add_conditional_edges(
        "apply_recommendation",
        is_end,
        {
            END: END,
            "clear_recommendation": "clear_recommendation",
            "regenerate_recommendation": "regenerate_recommendation",
        },
    )

    workflow.set_entry_point("read_words_from_file")

    app = workflow.compile()
```

Diagram of the agent's workflow:
![Connection Solver Workflow](./images/connection_solver_graph.png)


## Sample Runs

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
/usr/local/bin/python /workspaces/connection_solver/src/agent/app.py
Please enter the file location: data/word_list5.txt

Words read from file: ['uphold', 'discard', 'honor', 'energy', 'state', 'play', 'justice', 'labor', 'pass', 'fulfill', 'draw', 'keep', 'blanket', 'sham', 'sheet', 'throw']

RECOMMENDED WORDS ['blanket', 'sheet', 'sham', 'throw'] with connection bedding items
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['blanket', 'sheet', 'sham', 'throw'] is correct

RECOMMENDED WORDS ['play', 'discard', 'draw', 'pass'] with connection Card game actions
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['play', 'discard', 'draw', 'pass'] is correct

RECOMMENDED WORDS ['honor', 'uphold', 'keep', 'fulfill'] with connection ways to maintain or adhere to something (e.g., a promise, duty)
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['honor', 'uphold', 'keep', 'fulfill'] is correct

RECOMMENDED WORDS ['energy', 'state', 'justice', 'labor'] with connection Departments of the US Government
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['energy', 'state', 'justice', 'labor'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_purple': True,
    'found_yellow': True,
    'invalid_connections': [],
    'llm_temperature': 0.7,
    'mistake_count': 0,
    'recommendation_count': 4,
    'recommended_connection': 'Departments of the US Government',
    'recommended_correct': True,
    'recommended_words': ['energy', 'state', 'justice', 'labor'],
    'words_remaining': []}
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
/usr/local/bin/python /workspaces/connection_solver/src/agent/app.py
Please enter the file location: data/word_list2.txt

Words read from file: ['inspire', 'madden', 'jellyfish', 'metroid', 'insult', 'candle', 'halo', 'provoke', 'soap', 'generate', 'incense', 'civilization', 'lotion', 'wasp', 'prompt', 'nettle']

RECOMMENDED WORDS ['prompt', 'provoke', 'insult', 'inspire'] with connection Words related to stimulation or incitement
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['prompt', 'provoke', 'insult', 'inspire'] is incorrect

RECOMMENDED WORDS ['candle', 'lotion', 'soap', 'incense'] with connection Items related to fragrance or cleansing
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['candle', 'lotion', 'soap', 'incense'] is correct

RECOMMENDED WORDS ['madden', 'provoke', 'nettle', 'insult'] with connection to annoy or irritate
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['madden', 'provoke', 'nettle', 'insult'] is incorrect

RECOMMENDED WORDS ['generate', 'prompt', 'inspire', 'provoke'] with connection Words related to causing action or reaction
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['generate', 'prompt', 'inspire', 'provoke'] is correct

RECOMMENDED WORDS ['halo', 'metroid', 'civilization', 'madden'] with connection Video Game Titles
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['halo', 'metroid', 'civilization', 'madden'] is correct

RECOMMENDED WORDS ['wasp', 'jellyfish', 'nettle', 'insult'] with connection They all sting or hurt
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['wasp', 'jellyfish', 'nettle', 'insult'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_purple': True,
    'found_yellow': True,
    'invalid_connections': [   ['prompt', 'provoke', 'insult', 'inspire'],
                               ['madden', 'provoke', 'nettle', 'insult']],
    'llm_temperature': 0.7,
    'mistake_count': 2,
    'recommendation_count': 4,
    'recommended_connection': 'They all sting or hurt',
    'recommended_correct': True,
    'recommended_words': ['wasp', 'jellyfish', 'nettle', 'insult'],
    'words_remaining': []}
```

### Failed to Solve Connection Puzzle
**Expected Solution**
```text
🟡 FOOTBALL POSITIONS: CENTER ,GUARD ,QUARTERBACK ,SAFETY

🟢 CABLE CHANNELS: DISCOVERY ,HISTORY ,NICKELODEON ,OXYGEN

🔵 FICTIONAL CLOWNS: HOMEY ,JOKER ,PENNYWISE ,RONALD

🟣 WHAT “D” MIGHT STAND FOR: DEFENSE ,DEMOCRAT ,DIMENSIONAL ,DRIVE
```

**Example Run**
```text 
/usr/local/bin/python /workspaces/connection_solver/src/agent/app.py
Please enter the file location: data/word_list3.txt

Words read from file: ['center', 'pennywise', 'democrat', 'safety', 'oxygen', 'history', 'guard', 'homey', 'joker', 'quarterback', 'ronald', 'defense', 'discovery', 'drive', 'nickelodeon', 'dimensional']

RECOMMENDED WORDS ['quarterback', 'center', 'safety', 'guard'] with connection Football positions
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['quarterback', 'center', 'safety', 'guard'] is correct

RECOMMENDED WORDS ['joker', 'democrat', 'ronald', 'pennywise'] with connection Clown or clown-like characters
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['joker', 'democrat', 'ronald', 'pennywise'] is incorrect

RECOMMENDED WORDS ['ronald', 'nickelodeon', 'discovery', 'homey'] with connection Television Networks/Shows
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['ronald', 'nickelodeon', 'discovery', 'homey'] is incorrect

RECOMMENDED WORDS ['nickelodeon', 'discovery', 'drive', 'dimensional'] with connection TV Channels
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['nickelodeon', 'discovery', 'drive', 'dimensional'] is incorrect

RECOMMENDED WORDS ['ronald', 'joker', 'pennywise', 'nickelodeon'] with connection Fictional Characters/Brands Associated with Entertainment
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['ronald', 'joker', 'pennywise', 'nickelodeon'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!


FINAL PUZZLE STATE:
{   'found_blue': False,
    'found_purple': False,
    'found_yellow': True,
    'invalid_connections': [   ['joker', 'democrat', 'ronald', 'pennywise'],
                               ['ronald', 'nickelodeon', 'discovery', 'homey'],
                               [   'nickelodeon',
                                   'discovery',
                                   'drive',
                                   'dimensional'],
                               ['ronald', 'joker', 'pennywise', 'nickelodeon']],
    'llm_temperature': 0.7,
    'mistake_count': 4,
    'recommendation_count': 2,
    'recommended_connection': 'Fictional Characters/Brands Associated with '
                              'Entertainment',
    'recommended_correct': False,
    'recommended_words': ['ronald', 'joker', 'pennywise', 'nickelodeon'],
    'words_remaining': [   'ronald',
                           'dimensional',
                           'history',
                           'democrat',
                           'joker',
                           'pennywise',
                           'discovery',
                           'drive',
                           'nickelodeon',
                           'defense',
                           'homey',
                           'oxygen']}
```