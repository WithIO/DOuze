from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Text, Dict, NamedTuple

from typefit.narrows import DateTime

from ..models import Collection

__all__ = [
    "SubscriptionTierBase",
    "Registry",
    "RepositoryCollection",
    "RegistryInformation",
    "Repository",
    "RegistryRegion",
    "Tag",
    "TagCollection",
    "GarbageCollection",
    "RegistryOptions",
    "TierSlug",
    "Auth",
    "DockerAuth",
]

from ..types import Uuid


class RegistryRegion(Enum):
    NYC3 = "nyc3"
    SFO3 = "sfo3"
    AMS3 = "ams3"
    SGP1 = "sgp1"
    FRA1 = "fra1"


class TierSlug(Enum):
    STARTER = "started"
    BASIC = "basic"
    PROFESSIONAL = "professional"


@dataclass
class SubscriptionTierBase:
    name: str
    slug: str
    included_repositories: int
    included_storage_bytes: int
    allow_storage_overage: bool
    included_bandwidth_bytes: int
    monthly_price_in_cents: int
    storage_overage_price_in_cents: int


@dataclass
class SubscriptionTier(SubscriptionTierBase):
    eligible: bool
    eligibility_reasons: List[Text] = field(default_factory=list)


@dataclass
class Subscription:
    tier: SubscriptionTierBase
    created_at: DateTime
    updated_at: DateTime


@dataclass
class Registry:
    name: Text
    created_at: DateTime
    region: Text
    storage_usage_bytes: int
    read_only: bool
    storage_usage_bytes_updated_at: Optional[DateTime] = None


@dataclass
class RegistryInformation:
    registry: Registry
    subscription: Subscription


@dataclass
class Repository:
    registry_name: Text
    name: Text
    latest_manifest: Any
    tag_count: int
    manifest_count: int


@dataclass
class RepositoryCollection(Collection):
    repositories: List[Repository] = field(default_factory=list)


@dataclass
class Tag:
    registry_name: Text
    repository: Text
    tag: Text
    manifest_digest: Text
    compressed_size_bytes: int
    size_bytes: int
    updated_at: DateTime


@dataclass
class TagCollection:
    tags: List[Tag] = field(default_factory=list)


@dataclass
class GarbageCollection:
    uuid: Uuid
    registry_name: Text
    status: Text
    created_at: DateTime
    updated_at: DateTime
    blobs_deleted: int
    freed_bytes: int


@dataclass
class RegistryOptions:
    available_regions: List[Text]
    subscription_tiers: List[SubscriptionTier]


@dataclass
class Auth:
    auth: Text


DOCR_BASE = "registry.digitalocean.com"


class DockerAuth(NamedTuple):
    auths: Dict[Text, Auth]
