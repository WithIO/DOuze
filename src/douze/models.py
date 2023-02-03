from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Text, Type, Union
from urllib.parse import quote

from typefit.narrows import DateTime

from .types import Uuid

__all__ = [
    "EntryState",
    "Version",
    "Day",
    "Meta",
    "Collection",
]


class EntryState(Enum):
    present = "present"
    absent = "absent"


class Version(Enum):
    """
    Enum that provides a way to get the latest version of its members.
    Versions need to be sorted in the enum definition.
    Latest is just the last one.
    A version can be marked as 'stable' by using that label for the member.

    >>> class VersionedItem(Version):
    >>>     v1 = "1"
    >>>     v2 = "2"
    >>>     v3 = "3"
    >>>     v4 = "4"
    >>>     stable = "3"
    >>>
    >>> VersionedItem.latest() == VersionedItem.v4
    >>> VersionedItem.stable == VersionedItem.v3
    """

    @classmethod
    def latest(cls: Type["Version"]):
        """
        Return the last member of this enum.
        Ignore member named "stable"
        """
        labels = filter(lambda l: l.lower() != "stable", cls.__members__.keys())
        return cls.__members__[list(labels)[-1]]


class Day(Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


@dataclass
class Meta:
    total: int


@dataclass
class Collection:
    meta: Meta = None
