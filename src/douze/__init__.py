from logging import getLogger
from typing import Any, Callable, Optional, Text

from httpx import HTTPError, Timeout
from typefit import api
from typefit import httpx_models as hm

from .types import UndefinedSerializer

logger = getLogger("douze.api")


class DoApiMixin(api.SyncClient):
    BASE_URL = "https://api.digitalocean.com/v2/"

    def __init__(self, api_token: Text):
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

    @staticmethod
    def iterate_collection(page_getter, key, **kwargs):
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
