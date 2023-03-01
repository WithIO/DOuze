from functools import partial
from typing import Iterator, Text, Union

from httpx import HTTPError
from typefit import api

from .. import DoApiMixin
from ..api import DoApi
from .models import *


class RegistryApi(DoApiMixin):
    def __init__(self, root: DoApi):
        super().__init__(root.api_token)
        self.api = root

    @api.get("registry")
    def registry(self) -> RegistryInformation:
        """
        Get information about your container registry.
        """

    @api.post(
        "registry",
        json=lambda name, subscription_tier_slug, region: {
            "name": name,
            "subscription_tier_slug": subscription_tier_slug,
            "region": region,
        },
    )
    def registry_create(
        self,
        name: Text,
        subscription_tier_slug: TierSlug,
        region: RegistryRegion,
    ) -> Union[Registry, RegistryInformation]:
        """
        Create your container registry.
        The name becomes part of the URL for images stored in the registry.
        For example, if your registry is called `example`, an image in it will
        have the URL `registry.digitalocean.com/example/image:tag`.

        Parameters
        ----------
        name
            A globally unique name for the container registry.
            Must be lowercase and be composed only of numbers, letters and -, up to a limit of 63 characters.
        subscription_tier_slug
            The slug of the subscription tier to sign up for.
            Valid values can be retrieved using the options endpoint.
        region
            Slug of the region where registry data is stored. When not provided, a region will be selected.

        Returns
        -------
            Not sure if it will include the subscription information or not
        """

    @api.delete("registry")
    def _registry_delete(self) -> None:
        """
        Delete your container registry, destroying all container image data stored in it.
        """

    def registry_delete(self) -> bool:
        try:
            self._registry_delete()
            return True
        except HTTPError:
            return False

    @api.post("registry/validate-name", json=lambda name: {"name": name})
    def _validate_name(self, name: Text) -> None:
        """
        A globally unique name for the container registry.
        Must be lowercase and be composed only of numbers, letters and -, up to a limit of 63 characters.
        """

    def validate_name(self, name: Text) -> bool:
        """
        A globally unique name for the container registry.
        Must be lowercase and be composed only of numbers, letters and -, up to a limit of 63 characters.
        """
        from ..validations import registry_name

        if not registry_name(name):
            raise ValueError

        try:
            self._validate_name(name)
            return True
        except HTTPError:
            return False

    @api.get("registry/{name}/repositoriesV2?page={page}")
    def _list_repositories(self, name: Text, page: int) -> RepositoryCollection:
        """
        List all repositories in your container registry.
        """

    def repositories(self, name: Text) -> Iterator[Repository]:
        """
        List all repositories in your container registry.
        """
        page_getter = partial(self._list_repositories, name)
        yield from self.iterate_collection(page_getter, "repositories")

    @api.get("registry/{registry}/{repository}/tags")
    def _list_tags(self, registry: Text, repository: Text) -> TagCollection:
        """
        List all tags in your container registry repository.
        """

    def repository_tags(self, registry: Text, repository: Text) -> Iterator[Tag]:
        """
        List all tags in your container registry repository.
        """
        yield from self._list_tags(registry, repository).tags

    @api.post("registry/{registry}/garbage-collection", hint="garbage_collection")
    def garbage_collect(self, registry: Text) -> GarbageCollection:
        """
        Garbage collection enables users to clear out unreferenced blobs
        (layer & manifest data) after deleting one or more manifests from a repository.
        If there are no unreferenced blobs resulting from the deletion of one or more manifests,
        garbage collection is effectively a noop.

        See [here for more information](https://www.digitalocean.com/docs/container-registry/how-to/clean-up-container-registry/)
        about how and why you should clean up your container registry periodically.

        This will initiate the following sequence of events on your registry.

        - Set the registry to read-only mode, meaning no further write-scoped JWTs will be issued to registry clients.
          Existing write-scoped JWTs will continue to work until they expire which can take up to 15 minutes.
        - Wait until all existing write-scoped JWTs have expired.
        - Scan all registry manifests to determine which blobs are unreferenced.
        - Delete all unreferenced blobs from the registry.
        - Record the number of blobs deleted and bytes freed, mark the garbage collection status as success.
        - Remove the read-only mode restriction from the registry, meaning write-scoped JWTs will once again be issued to registry clients.
        """

    @api.get("registry/{registry}/garbage-collection")
    def garbage_collection_get(self, registry: Text) -> GarbageCollection:
        """
        Get information about the currently-active garbage collection for a registry
        """

    @api.get("registry/options", hint="options")
    def registry_options(self) -> RegistryOptions:
        """
        Provides additional information as to which option values are available when creating a container registry.
        There are multiple subscription tiers available for container registry.
        Each tier allows a different number of image repositories to be created in your registry,
        and has a different amount of storage and transfer included. There are multiple regions available
        for container registry and controls where your data is stored.
        """

    def on_response(self, request, response) -> None:
        json = response.json()
        print(json)

    @api.get("registry/docker-credentials", hint="auths")
    def docker_credentials(self) -> Auth:
        """

        Returns
        -------

        """
