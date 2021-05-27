import BTrees.OOBTree
import DirectoryStorage.Storage as DirStorage
import transaction
import zc.zlibstorage
import ZODB
import zope.component
from zope.component import globalregistry
from zope.generations.generations import SchemaManager, evolveMinimumSubscriber
from zope.generations.interfaces import ISchemaManager

gsm = globalregistry.getGlobalSiteManager()
gsm.unregisterUtility(provided=ISchemaManager, name="renku.core.utils.generations")


class dummy:
    def __init__(self, db):
        self.database = db


class ZODBConnectionHandler:
    connection = None
    storage = None

    @staticmethod
    def get_connection():
        if not ZODBConnectionHandler.connection:
            manager = SchemaManager(0, 0, "renku.core.utils.generations")
            zope.component.provideUtility(manager, ISchemaManager, name="renku.core.utils.generations")
            if not ZODBConnectionHandler.storage:
                ZODBConnectionHandler.storage = zc.zlibstorage.ZlibStorage(DirStorage.Storage("./dirstore"))
            db = ZODB.DB(ZODBConnectionHandler.storage)
            d = dummy(db)
            # breakpoint()
            evolveMinimumSubscriber(d)
            ZODBConnectionHandler.connection = db.open()

        # breakpoint()
        return ZODBConnectionHandler.connection

    @staticmethod
    def close_storage():
        """Close storage -> force flush of journal."""
        if not ZODBConnectionHandler.storage:
            return
        ZODBConnectionHandler.storage.close()
        ZODBConnectionHandler.storage = None
