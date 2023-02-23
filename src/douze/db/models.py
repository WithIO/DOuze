from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Text, Union
from urllib.parse import quote

from typefit.narrows import DateTime

from ..models import Collection, Day, Version
from ..types import Uuid

__all__ = [
    "DatabaseSize",
    "DatabaseEngine",
    "Engine",
    "PostgreSqlVersion",
    "MySqlVersion",
    "RedisVersion",
    "MongoVersion",
    "DatabaseUserRole",
    "MySqlAuthPlugin",
    "DatabaseStatus",
    "PgBouncerMode",
    "DbFirewallRuleType",
    "DatabaseCluster",
    "DatabaseClusterCreate",
    "DatabaseMaintenanceWindow",
    "DatabaseConnection",
    "DatabaseEngine",
    "DatabaseUser",
    "DatabaseUserCreate",
    "MySqlSettings",
    "Database",
    "DatabaseConnectionPoolCreate",
    "DatabaseConnectionPool",
    "DatabaseFirewallRule",
    "DatabaseFirewallRuleCreate",
    "DatabaseClusterCollection",
    "DatabaseCollection",
]


class DatabaseSize(Enum):
    db_s_1vcpu_1gb = "db-s-1vcpu-1gb"
    db_s_1vcpu_2gb = "db-s-1vcpu-2gb"
    db_s_2vcpu_4gb = "db-s-2vcpu-4gb"
    db_s_4vcpu_8gb = "db-s-4vcpu-8gb"
    db_s_6vcpu_16gb = "db-s-6vcpu-16gb"
    db_s_8vcpu_32gb = "db-s-8vcpu-32gb"
    db_s_16vcpu_64gb = "db-s-16vcpu-64gb"


class DatabaseEngine(Enum):
    redis = "redis"
    pg = "pg"
    mysql = "mysql"
    mongo = "mongo"


class Engine(Enum):
    mysql = "MYSQL"
    pg = "PG"
    redis = "REDIS"
    mongo = "MONGO"


class PostgreSqlVersion(Version):
    v10 = "10"
    v11 = "11"
    v12 = "12"
    v13 = "13"
    v14 = "14"
    v15 = "15"


class MySqlVersion(Version):
    v8 = "8"


class RedisVersion(Version):
    v5 = "5"
    v6 = "6"
    v7 = "7"


class MongoVersion(Version):
    v4 = "4.4"


class DatabaseUserRole(Enum):
    primary = "primary"
    normal = "normal"


class MySqlAuthPlugin(Enum):
    mysql_native = "mysql_native_password"
    caching_sha2 = "caching_sha2_password"


class DatabaseStatus(Enum):
    creating = "creating"
    online = "online"
    resizing = "resizing"
    migrating = "migrating"


class DbFirewallRuleType(Enum):
    droplet = "droplet"
    k8s = "k8s"
    ip_addr = "ip_addr"
    tag = "tag"


class PgBouncerMode(Enum):
    session = "session"
    transaction = "transaction"
    statement = "statement"


@dataclass
class DatabaseCluster:
    id: Text
    name: Text
    engine: DatabaseEngine
    version: Union[PostgreSqlVersion, MySqlVersion, RedisVersion]
    connection: Union["PgConnection", "RedisConnection"]
    private_connection: Union["PgConnection", "RedisConnection"]
    num_nodes: int
    size: DatabaseSize
    region: Text
    status: DatabaseStatus
    created_at: DateTime
    private_network_uuid: Uuid
    users: Optional[List["DatabaseUser"]] = None
    db_names: Optional[List[Text]] = None
    tags: Optional[List[Text]] = None
    maintenance_window: Optional["DatabaseMaintenanceWindow"] = None


@dataclass(frozen=True)
class DatabaseClusterCreate:
    name: Text
    engine: DatabaseEngine
    version: Union[PostgreSqlVersion, MySqlVersion, RedisVersion]
    size: DatabaseSize
    region: Text
    num_nodes: int
    tags: List[Text] = field(default_factory=list)
    private_network_uuid: Optional[Uuid] = None


@dataclass(frozen=True)
class DatabaseMaintenanceWindow:
    day: Day
    hour: Text
    pending: bool
    description: List[Text] = field(default_factory=list)


@dataclass(frozen=True)
class DatabaseUserCreate:
    name: Text
    mysql_settings: Optional["MySqlSettings"] = None


@dataclass(frozen=True)
class DatabaseUser(DatabaseUserCreate):
    name: Text = ""
    role: DatabaseUserRole = DatabaseUserRole.normal
    password: Text = ""


@dataclass(frozen=True)
class MySqlSettings:
    auth_plugin: MySqlAuthPlugin


@dataclass(frozen=True)
class Database:
    name: Text


@dataclass(frozen=True)
class DatabaseFirewallRuleCreate:
    type: DbFirewallRuleType
    value: Text


@dataclass(frozen=True)
class DatabaseFirewallRule(DatabaseFirewallRuleCreate):
    uuid: Text
    created_at: DateTime
    cluster_uuid: Text


@dataclass(frozen=True)
class DatabaseConnection:
    host: Text
    port: int
    user: Text
    password: Text
    ssl: bool


@dataclass(frozen=True)
class PgConnection(DatabaseConnection):
    database: Text

    @property
    def uri(self) -> Text:
        return (
            f"postgresql://{quote(self.user)}:{quote(self.password)}"
            f"@{quote(self.host)}:{quote(Text(self.port))}"
            f"/{quote(self.database)}"
            f'{"?sslmode=require" if self.ssl else ""}'
        )

    @property
    def env(self):
        return {
            "PGPASSWORD": self.password,
            **({"PGSSLMODE": "require"} if self.ssl else {}),
        }

    pg_env = env  # compat

    def flags(self, database: Text = ""):
        if not database:
            database = self.database

        return [
            f"{x}"
            for x in [
                "-U",
                self.user,
                "-h",
                self.host,
                "-p",
                self.port,
                "-d",
                database,
            ]
        ]

    pg_flags = flags  # compat


@dataclass(frozen=True)
class RedisConnection(DatabaseConnection):
    @property
    def uri(self) -> Text:
        return (
            f"{'rediss' if self.ssl else 'redis'}"
            f"://{quote(self.user)}:{quote(self.password)}"
            f"@{quote(self.host)}:{quote(Text(self.port))}"
            f"/{quote(self.database)}"
        )

    @property
    def env(self):
        return {}


@dataclass
class DatabaseConnectionPoolCreate:
    name: Text
    mode: PgBouncerMode
    size: int
    db: Text
    user: Text


@dataclass
class DatabaseConnectionPool(DatabaseConnectionPoolCreate):
    connection: PgConnection
    private_connection: PgConnection


@dataclass
class DatabaseClusterCollection(Collection):
    databases: List[Union[DatabaseCluster, Any]] = field(default_factory=list)


@dataclass
class DatabaseCollection(Collection):
    dbs: List[Database] = field(default_factory=list)
