"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── query parsing ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract a description, size, and max_price from a natural language query.

    Uses lightweight regex/string matching:
      - max_price: the first "$30" / "under 30" style number
      - size: a recognized size token (XXS-XXL, numeric, or words like "small")
      - description: the query with the size/price phrases stripped out
    """
    text = query or ""
    lowered = text.lower()

    # max_price — match "$30", "under 30", "below $25.50", "max 40"
    max_price = None
    # A number tied to a price cue ("under", "below", "max", "$", …).
    price_cue = re.search(
        r"(?:under|below|less than|max(?:\s*price)?|up to|<=?|\$)\s*\$?\s*(\d+(?:\.\d+)?)",
        lowered,
    )
    if price_cue:
        max_price = float(price_cue.group(1))

    # size — common size tokens
    size = None
    size_match = re.search(
        r"\bsize\s+(xxs|xs|s|m|l|xl|xxl|\d{1,2}|small|medium|large)\b",
        lowered,
    )
    if not size_match:
        size_match = re.search(r"\b(xxs|xs|xl|xxl)\b", lowered)
    if size_match:
        token = size_match.group(1)
        size = {"small": "S", "medium": "M", "large": "L"}.get(token, token.upper())

    # description — strip the size and price phrases so they don't pollute keywords
    description = lowered
    description = re.sub(
        r"(?:under|below|less than|max(?:\s*price)?|up to|<=?)?\s*\$\s*\d+(?:\.\d+)?",
        " ",
        description,
    )
    description = re.sub(
        r"(?:under|below|less than|max(?:\s*price)?|up to|<=?)\s*\d+(?:\.\d+)?",
        " ",
        description,
    )
    description = re.sub(
        r"\bsize\s+(?:xxs|xs|s|m|l|xl|xxl|\d{1,2}|small|medium|large)\b",
        " ",
        description,
    )
    # Drop filler words that aren't useful search keywords.
    description = re.sub(
        r"\b(looking|for|a|an|the|i|want|need|some|find|me)\b", " ", description
    )
    description = re.sub(r"\s+", " ", description).strip()
    if not description:
        description = (query or "").strip()

    return {"description": description, "size": size, "max_price": max_price}


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    session = _new_session(query, wardrobe)

    # Step 2: parse the query into search parameters.
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: search listings.
    results = search_listings(
        parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )

    # Branch: no results → set error and return early, skipping the other tools.
    if results == []:
        session["error"] = (
            "No listings matched your search. "
            "Try raising max_price or using broader keywords."
        )
        return session

    # Step 4: store results and select the top match.
    session["search_results"] = results
    session["selected_item"] = results[0]

    # Step 5: suggest an outfit using the selected item and the wardrobe.
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], session["wardrobe"]
    )

    # Step 6: create a shareable fit card from the outfit and selected item.
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )

    # Step 7: return the completed session.
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
