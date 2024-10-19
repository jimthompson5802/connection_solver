# src/agent/test_utils.py

import pytest
from src.agent.utils import chunk_words, flatten_list


def test_chunk_words_empty():
    assert chunk_words([]) == []


def test_chunk_words_less_than_4():
    assert chunk_words(["one", "two", "three"]) == [["one", "two", "three"]]


def test_chunk_words_exactly_4():
    assert chunk_words(["one", "two", "three", "four"]) == [["one", "two", "three", "four"]]


def test_chunk_words_more_than_4_not_multiple():
    assert chunk_words(["one", "two", "three", "four", "five"]) == [["one", "two", "three", "four"], ["five"]]


def test_chunk_words_multiple_of_4():
    assert chunk_words(["one", "two", "three", "four", "five", "six", "seven", "eight"]) == [
        ["one", "two", "three", "four"],
        ["five", "six", "seven", "eight"],
    ]


def test_flatten_list_empty():
    assert flatten_list([]) == []


def test_flatten_list_single_empty_list():
    assert flatten_list([[]]) == []


def test_flatten_list_multiple_empty_lists():
    assert flatten_list([[], [], []]) == []


def test_flatten_list_single_elements():
    assert flatten_list([[1], [2], [3]]) == [1, 2, 3]


def test_flatten_list_multiple_elements():
    assert flatten_list([[1, 2], [3, 4], [5, 6]]) == [1, 2, 3, 4, 5, 6]


def test_flatten_list_mixed_elements():
    assert flatten_list([[1, 2], [], [3], [4, 5, 6]]) == [1, 2, 3, 4, 5, 6]
