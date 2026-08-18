# Data Flow: Question to Answer

How a question typed into the chat screen becomes an answer.

```
 You type a question
        |
        v
 POST /api/chat  (FastAPI backend)
        |
        v
 Claude (Sonnet 5) reads the question
        |
        +-- Is this answerable by looking something up or ranking creators?
        |         |
        |        yes
        |         |
        |         v
        |   Claude calls a tool:
        |     rank_creators / get_creator_stats / compare_creators
        |         |
        |         v
        |   The tool runs real code (pandas) over the CSV
        |   and returns real numbers -- nothing is guessed here.
        |         |
        |         v
        |   Claude phrases the numbers as a plain-English answer.
        |   -> labeled "Computed from data"
        |
        +-- Is this a judgment call (brand fit, content style, etc.)?
                  |
                 yes
                  |
                  v
            No tool fits, so Claude answers from its own reasoning.
                  |
                  v
            -> labeled "AI opinion"
        |
        v
 Answer + label sent back to the browser and shown in the chat
```

The key design choice: **the label isn't a note the model adds to its own answer** — it's set by
the backend, based on whether a tool actually ran during that turn. The model has no way to fake
a "Computed from data" label on a guess, because that label only gets attached when real code
executed and returned real numbers.

See `README.md` for the "promising" definition and `docs/accuracy-honesty.md` for why this
design keeps the AI honest for a non-technical reader.
