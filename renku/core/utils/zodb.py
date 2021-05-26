import BTrees.OOBTree
import DirectoryStorage.Storage as DirStorage
import transaction
import zc.zlibstorage
import ZODB
from zope.generations.interfaces import ISchemaManager
from zope.generations.generations import SchemaManager
import zope.component
from zope.generations.generations import evolveMinimumSubscriber
from zope.component import globalregistry

gsm = globalregistry.getGlobalSiteManager()
gsm.unregisterUtility(provided=ISchemaManager, name="renku.core.utils.generations")


class dummy:
    def __init__(self, db):
        self.database = db


class ZODBConnectionHandler:
    connection = None

    @staticmethod
    def get_connection():
        if not ZODBConnectionHandler.connection:
            manager = SchemaManager(1, 1, "renku.core.utils.generations")
            zope.component.provideUtility(manager, ISchemaManager, name="renku.core.utils.generations")
            storage = zc.zlibstorage.ZlibStorage(DirStorage.Storage("./dirstore"))
            db = ZODB.DB(storage)
            d = dummy(db)
            # breakpoint()
            evolveMinimumSubscriber(d)
            ZODBConnectionHandler.connection = db.open()

        # breakpoint()
        return ZODBConnectionHandler.connection
