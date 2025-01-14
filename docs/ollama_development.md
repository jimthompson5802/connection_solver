# Ollama Development

Unless noted otherwise, the LLMOllamaInterface will be using OpenAi gpt-4o-mini as the LLM for the workflow manager.  Llama3.2 is used for all Connection Word Analyzers.  This combination is known as `hybrid`.

## Comparision run between OpenAI and Llama3.2 LLM use

### OpenAI
```text
$ python src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl 
Running Connection Solver Agent Tester 0.16.0-dev

>>>>SOLVING PUZZLE 1
Entering LLMOpenAIInterface.__init__
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(102, 102)
(102, 102)
candidate_lists size: 74

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['hail', 'rain', 'sleet', 'snow'] with connection The words are all types of precipitation.
The words are all types of precipitation. ~ wet weather: ['hail', 'rain', 'sleet', 'snow'] == ['hail', 'rain', 'sleet', 'snow']
Recommendation ['hail', 'rain', 'sleet', 'snow'] is correct

ENTERED EMBEDVEC_RECOMMENDER
found count: 1, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'level', 'racecar', 'bucks', 'tab']
(78, 78)
(78, 78)
candidate_lists size: 63

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['level', 'option', 'shift', 'tab'] with connection Connected by the theme of computer-related actions or features.
Recommendation ['level', 'option', 'shift', 'tab'] is incorrect, one away from correct

ENTERED ONE-AWAY ANALYZER
found count: 1, mistake_count: 1

>>>Number of single topic groups: 2
More than one single-topic group recommendations, selecting one at random.

>>>Selected single-topic group:
Recommended Group: ('option', 'shift', 'tab')
Connection Description: The three words 'option', 'shift', and 'tab' can all be related to a single topic within the context of computer keyboards and software applications. Each word is commonly associated with keyboard keys and their functions. 'Option' refers to a modifier key on Apple keyboards, 'Shift' is a key used to type uppercase letters or other alternate 'upper' characters, and 'Tab' is a key used to navigate between fields in applications or to insert a tab character. Therefore, all three words share a common context in computing, specifically keyboard usage.

>>>One-away group recommendations:
one_away_group_recommendation is a new recommendation
using one_away_group_recommendation

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['option', 'return', 'shift', 'tab'] with connection The common connection among the anchor words 'option', 'shift', and 'tab' is that they are all keys on a keyboard. 'Return' also refers to a key on a keyboard (often synonymous with 'enter'), making it the most connected word to the anchor words.
The common connection among the anchor words 'option', 'shift', and 'tab' is that they are all keys on a keyboard. 'Return' also refers to a key on a keyboard (often synonymous with 'enter'), making it the most connected word to the anchor words. ~ keyboard keys: ['option', 'return', 'shift', 'tab'] == ['option', 'return', 'shift', 'tab']
Recommendation ['option', 'return', 'shift', 'tab'] is correct

ENTERED EMBEDVEC_RECOMMENDER
found count: 2, mistake_count: 1
words_remaining: ['nets', 'heat', 'jazz', 'mom', 'kayak', 'level', 'racecar', 'bucks']
(53, 53)
(53, 53)
candidate_lists size: 26

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['heat', 'jazz', 'mom', 'racecar'] with connection The words are connected by their association with distinct characteristics or themes (heat, jazz, maternal care, racecars).
Recommendation ['heat', 'jazz', 'mom', 'racecar'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

ENTERED LLM_RECOMMENDER
found count: 2, mistake_count: 2
attempt_count: 1
words_remaining: ['heat', 'jazz', 'mom', 'level', 'kayak', 'racecar', 'bucks', 'nets']

LLM_RECOMMENDER: RECOMMENDED WORDS ['kayak', 'level', 'mom', 'racecar'] with connection palindromes
palindromes ~ palindromes: ['kayak', 'level', 'mom', 'racecar'] == ['kayak', 'level', 'mom', 'racecar']
Recommendation ['kayak', 'level', 'mom', 'racecar'] is correct

ENTERED LLM_RECOMMENDER
found count: 3, mistake_count: 2
attempt_count: 1
words_remaining: ['bucks', 'heat', 'jazz', 'nets']

LLM_RECOMMENDER: RECOMMENDED WORDS ['bucks', 'heat', 'jazz', 'nets'] with connection NBA basketball teams
NBA basketball teams ~ nba teams: ['bucks', 'heat', 'jazz', 'nets'] == ['bucks', 'heat', 'jazz', 'nets']
Recommendation ['bucks', 'heat', 'jazz', 'nets'] is correct
SOLVED THE CONNECTION PUZZLE!!!


FINAL PUZZLE STATE:
{'current_tool': 'llm_recommender',
 'found_count': 4,
 'invalid_connections': [['13d2a286f09038042098e5ab1874d93f',
                          ['level', 'option', 'shift', 'tab']],
                         ['a316f19aa1f69c8589f969d5a3b84982',
                          ['heat', 'jazz', 'mom', 'racecar']]],
 'llm_retry_count': 0,
 'llm_temperature': 0.7,
 'mistake_count': 2,
 'puzzle_status': 'initialized',
 'recommendation_answer_status': 'correct',
 'recommendation_correct_groups': [['hail', 'rain', 'sleet', 'snow'],
                                   ['option', 'shift', 'tab', 'return'],
                                   ['kayak', 'level', 'mom', 'racecar'],
                                   ['bucks', 'heat', 'jazz', 'nets']],
 'recommendation_count': 6,
 'recommended_connection': 'NBA basketball teams',
 'recommended_correct': True,
 'recommended_words': ['bucks', 'heat', 'jazz', 'nets'],
 'tool_status': 'puzzle_completed',
 'tool_to_use': 'END',
 'vocabulary_db_fp': '/tmp/tmp1hc3cli1.db',
 'words_remaining': []}

FOUND SOLUTIONS
[   ['hail', 'rain', 'sleet', 'snow'],
    ['option', 'shift', 'tab', 'return'],
    ['kayak', 'level', 'mom', 'racecar'],
    ['bucks', 'heat', 'jazz', 'nets']]
ALL GROUPS FOUND
[   [   ['hail', 'rain', 'sleet', 'snow'],
        ['option', 'shift', 'tab', 'return'],
        ['kayak', 'level', 'mom', 'racecar'],
        ['bucks', 'heat', 'jazz', 'nets']]]
   solved_puzzle  number_found                                       groups_found
0           True             4  [[hail, rain, sleet, snow], [option, shift, ta...
```

### Llama3.2  (hybrid)
```text
vscode ➜ /workspaces/connection_solver (support-ollama-models) $ python src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface hybrid
Running Connection Solver Agent Tester 0.16.0-dev

>>>>SOLVING PUZZLE 1
Entering LLMOllamaInterface.__init__
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(82, 82)
(82, 82)
candidate_lists size: 58

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['hail', 'jazz', 'snow', 'tab'] with connection to fall from the sky in the form of ice pellets, often accompanied by loud rattling or pounding sound; to make into ice or frost by snowfall; to press the keys on a keyboard in a rhythmic pattern
Recommendation ['hail', 'jazz', 'snow', 'tab'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

ENTERED LLM_RECOMMENDER
found count: 0, mistake_count: 1
attempt_count: 1
words_remaining: ['snow', 'hail', 'tab', 'bucks', 'racecar', 'level', 'sleet', 'rain', 'option', 'kayak', 'shift', 'mom', 'jazz', 'heat', 'return', 'nets']

LLM_RECOMMENDER: RECOMMENDED WORDS ['hail', 'rain', 'sleet', 'snow'] with connection precipitation
precipitation ~ wet weather: ['hail', 'rain', 'sleet', 'snow'] == ['hail', 'rain', 'sleet', 'snow']
Recommendation ['hail', 'rain', 'sleet', 'snow'] is correct

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 1
attempt_count: 1
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'level', 'racecar', 'bucks', 'tab']

LLM_RECOMMENDER: RECOMMENDED WORDS ['heat', 'jazz', 'nets', 'return'] with connection 
Recommendation ['heat', 'jazz', 'nets', 'return'] is incorrect, one away from correct

ENTERED ONE-AWAY ANALYZER
found count: 1, mistake_count: 2
Traceback (most recent call last):
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 188, in <module>
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
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 180, in main
    found_solutions = await asyncio.gather(
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 167, in solve_a_puzzle
    result = await run_workflow(
             ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/workflow_manager.py", line 120, in run_workflow
    async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1878, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/runner.py", line 362, in atick
    await arun_with_retry(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 132, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 445, in ainvoke
    input = await step.ainvoke(input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 236, in ainvoke
    ret = await asyncio.create_task(coro, context=context)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 516, in apply_recommendation
    one_away_group_recommendation = await one_away_analyzer(
                                    ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 264, in one_away_analyzer
    single_topic_groups = [
                          ^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 270, in <listcomp>
    if x[1]["response"] == "single"
       ~~~~^^^^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable
During task with name 'apply_recommendation' and id '7633233c-0507-e5ac-69c2-deccc20f9bdf'
```


## Run with using Llama3.2 as the LLM for the entire process, including workflow manager

llama3.2 as workflow llm is not working, falling back to use OpenAI for workflow.  Calling this combination `hybrid`.

```text
Running Connection Solver Agent Tester 0.15.0

>>>>SOLVING PUZZLE 1
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(76, 76)
(76, 76)
candidate_lists size: 48
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(145, 145)
(145, 145)
candidate_lists size: 98
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 
^CTraceback (most recent call last):
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 180, in main
    found_solutions = await asyncio.gather(
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 167, in solve_a_puzzle
    result = await run_workflow(
             ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/workflow_manager.py", line 120, in run_workflow
    async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1878, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/runner.py", line 362, in atick
    await arun_with_retry(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 132, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 445, in ainvoke
    input = await step.ainvoke(input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 236, in ainvoke
    ret = await asyncio.create_task(coro, context=context)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 136, in setup_puzzle
    vocabulary = await config["configurable"]["llm_interface"].generate_vocabulary(state["words_remaining"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/ollama_tools.py", line 125, in generate_vocabulary
    await asyncio.gather(*[process_word(word) for word in words])
  File "/workspaces/connection_solver/src/agent/ollama_tools.py", line 122, in process_word
    result = await structured_llm.ainvoke(prompt.to_messages())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 722, in agenerate
    results = await asyncio.gather(
              ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 924, in _agenerate_with_cache
    result = await self._agenerate(
             ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_ollama/chat_models.py", line 788, in _agenerate
    final_chunk = await self._achat_stream_with_aggregation(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langchain_ollama/chat_models.py", line 645, in _achat_stream_with_aggregation
    async for stream_resp in self._acreate_chat_stream(messages, stop, **kwargs):
  File "/usr/local/lib/python3.11/site-packages/langchain_ollama/chat_models.py", line 575, in _acreate_chat_stream
    async for part in await self._async_client.chat(**chat_params):
  File "/usr/local/lib/python3.11/site-packages/ollama/_client.py", line 664, in inner
    async with self._client.stream(*args, **kwargs) as r:
  File "/usr/local/lib/python3.11/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1628, in stream
    response = await self.send(
               ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1674, in send
    response = await self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1702, in _send_handling_auth
    response = await self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1739, in _send_handling_redirects
    response = await self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1776, in _send_single_request
    response = await transport.handle_async_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_transports/default.py", line 377, in handle_async_request
    resp = await self._pool.handle_async_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/connection_pool.py", line 256, in handle_async_request
    raise exc from None
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/connection_pool.py", line 236, in handle_async_request
    response = await connection.handle_async_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/connection.py", line 103, in handle_async_request
    return await self._connection.handle_async_request(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/http11.py", line 136, in handle_async_request
    raise exc
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/http11.py", line 106, in handle_async_request
    ) = await self._receive_response_headers(**kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/http11.py", line 177, in _receive_response_headers
    event = await self._receive_event(timeout=timeout)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_async/http11.py", line 217, in _receive_event
    data = await self._network_stream.read(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_backends/anyio.py", line 35, in read
    return await self._stream.receive(max_bytes=max_bytes)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/anyio/_backends/_asyncio.py", line 1246, in receive
    await self._protocol.read_event.wait()
  File "/usr/local/lib/python3.11/asyncio/locks.py", line 213, in wait
    await fut
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:
```


## Additional runs with Llama3.2 (hybrid)
It appears that asyncio is not returning correctly, the code will fail at different points in the process, usually just after a call the LLM that appears to return `None`, i.e., the LLM is not returning a response.   Following are examples of this error type.

```text
/workspaces/connection_solver/src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface hybrid 
Running Connection Solver Agent Tester 0.16.0-dev

>>>>SOLVING PUZZLE 1
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(253, 253)
(253, 253)
candidate_lists size: 91

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['hail', 'kayak', 'rain', 'snow'] with connection forming or consisting of ice pellets that fall from a cloud
Recommendation ['hail', 'kayak', 'rain', 'snow'] is incorrect, one away from correct

ENTERED ONE-AWAY ANALYZER
found count: 0, mistake_count: 1
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
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 188, in <module>
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
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 180, in main
    found_solutions = await asyncio.gather(
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 167, in solve_a_puzzle
    result = await run_workflow(
             ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/workflow_manager.py", line 120, in run_workflow
    async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1878, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/runner.py", line 362, in atick
    await arun_with_retry(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 132, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 445, in ainvoke
    input = await step.ainvoke(input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 236, in ainvoke
    ret = await asyncio.create_task(coro, context=context)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 516, in apply_recommendation
    one_away_group_recommendation = await one_away_analyzer(
                                    ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 264, in one_away_analyzer
    single_topic_groups = [
                          ^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 270, in <listcomp>
    if x[1]["response"] == "single"
       ~~~~^^^^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable
During task with name 'apply_recommendation' and id 'cb1d296b-ba73-b1d1-671d-b0adabac8ace'
```


```
/workspaces/connection_solver/src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface hybrid 
Running Connection Solver Agent Tester 0.16.0-dev

>>>>SOLVING PUZZLE 1
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(322, 322)
(322, 322)
candidate_lists size: 107
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
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 188, in <module>
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
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 180, in main
    found_solutions = await asyncio.gather(
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/app_embedvec_tester.py", line 167, in solve_a_puzzle
    result = await run_workflow(
             ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/workflow_manager.py", line 120, in run_workflow
    async for chunk in workflow_graph.astream(None, runtime_config, stream_mode="values"):
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/__init__.py", line 1878, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/runner.py", line 362, in atick
    await arun_with_retry(
  File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 132, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 445, in ainvoke
    input = await step.ainvoke(input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/langgraph/utils/runnable.py", line 236, in ainvoke
    ret = await asyncio.create_task(coro, context=context)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/connection_solver/src/agent/puzzle_solver.py", line 390, in get_embedvec_recommendation
    state["recommended_words"] = recommended_group["candidate_group"]
                                 ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable
During task with name 'get_embedvec_recommendation' and id '15f6f531-3a21-fb27-f351-0d5290e10626'

```

## Disabled asyncio in the LLM interface

### This is ayncio disabled for creating the vocabulary definitions.
```text
cd /workspaces/connection_solver ; /usr/bin/env /usr/local/bin/python /home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher 43929 -- /workspaces/connection_solver/src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface hybrid 
Running Connection Solver Agent Tester 0.16.0-dev

>>>>SOLVING PUZZLE 1
Entering LLMOllamaInterface.__init__
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(77, 77)
(77, 77)
candidate_lists size: 53

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['hail', 'rain', 'sleet', 'snow'] with connection weather conditions
weather conditions ~ wet weather: ['hail', 'rain', 'sleet', 'snow'] == ['hail', 'rain', 'sleet', 'snow']
Recommendation ['hail', 'rain', 'sleet', 'snow'] is correct

ENTERED EMBEDVEC_RECOMMENDER
found count: 1, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'level', 'racecar', 'bucks', 'tab']
(56, 56)
(56, 56)
candidate_lists size: 38

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['heat', 'jazz', 'level', 'shift'] with connection unique concept related to music
Recommendation ['heat', 'jazz', 'level', 'shift'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 1
attempt_count: 1
words_remaining: ['heat', 'tab', 'kayak', 'nets', 'mom', 'option', 'racecar', 'jazz', 'return', 'bucks', 'level', 'shift']

LLM_RECOMMENDER: RECOMMENDED WORDS ['heat', 'kayak', 'nets', 'tab'] with connection sports equipment
Recommendation ['heat', 'kayak', 'nets', 'tab'] is incorrect

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 2
attempt_count: 1
words_remaining: ['tab', 'kayak', 'bucks', 'mom', 'racecar', 'shift', 'jazz', 'nets', 'heat', 'level', 'return', 'option']

LLM_RECOMMENDER: RECOMMENDED WORDS ['bucks', 'kayak', 'mom', 'tab'] with connection vehicle
Recommendation ['bucks', 'kayak', 'mom', 'tab'] is incorrect

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 3
attempt_count: 1
words_remaining: ['option', 'mom', 'racecar', 'nets', 'bucks', 'kayak', 'shift', 'tab', 'return', 'level', 'jazz', 'heat']

LLM_RECOMMENDER: RECOMMENDED WORDS ['mom', 'nets', 'option', 'racecar'] with connection none
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!


FINAL PUZZLE STATE:
{'current_tool': 'llm_recommender',
 'found_count': 1,
 'invalid_connections': [['ed14c8fe76fc9710d31dc3a29639415b',
                          ['heat', 'jazz', 'level', 'shift']],
                         ['8f7e6c63951377b6a2d6b591fdc4a686',
                          ['heat', 'kayak', 'nets', 'tab']],
                         ['347774d7334b44d564a4e1d7403dac51',
                          ['bucks', 'kayak', 'mom', 'tab']],
                         ('916e20f0ee49fe415608590880f64182',
                          ['mom', 'nets', 'option', 'racecar'])],
 'llm_retry_count': 0,
 'llm_temperature': 0.7,
 'mistake_count': 4,
 'puzzle_status': 'initialized',
 'recommendation_answer_status': 'n',
 'recommendation_correct_groups': [['hail', 'rain', 'sleet', 'snow']],
 'recommendation_count': 5,
 'recommended_connection': '',
 'recommended_correct': False,
 'recommended_words': [],
 'tool_status': 'puzzle_completed',
 'tool_to_use': 'END',
 'vocabulary_db_fp': '/tmp/tmpoy0ge6eg.db',
 'words_remaining': ['option',
                     'mom',
                     'racecar',
                     'nets',
                     'bucks',
                     'kayak',
                     'shift',
                     'tab',
                     'return',
                     'level',
                     'jazz',
                     'heat']}

FOUND SOLUTIONS
[['hail', 'rain', 'sleet', 'snow']]
ALL GROUPS FOUND
[[['hail', 'rain', 'sleet', 'snow']]]
   solved_puzzle  number_found                 groups_found
0          False             1  [[hail, rain, sleet, snow]]
```

### Disabled asyncio for all lmm interactions using llama3.2, workflow uses gpt-4o-mini.
```text
cd /workspaces/connection_solver ; /usr/bin/env /usr/local/bin/python /home/vscode/.vscode-server/extensions/ms-python.debugpy-2024.14.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher 55163 -- /workspaces/connection_solver/src/agent/app_embedvec_tester.py --puzzle_setup_fp data/automated_test_set_0.jsonl --llm_interface hybrid 
Running Connection Solver Agent Tester 0.16.0-dev

>>>>SOLVING PUZZLE 1
Entering LLMOllamaInterface.__init__
word_analyzer_llm_name: llama3.2, workflow_llm_name: gpt-4o-mini, image_extraction_llm_name: None, embedding_model_name: llama3.2
Setting up Puzzle Words: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']

ENTERED SETUP_PUZZLE

Generating vocabulary and embeddings for the words...this may take several seconds 

Generating embeddings for the definitions

Storing vocabulary and embeddings in external database

ENTERED EMBEDVEC_RECOMMENDER
found count: 0, mistake_count: 0
words_remaining: ['nets', 'return', 'heat', 'jazz', 'mom', 'shift', 'kayak', 'option', 'rain', 'sleet', 'level', 'racecar', 'bucks', 'tab', 'hail', 'snow']
(73, 73)
(73, 73)
candidate_lists size: 56

EMBEDVEC_RECOMMENDER: RECOMMENDED WORDS ['heat', 'jazz', 'option', 'shift'] with connection not connected
Recommendation ['heat', 'jazz', 'option', 'shift'] is incorrect
Changing the recommender from 'embedvec_recommender' to 'llm_recommender'

ENTERED LLM_RECOMMENDER
found count: 0, mistake_count: 1
attempt_count: 1
words_remaining: ['snow', 'hail', 'tab', 'bucks', 'racecar', 'level', 'sleet', 'rain', 'option', 'kayak', 'shift', 'mom', 'jazz', 'heat', 'return', 'nets']

LLM_RECOMMENDER: RECOMMENDED WORDS ['hail', 'rain', 'sleet', 'snow'] with connection precipitation
precipitation ~ wet weather: ['hail', 'rain', 'sleet', 'snow'] == ['hail', 'rain', 'sleet', 'snow']
Recommendation ['hail', 'rain', 'sleet', 'snow'] is correct

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 1
attempt_count: 1
words_remaining: ['heat', 'tab', 'mom', 'bucks', 'return', 'nets', 'kayak', 'option', 'level', 'shift', 'racecar', 'jazz']

LLM_RECOMMENDER: RECOMMENDED WORDS ['bucks', 'heat', 'mom', 'tab'] with connection team
Recommendation ['bucks', 'heat', 'mom', 'tab'] is incorrect

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 2
attempt_count: 1
words_remaining: ['jazz', 'racecar', 'shift', 'level', 'option', 'kayak', 'nets', 'return', 'bucks', 'mom', 'tab', 'heat']

LLM_RECOMMENDER: RECOMMENDED WORDS ['jazz', 'level', 'racecar', 'shift'] with connection type of gear
Recommendation ['jazz', 'level', 'racecar', 'shift'] is incorrect

ENTERED LLM_RECOMMENDER
found count: 1, mistake_count: 3
attempt_count: 1
words_remaining: ['tab', 'heat', 'nets', 'bucks', 'racecar', 'kayak', 'level', 'option', 'shift', 'return', 'mom', 'jazz']

LLM_RECOMMENDER: RECOMMENDED WORDS ['bucks', 'heat', 'nets', 'tab'] with connection 
FAILED TO SOLVE THE CONNECTION PUZZLE TOO MANY MISTAKES!!!


FINAL PUZZLE STATE:
{'current_tool': 'llm_recommender',
 'found_count': 1,
 'invalid_connections': [['b1b322eb5be8755e5fbf7619db528aa5',
                          ['heat', 'jazz', 'option', 'shift']],
                         ['eac32a4a5796da996879432866676fd2',
                          ['bucks', 'heat', 'mom', 'tab']],
                         ['bf31f0ea6682f1989d3de6e07c1b34e6',
                          ['jazz', 'level', 'racecar', 'shift']],
                         ('e86357ebc44016c749e68300284758e6',
                          ['bucks', 'heat', 'nets', 'tab'])],
 'llm_retry_count': 0,
 'llm_temperature': 0.7,
 'mistake_count': 4,
 'puzzle_status': 'initialized',
 'recommendation_answer_status': 'o',
 'recommendation_correct_groups': [['hail', 'rain', 'sleet', 'snow']],
 'recommendation_count': 5,
 'recommended_connection': '',
 'recommended_correct': False,
 'recommended_words': [],
 'tool_status': 'puzzle_completed',
 'tool_to_use': 'END',
 'vocabulary_db_fp': '/tmp/tmpktyhnj2i.db',
 'words_remaining': ['tab',
                     'heat',
                     'nets',
                     'bucks',
                     'racecar',
                     'kayak',
                     'level',
                     'option',
                     'shift',
                     'return',
                     'mom',
                     'jazz']}

FOUND SOLUTIONS
[['hail', 'rain', 'sleet', 'snow']]
ALL GROUPS FOUND
[[['hail', 'rain', 'sleet', 'snow']]]
   solved_puzzle  number_found                 groups_found
0          False             1  [[hail, rain, sleet, snow]]
```