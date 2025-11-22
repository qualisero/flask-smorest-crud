def convert_snake_to_camel(word):
    """🐍 → 🐪."""
    if '_' not in word:
        return word
    return "".join(x.capitalize() or "_" for x in word.split("_"))

