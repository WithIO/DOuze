from douze.api import DoApi
from douze.idem_api import DoIdemApi


class UptimeIdemApi(DoIdemApi):
    def __init__(self, root: DoApi):
        super().__init__(root)
