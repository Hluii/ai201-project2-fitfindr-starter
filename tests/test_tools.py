# tests/test_tools.py
from dotenv import load_dotenv
load_dotenv()
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    results = search_listings("tee", size="M", max_price=None)
    assert all("M" in item["size"].upper() for item in results)

def test_search_no_price_filter():
    results = search_listings("jacket", size=None, max_price=None)
    assert isinstance(results, list)  # no crash when max_price is None


def test_suggest_outfit_with_wardrobe():
    item = load_listings()[0]
    result = suggest_outfit(item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    item = load_listings()[0]
    result = suggest_outfit(item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0  # general advice, not empty, not a crash


def test_create_fit_card_returns_string():
    item = load_listings()[0]
    result = create_fit_card("Pair with baggy jeans and chunky sneakers.", item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    item = load_listings()[0]
    result = create_fit_card("", item)
    assert isinstance(result, str)  # error string, not a crash
    assert len(result) > 0

def test_create_fit_card_varies():
    item = load_listings()[0]
    outfit = "Pair with baggy jeans and chunky sneakers."
    r1 = create_fit_card(outfit, item)
    r2 = create_fit_card(outfit, item)
    assert r1 != r2  # temperature > 0 means outputs should differ
