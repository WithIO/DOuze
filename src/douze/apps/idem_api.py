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


class AppsIdemApi(api.SyncClient):
    DEFAULT_PSQL_VERSION = PostgreSqlVersion.v14
    DEFAULT_REDIS_VERSION = RedisVersion.v7
    DEFAULT_MYSQL_VERSION = MySqlVersion.v8
    DEFAULT_MONGO_VERSION = MongoVersion.v4

    def __init__(self, do_api: DoApi):
        super().__init__(do_api)
        # this is for IntelliSense, as the type def in super does not match
        self.api: DoApi = self.api

    def _find_user_by_name(self, cluster_id: Text, user_name: Text):
        for candidate in self.api.db_user_list(cluster_id):
            if candidate.name == user_name:
                return candidate

    def _database_cluster(
        self,
        name: Text,
        region: Text,
        engine: Engine,
        size: DatabaseSize,
        nodes: int,
        private_network: Optional[Uuid] = None,
        skip_checks: bool = False,
        version: Union[
            PostgreSqlVersion, MySqlVersion, RedisVersion, MongoVersion
        ] = None,
    ) -> Outcome:
        """
        Makes sure that this cluster exists. If the existing cluster doesn't
        match the specifications, this function will fail and not attempt to
        make any changes.

        Parameters
        ----------
        name
            Name of the cluster
        region
            DigitalOcean region for that cluster (by example: "ams3"), see the
            documentation to get those.
        engine
            possible values: "redis", "pg", "mysql", "mongodb"
        size
            slug size of the cluster
        nodes
            How many nodes do you want? Minimum 1, maximum 3 (except on the
            smallest size which can have only 1 node)
        version
            desired version of the cluster
        private_network
            ID of the private network to connect this cluster to. If not
            specified, it will get connected to the default network for this
            region.
        skip_checks
            Don't check that existing clusters match specifications
        """

        cluster = self._find_cluster_by_name(name)
        changed = False
        output = None

        if cluster is None:
            changed = True
            cluster = self.api.db_cluster_create(
                DatabaseClusterCreate(
                    name=name,
                    engine=engine,
                    version=version,
                    size=size,
                    region=region,
                    num_nodes=nodes,
                    private_network_uuid=private_network,
                )
            )
            output = f"Created {engine.name} database cluster {name}"

        if cluster.status != DatabaseStatus.online:
            start = time()

            for _ in range(0, self.PROVISION_TIMEOUT // self.PROVISION_POLL + 1):
                sleep(self.PROVISION_POLL)
                cluster = self.api.db_cluster_get(cluster.id)

                if cluster.status == DatabaseStatus.online:
                    break

                if time() - start > self.PROVISION_TIMEOUT:
                    break

        if cluster.status != DatabaseStatus.online:
            raise IdemApiError("Cluster failed to come online")

        if not skip_checks:
            if cluster.size != size:
                raise IdemApiError("Existing cluster does not have the right size")

            if cluster.region != region:
                raise IdemApiError("Existing cluster is not in the right region")

            if cluster.num_nodes != nodes:
                raise IdemApiError(
                    "Existing cluster does not have the right nodes number"
                )

        self._cluster_cache[cluster.name] = cluster

        return Outcome(changed, output)

    def psql_cluster(
        self,
        name: Text,
        region: Text,
        size: DatabaseSize,
        nodes: int,
        version: PostgreSqlVersion = DEFAULT_PSQL_VERSION,
        private_network: Optional[Uuid] = None,
        skip_checks: bool = False,
    ) -> Outcome:
        return self._database_cluster(
            name=name,
            region=region,
            engine=Engine.pg,
            size=size,
            nodes=nodes,
            private_network=private_network,
            skip_checks=skip_checks,
            version=version,
        )

    def redis_cluster(
        self,
        name: Text,
        region: Text,
        size: DatabaseSize,
        nodes: int,
        version: RedisVersion = DEFAULT_REDIS_VERSION,
        private_network: Optional[Uuid] = None,
        skip_checks: bool = False,
    ) -> Outcome:
        return self._database_cluster(
            name=name,
            region=region,
            engine=Engine.redis,
            size=size,
            nodes=nodes,
            private_network=private_network,
            skip_checks=skip_checks,
            version=version,
        )

    def mysql_cluster(
        self,
        name: Text,
        region: Text,
        size: DatabaseSize,
        nodes: int,
        version: MySqlVersion = DEFAULT_MYSQL_VERSION,
        private_network: Optional[Uuid] = None,
        skip_checks: bool = False,
    ) -> Outcome:
        return self._database_cluster(
            name=name,
            region=region,
            engine=Engine.mysql,
            size=size,
            nodes=nodes,
            private_network=private_network,
            skip_checks=skip_checks,
            version=version,
        )

    def mongo_cluster(
        self,
        name: Text,
        region: Text,
        size: DatabaseSize,
        nodes: int,
        version: MongoVersion = DEFAULT_MONGO_VERSION,
        private_network: Optional[Uuid] = None,
        skip_checks: bool = False,
    ) -> Outcome:
        return self._database_cluster(
            name=name,
            region=region,
            engine=Engine.mongo,
            size=size,
            nodes=nodes,
            private_network=private_network,
            skip_checks=skip_checks,
            version=version,
        )

    def _find_app_by_name(self, app_name: Text):
        return self.api.apps.app_get(app_name=app_name)
