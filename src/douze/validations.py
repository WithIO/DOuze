import re
from typing import Text


def registry_name(name: Text):
    NAME_PATTERN = r"^[a-z0-9-]{1,63}$"

    return re.match(NAME_PATTERN, name)
