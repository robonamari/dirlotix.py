import gettext
from functools import cache
from pathlib import Path
from typing import Any


@cache
def get_translator(language: str = "en") -> gettext.NullTranslations:
    """Get a cached gettext translator for the specified language.

    Args:
        language (str): The language code to load.

    Returns:
        gettext.NullTranslations: The translation object.

    """
    languages_dir: Path = (Path(__file__).parent.parent / "languages").resolve()
    return gettext.translation(
        domain="messages",
        localedir=str(languages_dir),
        languages=[language.split("_", maxsplit=1)[0]],
        fallback=True,
    )


_: Any = get_translator().gettext
