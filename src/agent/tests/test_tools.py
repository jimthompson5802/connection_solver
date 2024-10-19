# src/agent/test_tools.py

import pytest
from unittest.mock import mock_open, patch
from src.agent.tools import read_file_to_word_list


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
