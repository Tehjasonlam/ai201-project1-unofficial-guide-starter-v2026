# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** After chunking `city_guides` on its `## ` section
headings (see Chunking Strategy below), every chunk is one complete,
self-contained section — one town, one topic, never split mid-thought. That
should make retrieval reliable for questions that live inside a single
section. The one I expect to be hardest is my fifth question ("which two
towns are easiest to find a meal on a Sunday evening"), because the answer is
an exception clause buried in the middle of `guide_eating.md`'s "Local
specifics" section rather than a single flatly-stated fact, so I'm leaving
room for one miss rather than claiming 5 of 5.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** This isn't left to the model's discretion — `store.py`
attaches the source filename to every chunk as metadata, and `generate.py`'s
system instruction requires the model to name the file it used, on top of the
gate already having refused anything too far off-topic to answer from. Because
it's enforced structurally rather than hoped for, I'm holding this one to all
five, not four — the only way to miss it is the model ignoring an explicit
instruction it's given every single time.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** I ran my 5 test questions and the 5 `OUT_OF_SCOPE`
questions through `app.py retrieve` at the shipped 0.6 cutoff. In-corpus best
distances came back 0.229, 0.250, 0.305, 0.442, 0.481. Out-of-scope best
distances came back 0.754, 0.818, 0.822, 0.882, 0.899. That's a clean, wide
gap — 0.481 to 0.754, no overlap — and 0.6 sits comfortably in the middle of
it, so I'm keeping the shipped default rather than moving it. All 10 of my 10
questions actually landed on the correct side of 0.6, which would justify a
5-of-5 target, but I'm writing down 4 of 5 anyway: five questions is a small
enough sample that I don't want to promise a target my measurement can't
actually distinguish from noise.

---

## 4. Every chunk has real content in it

Every one of my chunks (98 of 98) is at least 100 characters long.

**Why this target:** When I ran `python app.py chunks -n 5` after switching to
section-heading chunking, the shortest chunks it showed me were suspiciously
short. I checked the length distribution directly and found four chunks under
100 characters — each one is a bare `# Title` line with no lead-in sentence
before the first `## ` heading. That happens for four of the five
cross-cutting guides (`guide_eating.md`, `guide_walking.md`,
`guide_seasons.md`, `guide_regional_transport.md` — `guide_accessibility.md`
is the exception, with a two-sentence intro of its own) which jump straight
into their first heading, unlike all nine town guides, which open with a
one-to-three-sentence description of the town before their first heading. A chunk with nothing but a
title in it can't answer anything, so I'm setting the target at zero
exceptions rather than "most chunks," even though I already know it will miss.


---

## 5. The retrieved source is the *correct* one, not just *a* one

For at least 4 of my 5 test questions, the single closest retrieved chunk's
source file is the document that actually contains the answer — not merely a
document that happens to mention the same town or topic.

**Why this target:** A section like "## Getting there" never repeats the
town's name in its own body text, so without help the embedding for a
Kestrelford travel question could just as easily match Halden Bay's "Getting
there" section — same heading, same kind of sentence, wrong town. My fix was
to prefix every section chunk with its document's `# Title` line (see
Chunking Strategy), specifically so the town name rides along with each
section. This criterion is the direct test of whether that decision actually
worked, which criterion 2 (merely names *a* source) doesn't check. I'm holding
it to 4 of 5 rather than 5 of 5 for the same reason as criterion 1 — my fifth
question is the one whose answer lives in a cross-cutting document rather than
a single town's guide, so "the correct source" for it is less clear-cut.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
