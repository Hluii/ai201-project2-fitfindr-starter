"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    try:
        listings = load_listings()
    except Exception:
        return []

    # Extract keywords from the description (case-insensitive, deduplicated).
    keywords = {kw for kw in (description or "").lower().split() if kw}

    size_filter = size.lower().strip() if size else None

    scored: list[tuple[int, dict]] = []
    for listing in listings:
        # Price filter (inclusive).
        if max_price is not None:
            price = listing.get("price")
            if price is None or price > max_price:
                continue

        # Size filter (case-insensitive substring match).
        if size_filter is not None:
            listing_size = str(listing.get("size") or "").lower()
            if size_filter not in listing_size:
                continue

        # Build searchable text from title, description, and style_tags.
        style_tags = listing.get("style_tags") or []
        searchable = " ".join(
            [
                str(listing.get("title") or ""),
                str(listing.get("description") or ""),
                " ".join(str(tag) for tag in style_tags),
            ]
        ).lower()

        # Score by number of matching keywords.
        if keywords:
            score = sum(1 for kw in keywords if kw in searchable)
            if score == 0:
                continue
        else:
            # No keywords given: every listing passing the filters matches.
            score = 0

        scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    new_item = new_item or {}
    item_name = new_item.get("title") or "the item"

    # Compact description of the new item for the prompt.
    item_lines = [
        f"- Name: {item_name}",
        f"- Category: {new_item.get('category', 'unknown')}",
        f"- Colors: {', '.join(new_item.get('colors') or []) or 'unspecified'}",
        f"- Style tags: {', '.join(new_item.get('style_tags') or []) or 'none'}",
    ]
    if new_item.get("description"):
        item_lines.append(f"- Description: {new_item['description']}")
    item_block = "\n".join(item_lines)

    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            "You are a friendly personal stylist. A user is considering buying "
            "this thrifted item but hasn't shared their wardrobe yet:\n\n"
            f"{item_block}\n\n"
            "Give general styling advice for this piece: what kinds of items "
            "pair well with it, what vibe or aesthetic it suits, and how someone "
            "might wear it. Keep it concise (a short paragraph or a few bullets) "
            "and practical."
        )
    else:
        wardrobe_lines = []
        for it in items:
            colors = ", ".join(it.get("colors") or [])
            tags = ", ".join(it.get("style_tags") or [])
            details = " | ".join(p for p in [it.get("category"), colors, tags] if p)
            name = it.get("name") or it.get("title") or "item"
            wardrobe_lines.append(f"- {name}" + (f" ({details})" if details else ""))
        wardrobe_block = "\n".join(wardrobe_lines)

        prompt = (
            "You are a friendly personal stylist. A user is considering buying "
            "this thrifted item:\n\n"
            f"{item_block}\n\n"
            "Here is what's already in their wardrobe:\n\n"
            f"{wardrobe_block}\n\n"
            "Suggest 1-2 specific, complete outfit combinations that pair the new "
            "item with named pieces from their wardrobe. Refer to the wardrobe "
            "pieces by name. Keep it concise and practical."
        )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            return text
    except Exception:
        pass

    # Fallback so we always return a non-empty string.
    return (
        f"I couldn't reach the styling assistant right now, but {item_name} is a "
        "versatile piece — try pairing it with neutral basics and layering to match "
        "your personal vibe."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard: empty or whitespace-only outfit.
    if not outfit or not outfit.strip():
        return (
            "Can't create a fit card without an outfit suggestion — "
            "generate an outfit first, then try again."
        )

    new_item = new_item or {}
    item_name = new_item.get("title") or "this find"
    price = new_item.get("price")
    price_str = f"${price:.0f}" if isinstance(price, (int, float)) else "a steal"
    platform = new_item.get("platform") or "the resale app"

    prompt = (
        "You're writing a short, casual OOTD-style caption for an Instagram/TikTok "
        "post about a thrifted find. Here's the outfit:\n\n"
        f"{outfit.strip()}\n\n"
        "Item details:\n"
        f"- Name: {item_name}\n"
        f"- Price: {price_str}\n"
        f"- Found on: {platform}\n\n"
        "Write 2-4 sentences. It should feel authentic and casual (like a real "
        "OOTD post, not a product description), capture the vibe of the outfit in "
        f"specific terms, and naturally mention the item name ({item_name}), the "
        f"price ({price_str}), and the platform ({platform}) exactly once each. "
        "Return only the caption text."
    )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.2,
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            return text
    except Exception as e:
        print(f"Groq error: {e}")
        pass

    # Fallback so we always return a usable, non-empty string.
    return (
        f"Obsessed with my new {item_name} 😍 Snagged it for {price_str} on "
        f"{platform} and it pulls the whole look together. Thrifted and proud!"
    )
