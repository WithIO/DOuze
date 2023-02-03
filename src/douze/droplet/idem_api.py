from douze.idem_api import DoIdemApi


class DropletIdemApi(DoIdemApi):
    def __init__(self, root_api: DoIdemApi):
        super().__init__(root_api.api)
