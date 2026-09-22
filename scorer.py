"""
Unit 2: decides whether an answer counts as correct.

`run_eval.py` looks for a function called `judge` here and, if it finds one,
uses it to fill in the Run columns of the run log instead of leaving them
blank for me to read by hand.

judge(question, expects, answer, results) -> bool
"""

import gate


def judge(question: str, expects: str, answer: str, results) -> bool:
    """
    An answer passes if it isn't a refusal and it mentions the keyword I wrote
    down in questions.py's `expects` field when I wrote the question — before
    I'd seen any answers, so it's checking against what I predicted, not what
    came back.

    This is a keyword check, not a semantic one, on purpose: every one of my
    five questions has a specific, short, checkable fact as its answer (a bus
    frequency, a day of the week, a month), so if the answer text doesn't
    contain the word I expected, something is actually wrong rather than the
    model just having phrased it differently.
    """
    if answer.strip() == gate.REFUSAL:
        return False
    return expects.strip().lower() in answer.lower()
