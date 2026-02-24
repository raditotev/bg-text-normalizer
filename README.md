# Bulgarian Text Normalizer for TTS

A comprehensive text normalization package that converts written Bulgarian text into its spoken form, designed as a preprocessing step for Text-to-Speech (TTS) systems.

## Features

| Category | Examples |
|----------|----------|
| **Numbers** | `1500` → `хиляда и петстотин` |
| **Dates** | `15.02.2026 г.` → `петнадесети февруари две хиляди двадесет и шеста година` |
| **Time** | `14:30 ч.` → `четиринадесет и тридесет часа` |
| **Currency** | `99.99 лв.` → `деветдесет и девет лева и деветдесет и девет стотинки` |
| **Percentages** | `15.5%` → `петнадесет цяло и пет десети процента` |
| **Ordinals** | `21-ви` → `двадесет и първи` |
| **Abbreviations** | `бул. Витоша, гр. София` → `булевард Витоша, град София` |
| **Phone numbers** | `+359 888 123 456` → digit-by-digit reading |
| **Roman numerals** | `век XXI` → `век двадесет и първи` |
| **Symbols** | `№10` → `номер десет` |

## Grammatical Correctness

- **Gender agreement**: Handles masculine/feminine/neuter (`един`/`една`/`едно`, `два`/`две`)
- **Ordinal forms**: Full gender-aware ordinals (`първи`/`първа`/`първо`)
- **Year reading**: Ordinal feminine form matching "година" (`две хиляди двадесет и шеста`)
- **Space-separated thousands**: `7 000 000` → `седем милиона`

## Usage

### Quick usage
```python
from bg_text_normalizer import normalize_text

result = normalize_text("На 15.02.2026 г. в 14:30 ч. цената е 1500.50 лв.")
# "На петнадесети февруари две хиляди двадесет и шеста година в четиринадесет
#  и тридесет часа цената е хиляда и петстотин лева и петдесет стотинки."
```

### Class-based usage
```python
from bg_text_normalizer import BulgarianTextNormalizer

normalizer = BulgarianTextNormalizer(expand_abbrevs=True, verbose=False)
result = normalizer.normalize("бул. Витоша №10, гр. София")
# "булевард Витоша номер десет, град София"
```

### Individual modules
```python
from bg_text_normalizer.bg_numbers import number_to_words_cardinal, number_to_words_ordinal
from bg_text_normalizer.bg_dates import normalize_date
from bg_text_normalizer.bg_currency import normalize_currency

number_to_words_cardinal(2500, gender='m')    # "две хиляди и петстотин"
number_to_words_ordinal(15, gender='m')       # "петнадесети"
normalize_date(15, 2, 2026)                   # "петнадесети февруари две хиляди двадесет и шеста"
normalize_currency("99.99", "BGN")            # "деветдесет и девет лева и деветдесет и девет стотинки"
```

## Integration with TTS Training (Qwen3-TTS)

Use this normalizer as a preprocessing step when preparing your training data:

```python
import json
from bg_text_normalizer import normalize_text

# Process your JSONL training data
with open('raw_data.jsonl', 'r') as f_in, open('normalized_data.jsonl', 'w') as f_out:
    for line in f_in:
        entry = json.loads(line)
        entry['text'] = normalize_text(entry['text'])
        f_out.write(json.dumps(entry, ensure_ascii=False) + '\n')
```

For inference (runtime TTS), add normalization before synthesis:

```python
from bg_text_normalizer import normalize_text

def synthesize(text: str):
    normalized = normalize_text(text)
    # ... pass normalized text to TTS model
```

## File Structure

```
bg-text-normalizer/
├── src/
│   └── bg_text_normalizer/
│       ├── __init__.py           # Package entry point
│       ├── bg_normalizer.py      # Main orchestrator
│       ├── bg_numbers.py         # Cardinal, ordinal, decimal numbers
│       ├── bg_dates.py           # Date normalization
│       ├── bg_time.py            # Time normalization
│       ├── bg_currency.py        # Currency (BGN, EUR, USD, GBP)
│       ├── bg_abbreviations.py   # 100+ Bulgarian abbreviations
│       ├── bg_phone.py           # Phone number reading
│       └── bg_roman.py           # Roman numeral conversion
├── test_normalizer.py            # Test suite
├── pyproject.toml
└── README.md
```

## Adding Custom Abbreviations

Edit `src/bg_text_normalizer/bg_abbreviations.py` and add entries to the appropriate dictionary:

```python
# In ADDRESS_ABBREVS, TITLE_ABBREVS, etc.
CUSTOM_ABBREVS = {
    'your_abbrev.': 'пълна форма',
}
```

## Dependencies

**None** — pure Python, no external dependencies required.
