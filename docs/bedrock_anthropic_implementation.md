
## First run of the Connection Solver Agent with the Bedrock Anthropic LLM Interface
```text
/workspaces/connection_solver/src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface bedrock_anthropic 
Running Connection Solver Agent Tester 0.16.0-dev-bedrock

>>>>SOLVING PUZZLE 1
LLMBedrockAnthropicInterface __init__
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 
Processing word: nets
Processing word: return
Processing word: heat
Processing word: jazz
Processing word: mom
Processing word: shift
Processing word: kayak
Processing word: option
Processing word: rain
Processing word: sleet
Processing word: level
Processing word: racecar
Processing word: bucks
Processing word: tab
Processing word: hail
Processing word: snow
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/runpy.py", line 198, in _run_module_as_main
    return _run_code(code, main_globals, None,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/runpy.py", line 88, in _run_code
    exec(code, run_globals)
  File "/home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher/../../debugpy/__main__.py", line 71, in <module>
    cli.main()
  File "/home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher/../../debugpy/../debugpy/server/cli.py", line 501, in main
    run()
  File "/home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher/../../debugpy/../debugpy/server/cli.py", line 351, in run_file
    runpy.run_path(target, run_name="__main__")
  File "/home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/_vendored/pydevd/_pydevd_bundle/pydevd_runpy.py", line 310, in run_path
    return _run_module_code(code, init_globals, run_name, pkg_name=pkg_name, script_name=fname)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/_vendored/pydevd/_pydevd_bundle/pydevd_runpy.py", line 127, in _run_module_code
    _run_code(code, mod_globals, init_globals, mod_name, mod_spec, pkg_name, script_name)
  File "/home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/_vendored/pydevd/_pydevd_bundle/pydevd_runpy.py", line 118, in _run_code
    exec(code, run_globals)
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 184, in <module>
    results = asyncio.run(main(None, check_one_solution))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 176, in main
    found_solutions = await asyncio.gather(
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 163, in solve_a_puzzle
    result = await run_workflow(
             ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/workflow_manager.py", line 120, in run_workflow
    async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1899, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/runner.py", line 370, in atick
    await arun_with_retry(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 128, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 485, in ainvoke
    input = await step.ainvoke(input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 275, in ainvoke
    ret = await asyncio.create_task(coro, context=context)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 136, in setup_puzzle
    vocabulary = await config["configurable"]["llm_interface"].generate_vocabulary(state["words_remaining"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/bedrock_anthropic_tools.py", line 136, in generate_vocabulary
    await asyncio.gather(*[process_word(word) for word in words])
  File "/workspaces/connection_solver/src/agent/bedrock_anthropic_tools.py", line 133, in process_word
    result = await structured_llm.ainvoke(prompt)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/runnables/base.py", line 3064, in ainvoke
    input = await asyncio.create_task(part(), context=context)  # type: ignore
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/runnables/base.py", line 5364, in ainvoke
    return await self.bound.ainvoke(
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 307, in ainvoke
    llm_result = await self.agenerate_prompt(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 796, in agenerate_prompt
    return await self.agenerate(
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 756, in agenerate
    raise exceptions[0]
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 924, in _agenerate_with_cache
    result = await self._agenerate(
             ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 964, in _agenerate
    return await run_in_executor(
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/runnables/config.py", line 588, in run_in_executor
    return await asyncio.get_running_loop().run_in_executor(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/runnables/config.py", line 579, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_aws/chat_models/bedrock.py", line 570, in _generate
    completion, tool_calls, llm_output = self._prepare_input_and_invoke(
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_aws/llms/bedrock.py", line 841, in _prepare_input_and_invoke
    raise e
  File "/usr/local/lib/python3.11/site-packages/langchain_aws/llms/bedrock.py", line 827, in _prepare_input_and_invoke
    response = self.client.invoke_model(**request_options)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/botocore/client.py", line 569, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/botocore/client.py", line 1023, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.errorfactory.ThrottlingException: An error occurred (ThrottlingException) when calling the InvokeModel operation (reached max retries: 4): Too many requests, please wait before trying again.
During task with name 'setup_puzzle' and id 'f4ec9627-49f2-1ace-878b-7ca1e573db1d'
``` 

## Successfully solved test puzzle with Anthropic Claude Sonnet v1 LLM
Had to insert a bunch of asynio.sleep(8.0) before each call to LLM to avoid the ThrottlingException.
Need to work out a more robust solution for this.

```text
/workspaces/connection_solver/src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface bedrock_anthropic 
Running Connection Solver Agent Tester 0.16.0-dev-bedrock

>>>>SOLVING PUZZLE 1
LLMBedrockAnthropicInterface __init__
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 
Processing word: nets
Processing word: return
Processing word: heat
Processing word: jazz
Processing word: mom
Processing word: shift
Processing word: kayak
Processing word: option
Processing word: rain
Processing word: sleet
Processing word: level
Processing word: racecar
Processing word: bucks
Processing word: tab
Processing word: hail
Processing word: snow

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(146, 146)
(146, 146)
candidate_lists size: 98

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['hail', 'rain', 'sleet', 'snow'] with connection Connected by weather precipitation theme, unique among groups
Connected by weather precipitation theme, unique among groups ~ wet weather: ['hail', 'rain', 'sleet', 'snow'] == ['hail', 'rain', 'sleet', 'snow']
Recommendation ['hail', 'rain', 'sleet', 'snow'] is correct

ENTERED EMBEDVEC_RECOMMENDER
found count: 1, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'level', 'racecar', 'bucks', 'tab']
(113, 113)
(113, 113)
candidate_lists size: 76

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['level', 'racecar', 'return', 'tab'] with connection Computer keyboard and programming concepts
Recommendation ['level', 'racecar', 'return', 'tab'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 1
attempt_count: 1
words_remaining: ['tab', 'bucks', 'racecar', 'level', 'option', 'kayak', 'shift', 'mom', 'jazz', 'heat', 'return', 'nets']

LLM_RECOMMENDER: RECOMMENDED WORDS ['kayak', 'level', 'mom', 'tab'] with connection palindromes
Recommendation ['kayak', 'level', 'mom', 'tab'] is incorrect, one away from correct

ENTERED ONE-AWAY ANALYZER
found count: 1, mistake_count: 2

>>>Number of single topic groups: 2
More than one single-topic group recommendations, selecting one at random.

>>>Selected single-topic group:
Recommended Group: ('kayak', 'level', 'mom')
Connection Description: The words 'kayak', 'level', and 'mom' can be related to a single topic: palindromes. A palindrome is a word, phrase, number, or other sequence of characters that reads the same forward and backward. All three of these words are palindromes:

1. 'kayak' - reads the same from left to right and right to left
2. 'level' - also reads the same in both directions
3. 'mom' - another word that is identical when reversed

The shared context for these words is their linguistic property of being palindromes. This characteristic is a unique and specific feature that connects all three words, despite their different meanings in everyday usage. Therefore, we can confidently say that these words relate to a single topic within the realm of wordplay and linguistics.

>>>One-away group recommendations:
one_away_group_recommendation is a new recommendation
using one_away_group_recommendation

LLM_RECOMMENDER: RECOMMENDED WORDS ['kayak', 'level', 'mom', 'racecar'] with connection The common connection among the anchor words "kayak", "level", and "mom" is that they are all palindromes - words that read the same forwards and backwards. Among the candidate words, "racecar" is the only palindrome, making it the most highly connected to the anchor words. The other candidate words do not share this unique characteristic.
The common connection among the anchor words "kayak", "level", and "mom" is that they are all palindromes - words that read the same forwards and backwards. Among the candidate words, "racecar" is the only palindrome, making it the most highly connected to the anchor words. The other candidate words do not share this unique characteristic. ~ palindromes: ['kayak', 'level', 'mom', 'racecar'] == ['kayak', 'level', 'mom', 'racecar']
Recommendation ['kayak', 'level', 'mom', 'racecar'] is correct

ENTERED LLM_RECOMMENDER
found count: 2, mistake_count: 2
attempt_count: 1
words_remaining: ['return', 'heat', 'jazz', 'bucks', 'shift', 'tab', 'option', 'nets']

LLM_RECOMMENDER: RECOMMENDED WORDS ['bucks', 'heat', 'jazz', 'nets'] with connection NBA teams
NBA teams ~ nba teams: ['bucks', 'heat', 'jazz', 'nets'] == ['bucks', 'heat', 'jazz', 'nets']
Recommendation ['bucks', 'heat', 'jazz', 'nets'] is correct

ENTERED LLM_RECOMMENDER
found count: 3, mistake_count: 2
attempt_count: 1
words_remaining: ['option', 'tab', 'shift', 'return']

LLM_RECOMMENDER: RECOMMENDED WORDS ['option', 'return', 'shift', 'tab'] with connection Computer keyboard keys
Computer keyboard keys ~ keyboard keys: ['option', 'return', 'shift', 'tab'] == ['option', 'return', 'shift', 'tab']
Recommendation ['option', 'return', 'shift', 'tab'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{'current_tool': 'llm_recommender',
 'found_count': 4,
 'invalid_connections': [['586b2ed66c8dc1d5ef800e4ccbe2820c',
                          ['level', 'racecar', 'return', 'tab']],
                         ['99dc20319614ad73c0105e4afdf264bd',
                          ['kayak', 'level', 'mom', 'tab']]],
 'llm_retry_count': 0,
 'llm_temperature': 0.7,
 'mistake_count': 2,
 'puzzle_status': 'initialized',
 'recommendation_answer_status': 'correct',
 'recommendation_correct_groups': [['hail', 'rain', 'sleet', 'snow'],
                                   ['kayak', 'level', 'mom', 'racecar'],
                                   ['bucks', 'heat', 'jazz', 'nets'],
                                   ['option', 'return', 'shift', 'tab']],
 'recommendation_count': 6,
 'recommended_connection': 'Computer keyboard keys',
 'recommended_correct': True,
 'recommended_words': ['option', 'return', 'shift', 'tab'],
 'tool_status': 'puzzle_completed',
 'tool_to_use': 'END',
 'vocabulary_db_fp': '/tmp/tmpgh2b63hy.db',
 'words_remaining': []}

FOUND SOLUTIONS
[   ['hail', 'rain', 'sleet', 'snow'],
    ['kayak', 'level', 'mom', 'racecar'],
    ['bucks', 'heat', 'jazz', 'nets'],
    ['option', 'return', 'shift', 'tab']]
ALL GROUPS FOUND
[   [   ['hail', 'rain', 'sleet', 'snow'],
        ['kayak', 'level', 'mom', 'racecar'],
        ['bucks', 'heat', 'jazz', 'nets'],
        ['option', 'return', 'shift', 'tab']]]
   solved_puzzle  number_found                                       groups_found
0           True             4  [[hail, rain, sleet, snow], [kayak, level, mom...
```