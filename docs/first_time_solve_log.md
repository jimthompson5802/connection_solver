# Log for First Time Solves
## Agent with Embeddings Results for First Time Live Game

|Date|Agent Tag|Solved|Correct Groups|Mistakes|NYT Difficulty Rating (out of 5)|Comments|
|---|:---:|:---:|:---:|:---:|:---:|---|
|2024-11-12|v0.5.0|Yes|4|1|2?||
|2024-11-13|v0.5.0|Yes|4|0|3||
|2024-11-14|v0.5.0|No|0|4|3|3 of the 4 errors were "one away"|
|2024-11-15|v0.5.0|No|2|4|3|two "one away" errors, NCPA stuck in repeating previous invalid group|
|2024-11-16|v0.5.0|No|2|4|5|2 one away mistakes|
|2024-11-17|v0.5.0|Yes with manual assist|2|2|4|2 one aways mistakes, repeated previous incorrect guess, manual override to solve puzzle|

## Transcript
### 2024-11-12
```text
python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: data/connection_puzzle_2024_11_12.png
Puzzle Words: ['ram', 'robe', 'clove', 'crab', 'sword', 'speed', 'scales', 'spear', 'bellyache', 'blindfold', 'storage', 'carp', 'stalk', 'grumble', 'resolution', 'floret']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(88, 88)
(88, 88)
candidate_lists size: 61

RECOMMENDED WORDS ['bellyache', 'carp', 'crab', 'grumble'] with connection All words relate to complaining or expressing dissatisfaction.
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['bellyache', 'carp', 'crab', 'grumble'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(67, 67)
(67, 67)
candidate_lists size: 46

RECOMMENDED WORDS ['clove', 'floret', 'spear', 'stalk'] with connection Connected by a plant theme, focusing on plant parts or structures.
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['clove', 'floret', 'spear', 'stalk'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(49, 49)
(49, 49)
candidate_lists size: 25

RECOMMENDED WORDS ['resolution', 'scales', 'speed', 'storage'] with connection All words relate to technical or digital concepts and measurements.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['resolution', 'scales', 'speed', 'storage'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['blindfold', 'robe', 'scales', 'sword'] with connection Items associated with justice or a judge
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['blindfold', 'scales', 'sword', 'robe'] is correct

RECOMMENDED WORDS ['ram', 'resolution', 'speed', 'storage'] with connection Computer Specifications
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['ram', 'speed', 'resolution', 'storage'] is correct
SOLVED THE CONNECTION PUZZLE!!!
```
### 2024-11-13
```text
python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: /desktop/Screenshot-2024-11-13-at-04.10.17.png
Puzzle Words: ['mustard', 'wing', 'wednesday', 'worcestershire', 'colonel', 'tartar', 'lemon', 'minion', 'calculus', 'canary', 'addition', 'plaque', 'extension', 'pharaoh', 'cavity', 'annex']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(90, 90)
(90, 90)
candidate_lists size: 45

RECOMMENDED WORDS ['calculus', 'cavity', 'plaque', 'tartar'] with connection These words are all related to dental and oral health issues.
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['calculus', 'cavity', 'plaque', 'tartar'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(69, 69)
(69, 69)
candidate_lists size: 29

RECOMMENDED WORDS ['addition', 'annex', 'extension', 'wing'] with connection All four words relate to architectural elements or parts of a building that are added to increase space or functionality.
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['addition', 'annex', 'extension', 'wing'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(37, 37)
(37, 37)
candidate_lists size: 17

RECOMMENDED WORDS ['canary', 'lemon', 'minion', 'mustard'] with connection These words are connected by the theme of the color yellow.
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['canary', 'lemon', 'minion', 'mustard'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(14, 14)
(14, 14)
candidate_lists size: 1

RECOMMENDED WORDS ['colonel', 'pharaoh', 'wednesday', 'worcestershire'] with connection No single theme or concept connects the words; chosen due to highest group metric.
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['colonel', 'pharaoh', 'wednesday', 'worcestershire'] is correct
SOLVED THE CONNECTION PUZZLE!!!

```

### 2024-11-14
```text
 python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: /desktop/Screenshot-2024-11-14-at-06.08.24.png
Puzzle Words: ['grain', 'drain', 'total', 'cube', 'syrup', 'shred', 'signature', 'sap', 'jam', 'tax', 'powder', 'rock', 'empty', 'groove', 'tip', 'exhaust']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(122, 122)
(122, 122)
candidate_lists size: 83

RECOMMENDED WORDS ['cube', 'grain', 'powder', 'shred'] with connection These words all relate to forms or methods of reducing or processing materials.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['cube', 'grain', 'powder', 'shred'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['drain', 'groove', 'jam', 'rock'] with connection Music-related terms
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['jam', 'groove', 'rock', 'drain'] is incorrect

RECOMMENDED WORDS ['drain', 'jam', 'sap', 'syrup'] with connection Things that can flow
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['syrup', 'sap', 'jam', 'drain'] is incorrect

RECOMMENDED WORDS ['grain', 'powder', 'sap', 'syrup'] with connection Substances
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['syrup', 'sap', 'powder', 'grain'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!
```

### 2024-11-15
```text
python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: /desktop/Screenshot-2024-11-15-at-05.40.47.png
Puzzle Words: ['pipe', 'phrase', 'jug', 'passage', 'leak', 'letter', 'waste', 'whistle', 'nick', 'crack', 'recorder', 'word', 'hole', 'sands', 'sentence', 'puncture']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(117, 117)
(117, 117)
candidate_lists size: 80

RECOMMENDED WORDS ['passage', 'phrase', 'sentence', 'word'] with connection This group is uniquely thematically connected by language and text structure.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['passage', 'phrase', 'sentence', 'word'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['jug', 'pipe', 'recorder', 'whistle'] with connection Musical instruments or devices that produce sound
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['whistle', 'pipe', 'jug', 'recorder'] is correct

RECOMMENDED WORDS ['crack', 'hole', 'leak', 'puncture'] with connection Ways things can be damaged or let things through
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['leak', 'hole', 'crack', 'puncture'] is correct

RECOMMENDED WORDS ['letter', 'nick', 'sands', 'waste'] with connection Four-letter words
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['nick', 'waste', 'sands', 'letter'] is incorrect

<<<AT THIS POINT NCPA REPEATED PREVIOUS INVALID GUESS, HAD TO MANUALLY SELECT OTHER WORDS ALLOW PROGRESS>>>

RECOMMENDED WORDS ['passage', 'phrase', 'sentence', 'word'] with connection Linguistic components
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['passage', 'phrase', 'sentence', 'word'] is incorrect

RECOMMENDED WORDS ['letter', 'nick', 'sands', 'waste'] with connection four-letter words
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['nick', 'waste', 'sands', 'letter'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!
```

### 2024-11-16
```text
python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: /desktop/connection_puzzle_2024_11_16.png
Puzzle Words: ['rogue', 'cap', 'gator', 'seal', 'beret', 'wolverine', 'commando', 'figure', 'volunteer', 'derby', 'pillbox', 'cover', 'plug', 'snapback', 'sooner', 'bananas']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(103, 103)
(103, 103)
candidate_lists size: 64

RECOMMENDED WORDS ['cap', 'cover', 'plug', 'seal'] with connection These words are connected by the theme of closing or covering an opening or surface.
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['cap', 'cover', 'plug', 'seal'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(64, 64)
(64, 64)
candidate_lists size: 39

RECOMMENDED WORDS ['beret', 'derby', 'pillbox', 'snapback'] with connection All four words are types of hats.
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['beret', 'derby', 'pillbox', 'snapback'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(46, 46)
(46, 46)
candidate_lists size: 23

RECOMMENDED WORDS ['bananas', 'commando', 'rogue', 'volunteer'] with connection The words have a playful and informal theme, often used to describe unconventional or unexpected behavior or actions.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['bananas', 'commando', 'rogue', 'volunteer'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['figure', 'gator', 'sooner', 'wolverine'] with connection University sports team mascots
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['sooner', 'figure', 'gator', 'wolverine'] is incorrect

RECOMMENDED WORDS ['commando', 'gator', 'rogue', 'wolverine'] with connection Military or Aggressive Themes
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['rogue', 'commando', 'wolverine', 'gator'] is incorrect

RECOMMENDED WORDS ['bananas', 'figure', 'sooner', 'volunteer'] with connection Informal terms for people or things
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['sooner', 'figure', 'volunteer', 'bananas'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!
```

### 2024-11-17
```text
 python src/agent/app_embedvec.py 
Enter 'file' to read words from a file or 'image' to read words from an image: image
Please enter the image file location: data/connection_puzzle_2024_11_17.png
Puzzle Words: ['apology', 'quotation', 'association', 'contraction', 'clingy', 'union', 'possessive', 'slinky', 'proposal', 'snug', 'prayer', 'league', 'guild', 'dubbing', 'foot', 'sleek']

Generating vocabulary for the words...this may take about a minute

Generating embeddings for the definitions

ENTERED EMBEDVEC RECOMMENDATION
(83, 83)
(83, 83)
candidate_lists size: 48

RECOMMENDED WORDS ['association', 'guild', 'league', 'union'] with connection All four words represent types of organizations or groups formed by people for a common purpose or interest.
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['association', 'guild', 'league', 'union'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(61, 61)
(61, 61)
candidate_lists size: 33

RECOMMENDED WORDS ['clingy', 'sleek', 'slinky', 'snug'] with connection The words are connected by the theme of clothing or fabric characteristics, specifically how they fit or appear.
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['clingy', 'sleek', 'slinky', 'snug'] is correct

ENTERED EMBEDVEC RECOMMENDATION
(45, 45)
(45, 45)
candidate_lists size: 24

RECOMMENDED WORDS ['apology', 'prayer', 'proposal', 'quotation'] with connection These words are connected by the theme of formal communication or expression.
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['apology', 'prayer', 'proposal', 'quotation'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

RECOMMENDED WORDS ['contraction', 'dubbing', 'foot', 'possessive'] with connection Linguistic terms
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['foot', 'dubbing', 'possessive', 'contraction'] is incorrect

RECOMMENDED WORDS ['apology', 'prayer', 'proposal', 'quotation'] with connection Types of speeches or formal statements
Is the recommendation accepted? (y/g/b/p/n): ^CTraceback (most recent call last):
  File "/workspaces/connection_solver/src/agent/app_embedvec.py", line 318, in <module>
    result = app.invoke(initial_state, {"recursion_limit": 50})
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1586, in invoke
    for chunk in self.stream(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1315, in stream
    for _ in runner.tick(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/runner.py", line 56, in tick
    run_with_retry(t, retry_policy)
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 29, in run_with_retry
    task.proc.invoke(task.input, config)
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 410, in invoke
    input = context.run(step.invoke, input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 184, in invoke
    ret = context.run(self.func, input, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec.py", line 164, in apply_recommendation
    found_correct_group = interact_with_user(sorted(state["recommended_words"]), state["recommended_connection"])
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/tools.py", line 151, in interact_with_user
    user_response = input(user_instruction)
                    ^^^^^^^^^^^^^^^^^^^^^^^
KeyboardInterrupt
```