# src/agent/test_tools.py

import pytest
from unittest.mock import mock_open, patch, MagicMock
from src.agent.tools import read_file_to_word_list
from src.agent.tools import ask_llm_for_solution, SYSTEM_MESSAGE

# TODO: fix commented out tests
# from src.agent.app import apply_recommendation, clear_recommendation, PuzzleState


# @pytest.fixture
# def initial_state():
#     return PuzzleState(
#         words_remaining=["word1", "word2", "word3", "word4"],
#         invalid_connections=[],
#         recommended_words=["word1", "word2", "word3", "word4"],
#         recommended_connection="some connection",
#         recommended_correct=False,
#         found_blue=False,
#         found_green=False,
#         found_purple=False,
#         found_yellow=False,
#         mistake_count=0,
#         recommendation_count=0,
#         llm_temperature=0.7,
#     )


def test_read_file_to_word_list_success():
    mock_file_content = "word1, word2, word3"
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("builtins.input", return_value="dummy_path"):
            assert read_file_to_word_list() == ["word1", "word2", "word3"]


def test_read_file_to_word_list_empty_file():
    mock_file_content = ""
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("builtins.input", return_value="dummy_path"):
            assert read_file_to_word_list() == [""]
            # src/agent/tests/test_tools.py


def test_ask_llm_for_solution_success():
    mock_response = MagicMock()
    mock_response.content = '{"words": ["word1", "word2", "word3", "word4"], "connection": "some connection"}'

    with patch("src.agent.tools.ChatOpenAI") as MockChatOpenAI:
        instance = MockChatOpenAI.return_value
        instance.invoke.return_value = mock_response

        prompt = MagicMock()
        result = ask_llm_for_solution(prompt)

        assert result.content == '{"words": ["word1", "word2", "word3", "word4"], "connection": "some connection"}'
        instance.invoke.assert_called_once()


# @patch("..app.interact_with_user")
# def test_apply_recommendation_correct(mock_interact, initial_state):
#     mock_interact.return_value = "y"
#     state = apply_recommendation(initial_state)
#     assert state["found_yellow"] == True
#     assert state["recommended_correct"] == True
#     assert "word1" not in state["words_remaining"]


# @patch("..app.interact_with_user")
# def test_apply_recommendation_incorrect(mock_interact, initial_state):
#     mock_interact.return_value = "n"
#     state = apply_recommendation(initial_state)
#     assert state["mistake_count"] == 1
#     assert state["recommended_correct"] == False
#     assert state["invalid_connections"] == [["word1", "word2", "word3", "word4"]]


# def test_clear_recommendation(initial_state):
#     state = clear_recommendation(initial_state)
#     assert state["recommended_words"] == []
#     assert state["recommended_connection"] == ""
#     assert state["recommended_correct"] == False
