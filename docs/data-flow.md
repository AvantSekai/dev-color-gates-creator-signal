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
        v
 Does answering this call for looking something up, or ranking creators?
        |
        +-- yes --> Claude calls a tool:
        |             rank_creators / get_creator_stats / compare_creators
        |                   |
        |                   v
        |             The tool runs real code (pandas) over the CSV and
        |             returns real numbers -- nothing is guessed here.
        |             The exact call and its result are recorded as a
        |             "source" for this answer.
        |
        +-- no ---> No tool runs. Whatever Claude says next is pure
                     reasoning, with nothing to check it against.
        |
        v
 Claude writes the answer.
        |
        v
 A second, tool-free check: did that answer just report the tool's
 numbers, or did it also add judgment/interpretation on top?
        |
        +-- no tool ran at all --------------> "AI opinion"
        +-- tool ran, answer is pure numbers -> "Computed from data"
        +-- tool ran, answer adds judgment ---> "Opinion, grounded in data"
        |
        v
 Answer + label + sources sent back to the browser and shown in the chat.
 Expanding "Data used" on any grounded answer shows exactly which tool
 ran, what it was asked, and what it returned -- so you can check
 whether the AI's judgment on top of that data was the right call.
```

The key design choice: **the label isn't a note the model adds to its own answer** — it's decided
by the backend from what actually happened (did a tool run, and does the answer go beyond what it
returned), and the underlying data is always shown alongside it. The model can't fake a "Computed
from data" label on a guess, because that label only applies when a real tool ran, returned real
numbers, and the answer added nothing on top of them.

See `README.md` for the "promising" definition and `docs/accuracy-honesty.md` for why this
design keeps the AI honest for a non-technical reader.
