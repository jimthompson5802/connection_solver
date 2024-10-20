# Connection Solver Virtual Assistant Testbed

Experimental project to determine how to use GPT4 to solve the NYT Connection puzzles

## Sample Runs

### Solved Connection Puzzle
**Solution**
```text
🟡 MAKE GOOD ON, AS A PROMISE: FULFILL ,HONOR ,KEEP ,UPHOLD

🟢 BEDDING: BLANKET ,SHAM ,SHEET ,THROW

🔵 ACTIONS IN CARD GAMES: DISCARD ,DRAW ,PASS ,PLAY

🟣 CABINET DEPARTMENTS: ENERGY ,JUSTICE ,LABOR ,STATE
```
**Example Run**
```text
$ /usr/local/bin/python /workspaces/connection_solver/src/agent/app.py
Please enter the file location: data/word_list5.txt

RECOMMENDED WORDS ['blanket', 'throw', 'sham', 'sheet'] with connection Bedding items
Is the recommendation accepted? (y/g/b/p/n): g
Recommendation ['blanket', 'throw', 'sham', 'sheet'] is correct

RECOMMENDED WORDS ['keep', 'uphold', 'honor', 'fulfill'] with connection Actions associated with maintaining or supporting something
Is the recommendation accepted? (y/g/b/p/n): y
Recommendation ['keep', 'uphold', 'honor', 'fulfill'] is correct

RECOMMENDED WORDS ['state', 'labor', 'energy', 'justice'] with connection Departments of the US Government
Is the recommendation accepted? (y/g/b/p/n): p
Recommendation ['state', 'labor', 'energy', 'justice'] is correct

RECOMMENDED WORDS ['discard', 'play', 'pass', 'draw'] with connection Card Game Actions
Is the recommendation accepted? (y/g/b/p/n): b
Recommendation ['discard', 'play', 'pass', 'draw'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{   'found_blue': True,
    'found_purple': True,
    'found_yellow': True,
    'invalid_connections': [],
    'llm_temperature': 0.7,
    'mistake_count': 0,
    'recommendation_count': 4,
    'recommended_connection': 'Card Game Actions',
    'recommended_correct': True,
    'recommended_words': ['discard', 'play', 'pass', 'draw'],
    'words_remaining': []}
```

### Failed to Solve Connection Puzzle
**Solution**
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

RECOMMENDED WORDS ['quarterback', 'safety', 'center', 'defense'] with connection Football positions
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['quarterback', 'safety', 'center', 'defense'] is incorrect

RECOMMENDED WORDS ['quarterback', 'safety', 'guard', 'defense'] with connection Football Positions
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['quarterback', 'safety', 'guard', 'defense'] is incorrect

RECOMMENDED WORDS ['quarterback', 'center', 'guard', 'joker'] with connection Positions and roles in sports and entertainment
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['quarterback', 'center', 'guard', 'joker'] is incorrect

RECOMMENDED WORDS ['nickelodeon', 'oxygen', 'homey', 'discovery'] with connection Television Channels
Is the recommendation accepted? (y/g/b/p/n): n
Recommendation ['nickelodeon', 'oxygen', 'homey', 'discovery'] is incorrect
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!


FINAL PUZZLE STATE:
{   'found_blue': False,
    'found_purple': False,
    'found_yellow': False,
    'invalid_connections': [   ['quarterback', 'safety', 'center', 'defense'],
                               ['quarterback', 'safety', 'guard', 'defense'],
                               ['quarterback', 'center', 'guard', 'joker'],
                               ['nickelodeon', 'oxygen', 'homey', 'discovery']],
    'llm_temperature': 0.7,
    'mistake_count': 4,
    'recommendation_count': 1,
    'recommended_connection': 'Television Channels',
    'recommended_correct': False,
    'recommended_words': ['nickelodeon', 'oxygen', 'homey', 'discovery'],
    'words_remaining': [   'ronald',
                           'pennywise',
                           'joker',
                           'oxygen',
                           'homey',
                           'center',
                           'dimensional',
                           'safety',
                           'democrat',
                           'drive',
                           'quarterback',
                           'discovery',
                           'history',
                           'defense',
                           'nickelodeon',
                           'guard']}
```