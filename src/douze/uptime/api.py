from functools import partial
from typing import Any, Iterator, Text, Union
from urllib.parse import urljoin

from typefit import api

from douze.api import DoApi

from .. import DoApiMixin
from .models import Alert, AlertCollection, Check, ChecksCollection


class ChecksApi(DoApiMixin):
    """
    DigitalOcean Uptime Checks provide the ability to monitor your endpoints from around the world,
    and alert you when they're slow, unavailable, or SSL certificates are expiring.
    """

    BASE_URL = urljoin(DoApiMixin.BASE_URL, "uptime/")

    def __init__(self, root_api: DoApi):
        super().__init__(root_api.api_token)

    @api.get("checks?page={page}")
    def _checks_list(self, page: int) -> ChecksCollection:
        """
        Fetches one page of Checks list.
        """

    def checks_list(self) -> Iterator[Check]:
        """
        List all the Uptime checks on your account.
        """
        yield from self.iterate_collection(self._checks_list, "uptime")

    @api.get("checks/{check_id}", hint="check")
    def check_get(self, check_id: Text) -> Check:
        """
        Retrieve a Check by its ID.
        """

    @api.get("checks/{check_id}/alerts?page={page}")
    def _alerts_list(self, check_id: Text, page: int) -> AlertCollection:
        """
        Fetches one page of Alerts list.
        """

    def alert_list(self, check_id: Text) -> Iterator[Alert]:
        """
        List all the Uptime alerts on your account.
        """
        page_getter = partial(self._alerts_list, check_id)
        yield from self.iterate_collection(page_getter, "alerts")
