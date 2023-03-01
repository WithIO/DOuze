import logging
from typing import Any, NamedTuple, Optional

from .api import DoApi

try:
    from functools import cached_property
except ImportError:
    # fallback for python 3.7
    cached_property = property


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
        self.logger = logging.getLogger("douze.idem_api")

    @cached_property
    def apps(self):
        from .apps.idem_api import AppsIdemApi

        return AppsIdemApi(self.api)

    @cached_property
    def db(self):
        from .db.idem_api import DatabaseIdemApi

        return DatabaseIdemApi(self.api)

    @cached_property
    def droplet(self):
        from .droplet.idem_api import DropletIdemApi

        return DropletIdemApi(self.api)

    @cached_property
    def registry(self):
        from .registry.idem_api import RegistryIdemApi

        return RegistryIdemApi(self.api)

    @cached_property
    def uptime(self):
        from .uptime.idem_api import UptimeIdemApi

        return UptimeIdemApi(self.api)
