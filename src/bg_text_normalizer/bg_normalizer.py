"""
Bulgarian Text Normalizer for TTS
==================================
Converts written Bulgarian text into its spoken form for TTS systems.
Handles: numbers, dates, times, currency, abbreviations, percentages,
         phone numbers, ordinals, Roman numerals, and more.

Usage:
    from bg_text_normalizer import BulgarianTextNormalizer
    normalizer = BulgarianTextNormalizer()
    text = normalizer.normalize("На 15.02.2026 г. в 14:30 ч. цената е 1500.50 лв.")
    # Output: "На петнадесети февруари две хиляди двадесет и шеста година в четиринадесет и тридесет часа цената е хиляда и петстотин лева и петдесет стотинки."
"""

import re

from .bg_numbers import (
    number_to_words_cardinal,
    number_to_words_ordinal,
    float_to_words,
    fraction_to_words,
    noun_gender,
    short_decimal_to_words,
)
from .bg_dates import normalize_date, normalize_year, MONTH_NAMES
from .bg_time import normalize_time
from .bg_currency import normalize_currency, CURRENCY_SUFFIXES, CURRENCY_PREFIXES
from .bg_abbreviations import normalize_abbreviations, expand_abbreviation
from .bg_phone import normalize_phone_number
from .bg_roman import roman_to_arabic
from .bg_units import (
    normalize_units, quantity_to_words, half_quantity_to_words, TIME_NOUNS,
)
from .bg_scales import normalize_scales
from .bg_punctuation import sentence_period


class BulgarianTextNormalizer:
    """Main normalizer class that orchestrates all sub-normalizers."""

    def __init__(self, expand_abbrevs: bool = True, verbose: bool = False):
        self.expand_abbrevs = expand_abbrevs
        self.verbose = verbose

    def normalize(self, text: str) -> str:
        """
        Normalize Bulgarian text for TTS.
        Applies normalizations in a specific order to avoid conflicts.
        """
        if not isinstance(text, str):
            raise TypeError(f"Expected str, got {type(text).__name__}")
        if not text.strip():
            return text

        original = text

        # Step 1: Collapse space-separated large numbers: 7 000 000 → 7000000
        text = self._collapse_spaced_numbers(text)

        # Step 2: Year ranges: 2025/2026 г., сезон 2024/2025
        text = self._normalize_year_ranges(text)

        # Step 3: Number ranges: 5-10 км → 5 до 10 км
        text = self._normalize_number_ranges(text)

        # Step 4: Scale words (before currency, since €1,5 млн. is not €1.50)
        # Matches: 1,5 млн., 5 хил., 3 млрд. лв., 2 хиляди
        text = normalize_scales(text)

        # Step 5: Currency (before dates, since 12.05 € could match as a date)
        # Matches: 1500.50 лв., 25 лв, $100, €50, 100 EUR
        text = self._normalize_currency(text)

        # Step 6: Number + unit (before dates, since 3.5 кг could match as a date)
        # Matches: 10 км, 1 км, 5°C, -5°C, 60 км/ч, 2 мин.
        if self.expand_abbrevs:
            text = normalize_units(text)

        # Step 7: Abbreviations (units are already done)
        if self.expand_abbrevs:
            text = normalize_abbreviations(text, include_units=False)

        # Step 8: Percentages (before dates, since 15.5% could match as date)
        text = self._normalize_percentages(text)

        # Step 9: Dates (before generic numbers, since dates contain numbers)
        # Matches: 15.02.2026, 15.02.2026 г., 15/02/2026, 15-02-2026
        text = self._normalize_dates(text)

        # Step 10: Time (before generic numbers)
        # Matches: 14:30, 14:30 ч., 9:05 часа
        text = self._normalize_times(text)

        # Step 11: Phone numbers
        text = self._normalize_phones(text)

        # Step 12: Roman numerals (before generic numbers)
        text = self._normalize_roman_numerals(text)

        # Step 13: Symbols (№, &, etc.)
        text = self._normalize_symbols(text)

        # Step 14: Ordinal numbers (before cardinals)
        # Matches: 1-ви, 2-ри, 3-ти, 15-ти, 1-ва, 2-ра
        text = self._normalize_ordinals(text)

        # Step 15: Standalone years (4-digit numbers that look like years)
        text = self._normalize_standalone_years(text)

        # Step 16: Cardinal numbers (generic number-to-words)
        text = self._normalize_cardinal_numbers(text)

        # Step 17: Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        if self.verbose and text != original:
            print(f"[NORM] '{original}' -> '{text}'")

        return text

    def _collapse_spaced_numbers(self, text: str) -> str:
        """Collapse space-separated digit groups into single numbers.
        E.g., '7 000 000' → '7000000', '1 500' → '1500'
        But not 'в 5 часа' (single digits followed by words).
        """
        # Match digit groups separated by spaces where each group after first is exactly 3 digits
        pattern = r'\b(\d{1,3})((?:\s\d{3})+)\b'
        def collapse_repl(m):
            full = m.group(0).replace(' ', '')
            return full
        text = re.sub(pattern, collapse_repl, text)
        return text

    def _normalize_year_ranges(self, text: str) -> str:
        """Read 2025/2026 г. or сезон 2024/2025 as two years.

        A pair of years is a range when "г."/"година" follows it or when the
        years are consecutive. Otherwise "1500-1800 км" would become years.
        """
        pattern = (r'(?<![\w.,/\-–])(\d{4})\s?[/\-–]\s?(\d{4})(?![\w/\-–])'
                   r'(?:\s*(?:г(?!\w)(\.)?|(година)(?!\w)))?')
        def year_range_repl(m):
            first, second = int(m.group(1)), int(m.group(2))
            has_suffix = m.group(0).rstrip('.').endswith(('г', 'година'))
            if not (1000 <= first <= 2100 and 1000 <= second <= 2100):
                return m.group(0)
            if not has_suffix and second != first + 1:
                return m.group(0)
            # Same century: "2024-2025" → "две хиляди двадесет и четвърта, двадесет и пета"
            if first // 100 == second // 100 and second % 100:
                second_words = number_to_words_ordinal(second % 100, gender='f')
            else:
                second_words = normalize_year(second)
            words = normalize_year(first) + ', ' + second_words
            if has_suffix:
                words += ' година'
                if m.group(3):
                    words += sentence_period(m.string, m.end())
            return words
        return re.sub(pattern, year_range_repl, text)

    def _normalize_number_ranges(self, text: str) -> str:
        """Turn the dash of a two-number range into "до": 5-10 км → 5 до 10 км.

        Three-part forms (15-02-2026, 0888-123-456) and numbers with a
        leading zero are left for the date and phone steps.
        """
        pattern = (r'(?<![\w.,:/\-–])([1-9]\d{0,3}|0)(?:-|\s?–\s?)([1-9]\d{0,3}|0)'
                   r'(?![\w/]|[.,]\d|\s?[-–]\s?\d)')
        def range_repl(m):
            before = m.string[:m.start()].split()
            # "между 15 и 20", otherwise "5 до 10"
            joiner = 'и' if before and before[-1].lower() == 'между' else 'до'
            return f'{m.group(1)} {joiner} {m.group(2)}'
        return re.sub(pattern, range_repl, text)

    def _normalize_symbols(self, text: str) -> str:
        """Normalize special symbols."""
        text = text.replace('№', 'номер ')
        text = text.replace('&', ' и ')
        return text

    def _normalize_dates(self, text: str) -> str:
        """Normalize date patterns."""
        # Full date with year: 15.02.2026 г. or 15.02.2026
        pattern = r'\b(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})\s*г(?!\w)(\.)?'
        text = re.sub(pattern, lambda m: normalize_date(
            int(m.group(1)), int(m.group(2)), int(m.group(3)), include_year_suffix=True
        ) + (sentence_period(m.string, m.end()) if m.group(4) else ''), text)

        # Full date without г.: 15.02.2026
        pattern = r'\b(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})\b'
        text = re.sub(pattern, lambda m: normalize_date(
            int(m.group(1)), int(m.group(2)), int(m.group(3))
        ), text)

        # Fraction: 3/4, 1/2. Slash notation is only a date with all three parts.
        pattern = r'(?<![\d/])([1-9]\d{0,3})/(\d{1,4})(?![\d/])'
        def fraction_repl(m):
            numerator, denominator = int(m.group(1)), int(m.group(2))
            if denominator < 2:
                return (number_to_words_cardinal(numerator) + ' делено на '
                        + number_to_words_cardinal(denominator))
            return fraction_to_words(numerator, denominator)
        text = re.sub(pattern, fraction_repl, text)

        # Partial date: 15.02 (day.month, no year). The month needs two digits,
        # so 1.5 and 3.5 stay decimals.
        # Only match if not part of a longer number or followed by currency/unit
        pattern = r'\b(\d{1,2})\.(\d{2})\b(?!\.\d)(?!\s*(?:лв|лева|евро|долар|EUR|USD|BGN|GBP|%|ч\.|часа))'
        def partial_date_repl(m):
            day, month = int(m.group(1)), int(m.group(2))
            if 1 <= day <= 31 and 1 <= month <= 12:
                return normalize_date(day, month)
            return m.group(0)
        text = re.sub(pattern, partial_date_repl, text)

        # Date with month name: "15 май", "1 Януари 2026 г."
        month_names_pattern = '|'.join(MONTH_NAMES.values())
        month_name_to_num = {name.lower(): num for num, name in MONTH_NAMES.items()}

        # With year: "15 май 2026 г." or "15 май 2026"
        pattern = (r'\b(\d{1,2})\s+(' + month_names_pattern + r')\s+(\d{4})'
                   r'(?:\s*(г)(?!\w)(\.)?)?')
        def month_name_year_repl(m):
            day = int(m.group(1))
            month = month_name_to_num[m.group(2).lower()]
            year = int(m.group(3))
            has_suffix = m.group(4) is not None
            if 1 <= day <= 31:
                period = sentence_period(m.string, m.end()) if m.group(5) else ''
                return normalize_date(day, month, year, include_year_suffix=has_suffix) + period
            return m.group(0)
        text = re.sub(pattern, month_name_year_repl, text, flags=re.IGNORECASE)

        # Without year: "15 май"
        pattern = r'\b(\d{1,2})\s+(' + month_names_pattern + r')\b'
        def month_name_repl(m):
            day = int(m.group(1))
            month = month_name_to_num[m.group(2).lower()]
            if 1 <= day <= 31:
                return normalize_date(day, month)
            return m.group(0)
        text = re.sub(pattern, month_name_repl, text, flags=re.IGNORECASE)

        return text

    def _normalize_times(self, text: str) -> str:
        """Normalize time patterns."""
        # Time with ч./часа: 14:30 ч. or 14:30 часа
        pattern = r'\b(\d{1,2}):(\d{2})\s*(?:ч(?!\w)(\.)?|часа|часът)'
        text = re.sub(pattern, lambda m: normalize_time(
            int(m.group(1)), int(m.group(2)), include_suffix=True
        ) + (sentence_period(m.string, m.end()) if m.group(3) else ''), text)

        # Standalone time: 14:30
        pattern = r'\b(\d{1,2}):(\d{2})\b'
        text = re.sub(pattern, lambda m: normalize_time(
            int(m.group(1)), int(m.group(2))
        ), text)

        return text

    def _normalize_currency(self, text: str) -> str:
        """Normalize currency patterns."""
        amount = r'(\d+(?:[.,]\d{1,2})?)(?![\d.,]\d)'
        for code, tokens in CURRENCY_SUFFIXES.items():
            # Amount first: 1500.50 лв., 1500 €, 25 USD, 20 евро
            pattern = r'(?<![\w.,:/])' + amount + r'\s*(?:' + tokens + r')(?!\w)(\.(?!\w))?'
            text = re.sub(pattern, lambda m, code=code: normalize_currency(
                m.group(1), code
            ) + (sentence_period(m.string, m.end()) if m.group(2) else ''), text)

        for code, tokens in CURRENCY_PREFIXES.items():
            # Symbol first: €1500, $ 100, EUR 100
            pattern = r'(?<!\w)(?:' + tokens + r')\s*' + amount + r'(?!\w)'
            text = re.sub(pattern, lambda m, code=code: normalize_currency(
                m.group(1), code
            ), text)

        return text

    def _normalize_percentages(self, text: str) -> str:
        """Normalize percentage patterns."""
        pattern = r'\b(\d+(?:[.,]\d+)?)\s*%'
        def pct_repl(m):
            num_str = m.group(1).replace(',', '.')
            if '.' in num_str:
                return float_to_words(num_str) + ' процента'
            else:
                return number_to_words_cardinal(int(num_str)) + ' процента'
        text = re.sub(pattern, pct_repl, text)
        return text

    def _normalize_phones(self, text: str) -> str:
        """Normalize phone number patterns."""
        # Bulgarian phone: +359 2 1234567, 0888 123 456, 02/1234567
        pattern = r'(?:\+359[\s\-]?|(?<!\w)0)[\d\s\-/]{6,12}\d'
        text = re.sub(pattern, lambda m: normalize_phone_number(m.group(0)), text)
        return text

    def _normalize_roman_numerals(self, text: str) -> str:
        """Normalize Roman numerals to ordinal words."""
        # Roman numerals typically used for centuries, monarchs, chapters
        # Full pattern: M{0,3} CD/D?C{0,3} XC/XL/L?X{0,3} IX/IV/V?I{0,3}
        roman_pattern = r'(?=[IVXLCDM])M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'
        context_words = r'век|глава|том|книга|част|клас|степен'
        feminine_words = {'глава', 'книга', 'част', 'степен'}

        def _roman_to_ordinal(roman: str, context: str) -> str:
            if not roman:
                return None
            arabic = roman_to_arabic(roman)
            if arabic is None:
                return None
            gender = 'f' if context.lower() in feminine_words else 'm'
            return number_to_words_ordinal(arabic, gender=gender)

        # Pattern 1: context word THEN Roman numeral (e.g., "век XXI")
        pattern = r'\b(' + context_words + r')\s+(' + roman_pattern + r')\b'
        def roman_repl(m):
            ordinal = _roman_to_ordinal(m.group(2), m.group(1))
            if ordinal is None:
                return m.group(0)
            return f'{m.group(1)} {ordinal}'
        text = re.sub(pattern, roman_repl, text, flags=re.IGNORECASE)

        # Pattern 2: Roman numeral THEN context word (e.g., "XXI век")
        pattern = r'\b(' + roman_pattern + r')\s+(' + context_words + r')\b'
        def roman_repl_reversed(m):
            ordinal = _roman_to_ordinal(m.group(1), m.group(2))
            if ordinal is None:
                return m.group(0)
            return f'{ordinal} {m.group(2)}'
        text = re.sub(pattern, roman_repl_reversed, text, flags=re.IGNORECASE)

        return text

    def _normalize_ordinals(self, text: str) -> str:
        """Normalize ordinal number patterns like 1-ви, 2-ри, 3-ти, 1-ва."""
        # Hyphen or no space: "1 на 100" is not an ordinal
        pattern = r'\b(\d+)-?(ви|ри|ти|ми|ва|ра|та|на|во|ро|то|но)\b'
        def ordinal_repl(m):
            num = int(m.group(1))
            suffix = m.group(2).lower()
            # Determine gender from suffix
            if suffix in ('ва', 'ра', 'та', 'на'):
                gender = 'f'
            elif suffix in ('во', 'ро', 'то', 'но'):
                gender = 'n'
            else:
                gender = 'm'
            return number_to_words_ordinal(num, gender=gender)
        text = re.sub(pattern, ordinal_repl, text)
        return text

    def _normalize_standalone_years(self, text: str) -> str:
        """Normalize 4-digit years that appear in year-like contexts."""
        # Year with г./година: 2026 г., 1989 година
        # Do NOT match "години" (plural) — that means "years" as duration, not a year label
        # Before/after the common era a year is counted: "триста години преди новата ера"
        era = re.compile(r'\s*(?:преди|след)\s+(?:новата\s+ера|христа)', re.IGNORECASE)
        pattern = r'\b(\d{4})\s*(г\.|г(?!\w)|година)(?!и)'
        def year_repl(m):
            year = int(m.group(1))
            suffix = m.group(2)
            if suffix == 'г.' and era.match(m.string, m.end()):
                return (quantity_to_words(m.group(1), 'година', 'години', 'f')
                        + sentence_period(m.string, m.end()))
            if 1000 <= year <= 2100:
                period = sentence_period(m.string, m.end()) if suffix == 'г.' else ''
                return normalize_year(year) + ' година' + period
            return m.group(0)
        text = re.sub(pattern, year_repl, text)

        # "г." after a shorter number: a year (през 865 г.) from 100 on, or a
        # count of years: an age (на 35 г.) or a year of the era (300 г. пр.н.е.)
        pattern = r'(?<![\w.,:/])(\d{1,3})\s*г\.(?!\w)'
        def short_year_repl(m):
            n = int(m.group(1))
            period = sentence_period(m.string, m.end())
            if n >= 100 and not era.match(m.string, m.end()):
                return normalize_year(n) + ' година' + period
            return quantity_to_words(m.group(1), 'година', 'години', 'f') + period
        text = re.sub(pattern, short_year_repl, text)
        return text

    def _normalize_cardinal_numbers(self, text: str) -> str:
        """Normalize remaining standalone numbers to cardinal words."""
        # Negative numbers: -3 → минус три (not ranges like 5-10, handled earlier)
        text = re.sub(r'(?<![\w.,:/\-−])[-−](?=\d)', 'минус ', text)

        # Halves of time: 1.5 години → година и половина
        pattern = (r'\b(\d+)[.,]50*\s+(' + '|'.join(TIME_NOUNS) + r')(?!\w)')
        text = re.sub(pattern, lambda m: half_quantity_to_words(
            int(m.group(1)), *TIME_NOUNS[m.group(2).lower()]
        ), text, flags=re.IGNORECASE)

        # Decimal numbers, read as said aloud: 3.5 → три цяло и пет
        pattern = r'\b(\d+)[.,](\d+)\b'
        text = re.sub(pattern, lambda m: short_decimal_to_words(m.group(1), m.group(2)), text)

        # Integer numbers
        pattern = r'\b(\d+)\b'
        def cardinal_repl(m):
            num = int(m.group(1))
            if num > 999999999999:  # Skip very large numbers
                return m.group(0)
            next_word = re.match(r'\s+([^\W\d_]+)', m.string[m.end():])
            gender = noun_gender(num, next_word.group(1)) if next_word else 'm'
            try:
                return number_to_words_cardinal(num, gender)
            except (ValueError, KeyError):
                return m.group(0)
        text = re.sub(pattern, cardinal_repl, text)

        return text


_default_normalizer = None


def normalize_text(text: str, **kwargs) -> str:
    """Convenience function for quick normalization."""
    global _default_normalizer
    if kwargs:
        return BulgarianTextNormalizer(**kwargs).normalize(text)
    if _default_normalizer is None:
        _default_normalizer = BulgarianTextNormalizer()
    return _default_normalizer.normalize(text)


if __name__ == '__main__':
    normalizer = BulgarianTextNormalizer(verbose=True)

    test_cases = [
        "На 15.02.2026 г. в 14:30 ч. цената е 1500.50 лв.",
        "Среща на 01.03.2026 г. в 9:05 часа.",
        "Това е 21-ви век.",
        "Дължимата сума е $250 или €230.",
        "Населението е 7 000 000 души.",
        "Увеличение от 15.5%.",
        "бул. Витоша №10, гр. София",
        "На 3-ти март 1878 г.",
        "Доставка на 25.12.",
        "Цена: 99.99 лв.",
        "Обадете се на 0888 123 456.",
        "Роден на 01.01.2000 г.",
        "Той е на 35 години.",
    ]

    print("=" * 60)
    print("Bulgarian Text Normalizer - Test Cases")
    print("=" * 60)
    for test in test_cases:
        result = normalizer.normalize(test)
        print(f"\nInput:  {test}")
        print(f"Output: {result}")
