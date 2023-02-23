from typing import Iterator, List, Text, Union

from typefit import api

from .. import DoApiMixin
from ..api import DoApi
from .models import *


class DatabaseApi(DoApiMixin):
    def __init__(self, root: DoApi):
        super().__init__(root.api_token)
        self.api = root  # to access other parts of the api

    @api.get("databases?page={page}")
    def _cluster_list(self, page) -> DatabaseClusterCollection:
        """
        Fetches one page of database clusters list
        """

    def cluster_list(self) -> Iterator[DatabaseCluster]:
        """
        Lists all database clusters present on the account

        Notes
        -----
        Since new versions of DB engines get added and so forth, we don't want
        to avoid a crash in case things are not fit. That's why the databases
        attributes also allows to not fit. Here we're checking that we're
        returning only the instances that are indeed recognized. The other ones
        are just ignored.
        """

        for cluster in self.iterate_collection(self._cluster_list, "databases"):
            if isinstance(cluster, DatabaseCluster):
                yield cluster

    @api.post("databases", json=lambda cluster: cluster, hint="database")
    def cluster_create(self, cluster: DatabaseClusterCreate) -> DatabaseCluster:
        """
        Creates a database cluster
        """

    @api.get("databases/{cluster_id}", hint="database")
    def cluster_get(self, cluster_id: Text) -> DatabaseCluster:
        """
        Returns a database cluster
        """

    @api.get("databases/{cluster_id}/dbs?page={page}")
    def _database_list(self, page: int, cluster_id: Text) -> DatabaseCollection:
        """
        Retrieves a single page of the databases list for a cluster
        """

    def database_list(self, cluster_id: Text) -> Iterator[Database]:
        """
        Iterates through all the databases present in a cluster
        """

        yield from self.iterate_collection(
            self._database_list, "dbs", cluster_id=cluster_id
        )

    @api.post("databases/{cluster_id}/dbs", hint="db", json=lambda database: database)
    def database_create(self, cluster_id: Text, database: Database) -> Database:
        """
        Creates a database within a cluster
        """

    @api.delete("databases/{cluster_id}/dbs/{database_name}")
    def database_delete(self, cluster_id: Text, database_name: Text) -> None:
        """
        Deletes the specified database within the cluster
        """

    @api.get("databases/{cluster_id}/firewall", hint="rules")
    def firewall_list(self, cluster_id: Text) -> List[DatabaseFirewallRule]:
        """
        Lists all firewall rules for a given cluster
        """

    @api.put("databases/{cluster_id}/firewall", json=lambda rules: {"rules": rules})
    def firewall_update(
        self,
        cluster_id: Text,
        rules: List[Union[DatabaseFirewallRule, DatabaseFirewallRuleCreate]],
    ) -> None:
        """
        Updates the firewall rules for that cluster
        """

    @api.get("databases/{cluster_id}/users", hint="users")
    def user_list(self, cluster_id: Text) -> List[DatabaseUser]:
        """
        Retrieves the list of users found in a cluster
        """

    @api.post("databases/{cluster_id}/users", hint="user", json=lambda user: user)
    def user_create(self, cluster_id: Text, user: DatabaseUserCreate) -> DatabaseUser:
        """
        Creates a user within a cluster
        """

    @api.delete("databases/{cluster_id}/users/{user_name}")
    def user_delete(self, cluster_id: Text, user_name: Text) -> None:
        """
        Deletes a user within a cluster
        """

    @api.get("databases/{cluster_id}/pools", hint="pools")
    def pool_list(self, cluster_id: Text) -> List[DatabaseConnectionPool]:
        """
        Lists all connection pools present in the cluster
        """

    @api.post("databases/{cluster_id}/pools", hint="pool", json=lambda pool: pool)
    def pool_create(
        self, cluster_id: Text, pool: DatabaseConnectionPoolCreate
    ) -> DatabaseConnectionPool:
        """
        Creates a connection pool for that cluster
        """

    @api.delete("databases/{cluster_id}/pools/{pool_name}")
    def pool_delete(self, cluster_id: Text, pool_name: Text) -> None:
        """
        Deletes a connection pool for that cluster
        """

    @api.get("databases/{cluster_id}/pools/{pool_name}", hint="pool")
    def pool_get(self, cluster_id: Text, pool_name: Text) -> DatabaseConnectionPool:
        """
        Returns a connection pool from that cluster
        """
