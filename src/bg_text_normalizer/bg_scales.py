"""
Bulgarian Scale Word Normalization
====================================
Expands a number followed by a scale word or its abbreviation
(хил., млн., млрд.), with an optional currency after it or before it.

- 1 млн.       → "един милион"
- 2 млн.       → "два милиона"
- 5 хил.       → "пет хиляди"
- 1,5 млн.     → "един и половина милиона"
- 2,3 млн.     → "две цяло и три десети милиона"
- 3 млрд. лв.  → "три милиарда лева"
- €1,5 млн.    → "един и половина милиона евро"
"""

import re

from .bg_numbers import number_to_words_cardinal, float_to_words
from .bg_currency import CURRENCY_INFO, CURRENCY_SUFFIXES, CURRENCY_PREFIXES
from .bg_punctuation import sentence_period

# abbreviation → (full words, singular, plural, gender, multiplier)
SCALES = {
    'млрд': (r'милиарда|милиард', 'милиард', 'милиарда', 'm', 1_000_000_000),
    'млн': (r'милиона|милион', 'милион', 'милиона', 'm', 1_000_000),
    'хил': (r'хиляди|хиляда', 'хиляда', 'хиляди', 'f', 1_000),
}

_ALL_SUFFIXES = '|'.join(CURRENCY_SUFFIXES.values())
_ALL_PREFIXES = '|'.join(CURRENCY_PREFIXES.values())


def _currency_code(token: str, table: dict) -> str:
    for code, tokens in table.items():
        if re.fullmatch(tokens, token):
            return code
    return 'BGN'


def scaled_number_to_words(whole: int, fraction: str, scale: str) -> str:
    """
    Read a number with a scale word: (1, "5", "млн") → "един и половина милиона".
    `fraction` holds the digits after the decimal point ("" for none).
    """
    _, singular, plural, gender, multiplier = SCALES[scale]
    fraction = fraction.rstrip('0')
    if not fraction:
        return number_to_words_cardinal(whole * multiplier)
    if fraction == '5':
        if whole == 0:
            return f"половин {singular}"
        return f"{number_to_words_cardinal(whole, gender)} и половина {plural}"
    return f"{float_to_words(f'{whole}.{fraction}')} {plural}"


def normalize_scales(text: str) -> str:
    """Expand every "<number> <scale word>" in the text to spoken form."""
    for scale, (full_words, _, _, _, _) in SCALES.items():
        pattern = (
            r'(?:(?<!\w)(' + _ALL_PREFIXES + r')\s*)?'
            r'(?<![\w.,:/])(\d+)(?:[.,](\d+))?\s*'
            r'(?:' + scale + r'(?!\w)(\.(?!\w))?|(?:' + full_words + r')(?!\w))'
            r'(?:\s*(' + _ALL_SUFFIXES + r')(?!\w)(\.(?!\w))?)?'
        )

        def scale_repl(m, scale=scale):
            words = scaled_number_to_words(int(m.group(2)), m.group(3) or '', scale)
            prefix, scale_period, suffix, currency_period = (
                m.group(1), m.group(4), m.group(5), m.group(6))
            if suffix:
                code = _currency_code(suffix, CURRENCY_SUFFIXES)
            elif prefix:
                code = _currency_code(prefix, CURRENCY_PREFIXES)
            else:
                code = None
            if code:
                words += ' ' + CURRENCY_INFO[code]['main_plural']
            # The period belongs to the last abbreviation in the match
            last_period = currency_period if suffix else scale_period
            if last_period:
                words += sentence_period(m.string, m.end())
            return words

        text = re.sub(pattern, scale_repl, text)
    return text
