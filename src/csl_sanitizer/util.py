from os import getenv
from typing import Final

ns: Final = {"cs": "http://purl.org/net/xbiblio/csl"}
"""The XML namespace"""

Message = str


def get_bool_env(key: str) -> bool:
    """Get a boolean environment variable."""
    v = getenv(key, default="").strip()
    if v == "0" or v.lower() == "false":
        return False
    else:
        return bool(v)
