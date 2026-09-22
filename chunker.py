"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_TITLE_RE = re.compile(r"^#\s+(.+)")


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _sections(text: str) -> list[tuple[str, str]]:
    """Split one document's text on its `## ` headings.

    Returns a list of (heading, body) pairs. Anything before the first `## `
    heading (the `# Title` line and any intro paragraph) comes back as one
    entry with heading `""`. A document with no `## ` headings at all comes
    back as a single `("", text)` pair.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [("", text.strip())]

    sections = []
    preamble = text[: matches[0].start()].strip()
    intro = _TITLE_RE.sub("", preamble, count=1).strip()
    # A preamble that's nothing but the "# Title" line, with no lead-in
    # sentence of its own, carries no information the title prefix on every
    # later section chunk doesn't already carry — see criterion 4 in
    # criteria.md. Emitting it as its own chunk just produces a stub.
    if intro:
        sections.append(("", preamble))

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end() : end].strip()
        sections.append((m.group(1).strip(), body))

    return sections


def _title(text: str) -> str:
    m = _TITLE_RE.match(text)
    return m.group(1).strip() if m else ""


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on their `## ` section headings.

    Every document in `city_guides` is a short intro plus four to seven
    labelled sections (getting there, eating, when to go...) and the useful
    information for any one question sits entirely inside one section. Cutting
    on character count instead — the fallback's approach — slices straight
    through headings and mid-sentence: `fallback_split` on this corpus produces
    chunks that end "## Eat and drin" and start "he square and a handful of
    rooms". Splitting on the heading boundary the author already put there
    keeps every section whole instead.

    Each section chunk is prefixed with the document's `# Title` line (except
    the intro chunk, which already starts with it) because sections like
    "## Getting there" never repeat the town's name in their body text — the
    embedding needs "Kestrelford" attached to "Getting there" to tell one
    town's travel section from another's.

    A document with no `## ` headings at all (none exist in this corpus, but
    `ingest.py` would happily load one) falls back to one whole-document chunk
    if it's short, or to `fallback_split` if it's longer than CHUNK_SIZE — so
    this never silently produces a single giant chunk.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        sections = _sections(doc.text)

        if len(sections) == 1 and not sections[0][0]:
            body = sections[0][1]
            if len(body) <= config.CHUNK_SIZE:
                chunks.append(
                    Chunk(text=body, source=doc.source, index=0,
                          produced_by="chunker.py::split_documents")
                )
            else:
                for c in fallback_split([doc]):
                    c.produced_by = "chunker.py::split_documents"
                    chunks.append(c)
            continue

        title = _title(doc.text)
        index = 0
        for heading, body in sections:
            if not body:
                continue
            if heading:
                text = f"{title}\n\n## {heading}\n\n{body}" if title else f"## {heading}\n\n{body}"
            else:
                text = body
            chunks.append(
                Chunk(text=text, source=doc.source, index=index,
                      produced_by="chunker.py::split_documents")
            )
            index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
