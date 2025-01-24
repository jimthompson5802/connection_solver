
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