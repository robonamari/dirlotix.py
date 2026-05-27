import gettext
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=None)
def get_translator(language: str = "en") -> gettext.NullTranslations:
    """
    Get a gettext translation object for the specified language.
    Uses caching to avoid reloading translations on each call.

    Args:
        language (str): Two-letter language code (default: "en").

    Returns:
        gettext.NullTranslations: Translation object for the specified language.
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
