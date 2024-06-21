import logging
from os import getenv
from typing import Text

try:
    from functools import cached_property
except ImportError:
    # fallback for python 3.7
    cached_property = property


class DoApi:
    """
    Root class for all sub apis of DigitalOcean.
    """

    def __init__(self, api_token: Text = getenv("DO_API_TOKEN", "")):
        super().__init__()
        self.api_token = api_token
        self.logger = logging.getLogger("douze.api")

    @cached_property
    def apps(self):
        from .apps.api import AppsApi

        return AppsApi(self)

    @cached_property
    def db(self):
        from .db.api import DatabaseApi

        return DatabaseApi(self)

    @cached_property
    def droplet(self):
        from .droplet.api import DropletApi

        return DropletApi(self)

    @cached_property
    def registry(self):
        from .registry.api import RegistryApi

        return RegistryApi(self)

    @cached_property
    def uptime(self):
        from .uptime.api import ChecksApi

        return ChecksApi(self)
