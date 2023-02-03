from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Text, Union

from douze.models import Collection
from douze.types import Uuid


class CheckType(Text, Enum):
    ping = "ping"
    http = "http"
    https = "https"


class SourceRegion(Text, Enum):
    us_east = "us_east"
    us_west = "us_west"
    eu_west = "eu_west"
    se_asia = "se_asia"


class AlertType(Text, Enum):
    latency = "latency"
    down = "down"
    down_global = "down_global"
    ssl_expiry = "ssl_expiry"


class ComparisonOperator(Text, Enum):
    greater_than = "greater_than"
    less_than = "less_than"


@dataclass
class Check:
    id: Uuid
    name: Text
    type: CheckType
    target: Text
    regions: List[SourceRegion] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ChecksCollection(Collection):
    checks: List[Check] = field(default_factory=list)


@dataclass
class AlertNotification:
    pass


class TriggerPeriod(Text):
    def __init__(self, value: Text):
        allowed = {
            "2m": "2m",
            "3m": "3m",
            "5m": "5m",
            "10m": "10m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
        }

        if value not in allowed:
            raise ValueError(
                f"unknown trigger period {value}. supported choices are: {', '.join(allowed.keys())}"
            )


@dataclass
class Alert:
    id: Uuid
    name: Text
    type: AlertType
    threshold: int
    comparison: ComparisonOperator
    notifications: AlertNotification
    period: TriggerPeriod


@dataclass
class AlertCollection(Collection):
    alerts: List[Alert] = field(default_factory=list)
