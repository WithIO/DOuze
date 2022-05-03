from logging import getLogger
from os import getenv
from typing import Any, Callable, Iterator, List, Optional, Text, Union

from httpx import HTTPError, Timeout
from typefit import api
from typefit import httpx_models as hm

from .models import *
from .types import UndefinedSerializer

logger = getLogger("douze.api")


class DoApi(api.SyncClient):
    BASE_URL = "https://api.digitalocean.com/v2/"

    def __init__(self, api_token: Text = getenv("DO_API_TOKEN", "")):
        super().__init__()
        self.api_token = api_token
        self.helper.http.timeout = Timeout(30.0)

    def init_serialize(self) -> Callable[[Any], Any]:
        """
        We use a custom serializer to avoid sending some fields that are
        None while they should not
        """

        return UndefinedSerializer().serialize

    def headers(self) -> Optional[hm.HeaderTypes]:
        """
        The API expects the token in the headers
        """

        return {"Authorization": f"Bearer {self.api_token}"}

    def extract(self, data: Any, hint: Any) -> Any:
        """
        DigitalOcean had this fantastic idea that every API response is going
        to be a dictionary and the content you're looking for is always going
        to be in a different key that's more or less logic.

        The hint here serves to give the name of that key. By example, if the
        hint is "droplet" the response is expected to be something like

        >>> {
        >>>     "droplet": {
        >>>         # actual droplet content
        >>>     }
        >>> }

        Given that situation, the actual droplet content will be extracted and
        returned.

        If no hint is given, data is returned as-is.

        Parameters
        ----------
        data
            Data to exctract from
        hint
            Name of the key to look for
        """

        if hint:
            return data[hint]

        return data

    def decode(self, resp: hm.Response, hint: Any) -> Any:
        """
        Some responses will be 204 without any content, in that case don't
        try anything. But most of the time it's JSON.
        """

        if resp.status_code != 204:
            return resp.json()

    def raise_errors(self, resp: hm.Response, hint: Any) -> None:
        """
        Hacky way to report API errors to the developer
        """

        try:
            super().raise_errors(resp, hint)
        except HTTPError:
            # noinspection PyBroadException
            try:
                logger.error("API error: %s", resp.json())
            except Exception:
                pass

            raise

    def _iterate_collection(self, page_getter, key, **kwargs):
        """
        General system to iterate through all the pages of a given collection.
        It will return an iterator that goes through all items in all the pages
        of the collection.

        Parameters
        ----------
        page_getter
            Function that will get a specific page. It must accept "page" as
            argument and return a Collection.
        key
            Look for the data into that key inside the collection (like if it's
            the droplets collection, the key will be "droplets").
        kwargs
            Extra kwargs to be passed to the page_getter when called (on top
            of "page").
        """

        page = 1
        found = 0
        count = 1

        while found < count and page < 1000:
            collection = page_getter(page=page, **kwargs)
            items = getattr(collection, key)
            yield from items

            if collection.meta:
                count = collection.meta.total
                found += len(items)
                page += 1
            else:
                break

    @api.get("databases?page={page}")
    def _db_cluster_list(self, page) -> DatabaseClusterCollection:
        """
        Fetches one page of database clusters list
        """

    def db_cluster_list(self) -> Iterator[DatabaseCluster]:
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

        for cluster in self._iterate_collection(self._db_cluster_list, "databases"):
            if isinstance(cluster, DatabaseCluster):
                yield cluster

    @api.post("databases", json=lambda cluster: cluster, hint="database")
    def db_cluster_create(self, cluster: DatabaseClusterCreate) -> DatabaseCluster:
        """
        Creates a database cluster
        """

    @api.get("databases/{cluster_id}", hint="database")
    def db_cluster_get(self, cluster_id: Text) -> DatabaseCluster:
        """
        Returns a database cluster
        """

    @api.get("databases/{cluster_id}/dbs?page={page}")
    def _db_database_list(self, page: int, cluster_id: Text) -> DatabaseCollection:
        """
        Retrieves a single page of the databases list for a cluster
        """

    def db_database_list(self, cluster_id: Text) -> Iterator[Database]:
        """
        Iterates through all the databases present in a cluster
        """

        yield from self._iterate_collection(
            self._db_database_list, "dbs", cluster_id=cluster_id
        )

    @api.post("databases/{cluster_id}/dbs", hint="db", json=lambda database: database)
    def db_database_create(self, cluster_id: Text, database: Database) -> Database:
        """
        Creates a database within a cluster
        """

    @api.get("databases/{cluster_id}/firewall", hint="rules")
    def db_firewall_list(self, cluster_id: Text) -> List[DatabaseFirewallRule]:
        """
        Lists all firewall rules for a given cluster
        """

    @api.put("databases/{cluster_id}/firewall", json=lambda rules: {"rules": rules})
    def db_firewall_update(
        self,
        cluster_id: Text,
        rules: List[Union[DatabaseFirewallRule, DatabaseFirewallRuleCreate]],
    ) -> None:
        """
        Updates the firewall rules for that cluster
        """

    @api.get("databases/{cluster_id}/users", hint="users")
    def db_user_list(self, cluster_id: Text) -> List[DatabaseUser]:
        """
        Retrieves the list of users found in a cluster
        """

    @api.post("databases/{cluster_id}/users", hint="user", json=lambda user: user)
    def db_user_create(
        self, cluster_id: Text, user: DatabaseUserCreate
    ) -> DatabaseUser:
        """
        Creates a user within a cluster
        """

    @api.get("databases/{cluster_id}/pools", hint="pools")
    def db_pool_list(self, cluster_id: Text) -> List[DatabaseConnectionPool]:
        """
        Lists all connection pools present in the cluster
        """

    @api.post("databases/{cluster_id}/pools", hint="pool", json=lambda pool: pool)
    def db_pool_create(
        self, cluster_id: Text, pool: DatabaseConnectionPoolCreate
    ) -> DatabaseConnectionPool:
        """
        Creates a connection pool for that cluster
        """

    @api.get("database/{cluster_id}/pools/{pool_name}", hint="pool")
    def db_pool_get(self, cluster_id: Text, pool_name: Text) -> DatabaseConnectionPool:
        """
        Returns a connection pool from that cluster
        """

    @api.get("droplets?page={page}")
    def _droplet_list(self, page: int) -> DropletCollection:
        """
        Lists droplets on a specific page of the list
        """

    def droplet_list(self) -> Iterator[Droplet]:
        """
        Iterates through all the droplets in the account
        """

        yield from self._iterate_collection(self._droplet_list, "droplets")
