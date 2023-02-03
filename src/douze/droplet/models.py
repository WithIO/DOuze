from dataclasses import dataclass, field
from enum import Enum
from typing import List, Text

from typefit.narrows import DateTime

from douze.models import Collection

__all__ = [
    "DropletStatus",
    "Droplet",
    "DropletCollection",
]


class DropletStatus(Enum):
    new = "new"
    active = "active"
    off = "off"
    archive = "archive"


@dataclass
class Droplet:
    id: int
    name: Text
    memory: int
    vcpus: int
    disk: int
    locked: bool
    created_at: DateTime
    status: DropletStatus


@dataclass
class DropletCollection(Collection):
    droplets: List[Droplet] = field(default_factory=list)
