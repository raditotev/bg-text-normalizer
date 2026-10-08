"""
Bulgarian Phone Number Normalization
=======================================
Converts phone numbers to digit-by-digit spoken form.

Bulgarian phone formats:
- Mobile: 0888 123 456, 088 812 3456
- Landline: 02 123 4567, 032 12 34 56
- International: +359 888 123 456
"""

from .bg_numbers import DIGIT_WORDS


def normalize_phone_number(phone: str) -> str:
    """
    Convert a phone number to spoken Bulgarian form, digit by digit.

    Args:
        phone: Phone number string, e.g., "+359 888 123 456"

    Returns:
        Spoken form, e.g., "плюс три пет девет осем осем осем едно две три ..."
    """
    # Clean up
    cleaned = phone.strip()

    # Handle international prefix
    prefix = ''
    if cleaned.startswith('+359'):
        prefix = 'плюс три пет девет'
        cleaned = cleaned[4:].strip()

    # Remove all non-digits
    digits_only = ''.join(c for c in cleaned if c.isdigit())

    if not digits_only:
        return phone

    result_parts = [prefix] if prefix else []
    result_parts.extend(DIGIT_WORDS[d] for d in digits_only)

    return ' '.join(result_parts)


if __name__ == '__main__':
    test_phones = [
        "+359 888 123 456",
        "0888 123 456",
        "02 1234567",
        "0888123456",
        "+359 2 981 5678",
    ]

    print("=== Phone Number Normalization ===")
    for phone in test_phones:
        result = normalize_phone_number(phone)
        print(f"  {phone} → {result}")
