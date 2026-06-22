# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.** [x]
2. Verify the data loads correctly by running `python utils/data_loader.py`. [x]
3. Build and test each tool individually before connecting them through your planning loop. [x] 

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.


## Tool Inventory:

| Tool | Inputs | Output | Purpose |
|------|-------------|----------------| ----------------|
| search_listings | description(str), size(str or None), max_price(float) |  list [dict] — matching listing dicts sorted by relevance, or `[]` if none match | Searches thrift listings for items matching the user's query |
| suggest_outfit | new_item(dict), wardrobe(dict with `items') | str — outfit suggestion or general styling advice  | Pairs the selected item with wardrobe pieces into 1-2 outfit combos; returns general styling advice if wardrobe is empty |
| create_fit_card | outfit(str), new_item(dict) | str — OOTD-style Instagram/TikTok caption | Generates a short, shareable caption for the thrifted find mentioning item name, price, and platform |
 


## Planning Loop:

The agent uses a linear planning loop that calls tools in sequence, 
branching early if search returns no results.

1. The user's query is parsed to extract `description`, `size`, and 
`max_price`, stored in `session["parsed"]`.
2. `search_listings` is called with those values. If it returns `[]`, 
the loop sets `session["error"]` with a message telling the user to 
broaden their search and returns immediately — `suggest_outfit` and 
`create_fit_card` are never called.
3. If results are found, `session["selected_item"]` is set to 
`results[0]` and `suggest_outfit` is called with that item and the 
user's wardrobe. The result is stored in `session["outfit_suggestion"]`.
4. `create_fit_card` is called with `session["outfit_suggestion"]` and 
`session["selected_item"]`. The result is stored in `session["fit_card"]`.
5. The session is returned and the UI renders all three output panels.


## State Management:

The agent maintains a session dict that the planning loop reads from and 
writes to between tool calls — the tools themselves are plain functions 
and never access the session directly.

After `search_listings` returns a list of matches, the loop selects the 
top result and stores it as `session["selected_item"]`. That same dict 
is passed as the `new_item` argument to `suggest_outfit`. The string 
`suggest_outfit` returns is stored as `session["outfit_suggestion"]`, 
which is passed as the `outfit` argument to `create_fit_card`. Its 
return value is stored as `session["fit_card"]`, which is what the user 
ultimately sees.

If `search_listings` returns an empty list, the loop stores a message in 
`session["error"]` and returns early — `session["selected_item"]` and 
`session["outfit_suggestion"]` are never set, and `suggest_outfit` and 
`create_fit_card` are never called.

**Data tracked in session:** `session["parsed"]`, 
`session["search_results"]`, `session["selected_item"]`, 
`session["wardrobe"]`, `session["outfit_suggestion"]`, 
`session["fit_card"]`, `session["error"]`.

## Error Handling:
| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No results match the query | Sets `session["error"]` to "No listings matched your search. Try raising max_price or using broader keywords." and returns early without calling other tools |
| `suggest_outfit` | Wardrobe is empty | Returns general styling advice for the item rather than raising an exception or returning an empty string — treated as a normal branch, not an error |
| `create_fit_card` | `outfit` string is empty | Returns "Can't create a fit card without an outfit suggestion — generate an outfit first, then try again." without raising an exception |


**Concrete examples from testing:**

When running `search_listings('designer ballgown', size='XXS', max_price=5)` 
the function returned `[]`. The agent set `session["error"]` to the no-match 
message and returned without calling `suggest_outfit` or `create_fit_card`.

When running `suggest_outfit(results[0], get_empty_wardrobe())` the function 
returned general styling advice for the item ("consider pairing it with 
high-waisted jeans or a flowy skirt...") without crashing.

When running `create_fit_card('', results[0])` the function returned the 
descriptive error string without raising an exception.

**Milestone 5 Output:**

<img width="512" height="119" alt="image" src="https://github.com/user-attachments/assets/65d15b5e-6590-4b34-a375-fbd72d214a3d" />


## AI Usage:

**Instance 1** — `search_listings` implementation: 
I gave Claude the Tool 1 spec block from planning.md (inputs: `description`, `size`, `max_price`; returns: list of matching listing dicts sorted by relevance, or `[]` if none  match; failure: return `[]` without raising an exception) and asked it to  implement the function using `load_listings()`. I verified the generated code  skipped size and price filtering when those args were `None` and confirmed  the empty-list path returned `[]` before running tests.


**Instance 2** — `run_agent()` implementation: 
I gave Claude the Planning 
Loop, State Management, and Architecture diagram sections from planning.md 
and asked it to implement `run_agent()` in agent.py. I reviewed the generated 
code to confirm it branched on `search_listings` returning `[]` before 
accepting it, specifically checking that `suggest_outfit` and 
`create_fit_card` were not called unconditionally.

## Spec Reflection:

The empty wardrobe branch for `suggest_outfit` worked exactly as specced, 
returning general styling advice without treating it as an error kept the 
planning loop clean and avoided an unnecessary early return. The `.env` 
loading during testing required adding `load_dotenv()` explicitly to 
`test_tools.py` and debugging a API key fail(due to a typo earlier that was still in loaded env and not saved env), which wasn't anticipated in planning but didn't require any changes to the 
implementation itself.

One limitation discovered during testing is that `search_listings` 
relevance ranking doesn't always surface the most intuitive match — 
searching "leather miniskirt" returned Platform Mary Janes (which 
contains "leather" in its description) rather than a skirt, because 
the keyword match doesn't weight category or title over description 
text. In planning, relevance was described as "best matches first" 
without specifying how to break ties between a title match and a 
description match. A more precise spec would have defined relevance 
scoring explicitly (e.g. title matches weighted higher than description 
matches).

For example, searching "vintage graphic tee under $30, size M" (with 
quotes in the input) returned a Mesh Long-Sleeve Top, while the same 
query without quotes returned the Y2K Baby Tee — suggesting the query 
parser is sensitive to punctuation in ways the spec didn't anticipate.
