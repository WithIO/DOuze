from typing import Iterator

from typefit import api

from .. import DoApiMixin
from ..api import DoApi
from .models import *
from .models import DropletCollection


class DropletApi(DoApiMixin):
    def __init__(self, root: DoApi):
        super().__init__(root.api_token)
        self.api = root

    @api.get("droplets?page={page}")
    def _droplet_list(self, page: int) -> DropletCollection:
        """
        Lists droplets on a specific page of the list
        """

    def droplet_list(self) -> Iterator[Droplet]:
        """
        Iterates through all the droplets in the account
        """

        yield from self.iterate_collection(self._droplet_list, "droplets")
