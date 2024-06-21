from functools import partial
from typing import Any, Callable, Iterator, Optional, Text

from typefit import api
from typefit import httpx_models as hm

from .. import DoApiMixin
from ..api import DoApi
from ..types import IgnoreNoneSerializer
from .models import *


class AppsApi(DoApiMixin):
    def __init__(self, root: DoApi):
        super().__init__(root.api_token)
        self.api = root

    def init_serialize(self) -> Callable[[Any], Any]:
        return IgnoreNoneSerializer().serialize

    @api.get("apps?page={page}")
    def _apps_list(self, page) -> AppCollection:
        """
        Fetches one page of Apps list.
        """

    def apps_list(self) -> Iterator[App]:
        """
        List all apps on your account. Information about the current
        active deployment as well as any in progress ones will also be
        included for each app.
        """
        for app in self.iterate_collection(self._apps_list, "apps"):
            if isinstance(app, App):
                yield app

    @api.get("apps/{app_id}", hint="app")
    def _app_get_by_id(self, app_id: Text) -> App:
        """
        Retrieve details about an existing app by its ID.
        """

    def _app_get_by_name(self, app_name: Text) -> App:
        """
        Retrieve details about an existing app by its name.
        """
        for app in self.apps_list():
            if app.spec.name == app_name:
                return app

    def app_get(
        self,
        *,
        app_id: Optional[Text] = None,
        app_name: Optional[Text] = None,
    ) -> App:
        """
        Retrieve details about an existing app either by its ID or name.
        To retrieve an app by its name, do not include an ID.
        Information about the current active deployment as well as any in
        progress ones will also be included in the response.
        """
        if app_id is not None:
            return self._app_get_by_id(app_id)

        if app_name is not None:
            return self._app_get_by_name(app_name)

        raise ValueError("you must supply either 'app_id' or 'app_name'")

    @api.post("apps", json=lambda app_spec: {"spec": app_spec}, hint="app")
    def app_create(self, app_spec: AppSpec) -> App:
        """
        Create a new app by submitting an app specification.
        """

    @api.put("apps/{app_id}", json=lambda app_spec: {"spec": app_spec}, hint="app")
    def app_update(self, app_id: Text, app_spec: AppSpec) -> App:
        """
        Update an existing app by submitting a new app specification.
        """

    @api.delete("apps/{app_id}", hint="id")
    def app_delete(self, app_id: Text) -> Text:
        """
        UNTESTED
        Delete an existing app. Once deleted, all active deployments will be
        permanently shut down and the app deleted.
        """

    @api.get("apps/{app_id}/deployments?page={page}")
    def _app_deployments_list(self, app_id: Text, page: int) -> AppDeploymentCollection:
        """
        Fetches one page of Deployments list.
        """

    def app_deployments_list(self, app_id: Text) -> Iterator[AppDeployment]:
        """
        List all deployments of an app.

        Parameters
        ----------
        app_id
            The app ID.
        """
        return self.iterate_collection(
            partial(self._app_deployments_list, app_id), "deployments"
        )

    @api.post("apps/{app_id}", hint="deployment")
    def app_deployment_create(self, app_id: Text) -> AppDeployment:
        """
        Creating an app deployment will pull the latest changes from your
        repository and schedule a new deployment for your app.

        Parameters
        ----------
        app_id
            The app ID

        Returns
        -------
        The AppDeployment that was just created.
        """

    @api.get("apps/{app_id}/deployments/{deployment_id}")
    def app_deployment_get(self, app_id: Text, deployment_id: Text) -> AppDeployment:
        """
        Retrieve information about an app deployment.
        Parameters
        ----------
        app_id
            The app ID.
        deployment_id
            The deployment ID.

        Returns
        -------
        The requested deployment.
        """

    @api.post("apps/{app_id}/deployments/{deployment_id}/cancel")
    def app_deployment_cancel(self, app_id: Text, deployment_id: Text) -> AppDeployment:
        """
        Immediately cancel an in-progress deployment.

        Parameters
        ----------
        app_id
            The app ID.
        deployment_id
            The deployment ID.

        Returns
        -------
        The AppDeployment that was just cancelled.
        """
