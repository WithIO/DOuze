from typing import Text

from .models import RegistryRegion, Registry
from ..api import DoApi
from ..idem_api import DoIdemApi, Outcome


class RegistryIdemApi(DoIdemApi):
    def __init__(self, root: DoApi):
        super().__init__(root)

    def container_registry(self, name: Text, state: Text, subscription_slug: Text, region: RegistryRegion):
        reg = self.api.registry
        info = reg.registry()

        present = state == "present"
        absent = state == "absent"

        if info is None:
            if absent:
                return Outcome(changed=False)

            if not reg.validate_name(name):
                raise ValueError(f"{name} is not a valid name for a container registry")

            registry = reg.registry_create(name, subscription_slug, region)

            return Outcome(registry.name == name)

        else:
            if present and info.name == name:
                return Outcome(False)

            if absent:
                return Outcome(reg.registry_delete())

        return Outcome(False)
