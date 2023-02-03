from functools import cached_property
from typing import Any, NamedTuple, Optional

from .api import DoApi


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
    >>> i.db.psql_database('some-cluster', 'my-db')

    If the database does not exist yet, then it will be created while if it
    already exists it will stay in place.
    """

    def __init__(self, api: DoApi):
        self.api: DoApi = api
        self._cluster_cache = {}

    @cached_property
    def db(self):
        from .db.idem_api import DatabaseIdemApi

        return DatabaseIdemApi(self)

    @cached_property
    def apps(self):
        from .apps.idem_api import AppsIdemApi

        return AppsIdemApi(self)

    @cached_property
    def uptime(self):
        from .uptime.idem_api import UptimeIdemApi

        return UptimeIdemApi(self)

    @cached_property
    def auth(self):
        from .auth.idem_api import AuthIdemApi

        return AuthIdemApi(self)
