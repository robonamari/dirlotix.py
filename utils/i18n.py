import gettext
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=None)
def get_translator(language: str = "en") -> gettext.NullTranslations:
    """
    Get a gettext translation object for the specified language.

    Args:
        language (str): The language code for which to get the translator (default is "en").

    Returns:
        gettext.NullTranslations: A translation object for the specified language, or a NullTranslations object if the translation file is not found or an error occurs.

    """
    try:
        return gettext.translation(
            domain="messages",
            localedir=Path(__file__).resolve().parent.parent / "languages",
            languages=[language.split("_")[0]],
            fallback=True,
        )
    except Exception:
        return gettext.NullTranslations()


_ = get_translator().gettext
