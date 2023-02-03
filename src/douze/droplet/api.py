from typing import Iterator
from urllib.parse import urljoin

from typefit import api

from douze.api import DoApi

from .models import *
from .models import DropletCollection


class DropletApi(DoApi):
    def __init__(self, root_api: DoApi):
        super().__init__(root_api.api_token)
        self.BASE_URL = urljoin(super().BASE_URL, "droplets")

    @api.get("?page={page}")
    def _droplet_list(self, page: int) -> DropletCollection:
        """
        Lists droplets on a specific page of the list
        """

    def droplet_list(self) -> Iterator[Droplet]:
        """
        Iterates through all the droplets in the account
        """

        yield from self._iterate_collection(self._droplet_list, "droplets")
