# Keeping the AI Honest (Plain English)

The chat answers questions three different ways, and the app tells you which one it used —
plus, for anything grounded in real data, exactly what data that was.

1. **"Computed from data"** — For questions like "what's reus.fx's total views?", the AI doesn't
   guess. It asks a small piece of code to actually calculate the answer from the real
   spreadsheet of TikTok data, and just reports that number. It's physically not able to make up
   a name or a number here — the answer has to match what's actually in the data.

2. **"Opinion, grounded in data"** — Most real questions are a mix. "Would this creator fit a
   skincare brand?" isn't something a spreadsheet can answer on its own, but a good answer still
   starts from that creator's real numbers. The AI pulls the real stats first, then adds its own
   read on top — and the app labels the whole answer as opinion (not fact), even though part of
   it is backed by real numbers underneath.

3. **"AI opinion"** — For questions with no data to ground them at all (e.g. general
   brand-partnership advice), the AI answers purely from its own reasoning.

**You can always see the receipts.** Any answer labeled "Computed from data" or "Opinion,
grounded in data" has a "Data used" section you can expand — it shows exactly which lookup ran,
what was asked, and what came back. That means you don't have to just trust the label: you can
check the underlying numbers yourself and decide whether the AI's read on top of them was the
right call.

Why this matters: it would be easy for an AI tool to sound equally confident about a real number
and a guess, which is how people end up trusting a guess as if it were a fact. Labeling the three
cases differently — and showing the underlying data instead of just a badge — means you always
know whether you're looking at a real number, a reasoned guess, or something in between, and you
have what you need to double-check it.
