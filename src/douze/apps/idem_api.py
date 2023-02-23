from ..api import DoApi
from ..idem_api import DoIdemApi


class AppsIdemApi(DoIdemApi):

    def __init__(self, root: DoApi):
        super().__init__(root)
