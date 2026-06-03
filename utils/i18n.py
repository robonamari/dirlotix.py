import gettext
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=None)
def get_translator(language: str = "en") -> gettext.NullTranslations:
    """
    Get a gettext translation object for the specified language. This function uses caching to avoid reloading translations multiple times for the same language. It attempts to load the translation files from the "languages" directory relative to the current file's location. If the specified language is not found or an error occurs during loading, it falls back to a NullTranslations object, which will return the original strings without translation.

    Args:
        language (str): The language code for which to load the translation (e.g., "en" for English, "es" for Spanish). The default is "en".

    Returns:
        gettext.NullTranslations: A translation object that can be used to translate strings based on the specified language. If the translation files are not found, it returns a NullTranslations object that will return the original strings.
    """
    try:
        languages_dir: Path = (Path(__file__).parent.parent / "languages").resolve()
        return gettext.translation(
            domain="messages",
            localedir=str(languages_dir),
            languages=[language.split("_")[0]],
            fallback=True,
        )
    except Exception:
        return gettext.NullTranslations()


_: Any = get_translator().gettext
