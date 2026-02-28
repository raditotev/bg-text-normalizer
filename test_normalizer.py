"""Comprehensive test suite for Bulgarian Text Normalizer."""

import sys
from bg_text_normalizer import BulgarianTextNormalizer

normalizer = BulgarianTextNormalizer()

test_cases = [
    # === DATES ===
    ("На 15.02.2026 г. в 14:30 ч.", 
     "На петнадесети февруари две хиляди двадесет и шеста година в четиринадесет и тридесет часа"),
    ("Роден на 01.01.2000 г.", 
     "Роден на първи януари двехилядна година"),
    ("На 3-ти март 1878 г.",
     "На трети март хиляда осемстотин седемдесет и осма година"),
    ("Доставка на 25.12.",
     "Доставка на двадесет и пети декември."),
    
    # === NUMBERS ===
    ("Той е на 35 години.",
     "Той е на тридесет и пет години."),
    ("Населението е 7 000 000 души.",
     "Населението е седем милиона души."),
    ("Има 1 000 001 жители.",
     "Има един милион и един жители."),
    
    # === CURRENCY ===
    ("Цена: 99.99 лв.",
     "Цена: деветдесет и девет лева и деветдесет и девет стотинки."),
    ("Заплата: 2500 лв.",
     "Заплата: две хиляди и петстотин лева."),
    ("$250 или €230",
     None),  # Just check it doesn't crash
    
    # === PERCENTAGES ===
    ("Увеличение от 15.5%.",
     "Увеличение от петнадесет цяло и пет десети процента."),
    ("ДДС е 20%.",
     None),
    
    # === TIME ===
    ("Среща в 9:05 часа.",
     "Среща в девет и пет часа."),
    ("В 12:00 ч. е обяд.",
     "В дванадесет часа е обяд."),
    
    # === ABBREVIATIONS ===
    ("бул. Витоша №10, гр. София",
     "булевард Витоша номер десет, град София"),
    ("г-н Петров е проф. д-р",
     None),
    ("ж.к. Люлин, бл. 305",
     None),
    
    # === ORDINALS ===
    ("21-ви век",
     "двадесет и първи век"),
    ("1-ва категория",
     "първа категория"),
    ("5-то издание",
     "пето издание"),
    
    # === DATES WITH MONTH NAMES ===
    ("15 май",
     "петнадесети май"),
    ("1 януари",
     "първи януари"),
    ("25 декември 2025 г.",
     "двадесет и пети декември две хиляди двадесет и пета година"),
    ("3 март 1878 г.",
     "трети март хиляда осемстотин седемдесет и осма година"),
    ("от 1 март до 15 април",
     "от първи март до петнадесети април"),
    # Capitalized month names
    ("15 Май",
     "петнадесети май"),
    ("1 ЯНУАРИ 2026 г.",
     "първи януари две хиляди двадесет и шеста година"),
    # Day out of range should NOT become ordinal
    ("35 май",
     "тридесет и пет май"),
    # Month name without preceding number should be left alone
    ("месец май беше топъл",
     "месец май беше топъл"),

    # === ROMAN NUMERALS ===
    ("XXXII век",
     "тридесет и втори век"),
    ("XL глава",
     "четиридесета глава"),
    ("L глава",
     "петдесета глава"),
    ("XLII век",
     "четиридесет и втори век"),
    ("I век",
     "първи век"),

    # === MIXED COMPLEX ===
    ("На 01.09.2024 г. в 8:30 ч. на бул. Витоша №15, гр. София, цената на билета е 12.50 лв.",
     None),
    ("Фирма Тест ЕООД, ул. Иван Вазов №23, ет. 3, ап. 12",
     None),
]

print("=" * 70)
print("Bulgarian Text Normalizer - Comprehensive Tests")
print("=" * 70)

passed = 0
failed = 0

for i, (input_text, expected) in enumerate(test_cases):
    result = normalizer.normalize(input_text)
    
    if expected is not None:
        # Normalize whitespace for comparison
        result_clean = ' '.join(result.split())
        expected_clean = ' '.join(expected.split())
        
        if result_clean == expected_clean:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
    else:
        status = "• INFO"
        passed += 1  # If no expected, just verify it doesn't crash
    
    print(f"\n[{status}] Test {i+1}")
    print(f"  Input:    {input_text}")
    print(f"  Output:   {result}")
    if expected is not None and status == "✗ FAIL":
        print(f"  Expected: {expected}")

print(f"\n{'=' * 70}")
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print(f"{'=' * 70}")

# === Additional edge case tests ===
print("\n\n=== Edge Cases (visual inspection) ===\n")

edge_cases = [
    "0 лв.",
    "1 лев",
    "2 лева",
    "0.01 лв.",
    "1 000 000 000 лв.",
    "На 29.02.2024 г.",
    "Скорост 120 км/ч",
    "Площ 85.5 кв.м",
    "т.е. трябва да се направи",
    "вкл. ДДС",
    "+359 888 123 456",
    "100%",
    "3.14",
    "Глава III",
    "век XXI",
]

for text in edge_cases:
    result = normalizer.normalize(text)
    print(f"  {text:40s} → {result}")

sys.exit(1 if failed else 0)
