"""
Bulgarian Abbreviation Expansion
===================================
Expands common Bulgarian abbreviations to their full spoken forms.

Categories:
- Address abbreviations (бул., ул., пл., ж.к., кв.)
- Title abbreviations (г-н, г-жа, д-р, проф., инж.)
- Geographic (гр., с., обл.)
- Measurement units (км, м, кг, л, мм, см)
- Administrative (ЕТ, ООД, ЕООД, АД, ЕАД)
- Common abbreviations (т.е., т.н., напр., и т.н., и др.)
- Institution abbreviations (НАП, НОИ, МОН, МВР, НЗОК)
"""

import re
from typing import Dict, Tuple

from .bg_punctuation import sentence_period
from .bg_units import normalize_units

# Abbreviation → (full form, is_case_sensitive)
# Order matters: longer abbreviations should be checked first

# Address abbreviations
ADDRESS_ABBREVS: Dict[str, str] = {
    'бул.': 'булевард',
    'ул.': 'улица',
    'пл.': 'площад',
    'ж.к.': 'жилищен комплекс',
    'ж. к.': 'жилищен комплекс',
    'кв.': 'квартал',
    'бл.': 'блок',
    'вх.': 'вход',
    'ет.': 'етаж',
    'ап.': 'апартамент',
    'п.к.': 'пощенски код',
}

# Geographic abbreviations
GEO_ABBREVS: Dict[str, str] = {
    'гр.': 'град',
    'с.': 'село',
    'обл.': 'област',
    'общ.': 'община',
    'р-н': 'район',
}

# Title abbreviations
TITLE_ABBREVS: Dict[str, str] = {
    'г-н': 'господин',
    'г-жа': 'госпожа',
    'г-ца': 'госпожица',
    'г-жи': 'госпожи',
    'г-да': 'господа',
    'д-р': 'доктор',
    'проф.': 'професор',
    'доц.': 'доцент',
    'акад.': 'академик',
    'инж.': 'инженер',
    'арх.': 'архитект',
    'адв.': 'адвокат',
    'св.': 'свети',
}

# Measurement unit abbreviations
MEASUREMENT_ABBREVS: Dict[str, str] = {
    'км/ч': 'километра в час',
    'м/с': 'метра в секунда',
    'кв.м': 'квадратни метра',
    'кв. м': 'квадратни метра',
    'кв.м.': 'квадратни метра',
    'куб.м': 'кубически метра',
    'куб. м': 'кубически метра',
    'км': 'километра',
    'м': 'метра',
    'см': 'сантиметра',
    'мм': 'милиметра',
    'кг': 'килограма',
    'гр': 'грама',  # Note: context-dependent (could also be "град")
    'мг': 'милиграма',
    'т': 'тона',
    'л': 'литра',
    'мл': 'милилитра',
    'дка': 'декара',
    'ха': 'хектара',
}

# Administrative/business abbreviations
BUSINESS_ABBREVS: Dict[str, str] = {
    'ЕООД': 'еоод',  # Spelled out as abbreviation
    'ООД': 'оод',
    'ЕТ': 'едноличен търговец',
    'АД': 'акционерно дружество',
    'ЕАД': 'еад',
    'КД': 'командитно дружество',
    'СД': 'събирателно дружество',
}

# Common text abbreviations
COMMON_ABBREVS: Dict[str, str] = {
    'т.е.': 'тоест',
    'т. е.': 'тоест',
    'т.н.': 'така наречен',
    'т. н.': 'така наречен',
    'т.нар.': 'така наречен',
    'напр.': 'например',
    'и т.н.': 'и така нататък',
    'и т. н.': 'и така нататък',
    'и др.': 'и други',
    'вж.': 'виж',
    'тел.': 'телефон',
    'ср.': 'сравни',
    'вкл.': 'включително',
    'изд.': 'издание',
    'стр.': 'страница',
    'гл.': 'глава',
    'чл.': 'член',
    'ал.': 'алинея',
    'б.р.': 'бележка на редактора',
    'б. р.': 'бележка на редактора',
    'б.а.': 'бележка на автора',
    'б. а.': 'бележка на автора',
    'пр.н.е.': 'преди новата ера',
    'пр. н. е.': 'преди новата ера',
    'сл.н.е.': 'след новата ера',
    'сл. н. е.': 'след новата ера',
    'пр.Хр.': 'преди Христа',
    'сл.Хр.': 'след Христа',
}

# Abbreviations that come after what they modify, so they can end a sentence
# ("Купих ябълки, круши и т.н."). Their period is kept only when it is also
# the end of the sentence. All other abbreviations with a period precede a
# name or number (гр. София, проф. Иванов, стр. 5) and always drop it.
SENTENCE_FINAL_ABBREVS = {
    'и т.н.', 'и т. н.', 'и др.',
    'б.р.', 'б. р.', 'б.а.', 'б. а.',
    'пр.н.е.', 'пр. н. е.', 'сл.н.е.', 'сл. н. е.',
    'пр.Хр.', 'сл.Хр.',
}

# Institution abbreviations (spelled out letter by letter or as words)
INSTITUTION_ABBREVS: Dict[str, str] = {
    'НАП': 'национална агенция по приходите',
    'НОИ': 'национален осигурителен институт',
    'НЗОК': 'национална здравноосигурителна каса',
    'МОН': 'министерство на образованието и науката',
    'МВР': 'министерство на вътрешните работи',
    'МЗ': 'министерство на здравеопазването',
    'МФ': 'министерство на финансите',
    'МРРБ': 'министерство на регионалното развитие и благоустройството',
    'БНБ': 'българска народна банка',
    'БНТ': 'бнт',
    'БТВ': 'бтв',
    'НС': 'народно събрание',
    'ЕС': 'европейски съюз',
    'ООН': 'организация на обединените нации',
    'НАТО': 'нато',
    'ДДС': 'данък добавена стойност',
    'ДАНС': 'данс',
    'ЕГН': 'единен граждански номер',
    'БУЛСТАТ': 'булстат',
    'ПИН': 'пин',
    'ПДФ': 'пдф',
    'СМС': 'есемес',
}

# Number sign / hash
SYMBOL_ABBREVS: Dict[str, str] = {
    '№': 'номер',
    '&': 'и',
    '@': 'кльомба',
}


def expand_abbreviation(abbrev: str) -> str:
    """
    Expand a single abbreviation to its full form.

    Args:
        abbrev: The abbreviation to expand

    Returns:
        Full form or original if not found
    """
    # Check all dictionaries
    for d in [ADDRESS_ABBREVS, GEO_ABBREVS, TITLE_ABBREVS,
              MEASUREMENT_ABBREVS, BUSINESS_ABBREVS, COMMON_ABBREVS,
              INSTITUTION_ABBREVS, SYMBOL_ABBREVS]:
        if abbrev in d:
            return d[abbrev]
        # Case-insensitive check
        for key, val in d.items():
            if key.lower() == abbrev.lower():
                return val
    return abbrev


def normalize_abbreviations(text: str, include_units: bool = True) -> str:
    """
    Expand all recognized abbreviations in the text.

    Processes abbreviations in order of specificity (longer first)
    to avoid partial matches.

    With include_units, a number followed by a measurement unit is also
    expanded, number included ("1 км" → "един километър").
    """
    # Units first, so "кв. м" is not read as "квартал м"
    if include_units:
        text = normalize_units(text)

    # Collect all abbreviations, sorted by length (longest first)
    all_abbrevs = {}
    for d in [COMMON_ABBREVS, ADDRESS_ABBREVS, GEO_ABBREVS, TITLE_ABBREVS,
              BUSINESS_ABBREVS, INSTITUTION_ABBREVS, SYMBOL_ABBREVS]:
        all_abbrevs.update(d)

    # Sort by length descending to match longer abbreviations first
    sorted_abbrevs = sorted(all_abbrevs.items(), key=lambda x: len(x[0]), reverse=True)

    for abbrev, full_form in sorted_abbrevs:
        # Escape special regex characters in the abbreviation
        escaped = re.escape(abbrev)
        # Use word boundary or space/start/end boundary
        # Be careful with dots - they're part of some abbreviations
        pattern = r'(?<!\w)' + escaped + r'(?!\w)'
        def repl(m, full_form=full_form,
                 sentence_final=abbrev in SENTENCE_FINAL_ABBREVS):
            found = m.group(0)
            # Keep a capital (Проф. → Професор) so sentence starts stay visible,
            # but not for all-caps acronyms (ДДС → данък добавена стойност)
            if found[0].isupper() and not found.isupper():
                full_form = full_form[0].upper() + full_form[1:]
            if sentence_final:
                return full_form + sentence_period(m.string, m.end())
            return full_form
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


if __name__ == '__main__':
    test_cases = [
        "бул. Витоша №10, гр. София",
        "г-н Иванов е д-р по медицина",
        "Офис на 5 км от центъра",
        "Площ: 120 кв.м",
        "т.е. не може да се направи",
        "Фирма Тест ЕООД",
        "Скорост: 60 км/ч",
        "Заплата: 2500 лв. (вкл. ДДС)",
        "ж.к. Люлин, бл. 305, вх. А, ет. 5, ап. 20",
        "проф. д-р Петров",
        "и т.н. и т.н.",
    ]

    print("=== Abbreviation Expansion ===")
    for test in test_cases:
        result = normalize_abbreviations(test)
        print(f"  Input:  {test}")
        print(f"  Output: {result}")
        print()
