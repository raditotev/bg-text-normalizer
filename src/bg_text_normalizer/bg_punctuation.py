"""
Sentence Punctuation Helpers
==============================
Decides what happens to the period of an expanded abbreviation.

"Платих 5 лв. за книга." → the period belongs to "лв." only → dropped.
"Платих 5 лв. После..."  → the period also ends the sentence → kept.
"""

_CLOSERS = '"\'»“”)]'


def sentence_period(text: str, end: int) -> str:
    """
    Return '.' if the abbreviation period ending at `end` also ends the
    sentence, '' otherwise.

    The period ends the sentence when only whitespace or closing quotes and
    brackets follow it, or when the next word starts with a capital letter.
    """
    rest = text[end:].lstrip().lstrip(_CLOSERS).lstrip()
    return '.' if not rest or rest[0].isupper() else ''
