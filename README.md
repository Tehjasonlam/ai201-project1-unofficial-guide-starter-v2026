# The Unofficial Guide

Jason Lam — corpus: `city_guides`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a retrieval-augmented question-answering system built on `city_guides`,
a set of 14 travel guides covering nine small towns plus five cross-cutting
topics (eating, walking, regional transport, seasons, accessibility). It
answers concrete, factual questions about those towns — bus schedules,
opening hours, when a road is impassable, which town is easiest to visit with
limited mobility — by retrieving the specific guide section the answer lives
in and generating a short answer grounded only in that text, naming the source
file it used. Questions the corpus doesn't cover (unrelated trivia, anything
about a topic these guides never mention) are refused outright by a relevance
gate rather than answered with a guess.

## Chunking Strategy

**Chunk size:** one `## ` section per chunk (no fixed character count)
**Overlap:** none — sections don't need it, see below

Every document in `city_guides` is a short intro paragraph followed by four to
seven labelled sections — getting there, getting around, eat and drink, when
to go, and so on — each one a self-contained paragraph or two about one topic.
When I read them in Milestone 1, it was obvious the headings the author
already wrote were a far better chunk boundary than any character count:
`fallback_split` at the default 800/120 setting cuts straight through them.
Running it on `guide_kestrelford.md` produced a chunk that ends `## Eat and
drin` and the next one starts `he square and a handful of rooms` — a heading
sliced in half and a sentence sliced in half, in the same two chunks.

So `chunker.py::split_documents` now splits every document on its `## `
headings instead: the intro paragraph becomes one chunk, and each heading plus
its body becomes another. This means chunk size varies with the section's
actual content — the shortest is 100+ characters (see criterion 4) and the
longest is 760 — rather than being forced to a fixed number, and it means no
overlap is needed at all, because nothing is ever split mid-thought in the
first place; overlap exists to patch over a boundary cutting through
something, and here the boundary is the one the author already chose.

One thing I didn't get right the first time: a section like "## Getting
there" never repeats the town's name in its body, so two different towns'
"Getting there" sections looked nearly identical to the embedding model. I
fixed this by prefixing every section chunk with its document's `# Title`
line, so "Kestrelford" travels with its own "Getting there" section instead of
getting lost. Criterion 5 in `criteria.md` is the test I wrote to check that
this fix actually worked.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
# Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#6` — produced by: `chunker.py::split_documents`

```
Corry Vale

## When to go

May to September. Outside those months the pub in the third village closes, the farm shop reduces its hours, and several footpaths become genuinely boggy rather than merely wet. The road is not gritted above the second village and is impassable in snow.
```

**Chunk 3** — source: `guide_givens_mill.md#3` — produced by: `chunker.py::split_documents`

```
Givens Mill

## Eat and drink

A tearoom attached to the mill, open 10 to 4 daily except Tuesdays, which sells bread made from the flour ground twenty metres away and is the reason most people come. One pub, food served lunchtimes and Thursday to Saturday evenings.
```

**Chunk 4** — source: `guide_kestrelford.md#6` — produced by: `chunker.py::split_documents`

```
Kestrelford

## When to go

Late spring and early autumn. The Saturday market runs year-round but is much reduced from November to February. August is busy with walkers. The single-track approach road is genuinely difficult in snow and the town can be cut off for a day or two most winters.
```

**Chunk 5** — source: `guide_regional_transport.md#1` — produced by: `chunker.py::split_documents`

```
Getting around the region

## The railway

The line runs along the river valley, connecting Brightwater to the regional
hub in 50 minutes. Eleven services a day on weekdays, six on Sundays. The line
north of Brightwater closed in 1963 and everything beyond it is bus or car.

Tickets are cheaper booked the day before than on the day, and considerably
cheaper than that booked a week ahead. There is no ticket office at
Brightwater station outside weekday mornings; the machine on the platform takes
cards only.
```

## Sample Answer

**Question:** How often does the bus to Kestrelford run on weekdays?

**Answer:**

```
The bus to Kestrelford runs roughly hourly on weekdays (guide_kestrelford.md and guide_regional_transport.md).

Sources retrieved: guide_kestrelford.md, guide_regional_transport.md
(best distance 0.305, cutoff 0.6)
```

**My relevance cutoff:** 0.6 (the shipped default — measured, not just kept)

I ran my 5 test questions and the 5 `OUT_OF_SCOPE` questions through
`python app.py retrieve "..."` and recorded the best (lowest) distance each
one came back with. The in-corpus group landed between 0.229 and 0.481; the
out-of-scope group landed between 0.754 and 0.899. That's a clean gap of
almost 0.28 with no overlap, and 0.6 sits right in the middle of it, so I left
`THRESHOLD` at the default instead of moving it.

| Question | In corpus? | Best distance |
|---|---|---|
| How often does the bus to Kestrelford run on weekdays? | yes | 0.305 |
| What day of the week is the pub in Elder Ness closed? | yes | 0.250 |
| Is Marchwood's tram network step-free for wheelchair users? | yes | 0.442 |
| When does Kestrelford's Saturday market get much reduced? | yes | 0.229 |
| Which two towns are easiest to find a meal in on a Sunday evening? | yes | 0.481 |
| What is the capital of Mongolia? | no | 0.754 |
| How do I change the oil in a diesel engine? | no | 0.882 |
| Who won the 1994 World Cup? | no | 0.899 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.818 |
| How do I write a for loop in Rust? | no | 0.814 |

## How I Used AI

I built this project working directly with Claude Code end-to-end, but two
moments are worth calling out specifically because the first pass wasn't
right and needed a real correction, not just acceptance.

**1.** For the chunker, I asked for a strategy suited to `city_guides`
specifically, rather than a generic one. The first version split every
document on its `## ` headings, which fixed the obvious problem (fallback
chunking cutting sentences and headings in half). But reading the actual
retrieval output during Milestone 4 testing surfaced a second, less obvious
problem: a heading like "## Getting there" never repeats the town's name in
its body, so Kestrelford's and Halden Bay's "Getting there" sections read as
nearly identical text to the embedding model. That's not something you'd
catch by reading the chunker code — it only shows up once you run real
questions through retrieval and check *which* document came back. The fix was
prefixing every section chunk with its document's `# Title` line, and
criterion 5 in `criteria.md` exists specifically to check that fix actually
worked rather than just assuming it did.

**2.** For the relevance threshold, rather than leaving the shipped 0.6
default unexamined, I asked for it to be checked against this corpus
specifically. That meant actually running `app.py retrieve` on all 5 test
questions and all 5 `OUT_OF_SCOPE` questions and reading off the real
distances, instead of trusting that "0.6 is a reasonable starting point" from
`config.py`'s comment applied here unchanged. It turned out to hold — the two
groups came back at 0.229–0.481 and 0.754–0.899, a clean gap with 0.6 in the
middle — so the number in `config.py` didn't change, but that's a measured
result now, not an assumption carried over from the starter.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

Produced by `run_eval.py::main` (criteria 1-3) and a one-off check against
`chunker.py::split_documents` and `app.py retrieve` (criteria 4-5). Full raw
output: [`results/run_2026-09-22_0122_before.md`](results/run_2026-09-22_0122_before.md).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Every chunk is at least 100 characters | 98 of 98 | 94 of 98 | 94 of 98 | 94 of 98 | MISS |
| 5. Closest chunk is the *correct* source | 4 of 5 | 4 of 5 | 4 of 5 | 4 of 5 | MET |

Criteria 3 and 4 are each a single deterministic measurement (a gate
comparison against a fixed number, and a count over the chunk list), so the
same number is repeated in all three run columns rather than re-measured.
Criterion 5 is also deterministic — retrieval doesn't change between runs —
but I checked it by hand against all 5 questions rather than through
`run_eval.py`, so it's recorded here the same way.

Real output, from `run_eval.py::run_once`, question 3 (run 1) — the one that
turns out to matter for criterion 5:

```
### Is Marchwood's tram network step-free for wheelchair users? — run 1

- Best distance: 0.4416 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_marchwood.md

Yes, Marchwood has a modern tram network with level boarding on all four lines.

This information came from `guide_accessibility.md`.
```

Real output, from `run_eval.py::check_out_of_scope` (criterion 3):

```
Out-of-scope questions (the gate should refuse these):
  refused  (best distance 0.754)  What is the capital of Mongolia?
  refused  (best distance 0.882)  How do I change the oil in a diesel engine?
  refused  (best distance 0.899)  Who won the 1994 World Cup?
  refused  (best distance 0.818)  What is the recommended dosage of ibuprofen for a headache?
  refused  (best distance 0.814)  How do I write a for loop in Rust?
  -> gate refused 5 of 5
```

Real output, from the chunk-length check (criterion 4):

```
4 of 98 chunks are under 100 chars:
  guide_eating.md#0: '# Eating across the region'
  guide_regional_transport.md#0: '# Getting around the region'
  guide_seasons.md#0: '# When to visit the region'
  guide_walking.md#0: '# Walking in the region'
```

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer (4 of 5) | MET | All 5 questions passed `scorer.py`'s keyword check in all 3 runs, so the target held on every run, not just on average. |
| 2 | Every answer names a source (5 of 5) | MET | Read all 15 answer transcripts by hand: every single one names at least one `guide_*.md` filename in the answer text itself, matching what the structural enforcement in `generate.py` predicted. |
| 3 | Gate stops out-of-corpus questions (4 of 5) | MET | `run_eval.py::check_out_of_scope` refused all 5 `OUT_OF_SCOPE` questions, comfortably above target — the wide, clean distance gap from Milestone 4 held up. |
| 4 | Every chunk is at least 100 characters (98 of 98) | MISS | Counted directly: 94 of 98 pass, 4 don't. I set this target already suspecting it would miss (see criteria.md) — it did, exactly as predicted, and by exactly the 4 chunks I'd already identified. |
| 5 | Closest chunk is the correct source (4 of 5) | MET, but barely | 4 of 5 questions pass. It's a real MET, not a rounding call, but it's exactly at the target rather than comfortably above it like criteria 1-3 — one more failure would flip this to a MISS, so I'm treating it as the criterion worth watching rather than one that's actually solid. |

## Diagnoses

**Criterion 4 (chunking stage).** `chunker.py::_sections` treats everything
before a document's first `## ` heading as one preamble chunk. For nine of the
fourteen documents — the town guides — that preamble is a real sentence
("Kestrelford is a hill town of 12,000..."). For four of the five
cross-cutting guides (`guide_eating.md`, `guide_walking.md`,
`guide_seasons.md`, `guide_regional_transport.md`), the author wrote no
lead-in sentence at all — the document goes straight from its `# Title` line
into its first `## ` heading — so the "preamble" `_sections` extracts is
nothing but that title line, 23-27 characters, with no content. The mechanism
is specifically the *absence* of an authored intro paragraph in those four
files, not a flaw in the splitting logic itself: the code is doing exactly
what it's supposed to, on input that happens to be empty.

**Criterion 5 (retrieval stage), MET but worth diagnosing anyway.** The one
miss — "Is Marchwood's tram network step-free for wheelchair users?" — ranks
`guide_marchwood.md`'s own "Getting around" section first (distance 0.4416),
ahead of `guide_accessibility.md`'s section that actually states "level
boarding on all four lines" (distance 0.5672, rank 3). Both sections are about
the same town and the same general topic (getting around Marchwood), so they
embed close together; only one of them happens to contain the accessibility
fact. This isn't a chunking problem — both sections are already clean,
complete, well-formed chunks — it's that "closest by topic" and "contains the
answer" aren't always the same chunk when two documents cover overlapping
ground. The system still answered correctly, because `top_k=5` pulled in the
accessibility chunk anyway even at rank 3, but criterion 5 exists precisely to
notice that the *closest* one wasn't the *right* one, and it did.

No pattern links the two — one is missing source content, the other is
competing documents on the same topic — so this is genuinely two separate
things to think about, not one problem wearing two names.

## The Improvement

**What I changed:** In `chunker.py::_sections`, a document's preamble (the
text before its first `## ` heading) is now only kept as its own chunk when
it contains a real lead-in sentence beyond the `# Title` line. If stripping
the title line out of the preamble leaves nothing, no standalone preamble
chunk is emitted at all — the title still reaches every section chunk through
the existing title-prefix, so nothing is lost, only the empty stub is
dropped.

**Why I picked it:** This is the direct fix for the criterion 4 diagnosis
above — four chunks existed purely because four documents have no intro
sentence, and a chunk that's just a title can't contain an answer to
anything. Re-indexing after the change: 94 chunks total, all of them at least
174 characters, zero under 100.

### Run Log — After

Produced the same way as the before log: `run_eval.py::main` for criteria
1-3, a direct check for criteria 4-5. Full raw output:
[`results/run_2026-09-22_0126_after.md`](results/run_2026-09-22_0126_after.md).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Every chunk is at least 100 characters | 98 of 98 (now 94 of 94) | 94 of 94 | 94 of 94 | 94 of 94 | MET |
| 5. Closest chunk is the *correct* source | 4 of 5 | 4 of 5 | 4 of 5 | 4 of 5 | MET |

Real output, from the chunk-length check, after the fix:

```
0 of 94 chunks under 100 chars
```

Real output, from `run_eval.py::check_out_of_scope`, after the fix — note the
out-of-scope distances moved (the stub chunks that used to rank closest for
some of these are gone), but the verdict didn't:

```
Out-of-scope questions (the gate should refuse these):
  refused  (best distance 0.803)  What is the capital of Mongolia?
  refused  (best distance 0.882)  How do I change the oil in a diesel engine?
  refused  (best distance 0.975)  Who won the 1994 World Cup?
  refused  (best distance 0.818)  What is the recommended dosage of ibuprofen for a headache?
  refused  (best distance 0.814)  How do I write a for loop in Rust?
  -> gate refused 5 of 5
```

**Did it help?** Yes, and cleanly: criterion 4 goes from MISS (94 of 98) to
MET (94 of 94), because the fix removed exactly the 4 chunks that were
causing the miss and nothing else. Criteria 1, 2 and 3 stayed at 5 of 5,
unchanged — the fix touched only the four documents with no intro sentence,
not the town guides my test questions ask about, so there was no reason to
expect movement there and there wasn't any. Criterion 5 also stayed at 4 of
5, exactly as expected: the Marchwood/accessibility mismatch this fix didn't
touch is a retrieval-stage issue (two documents genuinely competing on
topic), not a chunking-stage one, so a chunking fix was never going to move
it. I didn't get a lucky improvement I can't explain — I got the one specific
number I targeted to move, and nothing else did.

## What's Still Broken

All five criteria are MET after the fix, but I don't think that means nothing
is left — criterion 5 is MET at exactly 4 of 5, the same as before the
improvement, and I already flagged it in the Verdicts table as the one worth
watching rather than trusting.

The mechanism (from Diagnoses, unchanged by the fix I made): when two
different documents cover the same town and a similar-sounding topic —
Marchwood's own "Getting around" section, and the accessibility guide's
Marchwood entry, both about getting around Marchwood — the one that's
topically closest to the question isn't always the one with the fact in it.
`top_k=5` papers over this for now, because the right chunk still gets into
the context window even at rank 3. But that's the retrieval margin doing the
work, not the ranking being right, and a corpus with more overlapping
documents per town — or a `top_k` set any lower — would expose it directly.

If I kept going, the fix I'd try is reranking: after the initial vector
search, add a second pass that also weights whether the question's likely
subject (a town name, extracted from the question text) matches the town name
already prefixed onto each chunk — a cheap keyword boost on top of the
embedding distance, rather than a second model call. I stopped short of
building this because it's a real design change to `store.py::search`'s
return contract, not a one-line fix, and I wanted the "before/after" pair in
this unit to isolate one variable (the chunker) rather than two.

I also want to be honest that criterion 3's target (4 of 5) never got
seriously tested — the gate refused all 5 out-of-scope questions in every run
I made, before and after, with a wide and in fact widening margin. That's a
real result, not a fabricated one, but five hand-picked, obviously-unrelated
questions were never going to stress this the way a question that's
*almost* in scope would. If I revisited this criterion I'd want at least one
adversarial case — a question about, say, hiking or weather in general,
close enough to travel-guide territory to actually test the boundary instead
of confirming what I already knew.

## What I'd Do Differently

Criterion 1 is the one I'd rewrite. I set a 4-of-5 target and reasoned about
which single question I expected to be hardest (the Sunday-evening one, an
exception clause rather than a flat fact) — but that question passed cleanly
in every run, while the actual near-miss showed up on a completely different
criterion (5) that I'd written for an unrelated reason (testing the
title-prefix fix). My risk assessment for criterion 1 wasn't wrong exactly,
it was just aimed at the wrong axis: I was predicting which *question* would
be hard, when the real risk in this corpus turned out to be about which
*documents* overlap, a property of the corpus's structure rather than of any
one question's phrasing. Next time I'd write criterion 1's "why this target"
by first mapping which documents share topics across town guides and
cross-cutting guides, and treat any question whose answer could plausibly
live in either as the risky one — that would have pointed straight at the
Marchwood question, which is exactly the one that ended up mattering, just
under a different criterion number.

I'd also design criterion 3's test harder on purpose — not by changing the
4-of-5 target itself, but by deliberately picking at least one out-of-scope
question that's adjacent to the corpus (about hiking, or weather, or public
transport in general — topics these guides touch without being about)
instead of five questions that are all obviously unrelated. As written, the
criterion measured something true but not very informative; a harder version
of the same test would have actually located where the gate's boundary is
instead of confirming that it exists somewhere comfortably far away.
