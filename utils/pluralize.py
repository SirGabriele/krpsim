def pluralize(word: str, plural_end: str, amount: int) -> str:
    return word + plural_end if amount > 1 else word
