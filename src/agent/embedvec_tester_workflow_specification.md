**Instructions**

use "setup_puzzle" tool to initialize the puzzle if the "puzzle_status" is not initialized.

if "tool_status" is "puzzle_completed" then use "END" tool.

Use the table to select the appropriate tool.

|current_tool| tool_status | tool |
| --- | --- | --- |
|setup_puzzle| initialized | get_embedvec_recommendation |
|embedvec_recommender| next_recommendation | get_embedvec_recommendation |
|embedvec_recommender| have_recommendation | apply_recommendation |
|llm_recommender| next_recommendation | get_llm_recommendation |
|llm_recommender| have_recommendation | apply_recommendation |
|llm_recommender| manual_recommendation | get_llm_recommendation |

If no tool is selected, use "ABORT" tool.
