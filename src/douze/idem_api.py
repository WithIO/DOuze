import subprocess
from contextlib import contextmanager
from dataclasses import replace
from os import environ
from tempfile import NamedTemporaryFile
from time import sleep, time
from typing import Any, List, NamedTuple, Optional, Sequence, Text

from httpx import Client

from .api import DoApi
from .models import *
from .types import Uuid


class IdemApiError(Exception):
    pass


class Outcome(NamedTuple):
    changed: bool
    output: Optional[Any] = None


class DoIdemApi:
    """
    DigitalOcean idempotent API. It's made to be used as a backend for Ansible
    modules. Basically, instead of describing actions, you describe what you
    would like to see and the API will make sure that it exists.

    Examples
    --------
    You could want to create a database within an existing cluster:

    >>> i = DoIdemApi(DoApi())
    >>> i.psql_database('some-cluster', 'my-db')

    If the database does not exist yet then it will be created while if it
    already exists it will stay in place.
    """

    DEFAULT_PSQL_VERSION = PostgreSqlVersion.v11
    PROVISION_TIMEOUT = 60 * 30
    PROVISION_POLL = 5

    def __init__(self, api: DoApi):
        self.api: DoApi = api
        self._cluster_cache = {}

    def _find_cluster_by_name(self, name) -> Optional[DatabaseCluster]:
        """
        For some reason, the API asks that you set a unique name to clusters
        but then references them based on a different ID. In order to make this
        class workable, it uses cluster names everywhere so this helper is
        used internally to find the clusters from their name and thus their ID.

        Please note that clusters associated to given names are kept in cache,
        so if you're developing new functions and they operate on clusters,
        don't forget to update the cache otherwise you're going to get into
        trouble.

        Parameters
        ----------
        name
            Name of the desired cluster
        """

        if name not in self._cluster_cache:
            cluster = None

            for candidate in self.api.db_cluster_list():
                if candidate.name == name:
                    cluster = candidate
                    break

            self._cluster_cache[name] = cluster

        return self._cluster_cache[name]

    def _find_database_by_name(
        self, cluster_id: Text, name: Text
    ) -> Optional[Database]:
        """
        Finds a specific database by name. Same thing as with the clusters.

        Parameters
        ----------
        cluster_id
            ID of the cluster containing a database.
        name
            Name of the database you're looking for
        """

        for candidate in self.api.db_database_list(cluster_id):
            if candidate.name == name:
                return candidate

    def _get_public_ipv4(self) -> Text:
        """
        Tries to figure out your public IPv4, this is helpful to gain temporary
        access to the firewall in order to copy the databases by example.
        """

        with Client() as c:
            return c.get("https://httpbin.org/get").json()["origin"]

    @contextmanager
    def _allow_self_access(self, cluster_name: Text):
        """
        That's a context manager which will make sure that your IP address is
        allowed in the cluster's firewall during the context.

        If the IP was already allowed, it'll stay there afterwards while if it
        was not there it'll get cleaned up when all is done (or failed).

        Notes
        -----
        The public IP is determined automatically by `_get_public_ipv4()`.

        Parameters
        ----------
        cluster_name
            Name of the cluster to allow the current IP for
        """

        ip = self._get_public_ipv4()
        roll_back, _ = self.db_firewall_rule(
            cluster_name,
            [DatabaseFirewallRuleCreate(DbFirewallRuleType.ip_addr, ip)],
            EntryState.present,
        )

        try:
            yield
        finally:
            if roll_back:
                self.db_firewall_rule(
                    cluster_name,
                    [DatabaseFirewallRuleCreate(DbFirewallRuleType.ip_addr, ip)],
                    EntryState.absent,
                )

    def db_firewall_allow_self(self, cluster_name: Text):
        """
        Ensures that there is a permanent rule allowing this computer's public
        IP address to connect the cluster.

        Parameters
        ----------
        cluster_name
            Name of the cluster to whitelist the IP in
        """

        ip = self._get_public_ipv4()
        return self.db_firewall_rule(
            cluster_name,
            [DatabaseFirewallRuleCreate(DbFirewallRuleType.ip_addr, ip)],
            EntryState.present,
        )

    def db_firewall_rule(
        self,
        cluster_name: Text,
        rules: List[DatabaseFirewallRuleCreate],
        state: EntryState = EntryState.present,
    ) -> Outcome:
        """
        Ensures that this list of rules is either present or absent from the
        cluster's firewall.

        Parameters
        ----------
        cluster_name
            Name of the cluster
        rules
            List of rules to be looked for
        state
            How do you want the rules?
        """

        cluster = self._find_cluster_by_name(cluster_name)
        changed = False
        rules_set = set(rules)
        new_rules = []

        for rule in self.api.db_firewall_list(cluster.id):
            rc = DatabaseFirewallRuleCreate(type=rule.type, value=rule.value)

            if state == EntryState.present:
                new_rules.append(rule)

                if rc in rules_set:
                    rules_set.remove(rc)
            else:
                if rc not in rules_set:
                    new_rules.append(rule)
                else:
                    changed = True

        if rules_set and state == EntryState.present:
            new_rules.extend(rules_set)
            changed = True

        if changed:
            self.api.db_firewall_update(cluster.id, new_rules)

        return Outcome(changed)

    def db_firewall_droplets(
        self, cluster_name: Text, droplet_names: Sequence[Text]
    ) -> Outcome:
        """
        Allows a given list of droplets (based on their name) to access the
        cluster.

        Parameters
        ----------
        cluster_name
            Name of the cluster for which you're doing this
        droplet_names
            Names of the droplets you want to whitelist
        """

        cluster = self._find_cluster_by_name(cluster_name)
        droplet_names = set(droplet_names)
        droplet_ids = []

        for droplet in self.api.droplet_list():
            if droplet.name in droplet_names:
                droplet_ids.append(droplet.id)
                droplet_names.remove(droplet.name)

            if not droplet_names:
                break

        if droplet_names:
            raise IdemApiError(f"Droplets not found: {droplet_names!r}")

        return self.db_firewall_rule(
            cluster.name,
            [
                DatabaseFirewallRuleCreate(DbFirewallRuleType.droplet, f"{x}")
                for x in droplet_ids
            ],
            EntryState.present,
        )

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
        size
            Size of the cluster
        nodes
            How many nodes do you want? Minimum 1, maximum 3 (except on the
            smallest size which can have only 1 node)
        version
            Version of PostgreSQL
        private_network
            ID of the private network to connect this cluster to. If not
            specified, it will get connected to the default network for this
            region.
        skip_checks
            Don't check that existing clusters match specifications
        """

        cluster = self._find_cluster_by_name(name)
        changed = False

        if cluster is None:
            changed = True
            cluster = self.api.db_cluster_create(
                DatabaseClusterCreate(
                    name=name,
                    engine=DatabaseEngine.pg,
                    version=version,
                    size=size,
                    region=region,
                    num_nodes=nodes,
                    private_network_uuid=private_network,
                )
            )

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

        return Outcome(changed)

    def psql_database(
        self,
        cluster_name: Text,
        name: Text,
        copy_db_name: Text = "",
    ) -> Outcome:
        """
        Makes sure that this database exists. If the copy_db_name is specified,
        then the content will be copied from that other database (only at
        create time, not on subsequent runs).

        Notes
        -----
        Copy uses "pg_dump" and "psql", of the binaries are not installed on
        your system this will fail.

        Also, after the copy, the owner of tables will be doadmin. This is
        fixed when you attribute a user to this database using the psql_user()
        method.

        Parameters
        ----------
        cluster_name
            Name of the cluster to create the DB into
        name
            Name of the DB you want
        copy_db_name
            If creating the DB, copy the content from that other DB (from the
            same cluster)
        """

        changed = False
        cluster = self._find_cluster_by_name(cluster_name)

        if not cluster:
            raise IdemApiError(f"Cluster {cluster_name!r} does not exist")

        db = self._find_database_by_name(cluster.id, name)

        with self._allow_self_access(cluster.name):
            if not db:
                changed = True
                self.api.db_database_create(cluster.id, Database(name=name))

            if changed and copy_db_name:
                with NamedTemporaryFile() as f_info:
                    env = {**environ, **cluster.connection.pg_env}

                    with open(f_info.name, "wb") as f:
                        ret = subprocess.run(
                            [
                                "pg_dump",
                                "-O",
                                *cluster.connection.pg_flags(copy_db_name),
                            ],
                            env=env,
                            stdout=f,
                            stderr=subprocess.PIPE,
                        )

                        if ret.returncode:
                            raise IdemApiError(
                                f"Error while dumping DB: {ret.stderr[0:1000]}"
                            )

                    with open(f_info.name, "rb") as f:
                        ret = subprocess.run(
                            ["psql", *cluster.connection.pg_flags(name)],
                            env=env,
                            stdin=f,
                            capture_output=True,
                        )

                        if ret.returncode:
                            raise IdemApiError(
                                f"Error while restoring DB dump: {ret.stderr[0:1000]}"
                            )

        return Outcome(changed)

    def psql_user(
        self,
        cluster_name: Text,
        user_name: Text,
        db_name: Text,
        pool_size: int = 1,
    ):
        """
        Ensures a user which has the rights to access the "db_name" database.
        If the user is being created, then all tables from "db_name" will be
        reassigned to this user. This is to fix the ownership of tables from
        the copy (see psql_database()).

        If a non-zero pool size is specified, a pool of that size will be
        created for this user.

        The outcome of this function will contain connection parameters for
        this user, both on the public and the private network. Please note
        that if a pool was created then the connection settings will be those
        of the pool instead of a direct connection.

        Parameters
        ----------
        cluster_name
            Name of the cluster you want to create this user in
        user_name
            Name of the user you're creating
        db_name
            Name of the database for which this user is destined
        pool_size
            Size of the connection pool. Put 0 if you don't want any pool to
            be created.
        """

        cluster = self._find_cluster_by_name(cluster_name)
        user = None
        changed = False

        for candidate in self.api.db_user_list(cluster.id):
            if candidate.name == user_name:
                user = candidate

        if not user:
            changed = True
            user = self.api.db_user_create(
                cluster.id, DatabaseUserCreate(name=user_name)
            )

            with self._allow_self_access(cluster.name):
                ret = subprocess.run(
                    ["psql", *cluster.connection.pg_flags(db_name)],
                    env={**environ, **cluster.connection.pg_env},
                    capture_output=True,
                    input=f'reassign owned by "{cluster.connection.user}" to "{user_name}"'.encode(
                        "utf-8"
                    ),
                )

            if ret.returncode:
                raise IdemApiError(
                    f"Error while re-assigning DB tables to user: {ret.stderr[0:1000]}"
                )

        pool = None

        for candidate in self.api.db_pool_list(cluster.id):
            if candidate.name == f"user_{user_name}":
                pool = candidate
                break

        if not pool and pool_size:
            changed = True
            pool = self.api.db_pool_create(
                cluster.id,
                DatabaseConnectionPoolCreate(
                    name=f"user_{user_name}",
                    mode=PgBouncerMode.transaction,
                    size=pool_size,
                    db=db_name,
                    user=user_name,
                ),
            )

        if pool:
            private_connection = pool.private_connection
            connection = pool.connection
        else:
            private_connection = replace(
                cluster.private_connection,
                user=user.name,
                database=db_name,
                password=user.password,
            )
            connection = replace(
                cluster.connection,
                user=user.name,
                database=db_name,
                password=user.password,
            )

        return Outcome(
            changed,
            {
                "private_connection": private_connection,
                "connection": connection,
            },
        )
