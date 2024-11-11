**Instructions**

use "setup_puzzle" tool to initialize the puzzle if the "puzzle_status" is not initialized.

if "puzzle_step" is "puzzle_completed" then use "END" tool.

Use the table to select the appropriate tool.

|puzzle_recommender| puzzle_step | tool |
| --- | --- | --- |
|rag_recommender| next_recommendation | get_rag_recommendation |
|rag_recommender| have_recommendation | apply_recommendation |
|fallback_recommender| next_recommendation | get_recommendation |
|fallback_recommender| have_recommendation | apply_recommendation |

If no tool is selected, use "ABORT" tool.
