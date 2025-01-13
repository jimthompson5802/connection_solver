## first run of the code, 
llama3.2 as workflow llm is not working.
```
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

## later run of code
It appears that asyncio is not returning correctly, the code will fail at different points in the process, usually just after a call the LLM that appears to return `None`, i.e., the LLM is not returning a response.   Following are examples of this error type.

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
