"""
Bulgarian Measurement Unit Normalization
==========================================
Converts a number followed by a unit to spoken Bulgarian form, using the
count form (бройна форма) of the unit and gender agreement for the number.

- 1 км     → "един километър"
- 10 km    → "десет километра"
- 2 мин.   → "две минути"
- -5°C     → "минус пет градуса"
- 85.5 кв.м → "осемдесет и пет цяло и пет десети квадратни метра"
"""

import re

from .bg_numbers import number_to_words_cardinal, float_to_words
from .bg_punctuation import sentence_period

_BARE_GRAM = r'g|г'

# (token regex, singular, count form, gender, may end with a period)
# Order matters: longer tokens must come before their prefixes (км/ч before км).
UNITS = [
    (r'°\s*C|℃', 'градус', 'градуса', 'm', True),
    (r'km/h|км/ч', 'километър в час', 'километра в час', 'm', True),
    (r'm/s|м/с', 'метър в секунда', 'метра в секунда', 'm', True),
    (r'кв\.\s?м|m²|м²', 'квадратен метър', 'квадратни метра', 'm', True),
    (r'куб\.\s?м|m³|м³', 'кубически метър', 'кубически метра', 'm', True),
    (r'km|км', 'километър', 'километра', 'm', True),
    (r'cm|см', 'сантиметър', 'сантиметра', 'm', True),
    (r'mm|мм', 'милиметър', 'милиметра', 'm', True),
    (r'kg|кг', 'килограм', 'килограма', 'm', True),
    (r'mg|мг', 'милиграм', 'милиграма', 'm', True),
    (r'ml|мл', 'милилитър', 'милилитра', 'm', True),
    (r'мин', 'минута', 'минути', 'f', True),
    (r'сек', 'секунда', 'секунди', 'f', True),
    (r'стр', 'страница', 'страници', 'f', True),
    (r'дка', 'декар', 'декара', 'm', True),
    (r'ha|ха', 'хектар', 'хектара', 'm', True),
    (r'гр', 'грам', 'грама', 'm', True),
    # "г." after a number is a year (2020 г.), so grams only without a period
    (_BARE_GRAM, 'грам', 'грама', 'm', False),
    (r'°', 'градус', 'градуса', 'm', True),
    (r'm|м', 'метър', 'метра', 'm', True),
    (r'l|л', 'литър', 'литра', 'm', True),
    (r'т', 'тон', 'тона', 'm', True),
    (r'ч', 'час', 'часа', 'm', True),
]

_SIGN_WORDS = {'-': 'минус', '−': 'минус', '+': 'плюс'}

# "през 2020 г" is a year, not grams
_YEAR_PREPOSITIONS = {'през', 'в', 'във', 'от', 'до', 'около', 'след', 'преди',
                      'към', 'между', 'за', 'и'}


def _is_year_without_period(m) -> bool:
    if not 1000 <= float(m.group(2).replace(',', '.')) <= 2100 or m.group(1):
        return False
    before = m.string[:m.start()].split()
    return bool(before) and before[-1].lower() in _YEAR_PREPOSITIONS

_UNIT_PATTERNS = [
    (token, re.compile(
        r'(?:(?<![\w.,:/+\-−])([-−+]))?'      # optional sign, not a range (5-10)
        r'(?<![\w.,:/])(\d+(?:[.,]\d+)?)'     # the number, not part of a date/time
        r'\s*(?:' + token + r')(?![\w-])'     # not г-жа, км-та
        + (r'(?!\.\w)(\.)?' if allow_period else r'(?!\.)()')
    ), singular, plural, gender)
    for token, singular, plural, gender, allow_period in UNITS
]


# Time units read with "и половина": "час и половина", "две години и половина"
HALVABLE_UNITS = {'година', 'месец', 'седмица', 'ден', 'час', 'минута', 'секунда'}

# Plural (or singular) as written after a number → (singular, plural, gender)
TIME_NOUNS = {
    'години': ('година', 'години', 'f'), 'година': ('година', 'години', 'f'),
    'месеца': ('месец', 'месеца', 'm'), 'месец': ('месец', 'месеца', 'm'),
    'седмици': ('седмица', 'седмици', 'f'), 'седмица': ('седмица', 'седмици', 'f'),
    'дни': ('ден', 'дни', 'm'), 'дена': ('ден', 'дни', 'm'), 'ден': ('ден', 'дни', 'm'),
    'часа': ('час', 'часа', 'm'), 'час': ('час', 'часа', 'm'),
    'минути': ('минута', 'минути', 'f'), 'минута': ('минута', 'минути', 'f'),
    'секунди': ('секунда', 'секунди', 'f'), 'секунда': ('секунда', 'секунди', 'f'),
}


def half_quantity_to_words(whole: int, singular: str, plural: str,
                           gender: str = 'm') -> str:
    """
    Read a whole-and-a-half amount: (1, "година") → "година и половина",
    (2, "година") → "две години и половина", (0, "час") → "половин час".
    """
    if whole == 0:
        return f"половин {singular}"
    if whole == 1:
        return f"{singular} и половина"
    return f"{number_to_words_cardinal(whole, gender)} {plural} и половина"


def quantity_to_words(number: str, singular: str, plural: str,
                      gender: str = 'm') -> str:
    """
    Read a number with a counted noun: ("1", "километър", "километра") →
    "един километър"; ("2", "минута", "минути", "f") → "две минути".
    Decimals take the count form: "1.5" → "едно цяло и пет десети ...",
    except halves of time units: "1.5" часа → "час и половина".
    """
    number = number.replace(',', '.')
    if '.' in number and number.split('.', 1)[1].strip('0'):
        whole, fraction = number.split('.', 1)
        if fraction.rstrip('0') == '5' and singular in HALVABLE_UNITS:
            return half_quantity_to_words(int(whole or 0), singular, plural, gender)
        return f"{float_to_words(number)} {plural}"
    n = int(float(number)) if '.' in number else int(number)
    unit = singular if n == 1 else plural
    return f"{number_to_words_cardinal(n, gender)} {unit}"


def normalize_units(text: str) -> str:
    """Expand every "<number> <unit>" in the text to spoken form."""
    for token, pattern, singular, plural, gender in _UNIT_PATTERNS:
        def unit_repl(m, token=token, singular=singular, plural=plural, gender=gender):
            if token == _BARE_GRAM and _is_year_without_period(m):
                return m.group(0)
            words = quantity_to_words(m.group(2), singular, plural, gender)
            if m.group(1):
                words = _SIGN_WORDS[m.group(1)] + ' ' + words
            if m.group(3):
                words += sentence_period(m.string, m.end())
            return words
        text = pattern.sub(unit_repl, text)
    return text
