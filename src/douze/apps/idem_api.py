from dataclasses import dataclass, field
from time import sleep, time
from typing import Iterator, Optional, Text, Union
from urllib.parse import quote

from douze import api
from douze.api import DoApi
from douze.apps.models import Engine
from douze.idem_api import DoIdemApi, IdemApiError, Outcome
from douze.models import (
    DatabaseSize,
    DatabaseStatus,
    MongoVersion,
    MySqlVersion,
    PostgreSqlVersion,
    RedisVersion,
)
from douze.types import Uuid


@dataclass
class DatabaseConnection:
    database: Text
    host: Text
    port: int
    user: Text
    password: Text
    ssl: bool


@dataclass
class PgConnection:
    conn: DatabaseConnection

    @property
    def uri(self) -> Text:
        return (
            f"postgresql://{quote(self.conn.user)}:{quote(self.conn.password)}"
            f"@{quote(self.conn.host)}:{quote(Text(self.conn.port))}"
            f"/{quote(self.conn.database)}"
            f'{"?sslmode=require" if self.conn.ssl else ""}'
        )

    @property
    def env(self):
        return {
            "PGPASSWORD": self.conn.password,
            **({"PGSSLMODE": "require"} if self.conn.ssl else {}),
        }

    pg_env = env  # compat

    def flags(self, database: Text = ""):
        if not database:
            database = self.conn.database

        return [
            f"{x}"
            for x in [
                "-U",
                self.conn.user,
                "-h",
                self.conn.host,
                "-p",
                self.conn.port,
                "-d",
                database,
            ]
        ]

    pg_flags = flags  # compat


@dataclass
class RedisConnection(PgConnection):
    @property
    def uri(self) -> Text:
        return (
            f"{'rediss' if self.conn.ssl else 'redis'}"
            f"://{quote(self.conn.user)}:{quote(self.conn.password)}"
            f"@{quote(self.conn.host)}:{quote(Text(self.conn.port))}"
            f"/{quote(self.conn.database)}"
        )

    @property
    def env(self):
        return {}


@dataclass
class DatabaseClusterCreate:
    name: Text
    engine: Engine
    version: Union[PostgreSqlVersion, MySqlVersion, RedisVersion, MongoVersion]
    size: DatabaseSize
    region: Text
    num_nodes: int
    tags: Iterator[Text] = field(default_factory=list)
    private_network_uuid: Optional[Uuid] = None


class AppsIdemApi(DoIdemApi):
    DEFAULT_PSQL_VERSION = PostgreSqlVersion.v14
    DEFAULT_REDIS_VERSION = RedisVersion.v7
    DEFAULT_MYSQL_VERSION = MySqlVersion.v8
    DEFAULT_MONGO_VERSION = MongoVersion.v4

    def __init__(self, root_api: DoIdemApi):
        super().__init__(root_api.api)
        # this is for IntelliSense, as the type def in super does not match

    def _find_user_by_name(self, cluster_id: Text, user_name: Text):
        for candidate in self.api.db.user_list(cluster_id):
            if candidate.name == user_name:
                return candidate

    def _find_app_by_name(self, app_name: Text):
        return self.api.apps.app_get(app_name=app_name)
