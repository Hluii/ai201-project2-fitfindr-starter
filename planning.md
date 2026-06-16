# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches listings for items matching description, optionally size and max price. Returns a list of matching items sorted by relavancy (best matches) first or an empty list if no matches found.
**Input parameters:**
<!-- Each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user is looking for(e.g., "vintage graphic tee").
- `size` (str): Size string to filter by, or None to skip size filtering. Matching is case-insensitive (e.g., "M" matches "S/M").
- `max_price` (float): Maximum price (inclusive), or None to skip price filtering.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
Returns a list of matching listing dicts(list[dict]), sorted by relavance(best matches first).
Listing dictionaries: Each listing has the following fields:
        - id (str)
        - title (str)
        - description (str)
        - category (str): one of tops, bottoms, outerwear, shoes, accessories
        - style_tags (list[str])
        - size (str)
        - condition (str): excellent, good, or fair
        - price (float)
        - colors (list[str])
        - brand (str or None)
        - platform (str): depop, thredUp, or poshmark
**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? --> 

Returns an empty list if nothing matches — does NOT raise an exception.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Suggests 1 or 2 outfit pairings in a short paragraph, given a new clothing item(`new_item`) and and user `wardrobe`. If `wardrobe` empty return general syling advice. 
**Input parameters:**
<!-- Each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict (the item the user is considering buying).
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty.

**What it returns:**
<!-- Describe the return value -->
Returns Non-empty string LLM output for styling 1-2 outfits using the user `wardrobe` and `new_item` if it is not empty. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the `wardrobe` is empty return general styling afvice for `new_item`, rather than raising an exception or returning an empty string.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Sound different each time for different inputs (use higher LLM temperature) -->
Generate a short, shareable casual, and authentic outfit(OOTD post) caption for the thrifted find . Mention the item name, price, and platform naturally (once each) while capturing the outfit vibe in specific terms.

**Input parameters:**
<!-- Each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string from `suggest_outfit()`.
- `new_item` (dict): The listing dict for the thrifted item.

**What it returns:**
<!-- Describe the return value -->
A 2–4 sentence string usable as an Instagram/TikTok caption.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or missing, return a descriptive error message string — do NOT raise an exception.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop
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
**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

Planning Loop(Intialize session):
     1. Parse the user's session["query"] to extract a description, size, and max_price.  
          - Store the result in session["parsed"].
     2. Call search_listings(description(session["parsed"]), size, max_price)
          - If results = []:
               - session["error"] = "No listings matched your search. Try raising max_price or using broader keywords."
               - Return session, DO NOT PROCEED to suggest_outfit with empty input.
          - Else: 
               - session["search_results"] = results.
               - session["selected_item"] = results[0]
     3. Call suggest_outfit(`new_item`(session["selected_item"]), wardrobe)
          - If wardrobe['items'] is empty:
               - result = general styling advice for `new_item`
               - Not an error, proceed normally
          - session["outfit_suggestion"] = result
     4. Call create_fit_card(outfit(session["outfit_suggestion"]), new_item(session["selected_item"]))
          - Guard: if session['outfit_suggestion'] == "", create_fit_card returns an error string instead of crashing (defensive, shouldn't trigger given step 3 always return a non-empty string)
          - session["fit_card"] = result
     5. Return session

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

Agent stores and accessses data thrhough the sessiomn dict. The tool calls on keys in the session dict to get the value then returns to another jkeyvalue parir in the same session dict. 

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
